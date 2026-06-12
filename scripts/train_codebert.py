"""Fine-tune CodeBERT for multiclass vulnerability classification."""

from __future__ import annotations

import argparse
import inspect
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ID2LABEL = {
    0: "Clean",
    1: "Buffer Overflow",
    2: "Format String",
    3: "Integer Overflow",
}
LABEL2ID = {label: index for index, label in ID2LABEL.items()}
LABEL_IDS = sorted(ID2LABEL)


def load_dependencies() -> bool:
    global AutoModelForSequenceClassification
    global AutoTokenizer
    global Trainer
    global TrainingArguments
    global accuracy_score
    global classification_report
    global confusion_matrix
    global f1_score
    global matplotlib
    global np
    global pd
    global plt
    global precision_recall_fscore_support
    global set_seed
    global torch

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import torch
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            f1_score,
            precision_recall_fscore_support,
        )
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
            set_seed,
        )
    except ModuleNotFoundError as exc:
        print(
            "ERROR: Missing Python dependency "
            f"{exc.name!r}. Install project dependencies with: "
            "python -m pip install -r requirements.txt"
        )
        return False

    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune microsoft/codebert-base for 4-class vulnerability classification."
    )
    parser.add_argument("--train", default="data/splits/train.csv")
    parser.add_argument("--val", default="data/splits/val.csv")
    parser.add_argument("--test", default="data/splits/test.csv")
    parser.add_argument("--model-name", default="microsoft/codebert-base")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--model-output-dir", default="models/codebert-final")
    parser.add_argument("--text-column", default="function_code")
    parser.add_argument("--label-column", default="final_label")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--train-batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def validate_args(args: argparse.Namespace) -> None:
    if args.max_length <= 0:
        raise ValueError("--max-length must be greater than zero")
    if args.epochs <= 0:
        raise ValueError("--epochs must be greater than zero")
    if args.train_batch_size <= 0:
        raise ValueError("--train-batch-size must be greater than zero")
    if args.eval_batch_size <= 0:
        raise ValueError("--eval-batch-size must be greater than zero")
    if args.learning_rate <= 0:
        raise ValueError("--learning-rate must be greater than zero")
    if args.weight_decay < 0:
        raise ValueError("--weight-decay must be zero or greater")


def validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input CSV does not exist: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Input path is not a file: {path}")


def read_split(path: Path, text_column: str, label_column: str) -> Any:
    validate_input_file(path)
    data = pd.read_csv(path)

    missing_columns = [
        column for column in (text_column, label_column) if column not in data.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"{path} is missing required column(s): {missing}")

    data[text_column] = data[text_column].fillna("").astype(str)
    data[label_column] = data[label_column].astype(int)

    invalid_labels = sorted(set(data[label_column].tolist()) - set(LABEL_IDS))
    if invalid_labels:
        raise ValueError(f"{path} contains unsupported label id(s): {invalid_labels}")

    return data


def class_distribution(data: Any, label_column: str) -> Counter[int]:
    return Counter(int(label) for label in data[label_column].tolist())


def print_distribution(name: str, data: Any, label_column: str) -> None:
    print(f"{name}: {len(data)} rows")
    for label_id, count in sorted(class_distribution(data, label_column).items()):
        print(f"  {label_id} ({ID2LABEL[label_id]}): {count}")


class CodeDataset:
    def __init__(self, encodings: dict[str, Any], labels: list[int]) -> None:
        self.encodings = encodings
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, Any]:
        item = {
            key: torch.tensor(value[index])
            for key, value in self.encodings.items()
        }
        item["labels"] = torch.tensor(self.labels[index], dtype=torch.long)
        return item


def tokenize_dataset(tokenizer: Any, data: Any, text_column: str, label_column: str, max_length: int) -> CodeDataset:
    encodings = tokenizer(
        data[text_column].tolist(),
        truncation=True,
        padding="max_length",
        max_length=max_length,
    )
    labels = [int(label) for label in data[label_column].tolist()]
    return CodeDataset(encodings, labels)


def metric_dict(y_true: Any, y_pred: Any) -> dict[str, float]:
    precision, recall, _, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=LABEL_IDS,
        average="macro",
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
    }


def compute_metrics(eval_prediction: Any) -> dict[str, float]:
    if hasattr(eval_prediction, "predictions"):
        logits = eval_prediction.predictions
        labels = eval_prediction.label_ids
    else:
        logits, labels = eval_prediction
    predictions = np.argmax(logits, axis=-1)
    return metric_dict(labels, predictions)


def trainer_arguments_kwargs(args: argparse.Namespace, checkpoint_dir: Path) -> dict[str, Any]:
    kwargs = {
        "output_dir": str(checkpoint_dir),
        "num_train_epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "per_device_train_batch_size": args.train_batch_size,
        "per_device_eval_batch_size": args.eval_batch_size,
        "weight_decay": args.weight_decay,
        "seed": args.seed,
        "save_strategy": "epoch",
        "load_best_model_at_end": True,
        "metric_for_best_model": "macro_f1",
        "greater_is_better": True,
        "logging_strategy": "epoch",
        "save_total_limit": 2,
        "report_to": "none",
    }

    signature = inspect.signature(TrainingArguments.__init__)
    if "eval_strategy" in signature.parameters:
        kwargs["eval_strategy"] = "epoch"
    else:
        kwargs["evaluation_strategy"] = "epoch"

    return kwargs


def classification_report_text(y_true: Any, y_pred: Any) -> str:
    return classification_report(
        y_true,
        y_pred,
        labels=LABEL_IDS,
        target_names=[f"{label_id} = {ID2LABEL[label_id]}" for label_id in LABEL_IDS],
        zero_division=0,
    )


