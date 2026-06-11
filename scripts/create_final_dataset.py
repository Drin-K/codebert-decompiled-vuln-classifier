"""Create the final balanced training dataset from suggested Juliet labels."""

from __future__ import annotations

import argparse
import csv
import random
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_CLASSES = ("Clean", "Buffer Overflow", "Format String", "Integer Overflow")
CLASS_TO_LABEL = {
    "Clean": "0",
    "Buffer Overflow": "1",
    "Format String": "2",
    "Integer Overflow": "3",
}
OUTPUT_COLUMNS = [
    "function_code",
    "final_label",
    "final_class",
    "suggested_label",
    "suggested_class",
    "label_confidence",
    "label_reason",
    "review_status",
    "sanity_check_status",
    "sanity_check_reason",
    "final_decision",
    "exclude_reason",
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

FORMAT_SINKS = ("printf", "fprintf", "sprintf", "snprintf", "vfprintf", "vprintf", "vsnprintf")
FORMAT_ARGUMENT_INDEX = {
    "printf": 0,
    "vprintf": 0,
    "fprintf": 1,
    "sprintf": 1,
    "vfprintf": 1,
    "snprintf": 2,
    "vsnprintf": 2,
}
BUFFER_COPY_SINK_RE = re.compile(
    r"\b(?:strcpy|strcat|sprintf|gets|memcpy|memmove|operator_new)\s*\(",
    re.IGNORECASE,
)
BUFFER_INDEX_WRITE_RE = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_]*\s*\[[^\]\n]*(?:data|iVar\d+|uVar\d+|lVar\d+|i|index)[^\]\n]*\]\s*=",
    re.IGNORECASE,
)
ARRAY_DECL_RE = re.compile(
    r"\b(?:char|int|short|long|uchar|uint|byte|undefined\d*|size_t)\s+"
    r"[A-Za-z_][A-Za-z0-9_]*\s*\[[^\]]+\]",
    re.IGNORECASE,
)
ARRAY_INDEX_RE = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_]*\s*\[[^\]\n]*(?:data|iVar\d+|uVar\d+|lVar\d+|i|index)[^\]\n]*\]",
    re.IGNORECASE,
)
LOWER_BOUND_ONLY_RE = re.compile(
    r"\b(?:data|iVar\d+|uVar\d+|lVar\d+|i|index)\s*(?:>=|>|!=)\s*-?1?\s*0\b",
    re.IGNORECASE,
)
INTEGER_ARITH_RE = re.compile(
    r"(?:"
    r"\b(?:result|data|iVar\d+|uVar\d+|lVar\d+)\s*=\s*[^;\n]*(?:\+|\*|-\s*1)[^;\n]*|"
    r"\b(?:print[A-Za-z0-9_]*|malloc)\s*\([^;\n]*(?:data|result|iVar\d+|uVar\d+|lVar\d+)[^;\n]*(?:\+|\*)[^;\n]*\)|"
    r"\b(?:data|result|iVar\d+|uVar\d+|lVar\d+)\s*(?:\+\+|--)|"
    r"(?:\+\+|--)\s*(?:data|result|iVar\d+|uVar\d+|lVar\d+)"
    r")",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply final sanity checks and create a balanced training dataset."
    )
    parser.add_argument("--input", default="data/processed/suggested_labels.csv")
    parser.add_argument("--output", default="data/processed/final_labeled_dataset.csv")
    parser.add_argument("--summary", default="data/processed/final_dataset_summary.md")
    parser.add_argument("--target-per-class", type=int, default=250)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def read_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def split_arguments(argument_text: str) -> list[str]:
    args: list[str] = []
    current: list[str] = []
    depth = 0
    quote = ""
    escaped = False

    for char in argument_text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and quote:
            current.append(char)
            escaped = True
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {'"', "'"}:
            current.append(char)
            quote = char
            continue
        if char in "([{":
            depth += 1
            current.append(char)
            continue
        if char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
            continue
        if char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
            continue
        current.append(char)

    if current or argument_text.strip():
        args.append("".join(current).strip())
    return args


def find_calls(code: str, function_names: tuple[str, ...]) -> list[tuple[str, list[str]]]:
    calls: list[tuple[str, list[str]]] = []
    name_group = "|".join(re.escape(name) for name in function_names)
    call_re = re.compile(rf"\b({name_group})\s*\(", re.IGNORECASE)

    for match in call_re.finditer(code):
        index = match.end()
        depth = 1
        quote = ""
        escaped = False
        while index < len(code):
            char = code[index]
            if escaped:
                escaped = False
            elif char == "\\" and quote:
                escaped = True
            elif quote:
                if char == quote:
                    quote = ""
            elif char in {'"', "'"}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    argument_text = code[match.end() : index]
                    calls.append((match.group(1), split_arguments(argument_text)))
                    break
            index += 1
    return calls


