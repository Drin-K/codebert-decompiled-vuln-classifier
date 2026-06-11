"""Print concise statistics for a cleaned function dataset."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print cleaned dataset statistics.")
    parser.add_argument("--input", default="data/processed/clean_functions.csv")
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def infer_cwe(row: dict[str, str]) -> str:
    text = " ".join(
        [
            row.get("binary_name", ""),
            row.get("source_csv", ""),
        ]
    )
    for cwe in ("CWE121", "CWE122", "CWE134", "CWE190"):
        if cwe in text:
            return cwe
    return "unknown"


def main() -> int:
    args = parse_args()
    input_path = resolve_repo_path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input CSV does not exist: {input_path}")
        return 1

    with input_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    binaries = Counter(row.get("binary_name", "") for row in rows)
    function_names = Counter(row.get("function_name", "") for row in rows)
    hashes = Counter(row.get("normalized_code_hash", "") for row in rows)
    cwes = Counter(infer_cwe(row) for row in rows)

    line_counts = []
    for row in rows:
        try:
            line_counts.append(int(row.get("code_line_count", "0")))
        except ValueError:
            line_counts.append(0)

    duplicate_hash_count = sum(1 for value, count in hashes.items() if value and count > 1)
    average_lines = sum(line_counts) / len(line_counts) if line_counts else 0

    print(f"Total rows: {len(rows)}")
    print(f"Unique binaries: {len(binaries)}")
    print()
    print("Rows per binary:")
    for binary_name, count in binaries.most_common():
        print(f"  {binary_name}: {count}")

    print()
    print("Top 20 function names:")
    for function_name, count in function_names.most_common(20):
        print(f"  {function_name}: {count}")

    print()
    print(f"Average code line count: {average_lines:.2f}")
    print(f"Min code line count: {min(line_counts) if line_counts else 0}")
    print(f"Max code line count: {max(line_counts) if line_counts else 0}")
    print(f"Duplicate hash count: {duplicate_hash_count}")

    print()
    print("Rows by inferred CWE:")
    for cwe, count in cwes.most_common():
        print(f"  {cwe}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