def save_classification_report(
    output_path: Path,
    validation_report: str,
    test_report: str,
) -> None:
    lines = [
        "CodeBERT Fine-Tuning Classification Report",
        "",
        "Label mapping:",
        "0 = Clean",
        "1 = Buffer Overflow",
        "2 = Format String",
        "3 = Integer Overflow",
        "",
        "Validation classification report:",
        validation_report,
        "",
        "Test classification report:",
        test_report,
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_confusion_matrix(output_path: Path, matrix: Any) -> None:
    display_names = [f"{label_id}\n{ID2LABEL[label_id]}" for label_id in LABEL_IDS]
    figure, axis = plt.subplots(figsize=(8, 6))
    image = axis.imshow(matrix, interpolation="nearest", cmap="Blues")
    figure.colorbar(image, ax=axis)

    axis.set(
        xticks=range(len(LABEL_IDS)),
        yticks=range(len(LABEL_IDS)),
        xticklabels=display_names,
        yticklabels=display_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="CodeBERT Confusion Matrix",
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


def prediction_labels(prediction_output: Any) -> tuple[Any, Any]:
    y_true = prediction_output.label_ids
    y_pred = np.argmax(prediction_output.predictions, axis=-1)
    return y_true, y_pred


def metrics_payload(
    args: argparse.Namespace,
    train_size: int,
    val_size: int,
    test_size: int,
    validation_metrics: dict[str, float],
    test_metrics: dict[str, float],
    device_name: str,
    gpu_name: str | None,
) -> dict[str, Any]:
    return {
        "model_name": args.model_name,
        "task": "multiclass sequence classification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "train_size": train_size,
        "validation_size": val_size,
        "test_size": test_size,
        "validation_accuracy": validation_metrics["accuracy"],
        "validation_macro_f1": validation_metrics["macro_f1"],
        "test_accuracy": test_metrics["accuracy"],
        "test_macro_f1": test_metrics["macro_f1"],
        "test_weighted_f1": test_metrics["weighted_f1"],
        "class_names": {str(label_id): label for label_id, label in ID2LABEL.items()},
        "hyperparameters": {
            "max_length": args.max_length,
            "epochs": args.epochs,
            "train_batch_size": args.train_batch_size,
            "eval_batch_size": args.eval_batch_size,
            "learning_rate": args.learning_rate,
            "weight_decay": args.weight_decay,
            "seed": args.seed,
        },
        "device_used": device_name,
        "gpu_name": gpu_name,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
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
        model_output_dir = resolve_repo_path(args.model_output_dir)

        train = read_split(train_path, args.text_column, args.label_column)
        validation = read_split(val_path, args.text_column, args.label_column)
        test = read_split(test_path, args.text_column, args.label_column)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    set_seed(args.seed)

    cuda_available = torch.cuda.is_available()
    device_name = "cuda" if cuda_available else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else None

    print(f"Selected device: {device_name}")
    if cuda_available:
        print(f"GPU: {gpu_name}")
    else:
        print("WARNING: CUDA is not available. CPU training will be much slower.")
    print()
    print("Loaded splits:")
    print_distribution("Train", train, args.label_column)
    print_distribution("Validation", validation, args.label_column)
    print_distribution("Test", test, args.label_column)
    print()
    print(f"Model: {args.model_name}")
    print(f"Max length: {args.max_length}")
    print(f"Train batch size: {args.train_batch_size}")
    print(f"Eval batch size: {args.eval_batch_size}")
    print(f"Epochs: {args.epochs}")
    print(f"Learning rate: {args.learning_rate}")

    output_dir.mkdir(parents=True, exist_ok=True)
    model_output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output_dir / "codebert_checkpoints"

    print()
    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=4,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    train_dataset = tokenize_dataset(
        tokenizer, train, args.text_column, args.label_column, args.max_length
    )
    validation_dataset = tokenize_dataset(
        tokenizer, validation, args.text_column, args.label_column, args.max_length
    )
    test_dataset = tokenize_dataset(
        tokenizer, test, args.text_column, args.label_column, args.max_length
    )

    training_args = TrainingArguments(
        **trainer_arguments_kwargs(args, checkpoint_dir)
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    print()
    print("Starting CodeBERT fine-tuning...")
    trainer.train()

    print()
    print("Evaluating best model on validation and test sets...")
    validation_prediction = trainer.predict(validation_dataset)
    test_prediction = trainer.predict(test_dataset)
    validation_true, validation_pred = prediction_labels(validation_prediction)
    test_true, test_pred = prediction_labels(test_prediction)
    validation_metrics = metric_dict(validation_true, validation_pred)
    test_metrics = metric_dict(test_true, test_pred)

    metrics_path = output_dir / "codebert_metrics.json"
    report_path = output_dir / "codebert_classification_report.txt"
    confusion_matrix_path = output_dir / "codebert_confusion_matrix.png"

    metrics_path.write_text(
        json.dumps(
            metrics_payload(
                args=args,
                train_size=len(train),
                val_size=len(validation),
                test_size=len(test),
                validation_metrics=validation_metrics,
                test_metrics=test_metrics,
                device_name=device_name,
                gpu_name=gpu_name,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    save_classification_report(
        report_path,
        classification_report_text(validation_true, validation_pred),
        classification_report_text(test_true, test_pred),
    )
    save_confusion_matrix(
        confusion_matrix_path,
        confusion_matrix(test_true, test_pred, labels=LABEL_IDS),
    )

    trainer.save_model(str(model_output_dir))
    tokenizer.save_pretrained(str(model_output_dir))

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
    print(f"  Final model and tokenizer: {model_output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
