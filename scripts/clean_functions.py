"""Clean merged Ghidra function rows by removing obvious non-useful functions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOILERPLATE_FUNCTION_NAMES = {
    "_init",
    "_fini",
    "_DT_INIT",
    "_FINI_0",
    "_DT_FINI",
    "_start",
    "entry",
    "_dl_relocate_static_pie",
    "_global_offset_table_",
    "__libc_start_main",
    "__cxa_finalize",
    "__stack_chk_fail",
    "__gmon_start__",
    "frame_dummy",
    "register_tm_clones",
    "deregister_tm_clones",
    "__do_global_dtors_aux",
    "_ITM_registerTMCloneTable",
    "_ITM_deregisterTMCloneTable",
}
ADDED_COLUMNS = [
    "normalized_code_hash",
    "code_line_count",
    "code_char_count",
    "cleaning_removed_reason",
]
ADDRESS_RE = re.compile(r"\b(?:0x)?[0-9a-fA-F]{6,16}\b")
WHITESPACE_RE = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean merged Ghidra function rows.")
    parser.add_argument("--input", default="data/processed/merged_raw_functions.csv")
    parser.add_argument("--output", default="data/processed/clean_functions.csv")
    parser.add_argument("--summary", default="data/processed/cleaning_summary.md")
    return parser.parse_args()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def non_empty_code_lines(function_code: str) -> list[str]:
    return [line.strip() for line in function_code.splitlines() if line.strip()]


def normalize_code(function_code: str) -> str:
    normalized = ADDRESS_RE.sub("", function_code)
    normalized = WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def normalized_hash(function_code: str) -> str:
    return hashlib.sha256(normalize_code(function_code).encode("utf-8")).hexdigest()


def looks_like_external_wrapper(function_name: str, function_code: str) -> bool:
    code = function_code.strip()
    lines = non_empty_code_lines(function_code)
    if "halt_baddata()" in code:
        return True
    if "PTR_" in code and "(*(code *)" in code and len(lines) <= 12:
        return True
    if "Unknown calling convention" in code and "PTR_" in code and len(lines) <= 16:
        return True
    if function_name.startswith("__imp_") or function_name.endswith("@plt"):
        return True
    return False


def first_removal_reason(
    row: dict[str, str],
    code_line_count: int,
    code_char_count: int,
    seen_hashes: set[str],
    code_hash: str,
) -> str:
    function_name = row.get("function_name", "").strip()
    function_code = row.get("function_code", "")

    if row.get("decompile_status", "") != "success":
        return "non_success_decompile_status"
    if not function_code or not function_code.strip():
        return "empty_function_code"
    if "halt_baddata()" in function_code:
        return "halt_baddata"
    if function_name in BOILERPLATE_FUNCTION_NAMES:
        return "compiler_runtime_boilerplate"
    if looks_like_external_wrapper(function_name, function_code):
        return "external_import_or_thunk"
    if code_line_count < 3:
        return "too_few_code_lines"
    if code_char_count < 40:
        return "too_few_code_characters"
    if code_hash in seen_hashes:
        return "duplicate_normalized_function_body"
    return ""


def inference_exclusion_reason(row: dict[str, str]) -> str:
    """Return a conservative reason a function should skip inference.

    Only unusable decompilations, explicitly named runtime functions, and strong
    import/thunk indicators are excluded. Short functions, ``FUN_*`` functions,
    ambiguous wrappers, duplicates, and unusual compiler output remain eligible
    because they may contain genuine user-code vulnerabilities.
    """
    function_name = row.get("function_name", "").strip()
    normalized_name = function_name.lower()
    function_code = row.get("function_code", "")
    memory_block = row.get("memory_block", "").strip().lower()
    is_external = row.get("is_external", "").strip().lower() in {"true", "1", "yes"}
    is_thunk = row.get("is_thunk", "").strip().lower() in {"true", "1", "yes"}
    has_ghidra_provenance = any(
        column in row for column in ("memory_block", "is_external", "is_thunk")
    )

    if row.get("decompile_status", "") != "success":
        return "non_success_decompile_status"
    if not function_code.strip():
        return "empty_function_code"
    if "halt_baddata()" in function_code:
        return "confirmed_import_stub"
    if function_name in BOILERPLATE_FUNCTION_NAMES:
        return "compiler_runtime_boilerplate"
    if is_external:
        return "ghidra_external_function"
    if is_thunk:
        return "ghidra_thunk_function"
    if memory_block.startswith(".plt"):
        return "ghidra_plt_function"
    if (
        normalized_name.startswith("__imp_")
        or normalized_name.startswith("imp_")
        or normalized_name.startswith("thunk_")
        or normalized_name.startswith("plt_")
        or normalized_name.endswith("@plt")
    ):
        return "confirmed_import_or_thunk"
    if (
        not has_ghidra_provenance
        and "PTR_" in function_code
        and "(*(code *)" in function_code
        and len(non_empty_code_lines(function_code)) <= 12
    ):
        return "legacy_plt_wrapper_pattern"
    return ""


def read_rows(input_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with input_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def write_clean_rows(
    output_path: Path,
    fieldnames: list[str],
    clean_rows: list[dict[str, str]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_fieldnames = list(dict.fromkeys([*fieldnames, *ADDED_COLUMNS]))
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)


def write_summary(
    summary_path: Path,
    input_path: Path,
    output_path: Path,
    total_rows: int,
    kept_rows: int,
    removed_counts: Counter[str],
) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    removed_total = sum(removed_counts.values())

    lines = [
        "# Cleaning Summary",
        "",
        f"Input: `{input_path}`",
        f"Output: `{output_path}`",
        "",
        f"Total input rows: {total_rows}",
        f"Kept rows: {kept_rows}",
        f"Removed rows: {removed_total}",
        "",
        "## Removed Rows By Reason",
        "",
    ]

    if removed_counts:
        for reason, count in removed_counts.most_common():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Functions named `FUN_...` are not removed just because of their names.",
            "- Vulnerability labels are not assigned in this phase.",
        ]
    )

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = resolve_repo_path(args.input)
    output_path = resolve_repo_path(args.output)
    summary_path = resolve_repo_path(args.summary)

    if not input_path.exists():
        print(f"ERROR: Input CSV does not exist: {input_path}")
        return 1

    fieldnames, rows = read_rows(input_path)
    clean_rows: list[dict[str, str]] = []
    removed_counts: Counter[str] = Counter()
    seen_hashes: set[str] = set()

    for row in rows:
        function_code = row.get("function_code", "")
        code_lines = non_empty_code_lines(function_code)
        code_line_count = len(code_lines)
        code_char_count = len(function_code.strip())
        code_hash = normalized_hash(function_code) if function_code.strip() else ""

        reason = first_removal_reason(
            row=row,
            code_line_count=code_line_count,
            code_char_count=code_char_count,
            seen_hashes=seen_hashes,
            code_hash=code_hash,
        )

        enriched_row = dict(row)
        enriched_row["normalized_code_hash"] = code_hash
        enriched_row["code_line_count"] = str(code_line_count)
        enriched_row["code_char_count"] = str(code_char_count)
        enriched_row["cleaning_removed_reason"] = reason

        if reason:
            removed_counts[reason] += 1
            continue

        seen_hashes.add(code_hash)
        enriched_row["cleaning_removed_reason"] = ""
        clean_rows.append(enriched_row)

    write_clean_rows(output_path, fieldnames, clean_rows)
    write_summary(
        summary_path=summary_path,
        input_path=input_path,
        output_path=output_path,
        total_rows=len(rows),
        kept_rows=len(clean_rows),
        removed_counts=removed_counts,
    )

    print(f"Input rows: {len(rows)}")
    print(f"Kept rows: {len(clean_rows)}")
    print(f"Removed rows: {sum(removed_counts.values())}")
    print(f"Output path: {output_path}")
    print(f"Summary path: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
