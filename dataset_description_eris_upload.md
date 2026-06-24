# Dataset Description

## Overview

This synthetic dataset contains small image crops that imitate conservation microscopy views of ink on aged manuscript paper. Each image shows a short ink stroke or mark with one dominant degradation pattern. The task is to recognize the visual degradation class from the image.

The dataset is fully synthetic and was generated with the included deterministic script `generate_raw.py`. It contains no real manuscript scans, cultural-heritage collection images, institutional data, or copyrighted source imagery.

The generator explicitly creates easy, medium, and hard examples. Easy cases have clear degradation cues, medium cases include scanner variation or light confounders, and hard cases combine subtle primary artifacts with low contrast, foxing, jitter, or secondary weak artifacts. This avoids making the task depend only on obvious synthetic signals.

## File Structure

| File or Folder | Rows / Files | Description |
|---|---:|---|
| `data.csv` | 3,000 rows | One row per synthetic manuscript crop. Contains a raw `sample_id`, relative `image_path`, degradation label, simulated material context, difficulty metadata, and post-generation diagnostic columns that are removed during challenge preparation. |
| `images/` | 3,000 PNG files | Synthetic 96x96 image crops of ink strokes on textured paper. Filenames match `image_path` values in `data.csv`. |
| `generate_raw.py` | 1 file | Deterministic generator used to create `data.csv` and all PNG image crops. |

The challenge preparation script removes post-generation leakage fields, remaps raw sample IDs to opaque IDs, copies every image into the public folder under the new opaque filename, shuffles rows, and creates public `train.csv`, public `test.csv`, `sample_submission.csv`, and private `answers.csv`.

## Features

| Column | Type | Description |
|---|---:|---|
| sample_id | string | Unique raw image identifier. |
| image_path | string | Relative path to the PNG image crop. |
| parchment_tone | string | Simulated substrate tone: warm, neutral, cool, or foxed. |
| ink_family | string | Simulated ink family: iron_gall, carbon, sepia, or mixed. |
| stroke_width_px | int | Approximate intended stroke width. |
| scan_gain | float | Simulated scanner brightness gain. |
| difficulty_tier | string | Generator-only tier: easy, medium, or hard. Removed from public files and retained privately for robust evaluation. |
| visual_variant | string | Generator-only rendering variant such as low_contrast, foxed_noise, scanner_jitter, or mixed_artifact. Removed from public files and retained privately for robust evaluation. |
| degradation_label | string | Target class. One of stable_ink, feathering, bleed_through, abrasion, salt_bloom. |
| edge_bleed_score | float | Post-generation diagnostic leakage column removed before solving. |
| reverse_showthrough_score | float | Post-generation diagnostic leakage column removed before solving. |
| pigment_loss_score | float | Post-generation diagnostic leakage column removed before solving. |

## Class Meanings

| Label | Visual Pattern |
|---|---|
| stable_ink | Dark, coherent ink stroke with limited haloing or damage. |
| feathering | Fine branching fibers and fuzzy edges radiating from the ink stroke. |
| bleed_through | Brownish reverse-side show-through patches around or beneath the stroke. |
| abrasion | Broken or scraped ink with pale gaps and missing pigment. |
| salt_bloom | Light crystalline speckles or haze near the ink. |

## License and Source

License: CC0 1.0 Public Domain.

Source: Synthetic dataset generated locally with a deterministic script and fixed random seed. No external image source data was used.
