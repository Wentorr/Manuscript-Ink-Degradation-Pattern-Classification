from pathlib import Path
import hashlib
import shutil

import pandas as pd


ID_COLUMN = "sample_id"
TARGET_COLUMN = "degradation_label"
LEAKAGE_COLUMNS = ["edge_bleed_score", "reverse_showthrough_score", "pigment_loss_score"]
HIDDEN_GROUP_COLUMNS = ["difficulty_tier", "visual_variant"]
PUBLIC_METADATA_COLUMNS = ["parchment_tone", "ink_family", "stroke_width_px", "scan_gain"]


def _stable_public_id(raw_id: str) -> str:
    digest = hashlib.sha256(f"eris-manuscript-ink-v1::{raw_id}".encode("utf-8")).hexdigest()
    return f"ms_{digest[:12]}"


def _shuffle(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _split_key(raw_id: str) -> int:
    digest = hashlib.sha256(f"eris-manuscript-ink-split-v2::{raw_id}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _stroke_width_bin(width: int) -> str:
    if width <= 5:
        return "thin"
    if width <= 7:
        return "medium"
    return "wide"


def _copy_images_with_public_ids(raw: Path, public: Path, frame: pd.DataFrame) -> pd.DataFrame:
    src_root = raw
    dst = public / "images"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    frame = frame.copy()
    public_ids = frame[ID_COLUMN].astype(str).map(_stable_public_id)
    new_paths = []
    for old_path, new_id in zip(frame["image_path"].astype(str), public_ids):
        src = src_root / old_path
        if not src.exists():
            raise ValueError(f"missing image referenced by data.csv: {old_path}")
        new_path = f"images/{new_id}.png"
        shutil.copy2(src, public / new_path)
        new_paths.append(new_path)

    frame[ID_COLUMN] = public_ids
    frame["image_path"] = new_paths
    return frame


def _find_raw_root(raw: Path) -> Path:
    if (raw / "data.csv").exists():
        return raw
    matches = sorted(raw.rglob("data.csv"))
    if not matches:
        raise ValueError(
            "data.csv was not found in the raw dataset upload. Upload a zip with data.csv, images/, "
            "and generate_raw.py at the top level."
        )
    return matches[0].parent


def _make_test_mask(data: pd.DataFrame) -> pd.Series:
    keys = data[ID_COLUMN].astype(str).map(_split_key)
    difficulty_fraction = {"easy": 0.12, "medium": 0.28, "hard": 0.46}
    mask = pd.Series(False, index=data.index)
    for (_, difficulty), group in data.groupby([TARGET_COLUMN, "difficulty_tier"], sort=False):
        fraction = difficulty_fraction[difficulty]
        take = max(1, int(round(len(group) * fraction)))
        ordered = group.assign(_key=keys.loc[group.index]).sort_values("_key")
        mask.loc[ordered.head(take).index] = True
    return mask


def prepare(raw: Path, public: Path, private: Path) -> None:
    """Create deterministic public/private image classification splits."""
    raw_root = _find_raw_root(raw)
    data = pd.read_csv(raw_root / "data.csv")
    required = {
        ID_COLUMN,
        "image_path",
        TARGET_COLUMN,
        *PUBLIC_METADATA_COLUMNS,
        *LEAKAGE_COLUMNS,
        *HIDDEN_GROUP_COLUMNS,
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"raw data missing required columns: {sorted(missing)}")

    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    data = data.sort_values(ID_COLUMN).reset_index(drop=True)
    data["stroke_width_bin"] = data["stroke_width_px"].map(_stroke_width_bin)
    data = _copy_images_with_public_ids(raw_root, public, data)
    test_mask = _make_test_mask(data)

    public_drop = LEAKAGE_COLUMNS + HIDDEN_GROUP_COLUMNS + ["stroke_width_bin"]
    train = data.loc[~test_mask].drop(columns=public_drop).reset_index(drop=True)
    test_full = data.loc[test_mask].drop(columns=LEAKAGE_COLUMNS).reset_index(drop=True)

    private_columns = [
        ID_COLUMN,
        TARGET_COLUMN,
        "difficulty_tier",
        "visual_variant",
        "parchment_tone",
        "ink_family",
        "stroke_width_bin",
    ]
    answers = test_full[private_columns].copy()
    test = test_full.drop(columns=[TARGET_COLUMN, *HIDDEN_GROUP_COLUMNS, "stroke_width_bin"])
    sample = pd.DataFrame({ID_COLUMN: test[ID_COLUMN], TARGET_COLUMN: "stable_ink"})

    _shuffle(train, 171).to_csv(public / "train.csv", index=False)
    _shuffle(test, 272).to_csv(public / "test.csv", index=False)
    _shuffle(sample, 272).to_csv(public / "sample_submission.csv", index=False)
    _shuffle(answers, 373).to_csv(private / "answers.csv", index=False)
