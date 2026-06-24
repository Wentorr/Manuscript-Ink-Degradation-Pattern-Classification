from pathlib import Path
import struct
import zlib

import numpy as np
import pandas as pd


LABELS = ["stable_ink", "feathering", "bleed_through", "abrasion", "salt_bloom"]
DIFFICULTY_TIERS = ["easy", "medium", "hard"]
VISUAL_VARIANTS = ["standard", "low_contrast", "foxed_noise", "scanner_jitter", "mixed_artifact"]


def _paper_background(rng, tone, gain):
    base = {
        "warm": np.array([222, 202, 166]),
        "neutral": np.array([214, 205, 184]),
        "cool": np.array([205, 207, 194]),
        "foxed": np.array([218, 196, 158]),
    }[tone].astype(float)
    noise = rng.normal(0, 9, (96, 96, 1))
    fiber = rng.normal(0, 5, (1, 96, 3)) + rng.normal(0, 4, (96, 1, 3))
    arr = base + noise + fiber
    if tone == "foxed":
        for _ in range(rng.integers(5, 12)):
            cx, cy = rng.integers(0, 96, 2)
            rr = rng.integers(3, 10)
            yy, xx = np.ogrid[:96, :96]
            mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= rr**2
            arr[mask] += np.array([18, -2, -18])
    arr = 128 + (arr - 128) * gain
    return np.clip(arr, 0, 255).astype(np.uint8)


def _draw_disk(arr, cx, cy, r, color):
    yy, xx = np.ogrid[: arr.shape[0], : arr.shape[1]]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r**2
    arr[mask] = color


