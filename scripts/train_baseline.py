"""Train and evaluate a TF-IDF + Logistic Regression baseline."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CLASS_NAMES = {
    "0": "Clean",
    "1": "Buffer Overflow",
    "2": "Format String",
    "3": "Integer Overflow",
}


def load_dependencies() -> bool:
    global LogisticRegression
    global Pipeline
    global TfidfVectorizer
    global accuracy_score
    global classification_report
    global confusion_matrix
    global f1_score
    global joblib
    global pd
    global plt
    global precision_recall_fscore_support

    try:
        import joblib
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            f1_score,
            precision_recall_fscore_support,
        )
        from sklearn.pipeline import Pipeline
    except ModuleNotFoundError as exc:
        missing_dependency = exc.name
        print(
            "ERROR: Missing Python dependency "
            f"{missing_dependency!r}. Install project dependencies with: "
            "python3 -m pip install -r requirements.txt"
        )
        return False

    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a TF-IDF + Logistic Regression baseline model."
    )
    parser.add_argument("--train", default="data/splits/train.csv")
    parser.add_argument("--val", default="data/splits/val.csv")
    parser.add_argument("--test", default="data/splits/test.csv")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--model-output", default="models/baseline_tfidf_logreg.joblib")
    parser.add_argument("--text-column", default="function_code")
    parser.add_argument("--label-column", default="final_label")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-features", type=int, default=50000)
    parser.add_argument("--ngram-min", type=int, default=1)
    parser.add_argument("--ngram-max", type=int, default=2)
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input CSV does not exist: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Input path is not a file: {path}")


def read_split(path: Path, text_column: str, label_column: str) -> pd.DataFrame:
    validate_input_file(path)
    data = pd.read_csv(path)

    missing_columns = [
        column for column in (text_column, label_column) if column not in data.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"{path} is missing required column(s): {missing}")

    data[text_column] = data[text_column].fillna("").astype(str)
    data[label_column] = data[label_column].astype(str)
    return data


def validate_args(args: argparse.Namespace) -> None:
    if args.max_features <= 0:
        raise ValueError("--max-features must be greater than zero")
    if args.ngram_min <= 0:
        raise ValueError("--ngram-min must be greater than zero")
    if args.ngram_max < args.ngram_min:
        raise ValueError("--ngram-max must be greater than or equal to --ngram-min")


def class_distribution(data: pd.DataFrame, label_column: str) -> Counter[str]:
    return Counter(data[label_column].astype(str).tolist())


def print_distribution(name: str, data: pd.DataFrame, label_column: str) -> None:
    print(f"{name}: {len(data)} rows")
    for label, count in sorted(class_distribution(data, label_column).items()):
        class_name = CLASS_NAMES.get(label, label)
        print(f"  {label} ({class_name}): {count}")


def build_pipeline(args: argparse.Namespace) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="word",
                    token_pattern=r"(?u)\b\w+\b",
                    lowercase=False,
                    ngram_range=(args.ngram_min, args.ngram_max),
                    max_features=args.max_features,
                    min_df=1,
                    max_df=0.95,
                ),
            ),
            (
                "logreg",
                LogisticRegression(
                    max_iter=2000,
                    class_weight=None,
                    solver="lbfgs",
                    random_state=args.seed,
                ),
            ),
        ]
    )


def evaluate(
    model: Pipeline,
    data: pd.DataFrame,
    text_column: str,
    label_column: str,
    labels: list[str],
) -> dict[str, Any]:
    y_true = data[label_column].astype(str)
    y_pred = model.predict(data[text_column])

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
    per_class = {
        label: {
            "class_name": CLASS_NAMES.get(label, label),
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(
            precision_recall_fscore_support(
                y_true, y_pred, average="macro", zero_division=0
            )[0]
        ),
        "macro_recall": float(
            precision_recall_fscore_support(
                y_true, y_pred, average="macro", zero_division=0
            )[1]
        ),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "per_class": per_class,
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=labels,
            target_names=[f"{label} = {CLASS_NAMES.get(label, label)}" for label in labels],
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels),
        "predictions": y_pred,
        "true_labels": y_true,
    }


def save_classification_report(
    output_path: Path,
    validation_metrics: dict[str, Any],
    test_metrics: dict[str, Any],
) -> None:
    lines = [
        "TF-IDF + Logistic Regression Baseline",
        "",
        "Label mapping:",
        "0 = Clean",
        "1 = Buffer Overflow",
        "2 = Format String",
        "3 = Integer Overflow",
        "",
        "Validation classification report:",
        validation_metrics["classification_report"],
        "",
        "Test classification report:",
        test_metrics["classification_report"],
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_confusion_matrix(
    output_path: Path,
    matrix: Any,
    labels: list[str],
) -> None:
    display_names = [f"{label}\n{CLASS_NAMES.get(label, label)}" for label in labels]
    figure, axis = plt.subplots(figsize=(8, 6))
    image = axis.imshow(matrix, interpolation="nearest", cmap="Blues")
    figure.colorbar(image, ax=axis)

    axis.set(
        xticks=range(len(labels)),
        yticks=range(len(labels)),
        xticklabels=display_names,
        yticklabels=display_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="Baseline Confusion Matrix - TF-IDF + Logistic Regression",
    )
    plt.setp(axis.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")

    threshold = matrix.max() / 2 if matrix.size else 0
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            axis.text(
                column_index,
                row_index,
                str(value),
                ha="center",
                va="center",
                color="white" if value > threshold else "black",
            )

    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def metrics_json(
    args: argparse.Namespace,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    labels: list[str],
    validation_metrics: dict[str, Any],
    test_metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "model_name": "TF-IDF + Logistic Regression",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "train_size": len(train),
        "validation_size": len(validation),
        "test_size": len(test),
        "validation_accuracy": validation_metrics["accuracy"],
        "validation_macro_f1": validation_metrics["macro_f1"],
        "test_accuracy": test_metrics["accuracy"],
        "test_macro_f1": test_metrics["macro_f1"],
        "test_weighted_f1": test_metrics["weighted_f1"],
        "class_names": {label: CLASS_NAMES.get(label, label) for label in labels},
        "validation_metrics": {
            "accuracy": validation_metrics["accuracy"],
            "macro_precision": validation_metrics["macro_precision"],
            "macro_recall": validation_metrics["macro_recall"],
            "macro_f1": validation_metrics["macro_f1"],
            "weighted_f1": validation_metrics["weighted_f1"],
            "per_class": validation_metrics["per_class"],
        },
        "test_metrics": {
            "accuracy": test_metrics["accuracy"],
            "macro_precision": test_metrics["macro_precision"],
            "macro_recall": test_metrics["macro_recall"],
            "macro_f1": test_metrics["macro_f1"],
            "weighted_f1": test_metrics["weighted_f1"],
            "per_class": test_metrics["per_class"],
        },
        "hyperparameters": {
            "tfidf": {
                "analyzer": "word",
                "token_pattern": r"(?u)\b\w+\b",
                "lowercase": False,
                "ngram_range": [args.ngram_min, args.ngram_max],
                "max_features": args.max_features,
                "min_df": 1,
                "max_df": 0.95,
            },
            "logistic_regression": {
                "max_iter": 2000,
                "class_weight": None,
                "solver": "lbfgs",
                "random_state": args.seed,
            },
        },
    }


def main() -> int:
    args = parse_args()
    if not load_dependencies():
        return 1

    try:
        validate_args(args)
        train_path = resolve_repo_path(args.train)
        val_path = resolve_repo_path(args.val)
        test_path = resolve_repo_path(args.test)
        output_dir = resolve_repo_path(args.output_dir)
        model_output = resolve_repo_path(args.model_output)

        train = read_split(train_path, args.text_column, args.label_column)
        validation = read_split(val_path, args.text_column, args.label_column)
        test = read_split(test_path, args.text_column, args.label_column)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    labels = sorted(train[args.label_column].astype(str).unique().tolist())

    print("Loaded splits:")
    print_distribution("Train", train, args.label_column)
    print_distribution("Validation", validation, args.label_column)
    print_distribution("Test", test, args.label_column)
    print()
    print("Training TF-IDF + Logistic Regression baseline...")

    model = build_pipeline(args)
    model.fit(train[args.text_column], train[args.label_column])

    validation_metrics = evaluate(
        model, validation, args.text_column, args.label_column, labels
    )
    test_metrics = evaluate(model, test, args.text_column, args.label_column, labels)

    output_dir.mkdir(parents=True, exist_ok=True)
    model_output.parent.mkdir(parents=True, exist_ok=True)

    metrics_path = output_dir / "baseline_metrics.json"
    report_path = output_dir / "baseline_classification_report.txt"
    confusion_matrix_path = output_dir / "baseline_confusion_matrix.png"

    metrics_payload = metrics_json(
        args=args,
        train=train,
        validation=validation,
        test=test,
        labels=labels,
        validation_metrics=validation_metrics,
        test_metrics=test_metrics,
    )
    metrics_path.write_text(
        json.dumps(metrics_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    save_classification_report(report_path, validation_metrics, test_metrics)
    save_confusion_matrix(
        confusion_matrix_path, test_metrics["confusion_matrix"], labels
    )
    joblib.dump(model, model_output)

    print()
    print("Validation metrics:")
    print(f"  Accuracy: {validation_metrics['accuracy']:.4f}")
    print(f"  Macro-F1: {validation_metrics['macro_f1']:.4f}")
    print()
    print("Test metrics:")
    print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  Macro-F1: {test_metrics['macro_f1']:.4f}")
    print(f"  Weighted-F1: {test_metrics['weighted_f1']:.4f}")
    print()
    print("Saved outputs:")
    print(f"  Metrics JSON: {metrics_path}")
    print(f"  Classification report: {report_path}")
    print(f"  Confusion matrix: {confusion_matrix_path}")
    print(f"  Model pipeline: {model_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