def looks_like_string_literal(argument: str) -> bool:
    return argument.strip().startswith('"')


def has_format_string_signal(code: str) -> bool:
    for sink, args in find_calls(code, FORMAT_SINKS):
        sink_lower = sink.lower()
        format_index = FORMAT_ARGUMENT_INDEX[sink_lower]
        if len(args) <= format_index:
            continue
        format_arg = args[format_index].strip()
        if looks_like_string_literal(format_arg):
            continue
        if re.search(
            r"\b(?:data[A-Za-z0-9_]*|input[A-Za-z0-9_]*|"
            r"[A-Za-z0-9_]*buffer[A-Za-z0-9_]*|param[A-Za-z0-9_]*|"
            r"local[A-Za-z0-9_]*|pcVar\d+)\b",
            format_arg,
            re.IGNORECASE,
        ):
            return True
    return False


def has_buffer_overflow_signal(code: str) -> bool:
    if BUFFER_COPY_SINK_RE.search(code):
        return True
    if BUFFER_INDEX_WRITE_RE.search(code):
        return True
    if ARRAY_DECL_RE.search(code) and ARRAY_INDEX_RE.search(code) and LOWER_BOUND_ONLY_RE.search(code):
        return True
    return False


def has_integer_overflow_signal(code: str) -> bool:
    return bool(INTEGER_ARITH_RE.search(code))


def sanity_check(row: dict[str, str]) -> tuple[str, str]:
    suggested_class = row.get("suggested_class", "")
    code = row.get("function_code", "")

    if suggested_class == "Buffer Overflow":
        if has_buffer_overflow_signal(code):
            return "passed", "Visible buffer write/copy/index operation in decompiled pseudo-C body"
        return "failed", "Vulnerability label not visible in decompiled pseudo-C body"

    if suggested_class == "Format String":
        if has_format_string_signal(code):
            return "passed", "Visible format-string sink using a non-literal format argument"
        return "failed", "Format string sink not visible in decompiled pseudo-C body"

    if suggested_class == "Integer Overflow":
        if has_integer_overflow_signal(code):
            return "passed", "Visible arithmetic operation in decompiled pseudo-C body"
        return "failed", "Integer overflow operation not visible in decompiled pseudo-C body"

    if suggested_class == "Clean":
        return "not_required", "Clean Juliet variant; vulnerable-pattern sanity check is not required"

    return "not_required", f"{suggested_class or 'Unknown'} rows are not eligible for training"


def finalize_row(row: dict[str, str]) -> dict[str, str]:
    finalized = {column: row.get(column, "") for column in OUTPUT_COLUMNS}
    suggested_class = row.get("suggested_class", "")
    status, reason = sanity_check(row)
    finalized["sanity_check_status"] = status
    finalized["sanity_check_reason"] = reason
    finalized["final_label"] = ""
    finalized["final_class"] = ""
    finalized["exclude_reason"] = ""

    if suggested_class in TARGET_CLASSES and status in {"passed", "not_required"}:
        finalized["final_decision"] = "include"
        finalized["final_class"] = suggested_class
        finalized["final_label"] = CLASS_TO_LABEL[suggested_class]
        return finalized

    finalized["final_decision"] = "exclude"
    if suggested_class == "Exclude":
        finalized["exclude_reason"] = row.get("label_reason", "Suggested label marked row as Exclude")
    elif suggested_class == "Uncertain":
        finalized["exclude_reason"] = row.get("label_reason", "Suggested label requires manual review")
    elif status == "failed":
        finalized["exclude_reason"] = reason
    else:
        finalized["exclude_reason"] = f"{suggested_class or 'Unknown'} rows are not used for training"
    return finalized


def balanced_sample(
    include_rows: list[dict[str, str]], target_per_class: int, seed: int
) -> tuple[list[dict[str, str]], int, str]:
    rows_by_class = {
        class_name: [row for row in include_rows if row.get("final_class") == class_name]
        for class_name in TARGET_CLASSES
    }
    available_counts = {class_name: len(rows) for class_name, rows in rows_by_class.items()}
    limiting_class = min(available_counts, key=available_counts.get)
    per_class = available_counts[limiting_class]
    rng = random.Random(seed)

    sampled_rows: list[dict[str, str]] = []
    for class_name in TARGET_CLASSES:
        class_rows = list(rows_by_class[class_name])
        class_rows.sort(
            key=lambda row: (
                row.get("binary_name", ""),
                row.get("function_name", ""),
                row.get("function_address", ""),
                row.get("normalized_code_hash", ""),
            )
        )
        sampled_rows.extend(rng.sample(class_rows, per_class))

    sampled_rows.sort(key=lambda row: (row.get("final_class", ""), row.get("binary_name", ""), row.get("function_name", "")))
    return sampled_rows, per_class, limiting_class