def _draw_line(arr, p0, p1, width, color):
    x0, y0 = p0
    x1, y1 = p1
    steps = int(max(abs(x1 - x0), abs(y1 - y0), 1)) + 1
    for t in np.linspace(0, 1, steps):
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        _draw_disk(arr, x, y, max(1, width // 2), color)


def _draw_stroke(rng, arr, width, ink_rgb):
    y0 = int(rng.integers(35, 61))
    points = []
    for x in range(-8, 108, 8):
        y = y0 + int(10 * np.sin((x + rng.uniform(-5, 5)) / 23)) + int(rng.normal(0, 2))
        points.append((x, y))
    for p0, p1 in zip(points[:-1], points[1:]):
        _draw_line(arr, p0, p1, width, ink_rgb)
    return points


def _add_feathering(rng, arr, points, ink_rgb, strength):
    for x, y in points[1:-1]:
        for _ in range(int(7 + strength * 16)):
            angle = rng.choice([-1, 1]) * rng.uniform(0.45, 1.25)
            length = rng.uniform(6, 18) * strength
            x2 = x + np.cos(angle) * length
            y2 = y + np.sin(angle) * length
            col = np.clip(np.array(ink_rgb) + rng.integers(10, 45, 3), 0, 255).astype(np.uint8)
            _draw_line(arr, (x, y), (x2, y2), 1, col)


def _add_bleedthrough(rng, arr, points, strength):
    yy, xx = np.ogrid[:96, :96]
    for x, y in points:
        r = rng.uniform(6, 15) * strength
        mask = (xx - x) ** 2 + (yy - y) ** 2 <= r**2
        alpha = 0.14 + 0.18 * strength
        arr[mask] = (1 - alpha) * arr[mask] + alpha * np.array([116, 72, 42])


def _add_abrasion(rng, arr, points, strength):
    for _ in range(int(18 + 42 * strength)):
        x = int(rng.integers(8, 88))
        y = int(np.interp(x, [p[0] for p in points], [p[1] for p in points]) + rng.normal(0, 7))
        w = rng.integers(3, 9)
        col = np.clip(rng.normal([221, 205, 176], [8, 8, 8]), 0, 255).astype(np.uint8)
        _draw_disk(arr, x, y, w, col)


def _add_salt_bloom(rng, arr, points, strength):
    for _ in range(int(35 + 80 * strength)):
        x0, y0 = points[rng.integers(0, len(points))]
        x = int(np.clip(x0 + rng.normal(0, 14), 0, 95))
        y = int(np.clip(y0 + rng.normal(0, 12), 0, 95))
        r = rng.choice([1, 1, 2])
        val = int(rng.integers(220, 255))
        _draw_disk(arr, x, y, r, np.array([val, val, max(0, val - rng.integers(0, 18))], dtype=np.uint8))


def _box_blur(arr):
    padded = np.pad(arr, ((1, 1), (1, 1), (0, 0)), mode="edge")
    out = np.zeros_like(arr, dtype=float)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out += padded[1 + dy : 97 + dy, 1 + dx : 97 + dx]
    return out / 9.0


def _add_background_specks(rng, arr, density):
    for _ in range(int(80 * density)):
        x = int(rng.integers(0, 96))
        y = int(rng.integers(0, 96))
        r = int(rng.choice([1, 1, 1, 2]))
        if rng.random() < 0.65:
            val = int(rng.integers(210, 248))
            col = np.array([val, val - rng.integers(0, 12), val - rng.integers(5, 25)])
        else:
            val = int(rng.integers(95, 145))
            col = np.array([val + rng.integers(15, 35), val, max(0, val - rng.integers(10, 25))])
        _draw_disk(arr, x, y, r, np.clip(col, 0, 255).astype(np.uint8))


def _apply_variant(rng, arr, variant, difficulty):
    if variant == "low_contrast":
        arr[:] = 128 + (arr - 128) * rng.uniform(0.62, 0.78)
        arr[:] = arr + rng.normal(0, 5.0, arr.shape)
    elif variant == "foxed_noise":
        _add_background_specks(rng, arr, 1.15 if difficulty == "hard" else 0.75)
    elif variant == "scanner_jitter":
        shifted = arr.copy()
        shifted[:, :, 0] = np.roll(shifted[:, :, 0], int(rng.choice([-1, 1])), axis=1)
        shifted[:, :, 2] = np.roll(shifted[:, :, 2], int(rng.choice([-1, 1])), axis=0)
        band = np.sin(np.linspace(0, 7 * np.pi, 96))[:, None, None] * rng.uniform(2.5, 5.5)
        arr[:] = shifted + band
    elif variant == "mixed_artifact":
        _add_background_specks(rng, arr, 0.55)
        arr[:] = 0.82 * arr + 0.18 * _box_blur(arr)

    if difficulty == "hard":
        arr[:] = 0.72 * arr + 0.28 * _box_blur(arr)
        arr[:] = arr + rng.normal(0, 7.5, arr.shape)
    elif difficulty == "medium":
        arr[:] = arr + rng.normal(0, 4.0, arr.shape)


def _write_png(path, arr):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    h, w, _ = arr.shape
    raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def make_image(rng, label, tone, ink_family, width, gain, difficulty, variant):
    arr = _paper_background(rng, tone, gain).astype(float)
    ink = {
        "iron_gall": np.array([36, 30, 24]),
        "carbon": np.array([18, 18, 17]),
        "sepia": np.array([70, 42, 25]),
        "mixed": np.array([45, 36, 33]),
    }[ink_family]
    strength_ranges = {
        "easy": (0.85, 1.18),
        "medium": (0.48, 0.88),
        "hard": (0.24, 0.62),
    }
    strength = rng.uniform(*strength_ranges[difficulty])
    points = _draw_stroke(rng, arr, width, ink)
    edge_bleed = reverse = pigment_loss = 0.0
    if label == "feathering":
        _add_feathering(rng, arr, points, ink, strength)
        edge_bleed = strength
    elif label == "bleed_through":
        _add_bleedthrough(rng, arr, points, strength)
        reverse = strength
    elif label == "abrasion":
        _add_abrasion(rng, arr, points, strength)
        pigment_loss = strength
    elif label == "salt_bloom":
        _add_salt_bloom(rng, arr, points, strength)
        pigment_loss = 0.35 * strength

    confound_strength = {"easy": 0.0, "medium": rng.uniform(0.05, 0.12), "hard": rng.uniform(0.13, 0.26)}[
        difficulty
    ]
    if confound_strength:
        confounders = [name for name in LABELS if name not in {label, "stable_ink"}]
        for confounder in rng.choice(confounders, size=1 + int(difficulty == "hard"), replace=False):
            if confounder == "feathering":
                _add_feathering(rng, arr, points, ink, confound_strength)
                edge_bleed = max(edge_bleed, 0.35 * confound_strength)
            elif confounder == "bleed_through":
                _add_bleedthrough(rng, arr, points, confound_strength)
                reverse = max(reverse, 0.35 * confound_strength)
            elif confounder == "abrasion":
                _add_abrasion(rng, arr, points, confound_strength)
                pigment_loss = max(pigment_loss, 0.35 * confound_strength)
            elif confounder == "salt_bloom":
                _add_salt_bloom(rng, arr, points, confound_strength)
                pigment_loss = max(pigment_loss, 0.20 * confound_strength)

    _apply_variant(rng, arr, variant, difficulty)
    return np.clip(arr, 0, 255).astype(np.uint8), edge_bleed, reverse, pigment_loss


def main() -> None:
    rng = np.random.default_rng(53177)
    root = Path(__file__).resolve().parent
    image_dir = root / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for old_file in image_dir.glob("*.png"):
        old_file.unlink()
    n = 3000
    tones = ["warm", "neutral", "cool", "foxed"]
    inks = ["iron_gall", "carbon", "sepia", "mixed"]
    probs = np.array([0.24, 0.20, 0.18, 0.19, 0.19])
    for i in range(n):
        label = rng.choice(LABELS, p=probs)
        difficulty = rng.choice(DIFFICULTY_TIERS, p=[0.30, 0.43, 0.27])
        if difficulty == "easy":
            variant = rng.choice(["standard", "low_contrast"], p=[0.82, 0.18])
        elif difficulty == "medium":
            variant = rng.choice(VISUAL_VARIANTS, p=[0.40, 0.18, 0.18, 0.14, 0.10])
        else:
            variant = rng.choice(VISUAL_VARIANTS, p=[0.16, 0.23, 0.22, 0.19, 0.20])
        tone = rng.choice(tones, p=[0.34, 0.30, 0.18, 0.18])
        ink = rng.choice(inks, p=[0.38, 0.24, 0.24, 0.14])
        width = int(rng.integers(4, 10 if difficulty != "hard" else 8))
        gain = float(np.round(rng.uniform(0.86, 1.15), 3))
        img, edge, reverse, loss = make_image(rng, label, tone, ink, width, gain, difficulty, variant)
        sample_id = f"raw_ms_{i:05d}"
        filename = f"images/{sample_id}.png"
        _write_png(root / filename, img)
        rows.append(
            {
                "sample_id": sample_id,
                "image_path": filename,
                "parchment_tone": tone,
                "ink_family": ink,
                "stroke_width_px": width,
                "scan_gain": gain,
                "difficulty_tier": difficulty,
                "visual_variant": variant,
                "degradation_label": label,
                "edge_bleed_score": round(edge, 3),
                "reverse_showthrough_score": round(reverse, 3),
                "pigment_loss_score": round(loss, 3),
            }
        )
    pd.DataFrame(rows).to_csv(root / "data.csv", index=False)
    print(f"wrote {n} images and {root / 'data.csv'}")


if __name__ == "__main__":
    main()
