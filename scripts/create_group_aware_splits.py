#!/usr/bin/env python3
"""Create class-balanced splits while keeping Juliet families wholly together."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


REPO_ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("train", "val", "test")
LABELS = (0, 1, 2, 3)
CLASS_NAMES = {0: "Clean", 1: "Buffer Overflow", 2: "Format String", 3: "Integer Overflow"}
TARGETS = {"train": (182, 182, 182, 182), "val": (39, 39, 39, 39), "test": (39, 39, 39, 39)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/final_labeled_dataset.csv")
    parser.add_argument("--output-dir", default="data/experiments/group_aware")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true", help="Replace files only inside the requested output directory.")
    return parser.parse_args()


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def family_key(binary_name: str) -> str:
    return re.sub(r"_(?:0[1-9]|1[0-8])$", "", binary_name.strip())


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    required = {"binary_name", "final_label", "function_code"}
    if not required.issubset(fields):
        raise ValueError(f"Input is missing columns: {sorted(required - set(fields))}")
    for row in rows:
        label = int(row["final_label"])
        if label not in LABELS:
            raise ValueError(f"Unsupported label: {label}")
        row["group_family"] = family_key(row["binary_name"])
    return fields, rows


def solve_assignment(rows: list[dict[str, str]], seed: int) -> dict[str, str]:
    families = sorted({row["group_family"] for row in rows})
    family_index = {family: index for index, family in enumerate(families)}
    counts = np.zeros((len(families), len(LABELS)), dtype=float)
    for row in rows:
        counts[family_index[row["group_family"]], int(row["final_label"])] += 1

    group_vars = len(families) * len(SPLITS)
    cells = len(SPLITS) * len(LABELS)
    variable_count = group_vars + 2 * cells
    objective = np.zeros(variable_count)
    rng = random.Random(seed)
    # Tiny deterministic costs break ties without changing the primary deviation objective.
    objective[:group_vars] = [rng.random() * 1e-8 for _ in range(group_vars)]
    for split_index, split in enumerate(SPLITS):
        for label in LABELS:
            cell = split_index * len(LABELS) + label
            weight = 1.0 / TARGETS[split][label]
            objective[group_vars + cell] = weight
            objective[group_vars + cells + cell] = weight

    matrix = lil_matrix((len(families) + cells, variable_count))
    lower: list[float] = []
    upper: list[float] = []
    for family_index_value in range(len(families)):
        for split_index in range(len(SPLITS)):
            matrix[family_index_value, family_index_value * len(SPLITS) + split_index] = 1
        lower.append(1); upper.append(1)

    for split_index, split in enumerate(SPLITS):
        for label in LABELS:
            row_index = len(families) + split_index * len(LABELS) + label
            for family_index_value in range(len(families)):
                matrix[row_index, family_index_value * len(SPLITS) + split_index] = counts[family_index_value, label]
            cell = split_index * len(LABELS) + label
            matrix[row_index, group_vars + cell] = -1
            matrix[row_index, group_vars + cells + cell] = 1
            target = TARGETS[split][label]
            lower.append(target); upper.append(target)

    result = milp(
        objective,
        integrality=np.r_[np.ones(group_vars), np.zeros(2 * cells)],
        bounds=Bounds(np.zeros(variable_count), np.r_[np.ones(group_vars), np.full(2 * cells, np.inf)]),
        constraints=LinearConstraint(matrix.tocsr(), lower, upper),
    )
    if not result.success or result.x is None:
        raise RuntimeError(f"Could not construct group-aware split: {result.message}")
    choices = result.x[:group_vars].reshape(len(families), len(SPLITS)).argmax(axis=1)
    return {family: SPLITS[int(choices[index])] for index, family in enumerate(families)}


def verify(partitions: dict[str, list[dict[str, str]]]) -> dict[str, object]:
    family_sets = {split: {row["group_family"] for row in rows} for split, rows in partitions.items()}
    binary_sets = {split: {row["binary_name"] for row in rows} for split, rows in partitions.items()}
    family_overlap = {}; binary_overlap = {}
    for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
        family_overlap[f"{left}_{right}"] = len(family_sets[left] & family_sets[right])
        binary_overlap[f"{left}_{right}"] = len(binary_sets[left] & binary_sets[right])
    if any(family_overlap.values()) or any(binary_overlap.values()):
        raise RuntimeError("Group-aware split verification failed: overlap detected")
    return {
        "family_overlap": family_overlap,
        "binary_overlap": binary_overlap,
        "rows": {split: len(rows) for split, rows in partitions.items()},
        "families": {split: len(family_sets[split]) for split in SPLITS},
        "binaries": {split: len(binary_sets[split]) for split in SPLITS},
        "class_counts": {split: {str(label): Counter(int(row["final_label"]) for row in rows)[label] for label in LABELS} for split, rows in partitions.items()},
    }


def main() -> int:
    config = parse_args(); input_path = resolve(config.input); output_dir = resolve(config.output_dir)
    output_paths = [output_dir / f"{split}.csv" for split in SPLITS] + [output_dir / "group_assignments.csv", output_dir / "split_summary.json", output_dir / "split_summary.md"]
    existing = [path for path in output_paths if path.exists()]
    if existing and not config.force:
        raise SystemExit("ERROR: outputs already exist; refusing to overwrite without --force: " + ", ".join(map(str, existing)))
    fields, rows = read_rows(input_path)
    assignment = solve_assignment(rows, config.seed)
    partitions: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows: partitions[assignment[row["group_family"]]].append(row)
    rng = random.Random(config.seed)
    for split in SPLITS: rng.shuffle(partitions[split])
    verification = verify(partitions)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_fields = [*fields, "group_family"]
    for split in SPLITS:
        with (output_dir / f"{split}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=output_fields); writer.writeheader(); writer.writerows(partitions[split])
    with (output_dir / "group_assignments.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["group_family", "split"]); writer.writeheader()
        writer.writerows({"group_family": family, "split": assignment[family]} for family in sorted(assignment))
    payload = {"input": str(input_path), "seed": config.seed, "grouping_rule": "remove terminal Juliet control-flow variant _01 through _18 from binary_name", "target_class_counts": {split: list(TARGETS[split]) for split in SPLITS}, **verification}
    (output_dir / "split_summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# Group-Aware Split Summary", "", f"- Input: `{input_path}`", f"- Random seed for deterministic tie-breaking and row ordering: {config.seed}", "- Grouping rule: terminal Juliet control-flow variant `_01` through `_18` is removed from `binary_name`", "- Assignment method: mixed-integer optimization minimizing class-count deviation", "", "## Distribution", "", "| Split | Rows | Families | Binaries | Clean | Buffer Overflow | Format String | Integer Overflow |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for split in SPLITS:
        counts=verification["class_counts"][split]
        lines.append(f"| {split} | {verification['rows'][split]} | {verification['families'][split]} | {verification['binaries'][split]} | {counts['0']} | {counts['1']} | {counts['2']} | {counts['3']} |")
    lines.extend(["", "## Verification", "", "- Family overlap across all split pairs: 0", "- Binary overlap across all split pairs: 0", f"- Total rows preserved: {sum(verification['rows'].values())}/{len(rows)}", "- Every input row occurs in exactly one output split", "", "## Limitation", "", f"Class counts are nearly balanced but validation and test contain {verification['rows']['val']} and {verification['rows']['test']} rows because complete Juliet families cannot be divided between partitions. This independence constraint is more important than reproducing the exact Experiment 0 sizes.", ""])
    (output_dir / "split_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2)); print(f"Outputs: {output_dir}"); return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as error: raise SystemExit(f"ERROR: {error}") from None
