"""Regression tests for conservative inference-time function filtering."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from clean_functions import inference_exclusion_reason  # noqa: E402


def function_row(name: str) -> dict[str, str]:
    return {
        "function_name": name,
        "function_code": "void function(void) { return; }",
        "decompile_status": "success",
        "memory_block": ".text",
        "is_external": "False",
        "is_thunk": "False",
    }


class InferenceFilteringTests(unittest.TestCase):
    def test_confirmed_stripped_runtime_names_are_excluded(self) -> None:
        for name in ("entry", "_DT_INIT", "_FINI_0", "_DT_FINI"):
            with self.subTest(name=name):
                self.assertEqual(
                    inference_exclusion_reason(function_row(name)),
                    "compiler_runtime_boilerplate",
                )

    def test_ambiguous_names_remain_eligible(self) -> None:
        for name in ("FUN_00401234", "short_helper", "wrapper_like_name"):
            with self.subTest(name=name):
                self.assertEqual(inference_exclusion_reason(function_row(name)), "")


if __name__ == "__main__":
    unittest.main()
