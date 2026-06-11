"""Print random final-dataset samples for manual inspection."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample final labeled dataset rows.")
    parser.add_argument("--input", default="data/processed/final_labeled_dataset.csv")
    parser.add_argument("--class-name")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def first_code_lines(function_code: str, limit: int = 80) -> str:
    return "\n".join(function_code.splitlines()[:limit])


def matches_filters(row: dict[str, str], args: argparse.Namespace) -> bool:
    if args.class_name and row.get("final_class") != args.class_name:
        return False
    return True


def main() -> int:
    args = parse_args()
    input_path = resolve_repo_path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input CSV does not exist: {input_path}")
        return 1

    with input_path.open(newline="", encoding="utf-8") as file:
        rows = [row for row in csv.DictReader(file) if matches_filters(row, args)]

    rng = random.Random(args.seed)
    sample_size = min(args.n, len(rows))
    sampled_rows = rng.sample(rows, sample_size) if sample_size else []

    print(f"Rows matching filters: {len(rows)}")
    print(f"Samples printed: {len(sampled_rows)}")
    for index, row in enumerate(sampled_rows, start=1):
        print()
        print("=" * 80)
        print(f"Sample {index}")
        print(f"final_class: {row.get('final_class', '')}")
        print(f"final_label: {row.get('final_label', '')}")
        print(f"suggested_class: {row.get('suggested_class', '')}")
        print(f"sanity_check_status: {row.get('sanity_check_status', '')}")
        print(f"sanity_check_reason: {row.get('sanity_check_reason', '')}")
        print(f"binary_name: {row.get('binary_name', '')}")
        print(f"function_name: {row.get('function_name', '')}")
        print("-" * 80)
        print(first_code_lines(row.get("function_code", "")))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
