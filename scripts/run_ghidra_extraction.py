"""Run Ghidra headless extraction for one ELF binary."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GHIDRA_SCRIPT_DIR = REPO_ROOT / "ghidra_scripts"
GHIDRA_SCRIPT_NAME = "extract_functions.py"
GHIDRA_SCRIPT = GHIDRA_SCRIPT_DIR / GHIDRA_SCRIPT_NAME


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Ghidra headless pseudo-C extraction for one ELF binary."
    )
    parser.add_argument("--binary", required=True, help="Path to the ELF binary.")
    parser.add_argument("--output", required=True, help="Path to the output CSV.")
    parser.add_argument(
        "--ghidra-home",
        required=True,
        help="Path to the Ghidra installation, for example /opt/ghidra.",
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Temporary directory for the Ghidra project.",
    )
    parser.add_argument(
        "--project-name",
        required=True,
        help="Temporary Ghidra project name.",
    )
    return parser.parse_args()


def read_ghidra_properties(ghidra_home: Path) -> dict[str, str]:
    properties_path = ghidra_home / "Ghidra" / "application.properties"
    properties: dict[str, str] = {}
    if not properties_path.exists():
        return properties

    for line in properties_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            properties[key.strip()] = value.strip()

    return properties


def ghidra_settings_dir(ghidra_home: Path) -> Path | None:
    properties = read_ghidra_properties(ghidra_home)
    app_name = properties.get("application.name")
    app_version = properties.get("application.version")
    release_name = properties.get("application.release.name")

    if not app_name or not app_version or not release_name:
        return None

    normalized_name = app_name.replace(" ", "").lower()
    versioned_name = f"{normalized_name}_{app_version}_{release_name}"
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return base_dir / normalized_name / versioned_name


def find_pyghidra_python(ghidra_home: Path) -> Path | None:
    settings_dir = ghidra_settings_dir(ghidra_home)
    if settings_dir is None:
        return None

    python_path = settings_dir / "venv" / "bin" / "python3"
    if python_path.exists() and python_path.is_file():
        return python_path

    return None


def pyghidra_available(python_path: Path) -> bool:
    result = subprocess.run(
        [str(python_path), "-c", "import pyghidra"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def validate_paths(binary: Path, ghidra_home: Path) -> None:
    if not binary.exists():
        raise FileNotFoundError(f"Binary path does not exist: {binary}")
    if not binary.is_file():
        raise ValueError(f"Binary path is not a file: {binary}")

    analyze_headless = ghidra_home / "support" / "analyzeHeadless"
    if not analyze_headless.exists():
        raise FileNotFoundError(
            "Ghidra analyzeHeadless was not found at: "
            f"{analyze_headless}"
        )
    if not analyze_headless.is_file():
        raise ValueError(
            "Ghidra analyzeHeadless path is not a file: "
            f"{analyze_headless}"
        )

    pyghidra_run = ghidra_home / "support" / "pyghidraRun"
    if pyghidra_run.exists() and pyghidra_run.is_file():
        return [str(pyghidra_run), "-H", str(ghidra_home)]

    if not GHIDRA_SCRIPT.exists():
        raise FileNotFoundError(f"Ghidra extraction script not found: {GHIDRA_SCRIPT}")


def build_analyze_headless_command(
    analyze_headless: Path,
    project_dir: Path,
    project_name: str,
    binary: Path,
    output: Path,
) -> list[str]:
    return [
        str(analyze_headless),
        str(project_dir),
        project_name,
        "-import",
        str(binary),
        "-scriptPath",
        str(GHIDRA_SCRIPT_DIR),
        "-postScript",
        GHIDRA_SCRIPT_NAME,
        str(output),
        "-deleteProject",
    ]


def build_pyghidra_command(
    pyghidra_python: Path,
    ghidra_home: Path,
    project_dir: Path,
    project_name: str,
    binary: Path,
    output: Path,
) -> list[str]:
    return [
        str(pyghidra_python),
        "-m",
        "pyghidra",
        "--install-dir",
        str(ghidra_home),
        "--project-name",
        project_name,
        "--project-path",
        str(project_dir),
        str(binary),
        str(GHIDRA_SCRIPT),
        str(output),
    ]


def build_command(
    ghidra_home: Path,
    project_dir: Path,
    project_name: str,
    binary: Path,
    output: Path,
) -> list[str]:
    pyghidra_run = ghidra_home / "support" / "pyghidraRun"
    pyghidra_python = find_pyghidra_python(ghidra_home)

    if pyghidra_run.exists() and pyghidra_python is not None:
        if pyghidra_available(pyghidra_python):
            return build_pyghidra_command(
                pyghidra_python=pyghidra_python,
                ghidra_home=ghidra_home,
                project_dir=project_dir,
                project_name=project_name,
                binary=binary,
                output=output,
            )

        raise RuntimeError(
            "PyGhidra is not installed in Ghidra's local virtual environment. "
            "Install it with: "
            f"{pyghidra_python} -m pip install --no-index -f "
            f"{ghidra_home}/Ghidra/Features/PyGhidra/pypkg/dist pyghidra"
        )

    analyze_headless = ghidra_home / "support" / "analyzeHeadless"
    return build_analyze_headless_command(
        analyze_headless=analyze_headless,
        project_dir=project_dir,
        project_name=project_name,
        binary=binary,
        output=output,
    )


def main() -> int:
    args = parse_args()

    binary = Path(args.binary).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    ghidra_home = Path(args.ghidra_home).expanduser().resolve()
    project_dir = Path(args.project_dir).expanduser().resolve()

    try:
        validate_paths(binary, ghidra_home)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        command = build_command(
            ghidra_home=ghidra_home,
            project_dir=project_dir,
            project_name=args.project_name,
            binary=binary,
            output=output,
        )
    except RuntimeError as error:
        print(f"ERROR: {error}")
        return 1

    print("Executing Ghidra command:")
    print(shlex.join(command), flush=True)

    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"ERROR: Ghidra extraction failed with exit code {result.returncode}.")
        return result.returncode

    if not output.exists():
        print(
            "ERROR: Ghidra finished without creating the expected output CSV: "
            f"{output}"
        )
        print("Check the Ghidra log above for script loading or decompilation errors.")
        return 1

    if output.stat().st_size == 0:
        print(f"ERROR: Ghidra created an empty output CSV: {output}")
        return 1

    print(f"Ghidra extraction completed successfully: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
