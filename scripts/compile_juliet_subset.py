"""Compile a deterministic subset of Juliet CWE sources into ELF binaries."""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VARIANT_RE = re.compile(r"_(0[1-9]|1[0-8])\.(c|cpp)$", re.IGNORECASE)


@dataclass(frozen=True)
class CweTarget:
    folder: str
    cwe: str
    expected_class: str
    output_folder: str
    prefer_c: bool


@dataclass(frozen=True)
class CompilePlan:
    source_path: Path
    target: CweTarget
    output_path: Path
    harness_path: Path
    support_object_path: Path | None
    io_c_path: Path | None
    compiler: str
    command: list[str]


TARGETS = [
    CweTarget(
        folder="CWE121_Stack_Based_Buffer_Overflow",
        cwe="CWE-121",
        expected_class="Buffer Overflow",
        output_folder="CWE121",
        prefer_c=True,
    ),
    CweTarget(
        folder="CWE122_Heap_Based_Buffer_Overflow",
        cwe="CWE-122",
        expected_class="Buffer Overflow",
        output_folder="CWE122",
        prefer_c=False,
    ),
    CweTarget(
        folder="CWE134_Uncontrolled_Format_String",
        cwe="CWE-134",
        expected_class="Format String",
        output_folder="CWE134",
        prefer_c=True,
    ),
    CweTarget(
        folder="CWE190_Integer_Overflow",
        cwe="CWE-190",
        expected_class="Integer Overflow",
        output_folder="CWE190",
        prefer_c=True,
    ),
]


MANIFEST_COLUMNS = [
    "binary_name",
    "binary_path",
    "source_path",
    "source_type",
    "source_name",
    "cwe",
    "expected_class",
    "architecture",
    "compiler",
    "optimization",
    "debug_symbols",
    "compile_status",
    "notes",
]
SUPPORTED_CWE_LIMIT_KEYS = tuple(target.output_folder for target in TARGETS)


def normalize_argv(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "--optimization" and index + 1 < len(argv):
            normalized.append(f"--optimization={argv[index + 1]}")
            index += 2
            continue
        normalized.append(argv[index])
        index += 1
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a small deterministic Juliet subset into ELF binaries."
    )
    parser.add_argument("--juliet-root", default="data/source_datasets/elfFILES")
    parser.add_argument("--output-dir", default="data/binaries/juliet")
    parser.add_argument("--manifest", default="data/binaries_manifest.csv")
    parser.add_argument("--limit-per-cwe", type=int, default=10)
    parser.add_argument(
        "--cwe-limits",
        help=(
            "Comma-separated per-CWE source limits, for example "
            "CWE121=250,CWE122=250,CWE134=400,CWE190=400. "
            "When provided, all supported CWE keys must be present."
        ),
    )
    parser.add_argument("--optimization", default="-O0")
    parser.add_argument("--debug-symbols", action="store_true")
    parser.add_argument("--strip", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(normalize_argv(sys.argv[1:]))


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def is_eligible_source(path: Path) -> bool:
    name_lower = path.name.lower()
    if path.suffix.lower() not in {".c", ".cpp"}:
        return False
    if any(token in name_lower for token in ("w32", "windows", "wchar_t")):
        return False
    if not VARIANT_RE.search(path.name):
        return False
    return True


def source_sort_key(path: Path, prefer_c: bool) -> tuple[int, str]:
    language_priority = 0 if path.suffix.lower() == ".c" else 1
    if not prefer_c:
        language_priority = 0
    return language_priority, str(path).lower()


def find_support_dirs(juliet_root: Path) -> list[Path]:
    preferred_support_dir = juliet_root / "testcasesupport"
    support_dirs: list[Path] = []
    seen: set[Path] = set()

    if preferred_support_dir.exists() and preferred_support_dir.is_dir():
        preferred = preferred_support_dir.resolve()
        support_dirs.append(preferred)
        seen.add(preferred)

    search_roots = [juliet_root, juliet_root.parent]

    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_dir() and path.name.lower() == "testcasesupport":
                resolved = path.resolve()
                if resolved not in seen:
                    support_dirs.append(resolved)
                    seen.add(resolved)

    return support_dirs


def validate_required_support(juliet_root: Path) -> Path | None:
    support_dir = juliet_root / "testcasesupport"
    std_testcase = support_dir / "std_testcase.h"

    if support_dir.exists() and support_dir.is_dir() and std_testcase.exists():
        return support_dir.resolve()

    print("Missing Juliet testcasesupport folder or std_testcase.h.")
    print("Please copy the Juliet C/testcasesupport folder into:")
    print("data/source_datasets/elfFILES/testcasesupport")
    return None


def find_io_c(support_dirs: list[Path]) -> Path | None:
    for support_dir in support_dirs:
        io_c = support_dir / "io.c"
        if io_c.exists() and io_c.is_file():
            return io_c
    return None


def safe_binary_name(output_folder: str, source_path: Path) -> str:
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", source_path.stem)
    return f"juliet_{output_folder}_{safe_stem}"


def parse_cwe_limits(cwe_limits_text: str) -> dict[str, int]:
    limits: dict[str, int] = {}
    supported = set(SUPPORTED_CWE_LIMIT_KEYS)

    for item in cwe_limits_text.split(","):
        item = item.strip()
        if not item:
            raise ValueError("empty item in --cwe-limits")
        if "=" not in item:
            raise ValueError(
                f"invalid --cwe-limits item {item!r}; expected KEY=VALUE"
            )

        key, value_text = (part.strip() for part in item.split("=", 1))
        if key not in supported:
            supported_text = ", ".join(SUPPORTED_CWE_LIMIT_KEYS)
            raise ValueError(
                f"unknown CWE key {key!r}; supported keys are: {supported_text}"
            )
        if key in limits:
            raise ValueError(f"duplicate CWE key {key!r} in --cwe-limits")

        try:
            value = int(value_text)
        except ValueError as exc:
            raise ValueError(
                f"limit for {key} must be an integer, got {value_text!r}"
            ) from exc

        if value <= 0:
            raise ValueError(f"limit for {key} must be greater than zero")

        limits[key] = value

    missing = [key for key in SUPPORTED_CWE_LIMIT_KEYS if key not in limits]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            "missing CWE limit(s): "
            f"{missing_text}. Provide all supported keys when using --cwe-limits."
        )

    return limits


