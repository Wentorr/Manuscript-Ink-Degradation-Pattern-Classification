import numpy as np
import pandas as pd


ID_COLUMN = "sample_id"
TARGET_COLUMN = "degradation_label"
VALID_LABELS = {"stable_ink", "feathering", "bleed_through", "abrasion", "salt_bloom"}
GROUP_COLUMNS = ["difficulty_tier", "visual_variant", "ink_family", "parchment_tone", "stroke_width_bin"]


def _macro_f1(y_true: pd.Series, y_pred: pd.Series, labels=None) -> float:
    scores = []
    if labels is None:
        labels = sorted(VALID_LABELS)
    for label in sorted(labels):
        true_pos = ((y_true == label) & (y_pred == label)).sum()
        false_pos = ((y_true != label) & (y_pred == label)).sum()
        false_neg = ((y_true == label) & (y_pred != label)).sum()
        precision = true_pos / (true_pos + false_pos) if true_pos + false_pos else 0.0
        recall = true_pos / (true_pos + false_neg) if true_pos + false_neg else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores.append(f1)
    return float(np.mean(scores))


def _worst_group_macro_f1(aligned: pd.DataFrame, group_column: str) -> float:
    scores = []
    for _, group in aligned.groupby(group_column):
        labels = sorted(set(group[f"{TARGET_COLUMN}_true"]))
        if labels:
            scores.append(_macro_f1(group[f"{TARGET_COLUMN}_true"], group[f"{TARGET_COLUMN}_pred"], labels=labels))
    return float(min(scores)) if scores else 0.0


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    expected_columns = [ID_COLUMN, TARGET_COLUMN]
    required_answer_columns = {ID_COLUMN, TARGET_COLUMN, *GROUP_COLUMNS}
    if list(submission.columns) != expected_columns:
        raise Exception(f"submission must contain exactly: {ID_COLUMN}, {TARGET_COLUMN}")
    missing_answer_columns = required_answer_columns.difference(answers.columns)
    if missing_answer_columns:
        raise Exception(f"answers missing required columns: {sorted(missing_answer_columns)}")
    if submission[ID_COLUMN].isna().any():
        raise Exception(f"submission contains missing {ID_COLUMN} values")
    if submission[ID_COLUMN].duplicated().any():
        raise Exception(f"submission contains duplicate {ID_COLUMN} values")
    if set(submission[ID_COLUMN]) != set(answers[ID_COLUMN]):
        raise Exception("submission sample_id values must exactly match the private test IDs")
    if submission[TARGET_COLUMN].isna().any():
        raise Exception("submission contains missing labels")
    unknown = set(submission[TARGET_COLUMN]) - VALID_LABELS
    if unknown:
        raise Exception(f"submission contains unknown labels: {sorted(unknown)}")

    aligned = submission.merge(answers, on=ID_COLUMN, suffixes=("_pred", "_true"), validate="one_to_one")
    overall = _macro_f1(aligned[f"{TARGET_COLUMN}_true"], aligned[f"{TARGET_COLUMN}_pred"])
    difficulty = _worst_group_macro_f1(aligned, "difficulty_tier")
    variant = _worst_group_macro_f1(aligned, "visual_variant")
    ink = _worst_group_macro_f1(aligned, "ink_family")
    tone = _worst_group_macro_f1(aligned, "parchment_tone")
    width = _worst_group_macro_f1(aligned, "stroke_width_bin")
    score = 0.50 * overall + 0.20 * difficulty + 0.12 * variant + 0.08 * ink + 0.05 * tone + 0.05 * width
    return float(np.clip(score, 0.0, 1.0))
