#!/usr/bin/env python3
"""Audit existing dataset splits for overlap and shortcut-learning signals."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("train", "val", "test")
PAIR_NAMES = (("train", "val"), ("train", "test"), ("val", "test"))
LABEL_NAMES = {0: "Clean", 1: "Buffer Overflow", 2: "Format String", 3: "Integer Overflow"}
IDENTIFIER_SIGNALS = {
    "contains_good": re.compile(r"good", re.I),
    "contains_bad": re.compile(r"bad", re.I),
    "good_to_bad_variant": re.compile(r"goodg2b|g2b", re.I),
    "bad_to_good_variant": re.compile(r"goodb2g|b2g", re.I),
    "sink_or_source_role": re.compile(r"(?:good|bad)?(?:sink|source)", re.I),
    "cwe_identifier": re.compile(r"cwe[_-]?(?:121|122|134|190)", re.I),
    "explicit_vulnerability_name": re.compile(r"buffer[_ ]overflow|format[_ ]string|integer[_ ]overflow", re.I),
}
SHORTCUT_SIGNALS = {
    "unsafe_string_api": re.compile(r"\b(?:strcpy|strcat|sprintf|vsprintf|gets)\s*\(", re.I),
    "memory_copy_api": re.compile(r"\b(?:memcpy|memmove)\s*\(", re.I),
    "printf_family": re.compile(r"\b(?:printf|fprintf|sprintf|snprintf|vprintf|vfprintf|syslog)\s*\(", re.I),
    "allocation_api": re.compile(r"\b(?:malloc|calloc|realloc)\s*\(", re.I),
    "arithmetic_operator": re.compile(r"(?:\+|-|\*)"),
    "comparison_check": re.compile(r"\bif\s*\([^)]*(?:<=|>=|<|>)", re.I),
}
TOKEN_RE = re.compile(r"[A-Za-z_]\w*|0x[0-9a-fA-F]+|\d+|==|!=|<=|>=|<<|>>|[-+*/%<>&|^]=?|[{}()[\],;]")
C_KEYWORDS = {
    "if", "else", "for", "while", "do", "return", "switch", "case", "break", "continue",
    "void", "char", "short", "int", "long", "float", "double", "signed", "unsigned", "const",
    "struct", "union", "enum", "sizeof", "static", "true", "false", "null", "nullterm",
}
KNOWN_APIS = {"strcpy", "strcat", "sprintf", "vsprintf", "gets", "memcpy", "memmove", "printf", "fprintf", "snprintf", "vprintf", "vfprintf", "malloc", "calloc", "realloc", "free", "strlen", "sizeof"}


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-dir", default="data/splits")
    parser.add_argument("--output-dir", default="results/experiment_group_aware/leakage_audit")
    parser.add_argument("--near-duplicate-threshold", type=float, default=0.90)
    return parser.parse_args()


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def family_key(binary_name: str) -> str:
    """Group Juliet control-flow variants 01..18 under one testcase family."""
    return re.sub(r"_(?:0[1-9]|1[0-8])$", "", binary_name.strip())


def read_splits(split_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for split in SPLITS:
        path = split_dir / f"{split}.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            for index, row in enumerate(csv.DictReader(handle)):
                enriched = dict(row)
                enriched["_split"] = split
                enriched["_row"] = str(index)
                enriched["_family"] = family_key(row["binary_name"])
                rows.append(enriched)
    return rows


def overlap_rows(rows: list[dict[str, str]], key: str, output_name: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        value = row.get(key, "").strip()
        if value:
            groups[value].append(row)
    output = []
    for value, members in groups.items():
        splits = sorted({row["_split"] for row in members})
        if len(splits) < 2:
            continue
        counts = Counter(row["_split"] for row in members)
        output.append({output_name: value, "splits": ",".join(splits), **{f"{s}_rows": counts[s] for s in SPLITS}, "total_rows": len(members)})
    return sorted(output, key=lambda row: (-row["total_rows"], row[output_name]))


def canonical_shingles(code: str, size: int = 5) -> set[tuple[str, ...]]:
    tokens = []
    for token in TOKEN_RE.findall(code.lower()):
        if token.startswith("0x") or token.isdigit():
            tokens.append("NUM")
        elif re.fullmatch(r"[a-z_]\w*", token) and token not in C_KEYWORDS and token not in KNOWN_APIS:
            tokens.append("ID")
        else:
            tokens.append(token)
    return {tuple(tokens[i:i + size]) for i in range(max(0, len(tokens) - size + 1))}


def near_duplicates(rows: list[dict[str, str]], threshold: float) -> list[dict[str, Any]]:
    prepared = [(row, canonical_shingles(row["function_code"])) for row in rows]
    output = []
    for (left, ls), (right, rs) in combinations(prepared, 2):
        if left["_split"] == right["_split"] or not ls or not rs:
            continue
        if min(len(ls), len(rs)) / max(len(ls), len(rs)) < threshold:
            continue
        score = len(ls & rs) / len(ls | rs)
        if score >= threshold:
            output.append({
                "similarity": round(score, 6), "left_split": left["_split"], "right_split": right["_split"],
                "left_binary": left["binary_name"], "right_binary": right["binary_name"],
                "left_function": left["function_name"], "right_function": right["function_name"],
                "left_label": left["final_label"], "right_label": right["final_label"],
            })
    return sorted(output, key=lambda row: (-row["similarity"], row["left_binary"], row["right_binary"]))


def signal_table(rows: list[dict[str, str]], patterns: dict[str, re.Pattern[str]], include_name: bool) -> list[dict[str, Any]]:
    output = []
    for split in (*SPLITS, "all"):
        subset = rows if split == "all" else [row for row in rows if row["_split"] == split]
        for label in range(4):
            class_rows = [row for row in subset if int(row["final_label"]) == label]
            for signal, pattern in patterns.items():
                matched = 0
                for row in class_rows:
                    text = row["function_code"]
                    if include_name:
                        text += " " + row["function_name"]
                    matched += bool(pattern.search(text))
                output.append({"split": split, "label": label, "class": LABEL_NAMES[label], "signal": signal, "matched_rows": matched, "total_rows": len(class_rows), "percent": round(100 * matched / len(class_rows), 4) if class_rows else 0})
    return output


def write_csv(path: Path, rows: list[dict[str, Any]], fallback_fields: list[str]) -> None:
    fields = list(rows[0]) if rows else fallback_fields
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def pair_summary(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, int]]:
    sets = {split: {row[key] for row in rows if row["_split"] == split} for split in SPLITS}
    return {f"{a}_{b}": {"shared_groups": len(sets[a] & sets[b]), "affected_rows_in_second_split": sum(row[key] in sets[a] for row in rows if row["_split"] == b)} for a, b in PAIR_NAMES}


def main() -> int:
    config = args(); split_dir = resolve(config.split_dir); output_dir = resolve(config.output_dir)
    if not 0 <= config.near_duplicate_threshold <= 1:
        raise SystemExit("ERROR: threshold must be between 0 and 1")
    rows = read_splits(split_dir); output_dir.mkdir(parents=True, exist_ok=True)
    binary = overlap_rows(rows, "binary_name", "binary_name")
    family = overlap_rows(rows, "_family", "family_key")
    exact = overlap_rows(rows, "normalized_code_hash", "normalized_code_hash")
    near = near_duplicates(rows, config.near_duplicate_threshold)
    identifiers = signal_table(rows, IDENTIFIER_SIGNALS, True)
    shortcuts = signal_table(rows, SHORTCUT_SIGNALS, False)
    write_csv(output_dir / "binary_overlap.csv", binary, ["binary_name", "splits", "train_rows", "val_rows", "test_rows", "total_rows"])
    write_csv(output_dir / "family_overlap.csv", family, ["family_key", "splits", "train_rows", "val_rows", "test_rows", "total_rows"])
    write_csv(output_dir / "exact_duplicate_overlap.csv", exact, ["normalized_code_hash", "splits", "train_rows", "val_rows", "test_rows", "total_rows"])
    write_csv(output_dir / "near_duplicate_overlap.csv", near, ["similarity", "left_split", "right_split", "left_binary", "right_binary", "left_function", "right_function", "left_label", "right_label"])
    write_csv(output_dir / "identifier_leakage.csv", identifiers, list(identifiers[0]))
    write_csv(output_dir / "shortcut_patterns.csv", shortcuts, list(shortcuts[0]))
    summary = {
        "method": {"family_key": "remove terminal Juliet control-flow variant _01 through _18 from binary_name", "near_duplicate": f"Jaccard similarity >= {config.near_duplicate_threshold:.2f} over canonical token 5-shingles"},
        "rows": dict(Counter(row["_split"] for row in rows)),
        "binary_overlap": pair_summary(rows, "binary_name"), "family_overlap": pair_summary(rows, "_family"),
        "exact_hash_overlap_groups": len(exact), "near_duplicate_candidate_pairs": len(near),
        "rows_with_identifier_signals": {signal: sum(bool(pattern.search(row["function_code"] + " " + row["function_name"])) for row in rows) for signal, pattern in IDENTIFIER_SIGNALS.items()},
    }
    (output_dir / "leakage_audit.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = ["# Dataset Leakage Audit", "", "This audit reads the supplied splits without modifying them or retraining a model.", "", "## Split rows", "", *[f"- {s}: {summary['rows'][s]}" for s in SPLITS], "", "## Cross-split overlap", "", "| Comparison | Shared binaries | Rows in second split from seen binaries | Shared families | Rows in second split from seen families |", "|---|---:|---:|---:|---:|"]
    for a, b in PAIR_NAMES:
        k=f"{a}_{b}"; br=summary["binary_overlap"][k]; fr=summary["family_overlap"][k]
        lines.append(f"| {a} → {b} | {br['shared_groups']} | {br['affected_rows_in_second_split']} | {fr['shared_groups']} | {fr['affected_rows_in_second_split']} |")
    lines.extend(["", f"- Exact normalized-hash groups crossing splits: {len(exact)}", f"- Structural near-duplicate candidate pairs (threshold {config.near_duplicate_threshold:.2f}): {len(near)}", "", "## Label-revealing identifiers", ""])
    for signal, count in summary["rows_with_identifier_signals"].items(): lines.append(f"- {signal}: {count}/{len(rows)} rows ({100*count/len(rows):.2f}%)")
    overlap_found = any(item["shared_groups"] for item in summary["family_overlap"].values()) or any(item["shared_groups"] for item in summary["binary_overlap"].values())
    overlap_interpretation = "Binary and family overlap can make evaluation optimistic because related functions occur across partitions." if overlap_found else "No binary or derived-family overlap was found; the supplied splits satisfy the group-independence checks."
    overlap_recommendation = "Create a group-aware split that keeps every derived Juliet family, and preferably every binary, in exactly one partition." if overlap_found else "Use these group-independent splits for the additional evaluation."
    lines.extend(["", "## Interpretation", "", overlap_interpretation + " Identifier signals may still permit shortcut learning from Juliet names rather than vulnerability semantics.", "", "Exact hash overlap and structural similarity use documented deterministic definitions; structural matches are candidates for review, not proof of semantic duplication.", "", "## Recommendation", "", overlap_recommendation + " Evaluate identifier normalization as a separate ablation and preserve Experiment 0 unchanged.", ""])
    (output_dir / "leakage_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2)); print(f"Outputs: {output_dir}"); return 0


if __name__ == "__main__": raise SystemExit(main())