def compile_limits(limit_per_cwe: int, cwe_limits_text: str | None) -> dict[str, int]:
    if cwe_limits_text is not None:
        return parse_cwe_limits(cwe_limits_text)
    return {target.output_folder: limit_per_cwe for target in TARGETS}


def selected_sources(
    juliet_root: Path,
    limits_by_cwe: dict[str, int],
) -> dict[str, list[Path]]:
    selected: dict[str, list[Path]] = {}

    for target in TARGETS:
        cwe_dir = juliet_root / target.folder
        if not cwe_dir.exists():
            selected[target.output_folder] = []
            continue

        candidates = [
            path
            for path in cwe_dir.rglob("*")
            if path.is_file() and is_eligible_source(path)
        ]
        candidates.sort(key=lambda path: source_sort_key(path, target.prefer_c))
        limit = limits_by_cwe[target.output_folder]
        selected[target.output_folder] = candidates[:limit]

    return selected


def build_compile_plan(
    source_path: Path,
    target: CweTarget,
    output_dir: Path,
    juliet_root: Path,
    support_dirs: list[Path],
    io_c: Path | None,
    optimization: str,
    debug_symbols: bool,
) -> CompilePlan:
    compiler = "g++" if source_path.suffix.lower() == ".cpp" else "gcc"
    binary_name = safe_binary_name(target.output_folder, source_path)
    output_path = output_dir / target.output_folder / binary_name
    harness_suffix = ".main.cpp" if source_path.suffix.lower() == ".cpp" else ".main.c"
    harness_path = output_path.with_suffix(harness_suffix)
    support_object_path = (
        output_path.with_suffix(".io.o")
        if io_c is not None and source_path.suffix.lower() == ".cpp"
        else None
    )

    include_dirs = [source_path.parent, juliet_root, *support_dirs]
    deduped_include_dirs = list(dict.fromkeys(include_dirs))

    command = [compiler, optimization]
    if debug_symbols:
        command.append("-g")

    for include_dir in deduped_include_dirs:
        command.extend(["-I", str(include_dir)])

    command.append(str(source_path))
    command.append(str(harness_path))
    if io_c is not None and source_path.suffix.lower() == ".c":
        command.append(str(io_c))
    if support_object_path is not None:
        command.append(str(support_object_path))

    command.extend(["-o", str(output_path)])

    return CompilePlan(
        source_path=source_path,
        target=target,
        output_path=output_path,
        harness_path=harness_path,
        support_object_path=support_object_path,
        io_c_path=io_c,
        compiler=compiler,
        command=command,
    )