def write_rows(output_path: Path, rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def counter_lines(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- None"]
    return [f"- {key or '(blank)'}: {count}" for key, count in counter.most_common()]


def write_summary(
    summary_path: Path,
    input_path: Path,
    output_path: Path,
    finalized_rows: list[dict[str, str]],
    sampled_rows: list[dict[str, str]],
    target_per_class: int,
    balanced_rows_per_class: int,
    limiting_class: str,
) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    include_rows = [row for row in finalized_rows if row["final_decision"] == "include"]
    available_counts = Counter(row["final_class"] for row in include_rows)
    sanity_excluded = [
        row
        for row in finalized_rows
        if row["sanity_check_status"] == "failed" and row["final_decision"] == "exclude"
    ]
    target_achieved = balanced_rows_per_class >= target_per_class
    final_counts = Counter(row["final_class"] for row in sampled_rows)
    final_label_counts = Counter(row["final_label"] for row in sampled_rows)

    lines = [
        "# Final Dataset Summary",
        "",
        f"Input: `{input_path}`",
        f"Output: `{output_path}`",
        "",
        f"Total rows in suggested labels: {len(finalized_rows)}",
        f"Rows included after sanity checks: {len(include_rows)}",
        f"Rows excluded after sanity checks: {len(sanity_excluded)}",
        "",
        "## Count Per Sanity Check Status",
        "",
        *counter_lines(Counter(row["sanity_check_status"] for row in finalized_rows)),
        "",
        "## Count Per Final Decision",
        "",
        *counter_lines(Counter(row["final_decision"] for row in finalized_rows)),
        "",
        "## Count Per Final Class Before Balancing",
        "",
        *counter_lines(available_counts),
        "",
        "## Final Balanced Dataset Count Per Class",
        "",
        *counter_lines(final_counts),
        "",
        "## Final Balanced Dataset Count Per Label",
        "",
        *counter_lines(final_label_counts),
        "",
        f"Minimum target per class: {target_per_class}",
        f"Minimum target achieved: {'yes' if target_achieved else 'no'}",
        f"Smallest available class: {limiting_class}",
        f"Limiting class: {'None' if target_achieved else limiting_class}",
        f"Balanced rows per class used: {balanced_rows_per_class}",
        "Balancing strategy: downsample all classes to the smallest available class count",
        f"Total final dataset rows: {len(sampled_rows)}",
        "",
        "## Top Exclude Reasons",
        "",
        *counter_lines(Counter(row["exclude_reason"] for row in finalized_rows if row["exclude_reason"])),
        "",
        "## Notes",
        "",
        "- The final dataset is still weak-labeled and benchmark-derived from Juliet CWE metadata and function naming.",
        "- Vulnerable samples where the vulnerability was not visible in decompiled pseudo-C were excluded.",
        "- Exclude, Uncertain, review, and failed sanity-check rows are not used for training.",
        "- This dataset is suitable for bachelor thesis prototype training, not production-grade exploitation detection.",
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

    finalized_rows = [finalize_row(row) for row in read_rows(input_path)]
    include_rows = [row for row in finalized_rows if row["final_decision"] == "include"]
    sampled_rows, balanced_rows_per_class, limiting_class = balanced_sample(
        include_rows, args.target_per_class, args.seed
    )

    write_rows(output_path, sampled_rows)
    write_summary(
        summary_path,
        input_path,
        output_path,
        finalized_rows,
        sampled_rows,
        args.target_per_class,
        balanced_rows_per_class,
        limiting_class,
    )

    print(f"Input rows: {len(finalized_rows)}")
    print(f"Rows included after sanity checks: {len(include_rows)}")
    print(
        "Rows excluded by sanity checks: "
        f"{sum(1 for row in finalized_rows if row['sanity_check_status'] == 'failed')}"
    )
    print(f"Output path: {output_path}")
    print(f"Summary path: {summary_path}")
    print("Final class distribution:")
    for class_name, count in Counter(row["final_class"] for row in sampled_rows).items():
        print(f"  {class_name}: {count}")
    print(
        "Minimum target per class achieved: "
        f"{'yes' if balanced_rows_per_class >= args.target_per_class else 'no'}"
    )
    print(f"Balanced rows per class used: {balanced_rows_per_class}")
    if balanced_rows_per_class < args.target_per_class:
        print(f"Limiting class: {limiting_class}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
