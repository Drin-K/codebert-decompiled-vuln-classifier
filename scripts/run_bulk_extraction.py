"""Run Ghidra extraction for every ELF binary in an input directory."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SINGLE_EXTRACTION_SCRIPT = REPO_ROOT / "scripts" / "run_ghidra_extraction.py"
NON_BINARY_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".csv",
    ".h",
    ".hpp",
    ".json",
    ".md",
    ".py",
    ".txt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Ghidra pseudo-C extraction for all ELF binaries in a folder."
    )
    parser.add_argument("--input-dir", default="data/binaries")
    parser.add_argument("--output-dir", default="data/raw")
    parser.add_argument("--ghidra-home", default="/opt/ghidra")
    parser.add_argument("--project-dir", default="/tmp/ghidra_projects")
    return parser.parse_args()


def is_elf_file(path: Path) -> bool:
    if path.name == ".gitkeep" or not path.is_file():
        return False
    if path.suffix.lower() in NON_BINARY_SUFFIXES:
        return False

    try:
        with path.open("rb") as file:
            return file.read(4) == b"\x7fELF"
    except OSError:
        return False


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def safe_project_name(binary: Path) -> str:
    safe_binary_name = safe_name(binary.stem)
    return f"{safe_binary_name}_ghidra_project"


def output_csv_path(output_dir: Path, input_dir: Path, binary: Path) -> Path:
    relative_binary = binary.relative_to(input_dir)
    relative_stem = relative_binary.with_suffix("").as_posix()
    safe_relative_name = safe_name(relative_stem.replace("/", "_"))
    return output_dir / f"{safe_relative_name}_functions.csv"


def run_one_binary(
    binary: Path,
    output: Path,
    ghidra_home: Path,
    project_dir: Path,
) -> int:
    command = [
        sys.executable,
        str(SINGLE_EXTRACTION_SCRIPT),
        "--binary",
        str(binary),
        "--output",
        str(output),
        "--ghidra-home",
        str(ghidra_home),
        "--project-dir",
        str(project_dir),
        "--project-name",
        safe_project_name(binary),
    ]

    print()
    print(f"Processing binary: {binary}")
    result = subprocess.run(command, check=False)
    return result.returncode


def main() -> int:
    args = parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    ghidra_home = Path(args.ghidra_home).expanduser().resolve()
    project_dir = Path(args.project_dir).expanduser().resolve()

    if not input_dir.exists():
        print(f"ERROR: Input directory does not exist: {input_dir}")
        return 1
    if not input_dir.is_dir():
        print(f"ERROR: Input path is not a directory: {input_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    binaries = sorted(path for path in input_dir.rglob("*") if is_elf_file(path))
    if not binaries:
        print(f"No ELF binaries found in: {input_dir}")
        return 0

    processed = 0
    successful = 0
    failed = 0

    for binary in binaries:
        processed += 1
        output = output_csv_path(output_dir, input_dir, binary)
        return_code = run_one_binary(binary, output, ghidra_home, project_dir)

        if return_code == 0:
            successful += 1
        else:
            failed += 1

    print()
    print("Bulk extraction summary:")
    print(f"Processed binaries: {processed}")
    print(f"Successful extractions: {successful}")
    print(f"Failed extractions: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
