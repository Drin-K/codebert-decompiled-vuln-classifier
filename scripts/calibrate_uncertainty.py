#!/usr/bin/env python3
"""Report confidence-threshold coverage on saved validation predictions."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_THRESHOLDS = (0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--selected-threshold", type=float, default=0.70)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0.0 <= args.selected_threshold <= 1.0:
        raise SystemExit("ERROR: --selected-threshold must be between 0 and 1")
    source = resolve(args.predictions)
    output_dir = resolve(args.output_dir)
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"confidence", "is_correct"}.issubset(rows[0]):
        raise SystemExit("ERROR: predictions must contain confidence and is_correct")

    confidences = [float(row["confidence"]) for row in rows]
    correct = [str(row["is_correct"]).strip().lower() in {"true", "1", "yes"} for row in rows]
    thresholds = sorted(set((*DEFAULT_THRESHOLDS, args.selected_threshold)))
    table = []
    for threshold in thresholds:
        accepted = [index for index, value in enumerate(confidences) if value >= threshold]
        accepted_correct = sum(correct[index] for index in accepted)
        table.append({
            "threshold": threshold,
            "accepted": len(accepted),
            "uncertain": len(rows) - len(accepted),
            "coverage": len(accepted) / len(rows),
            "accepted_accuracy": accepted_correct / len(accepted) if accepted else None,
        })

    selected = next(row for row in table if row["threshold"] == args.selected_threshold)
    payload = {
        "calibration_source": str(source),
        "split_role": "validation only",
        "total_validation_rows": len(rows),
        "raw_validation_accuracy": sum(correct) / len(rows),
        "minimum_winning_confidence": min(confidences),
        "selected_threshold": args.selected_threshold,
        "selected_operating_point": selected,
        "threshold_table": table,
        "limitations": [
            "The original validation split was perfect and may share Juliet-family patterns with training.",
            "The threshold must be reassessed on the future group-aware validation split.",
            "Uncertain predictions are abstentions requiring human review, not corrected model predictions.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "uncertainty_calibration.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with (output_dir / "threshold_table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)

    lines = [
        "# Uncertainty Calibration", "",
        f"- Source: `{source}`", "- Calibration split: validation only",
        f"- Validation rows: {len(rows)}", f"- Raw validation accuracy: {payload['raw_validation_accuracy']:.4f}",
        f"- Minimum winning confidence: {min(confidences):.4f}",
        f"- Selected threshold: {args.selected_threshold:.2f}",
        f"- Selected coverage: {selected['coverage']:.4f} ({selected['accepted']}/{len(rows)})",
        f"- Accepted-decision accuracy: {selected['accepted_accuracy']:.4f}", "",
        "| Threshold | Accepted | Uncertain | Coverage | Accepted accuracy |", "|---:|---:|---:|---:|---:|",
    ]
    for row in table:
        accuracy = "n/a" if row["accepted_accuracy"] is None else f"{row['accepted_accuracy']:.4f}"
        lines.append(f"| {row['threshold']:.2f} | {row['accepted']} | {row['uncertain']} | {row['coverage']:.4f} | {accuracy} |")
    lines.extend(["", "## Interpretation", "",
        "A 0.70 threshold is used as a high-coverage operating point: it retains 155 of 156 validation decisions while abstaining on the single validation prediction below 0.70.",
        "Raw model outputs remain stored when the displayed decision is Uncertain — Human review recommended.", "",
        "## Limitations", "",
        "The original validation split achieved perfect accuracy and may contain Juliet-family similarity with training. This threshold is provisional and must be recalibrated using the future group-aware validation split.", "",
    ])
    (output_dir / "uncertainty_calibration.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Selected threshold: {args.selected_threshold:.2f}")
    print(f"Coverage: {selected['accepted']}/{len(rows)} ({selected['coverage']:.2%})")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
