# Manuscript Ink Degradation Pattern Classification

## Overview

Conservation teams often inspect manuscript ink under magnification to identify visible degradation patterns before deciding how to store, digitize, or treat a page. Your task is to classify each synthetic manuscript crop into the dominant ink degradation pattern visible in the image.

The dataset contains generated 96x96 PNG crops of ink strokes on textured paper. Each image belongs to one of five labels: `stable_ink`, `feathering`, `bleed_through`, `abrasion`, or `salt_bloom`. The images include variation in substrate tone, scanner gain, ink family, stroke width, local noise, and artifact intensity.

## Evaluation

Submissions are evaluated using a robust macro F1 score. The score combines overall macro F1 across the five classes with worst-group macro F1 over hidden difficulty and rendering groups:

`score = 0.50 * macro_f1_all + 0.20 * worst_macro_f1_by_difficulty + 0.12 * worst_macro_f1_by_visual_variant + 0.08 * worst_macro_f1_by_ink_family + 0.05 * worst_macro_f1_by_parchment_tone + 0.05 * worst_macro_f1_by_stroke_width_bin`

Scores are maximized and range from 0 to 1. This metric rewards solutions that perform well on all labels and remain robust on subtle hard examples, low-contrast scans, foxed paper, scanner jitter, mixed artifacts, ink families, and stroke widths. Invalid submissions, missing rows, duplicate IDs, unknown labels, or malformed columns will raise a grading error.

## Dataset

The prepared public data contains:

| File or Folder | Description |
|---|---|
| `train.csv` | Labeled training images with `sample_id`, `image_path`, metadata, and `degradation_label`. |
| `test.csv` | Unlabeled images with `sample_id`, `image_path`, and metadata. |
| `sample_submission.csv` | Example submission with the required columns. |
| `images/` | PNG image files referenced by `image_path`. |

## Columns

| Column | Type | Present In | Description |
|---|---:|---|---|
| `sample_id` | string | train, test, submission | Opaque image identifier. |
| `image_path` | string | train, test | Relative path to the PNG crop. |
| `parchment_tone` | string | train, test | Simulated paper tone: warm, neutral, cool, or foxed. |
| `ink_family` | string | train, test | Simulated ink family: iron_gall, carbon, sepia, or mixed. |
| `stroke_width_px` | int | train, test | Approximate intended stroke width. |
| `scan_gain` | float | train, test | Simulated scanner brightness gain. |
| `degradation_label` | string | train only | Target class. |

## Labels

| Label | Description |
|---|---|
| `stable_ink` | Coherent dark ink stroke with limited haloing. |
| `feathering` | Fine branching fibers and fuzzy edge spread. |
| `bleed_through` | Brown reverse-side show-through patches around the stroke. |
| `abrasion` | Broken or scraped stroke with missing pigment gaps. |
| `salt_bloom` | Pale crystalline speckles or haze near the ink. |

## Modeling Considerations

Strong solutions should inspect the image pixels, not rely only on metadata. Useful cues include edge fuzziness, halo color, local contrast, dark-pixel continuity, pale speckle density, and show-through patches.

Metadata such as `parchment_tone`, `ink_family`, `stroke_width_px`, and `scan_gain` can help normalize visual appearance, but these fields should not replace image analysis.

The classes are intentionally related. For example, `feathering` and `bleed_through` can both create halos, while `abrasion` and `salt_bloom` can both introduce light regions. Models should distinguish these using spatial texture and color patterns.

The private test set is intentionally richer in medium and hard examples than a random sample. A solution that only learns obvious easy cases or memorizes public metadata should underperform on the hidden difficulty groups.

## Submission

Submit a CSV file named `submission.csv` with exactly these columns:

| Column | Type | Description |
|---|---:|---|
| `sample_id` | string | Row identifier from `test.csv`. |
| `degradation_label` | string | Predicted label. |

Valid labels are:

- `stable_ink`
- `feathering`
- `bleed_through`
- `abrasion`
- `salt_bloom`

Example:

| sample_id | degradation_label |
|---|---|
| ms_a1b2c3d4e5f6 | feathering |
| ms_0f9e8d7c6b5a | stable_ink |
| ms_112233445566 | salt_bloom |

Requirements:

- Must contain exactly one row for every row in `test.csv`.
- Must include a header row.
- Must not include duplicate or missing `sample_id` values.
- Predictions must be one of the five valid labels.
- Do not use private labels, post-generation diagnostic leakage columns, external image datasets, pretrained models, or internet access.
