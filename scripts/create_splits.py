"""Create stratified train/validation/test splits from the final labeled dataset."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

try:
    import pandas as pd
    from sklearn.model_selection import train_test_split
except ModuleNotFoundError as exc:
    missing_dependency = exc.name
    print(
        "ERROR: Missing Python dependency "
        f"{missing_dependency!r}. Install project dependencies with: "
        "python3 -m pip install -r requirements.txt"
    )
    raise SystemExit(1) from exc


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create stratified train/validation/test CSV splits."
    )
    parser.add_argument("--input", default="data/processed/final_labeled_dataset.csv")
    parser.add_argument("--output-dir", default="data/splits")
    parser.add_argument("--train-size", type=float, default=0.70)
    parser.add_argument("--val-size", type=float, default=0.15)
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stratify-column", default="final_label")
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def validate_ratios(train_size: float, val_size: float, test_size: float) -> None:
    ratios = {
        "train-size": train_size,
        "val-size": val_size,
        "test-size": test_size,
    }
    for name, value in ratios.items():
        if value <= 0 or value >= 1:
            raise ValueError(f"--{name} must be greater than 0 and less than 1")

    total = train_size + val_size + test_size
    if abs(total - 1.0) > 1e-9:
        raise ValueError(
            "--train-size + --val-size + --test-size must equal 1.0 "
            f"(got {total:.6f})"
        )


def class_distribution(frame: pd.DataFrame, column: str) -> Counter[str]:
    return Counter(str(value) for value in frame[column].tolist())


def distribution_lines(frame: pd.DataFrame, column: str) -> list[str]:
    distribution = class_distribution(frame, column)
    total = len(frame)
    lines = []
    for class_value, count in sorted(distribution.items()):
        percent = (count / total * 100) if total else 0
        lines.append(f"- {class_value}: {count} ({percent:.2f}%)")
    return lines or ["- None"]


def split_dataset(
    data: pd.DataFrame,
    train_size: float,
    val_size: float,
    test_size: float,
    seed: int,
    stratify_column: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train, temp = train_test_split(
        data,
        train_size=train_size,
        random_state=seed,
        stratify=data[stratify_column],
        shuffle=True,
    )

    relative_val_size = val_size / (val_size + test_size)
    val, test = train_test_split(
        temp,
        train_size=relative_val_size,
        random_state=seed,
        stratify=temp[stratify_column],
        shuffle=True,
    )

    return (
        train.reset_index(drop=True),
        val.reset_index(drop=True),
        test.reset_index(drop=True),
    )


def write_summary(
    summary_path: Path,
    input_path: Path,
    output_paths: dict[str, Path],
    splits: dict[str, pd.DataFrame],
    train_size: float,
    val_size: float,
    test_size: float,
    seed: int,
    stratify_column: str,
) -> None:
    total_rows = sum(len(frame) for frame in splits.values())

    lines = [
        "# Split Summary",
        "",
        f"Input dataset: `{input_path}`",
        "",
        "## Output Paths",
        "",
        *[f"- {name}: `{path}`" for name, path in output_paths.items()],
        "",
        "## Configuration",
        "",
        f"- Train size: {train_size:.2f}",
        f"- Validation size: {val_size:.2f}",
        f"- Test size: {test_size:.2f}",
        f"- Random seed: {seed}",
        f"- Stratify column: `{stratify_column}`",
        "",
        f"Total rows: {total_rows}",
        "",
        "## Split Distributions",
        "",
    ]

    for name, frame in splits.items():
        split_percent = (len(frame) / total_rows * 100) if total_rows else 0
        lines.extend(
            [
                f"### {name.title()}",
                "",
                f"- Rows: {len(frame)} ({split_percent:.2f}% of dataset)",
                "- Class distribution:",
                *distribution_lines(frame, stratify_column),
                "",
            ]
        )

    lines.extend(
        [
            "## Notes",
            "",
            "- This is a stratified split, so class proportions are preserved across train, validation, and test files.",
            "- Limitation: this split is stratified by class, but not fully group-aware by binary or testcase family unless implemented later.",
        ]
    )

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_split_summary(splits: dict[str, pd.DataFrame], stratify_column: str) -> None:
    total_rows = sum(len(frame) for frame in splits.values())
    print(f"Total rows: {total_rows}")
    for name, frame in splits.items():
        split_percent = (len(frame) / total_rows * 100) if total_rows else 0
        print()
        print(f"{name.title()}: {len(frame)} rows ({split_percent:.2f}%)")
        print("Class distribution:")
        for line in distribution_lines(frame, stratify_column):
            print(f"  {line[2:] if line.startswith('- ') else line}")


def main() -> int:
    args = parse_args()
    input_path = resolve_repo_path(args.input)
    output_dir = resolve_repo_path(args.output_dir)

    if not input_path.exists():
        print(f"ERROR: Input CSV does not exist: {input_path}")
        return 1

    try:
        validate_ratios(args.train_size, args.val_size, args.test_size)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    data = pd.read_csv(input_path)
    if args.stratify_column not in data.columns:
        print(f"ERROR: Stratify column does not exist: {args.stratify_column}")
        return 1

    try:
        train, val, test = split_dataset(
            data=data,
            train_size=args.train_size,
            val_size=args.val_size,
            test_size=args.test_size,
            seed=args.seed,
            stratify_column=args.stratify_column,
        )
    except ValueError as exc:
        print(f"ERROR: Could not create stratified split: {exc}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "train": output_dir / "train.csv",
        "validation": output_dir / "val.csv",
        "test": output_dir / "test.csv",
    }
    splits = {
        "train": train,
        "validation": val,
        "test": test,
    }

    for name, frame in splits.items():
        frame.to_csv(output_paths[name], index=False)

    summary_path = output_dir / "split_summary.md"
    write_summary(
        summary_path=summary_path,
        input_path=input_path,
        output_paths=output_paths,
        splits=splits,
        train_size=args.train_size,
        val_size=args.val_size,
        test_size=args.test_size,
        seed=args.seed,
        stratify_column=args.stratify_column,
    )

    print_split_summary(splits, args.stratify_column)
    print()
    print(f"Wrote train split: {output_paths['train']}")
    print(f"Wrote validation split: {output_paths['validation']}")
    print(f"Wrote test split: {output_paths['test']}")
    print(f"Wrote summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