def short_error_summary(stderr: str, stdout: str) -> str:
    text = "\n".join(part for part in (stderr, stdout) if part).strip()
    if not text:
        return "compiler returned a non-zero exit code"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " | ".join(lines[:3])[:500]


def architecture_for_binary(binary_path: Path) -> str:
    result = subprocess.run(
        ["file", str(binary_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def manifest_row(
    plan: CompilePlan,
    optimization: str,
    debug_symbols: bool,
    compile_status: str,
    notes: str,
    architecture: str = "",
) -> dict[str, str]:
    return {
        "binary_name": plan.output_path.name,
        "binary_path": str(plan.output_path.relative_to(REPO_ROOT)),
        "source_path": str(plan.source_path.relative_to(REPO_ROOT)),
        "source_type": plan.source_path.suffix.lower().lstrip("."),
        "source_name": plan.source_path.name,
        "cwe": plan.target.cwe,
        "expected_class": plan.target.expected_class,
        "architecture": architecture,
        "compiler": plan.compiler,
        "optimization": optimization,
        "debug_symbols": str(debug_symbols),
        "compile_status": compile_status,
        "notes": notes,
    }


def read_existing_manifest(manifest_path: Path) -> list[dict[str, str]]:
    if not manifest_path.exists():
        return []

    with manifest_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            rows.append({column: row.get(column, "") for column in MANIFEST_COLUMNS})
        return rows


def write_manifest(manifest_path: Path, new_rows: list[dict[str, str]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    existing_rows = read_existing_manifest(manifest_path)
    replaced_sources = {row["source_path"] for row in new_rows}
    kept_rows = [
        row for row in existing_rows if row.get("source_path", "") not in replaced_sources
    ]
    rows = kept_rows + new_rows

    with manifest_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def harness_code(plan: CompilePlan) -> str:
    function_prefix = plan.source_path.stem
    if plan.source_path.suffix.lower() == ".cpp":
        return "\n".join(
            [
                "/* Auto-generated temporary Juliet harness for static compilation. */",
                "#include \"std_testcase.h\"",
                "",
                f"namespace {function_prefix}",
                "{",
                "    void bad();",
                "    void good();",
                "}",
                "",
                "int main(int argc, char **argv)",
                "{",
                "    globalArgc = argc;",
                "    globalArgv = argv;",
                f"    {function_prefix}::bad();",
                f"    {function_prefix}::good();",
                "    return 0;",
                "}",
                "",
            ]
        )

    return "\n".join(
        [
            "/* Auto-generated temporary Juliet harness for static compilation. */",
            "#include \"std_testcase.h\"",
            "",
            f"void {function_prefix}_bad();",
            f"void {function_prefix}_good();",
            "",
            "int main(int argc, char **argv)",
            "{",
            "    globalArgc = argc;",
            "    globalArgv = argv;",
            f"    {function_prefix}_bad();",
            f"    {function_prefix}_good();",
            "    return 0;",
            "}",
            "",
        ]
    )


def compile_plan(plan: CompilePlan, strip_binary: bool) -> tuple[str, str, str]:
    plan.output_path.parent.mkdir(parents=True, exist_ok=True)

    plan.harness_path.write_text(harness_code(plan), encoding="utf-8")

    try:
        if plan.support_object_path is not None and plan.io_c_path is not None:
            support_result = subprocess.run(
                [
                    "gcc",
                    "-c",
                    str(plan.io_c_path),
                    "-o",
                    str(plan.support_object_path),
                    "-I",
                    str(plan.io_c_path.parent),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if support_result.returncode != 0:
                return (
                    "failed",
                    "support io.c compile failed: "
                    + short_error_summary(support_result.stderr, support_result.stdout),
                    "",
                )

        result = subprocess.run(
            plan.command,
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        plan.harness_path.unlink(missing_ok=True)
        if plan.support_object_path is not None:
            plan.support_object_path.unlink(missing_ok=True)

    if result.returncode != 0:
        return "failed", short_error_summary(result.stderr, result.stdout), ""

    if strip_binary:
        strip_result = subprocess.run(
            ["strip", str(plan.output_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if strip_result.returncode != 0:
            notes = "compiled, but strip failed: "
            notes += short_error_summary(strip_result.stderr, strip_result.stdout)
            return "success", notes, architecture_for_binary(plan.output_path)

    return "success", "", architecture_for_binary(plan.output_path)


def print_dry_run(plans: list[CompilePlan]) -> None:
    current_cwe = None
    for plan in plans:
        if current_cwe != plan.target.output_folder:
            current_cwe = plan.target.output_folder
            print()
            print(f"{current_cwe}:")
        print(f"  source: {plan.source_path}")
        print(f"  output: {plan.output_path}")
        print(f"  command: {' '.join(plan.command)}")


def main() -> int:
    args = parse_args()

    juliet_root = resolve_repo_path(args.juliet_root)
    output_dir = resolve_repo_path(args.output_dir)
    manifest_path = resolve_repo_path(args.manifest)

    if args.limit_per_cwe < 0:
        print("ERROR: --limit-per-cwe must be zero or greater.")
        return 1
    try:
        limits_by_cwe = compile_limits(args.limit_per_cwe, args.cwe_limits)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if not juliet_root.exists():
        print(f"ERROR: Juliet root does not exist: {juliet_root}")
        return 1
    if not juliet_root.is_dir():
        print(f"ERROR: Juliet root is not a directory: {juliet_root}")
        return 1

    required_support_dir = validate_required_support(juliet_root)
    if required_support_dir is None:
        return 1

    support_dirs = find_support_dirs(juliet_root)
    if required_support_dir not in support_dirs:
        support_dirs.insert(0, required_support_dir)

    io_c = find_io_c(support_dirs)
    selected = selected_sources(juliet_root, limits_by_cwe)

    target_by_output = {target.output_folder: target for target in TARGETS}
    plans: list[CompilePlan] = []
    for output_folder, sources in selected.items():
        target = target_by_output[output_folder]
        for source_path in sources:
            plans.append(
                build_compile_plan(
                    source_path=source_path,
                    target=target,
                    output_dir=output_dir,
                    juliet_root=juliet_root,
                    support_dirs=support_dirs,
                    io_c=io_c,
                    optimization=args.optimization,
                    debug_symbols=args.debug_symbols,
                )
            )

    print(f"Selected files: {len(plans)}")
    for target in TARGETS:
        print(f"  {target.output_folder}: {len(selected[target.output_folder])}")

    if args.dry_run:
        print_dry_run(plans)
        print()
        print("Dry run complete. No files were compiled and no manifest was written.")
        return 0

    new_rows: list[dict[str, str]] = []
    successes = {target.output_folder: 0 for target in TARGETS}
    failures = {target.output_folder: 0 for target in TARGETS}

    for plan in plans:
        print(f"Compiling {plan.source_path} -> {plan.output_path}")
        status, notes, architecture = compile_plan(plan, args.strip)
        if status == "success":
            successes[plan.target.output_folder] += 1
        else:
            failures[plan.target.output_folder] += 1

        new_rows.append(
            manifest_row(
                plan=plan,
                optimization=args.optimization,
                debug_symbols=args.debug_symbols,
                compile_status=status,
                notes=notes,
                architecture=architecture,
            )
        )

    write_manifest(manifest_path, new_rows)

    print()
    print("Juliet compile summary:")
    print(f"Total selected files: {len(plans)}")
    for target in TARGETS:
        print(
            f"{target.output_folder}: "
            f"success={successes[target.output_folder]}, "
            f"failed={failures[target.output_folder]}"
        )
    print(f"Output directory: {output_dir}")
    print(f"Manifest path: {manifest_path}")

    total_failures = sum(failures.values())
    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
