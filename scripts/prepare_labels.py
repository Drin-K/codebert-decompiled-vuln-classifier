"""Prepare deterministic suggested labels for cleaned Juliet functions."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_COLUMNS = [
    "function_code",
    "suggested_label",
    "suggested_class",
    "label_confidence",
    "label_reason",
    "review_status",
    "final_label",
    "final_class",
    "binary_name",
    "function_name",
    "function_address",
    "source_csv",
    "inferred_cwe",
    "source_type",
    "code_line_count",
    "code_char_count",
    "normalized_code_hash",
]
CWE_TO_CLASS = {
    "CWE-121": ("1", "Buffer Overflow"),
    "CWE-122": ("1", "Buffer Overflow"),
    "CWE-134": ("2", "Format String"),
    "CWE-190": ("3", "Integer Overflow"),
}
GOOD_NAME_RE = re.compile(
    r"^(?:good[A-Za-z0-9_]*|.*_good)$",
    re.IGNORECASE,
)
BAD_NAME_RE = re.compile(r"^(?:bad[A-Za-z0-9_]*|.*_bad)$", re.IGNORECASE)
HELPER_NAME_RE = re.compile(
    r"^(?:"
    r"decodeHexChars|decodeHexWChars|"
    r"print.*|"
    r"globalReturns.*|staticReturns.*|"
    r"globalTrue|globalFalse|globalFive|globalReturnsTrueOrFalse"
    r")$",
    re.IGNORECASE,
)
CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
FORMAT_WITH_CONSTANT_RE = re.compile(
    r"\b(?:printf|fprintf|sprintf|snprintf)\s*\([^;]*\"",
    re.IGNORECASE | re.DOTALL,
)
FORMAT_WITH_VARIABLE_RE = re.compile(
    r"\b(?:printf|fprintf|sprintf|snprintf)\s*\([^;]*(?:data|input|buffer|param|local)",
    re.IGNORECASE | re.DOTALL,
)
BUFFER_PATTERN_RE = re.compile(
    r"\b(?:strcpy|strcat|sprintf|gets|memcpy|memmove)\s*\(",
    re.IGNORECASE,
)
LOCAL_BUFFER_RE = re.compile(r"\b(?:char|int|short|long|uchar|uint|byte)\s+\w+\s*\[[^\]]+\]")
ARRAY_WRITE_RE = re.compile(r"\w+\s*\[[^\]]+\]\s*=")
INTEGER_PATTERN_RE = re.compile(
    r"(?:\b\w+\s*=\s*\w+\s*[\+\*]\s*\w+|\+\+|--|\bmalloc\s*\([^)]*[\+\*][^)]*\)|\[\s*\w+\s*[\+\*])",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare suggested labels for manual review.")
    parser.add_argument("--input", default="data/processed/clean_functions.csv")
    parser.add_argument("--output", default="data/processed/suggested_labels.csv")
    parser.add_argument("--summary", default="data/processed/labeling_summary.md")
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def infer_cwe(row: dict[str, str]) -> str:
    text = " ".join([row.get("binary_name", ""), row.get("source_csv", "")])
    for compact, dashed in (
        ("CWE121", "CWE-121"),
        ("CWE122", "CWE-122"),
        ("CWE134", "CWE-134"),
        ("CWE190", "CWE-190"),
    ):
        if compact in text or dashed in text:
            return dashed
    return "UNKNOWN"


def is_good_name(function_name: str) -> bool:
    return bool(GOOD_NAME_RE.match(function_name.strip()))


def is_bad_name(function_name: str) -> bool:
    return bool(BAD_NAME_RE.match(function_name.strip()))


def is_helper_name(function_name: str) -> bool:
    return bool(HELPER_NAME_RE.match(function_name.strip()))


def code_body(function_code: str) -> str:
    start = function_code.find("{")
    end = function_code.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return function_code
    return function_code[start + 1 : end]


def meaningful_body_lines(function_code: str) -> list[str]:
    lines = []
    for line in code_body(function_code).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("/*") or stripped.startswith("*") or stripped.startswith("//"):
            continue
        if stripped in {"{", "}"}:
            continue
        if stripped.startswith("/* WARNING:"):
            continue
        lines.append(stripped)
    return lines


def is_empty_return_stub(function_code: str) -> bool:
    lines = meaningful_body_lines(function_code)
    return lines in ([], ["return;"])


def is_juliet_variant_call(name: str) -> bool:
    return bool(
        re.match(
            r"^(?:bad[A-Za-z0-9_]*|good[A-Za-z0-9_]*|.*_bad|.*_good)$",
            name,
            re.IGNORECASE,
        )
    )


def is_dispatch_wrapper(function_code: str) -> bool:
    lines = meaningful_body_lines(function_code)
    if not lines:
        return False

    call_lines = []
    for line in lines:
        if line == "return;":
            continue
        if not line.endswith(";"):
            return False
        calls = CALL_RE.findall(line)
        if len(calls) != 1:
            return False
        if not is_juliet_variant_call(calls[0]):
            return False
        call_lines.append(line)

    return bool(call_lines)


def has_buffer_pattern(code: str) -> bool:
    return bool(BUFFER_PATTERN_RE.search(code)) or (
        bool(LOCAL_BUFFER_RE.search(code)) and bool(ARRAY_WRITE_RE.search(code))
    )


def has_format_string_pattern(code: str) -> bool:
    if not FORMAT_WITH_VARIABLE_RE.search(code):
        return False
    return not FORMAT_WITH_CONSTANT_RE.search(code)


def has_integer_pattern(code: str) -> bool:
    return bool(INTEGER_PATTERN_RE.search(code))


def class_pattern_matches(cwe: str, code: str) -> bool:
    if cwe in {"CWE-121", "CWE-122"}:
        return has_buffer_pattern(code)
    if cwe == "CWE-134":
        return has_format_string_pattern(code)
    if cwe == "CWE-190":
        return has_integer_pattern(code)
    return False


def exclude_label(reason: str) -> tuple[str, str, str, str, str]:
    return "-2", "Exclude", "high", reason, "exclude"


def suggest_label(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    function_name = row.get("function_name", "").strip()
    function_code = row.get("function_code", "")
    cwe = infer_cwe(row)
    target = CWE_TO_CLASS.get(cwe)
    good_name = is_good_name(function_name)
    bad_name = is_bad_name(function_name)
    pattern_match = class_pattern_matches(cwe, function_code)

    if function_name == "main":
        return exclude_label(
            "main dispatcher function calling Juliet good/bad variants; excluded from function-level training dataset"
        )

    if is_empty_return_stub(function_code):
        return exclude_label(
            "empty return-only stub function; excluded from function-level training dataset"
        )

    if is_dispatch_wrapper(function_code):
        return exclude_label(
            "Juliet wrapper function that only dispatches to good/bad variant functions; excluded to avoid training on dispatcher logic"
        )

    if is_helper_name(function_name) and not pattern_match:
        return exclude_label(
            "Juliet support/helper function without target vulnerability logic; excluded from model training dataset"
        )

    if good_name:
        confidence = "medium" if pattern_match else "high"
        reason = (
            "Juliet good-function naming indicates a non-vulnerable variant. "
            "Vulnerability-related APIs may appear, but the function belongs to a Juliet good source/sink path."
        )
        return (
            "0",
            "Clean",
            confidence if cwe != "UNKNOWN" else "medium",
            reason,
            "suggested",
        )

    if target and bad_name:
        label, class_name = target
        confidence = "high" if pattern_match else "medium"
        reason = (
            f"{cwe} metadata maps to {class_name} and Juliet bad-function naming pattern"
        )
        if pattern_match:
            reason += " with supporting vulnerable code pattern"
        return label, class_name, confidence, reason, "suggested"

    if target and pattern_match:
        label, class_name = target
        return (
            label,
            class_name,
            "medium",
            f"{cwe} metadata maps to {class_name} and code contains supporting vulnerability pattern",
            "suggested",
        )

    return (
        "-1",
        "Uncertain",
        "low",
        "No reliable Juliet good/bad naming agreement or supporting class-specific pattern",
        "needs_manual_review",
    )


def read_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def output_row(row: dict[str, str]) -> dict[str, str]:
    label, class_name, confidence, reason, review_status = suggest_label(row)
    enriched = {column: "" for column in OUTPUT_COLUMNS}
    enriched.update(
        {
            "function_code": row.get("function_code", ""),
            "suggested_label": label,
            "suggested_class": class_name,
            "label_confidence": confidence,
            "label_reason": reason,
            "review_status": review_status,
            "final_label": "",
            "final_class": "",
            "binary_name": row.get("binary_name", ""),
            "function_name": row.get("function_name", ""),
            "function_address": row.get("function_address", ""),
            "source_csv": row.get("source_csv", ""),
            "inferred_cwe": infer_cwe(row),
            "source_type": "Juliet",
            "code_line_count": row.get("code_line_count", ""),
            "code_char_count": row.get("code_char_count", ""),
            "normalized_code_hash": row.get("normalized_code_hash", ""),
        }
    )
    return enriched


def write_rows(output_path: Path, rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary_path: Path, input_path: Path, output_path: Path, rows: list[dict[str, str]]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    class_counts = Counter(row["suggested_class"] for row in rows)
    label_counts = Counter(row["suggested_label"] for row in rows)
    cwe_counts = Counter(row["inferred_cwe"] for row in rows)
    confidence_counts = Counter(row["label_confidence"] for row in rows)
    review_counts = Counter(row["review_status"] for row in rows)
    uncertain_count = class_counts.get("Uncertain", 0)
    exclude_count = class_counts.get("Exclude", 0)

    def counter_lines(counter: Counter[str]) -> list[str]:
        if not counter:
            return ["- None"]
        return [f"- {key}: {count}" for key, count in counter.most_common()]

    lines = [
        "# Labeling Summary",
        "",
        f"Input: `{input_path}`",
        f"Output: `{output_path}`",
        "",
        f"Total input rows: {len(rows)}",
        f"Total suggested labels: {len(rows)}",
        f"Uncertain rows: {uncertain_count}",
        f"Exclude rows: {exclude_count}",
        "",
        "## Count Per Suggested Class",
        "",
        *counter_lines(class_counts),
        "",
        "## Count Per Suggested Label",
        "",
        *counter_lines(label_counts),
        "",
        "## Count Per Inferred CWE",
        "",
        *counter_lines(cwe_counts),
        "",
        "## Count Per Label Confidence",
        "",
        *counter_lines(confidence_counts),
        "",
        "## Count Per Review Status",
        "",
        *counter_lines(review_counts),
        "",
        "## Notes",
        "",
        "- `Exclude` rows are not used for model training.",
        "- These are suggested labels only; final labels are not assigned in this phase.",
        "- Manual verification is required before training or evaluation.",
        "- `final_label` and `final_class` are intentionally left blank.",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = resolve_repo_path(args.input)
    output_path = resolve_repo_path(args.output)
    summary_path = resolve_repo_path(args.summary)

    if not input_path.exists():
        print(f"ERROR: Input CSV does not exist: {input_path}")
        return 1

    rows = [output_row(row) for row in read_rows(input_path)]
    write_rows(output_path, rows)
    write_summary(summary_path, input_path, output_path, rows)

    class_counts = Counter(row["suggested_class"] for row in rows)
    confidence_counts = Counter(row["label_confidence"] for row in rows)
    print(f"Input rows: {len(rows)}")
    print(f"Output path: {output_path}")
    print(f"Summary path: {summary_path}")
    print("Suggested class distribution:")
    for class_name, count in class_counts.most_common():
        print(f"  {class_name}: {count}")
    print("Confidence distribution:")
    for confidence, count in confidence_counts.most_common():
        print(f"  {confidence}: {count}")
    print(f"Uncertain rows: {class_counts.get('Uncertain', 0)}")
    print(f"Exclude rows: {class_counts.get('Exclude', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
