# Manuscript Ink Degradation Pattern Classification

Complete Eris-style challenge package for a synthetic computer-vision task.

- `raw/generate_raw.py` creates deterministic synthetic manuscript image crops and `raw/data.csv`.
- `dataset_description_eris_upload.md` is the dataset description for Eris.
- `prepare.py` creates public/private splits and copies images.
- `problem.md` is the solver-facing challenge statement.
- `grade.py` validates submissions and computes macro F1.
- `rubrics.yaml` contains task-specific rubric criteria.
- `solution.ipynb` and `reference_solution.py` provide a solvability baseline.

## Submission Mapping

Dataset upload:
- Title: `Synthetic Manuscript Ink Degradation Image Dataset`
- Description: paste `dataset_description_eris_upload.md`
- Data files: upload a zip containing top-level `data.csv` and `images/`
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

