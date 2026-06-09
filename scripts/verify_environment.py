"""Verify the Phase 1 Python environment for the thesis repository."""

from __future__ import annotations

import importlib
import platform
import sys


PACKAGES = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("scikit-learn", "sklearn"),
    ("torch", "torch"),
    ("transformers", "transformers"),
    ("datasets", "datasets"),
]


def package_version(module: object) -> str:
    return str(getattr(module, "__version__", "version unavailable"))


def check_import(display_name: str, import_name: str) -> bool:
    try:
        module = importlib.import_module(import_name)
    except ImportError as error:
        print(f"[MISSING] {display_name}: {error}")
        return False

    print(f"[OK] {display_name}: {package_version(module)}")
    return True


def check_cuda() -> None:
    try:
        torch = importlib.import_module("torch")
    except ImportError:
        print("[CUDA] PyTorch is not installed, so CUDA could not be checked.")
        return

    cuda_available = torch.cuda.is_available()
    print(f"[CUDA] Available: {cuda_available}")

    if cuda_available:
        print(f"[CUDA] Device: {torch.cuda.get_device_name(0)}")
    else:
        print("[CUDA] No CUDA GPU detected. This is acceptable for Phase 1.")


def main() -> int:
    print("CodeBERT Decompiled Vulnerability Classifier - Environment Check")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print()

    results = [check_import(name, import_name) for name, import_name in PACKAGES]
    print()
    check_cuda()
    print()

    if all(results):
        print("Environment check completed successfully.")
        return 0

    print("Environment check completed with missing dependencies.")
    print("Install dependencies with: pip install -r requirements.txt")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
