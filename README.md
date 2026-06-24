# Manuscript Ink Degradation Pattern Classification

Complete Eris-style challenge package for a synthetic computer-vision task.

- `raw/generate_raw.py` creates deterministic synthetic manuscript image crops and `raw/data.csv`.
- `dataset_description_eris_upload.md` is the dataset description for Eris.
- `prepare.py` creates public/private splits and copies each image to an opaque public filename.
- `problem.md` is the solver-facing challenge statement.
- `grade.py` validates submissions and computes macro F1.
- `rubrics.yaml` contains task-specific rubric criteria.
- `solution.ipynb` and `reference_solution.py` provide a solvability baseline.

## Submission Mapping

Dataset upload:
- Title: `Synthetic Manuscript Ink Degradation Image Dataset`
- Description: paste `dataset_description_eris_upload.md`
- Data files: upload a zip containing top-level `data.csv`, `images/`, and `generate_raw.py`
- License: `CC0 1.0 Public Domain`

Challenge:
- Domain: `Computer Vision`
- Difficulty: `Medium`
- Title: `Manuscript Ink Degradation Pattern Classification`
- Grade direction: `Maximize`
- Min score: `0`
- Max score: `1`
- Problem description: paste `problem.md`
- Grading script: paste `grade.py`
- Prepare script: paste `prepare.py`
- Rubrics: use `rubrics.yaml`
- Reference solution: upload `solution.ipynb`

Reviewer-facing notes:
- The raw upload includes `generate_raw.py` so the synthetic source process is auditable.
- `prepare.py` remaps `sample_id` values and physically copies images to `public/images/ms_<hash>.png`, so public filenames no longer expose raw generation order.
- Private scoring includes hidden difficulty and rendering groups, making medium/hard cases and visual variants matter instead of plain easy-case macro F1.
