"""Merge raw Ghidra extraction CSV files into one dataset file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = [
    "binary_name",
    "function_name",
    "function_address",
    "function_code",
    "decompile_status",
]
OUTPUT_COLUMNS = [*REQUIRED_COLUMNS, "source_csv"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge raw Ghidra CSV outputs.")
    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--output", default="data/processed/merged_raw_functions.csv")
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(missing)}")

        rows = []
        for row in reader:
            merged_row = {column: row.get(column, "") for column in REQUIRED_COLUMNS}
            merged_row["source_csv"] = relative_path(path)
            rows.append(merged_row)
        return rows


def main() -> int:
    args = parse_args()
    input_dir = resolve_repo_path(args.input_dir)
    output_path = resolve_repo_path(args.output)

    if not input_dir.exists():
        print(f"ERROR: Input directory does not exist: {input_dir}")
        return 1
    if not input_dir.is_dir():
        print(f"ERROR: Input path is not a directory: {input_dir}")
        return 1

    csv_files = sorted(input_dir.rglob("*.csv"))
    all_rows: list[dict[str, str]] = []

    for csv_path in csv_files:
        all_rows.extend(read_csv_rows(csv_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"CSV files read: {len(csv_files)}")
    print(f"Total rows merged: {len(all_rows)}")
    print(f"Output path: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
