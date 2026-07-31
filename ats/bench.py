"""Scoring the detector against resumes whose defects are known in advance.

The claim this repository makes is that it can tell you whether a resume will
survive an ATS. That claim is only worth anything if the detector itself has
been measured, so this benchmark builds the fixture corpus, runs every check,
and reports precision and recall against the planted defects.

Recall answers "does it find real problems". Precision answers the question
that actually decides whether a tool gets used twice: "does it invent problems
that are not there". A linter that cries wolf on a clean resume is worse than
no linter, because people learn to ignore it.

Everything is deterministic: fixtures are generated from code, checks have no
randomness, and no network call is involved.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence

from .fixtures import JOB_POSTING, build_all
from .score import score_resume


def run_benchmark(directory: str | Path | None = None) -> Dict:
    """Build the corpus, audit every fixture, and score the detector."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(directory) if directory else Path(tmp)
        expected = build_all(target)

        cases: List[Dict] = []
        true_positives = false_positives = false_negatives = 0

        for name, planted in expected.items():
            card = score_resume(target / f"{name}.docx", JOB_POSTING)
            fired = sorted({f.check for f in card.findings})

            # A fixture is built to contain specific defects. Anything else the
            # detector reports on it is counted against precision, which is
            # strict on purpose: the "clean" fixture must fire nothing at all.
            hits = [c for c in planted if c in fired]
            spurious = [c for c in fired if c not in planted]
            missed = [c for c in planted if c not in fired]

            true_positives += len(hits)
            false_positives += len(spurious)
            false_negatives += len(missed)

            cases.append(
                {
                    "fixture": name,
                    "planted": planted,
                    "fired": fired,
                    "missed": missed,
                    "spurious": spurious,
                    "parse_score": card.parse_score,
                    "grade": card.grade,
                    "match_score": card.match_score,
                    "critical": len(card.critical),
                    "warnings": len(card.warnings),
                }
            )

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) else 1.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) else 1.0
    )
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    clean = next(c for c in cases if c["fixture"] == "clean")
    defective = [c for c in cases if c["fixture"] != "clean"]

    return {
        "cases": sorted(cases, key=lambda c: c["fixture"]),
        "totals": {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
        "separation": {
            # The number that matters in practice: a clean resume has to score
            # clearly above the broken ones, not merely one point above.
            "clean_parse_score": clean["parse_score"],
            "worst_defective_parse_score": min(c["parse_score"] for c in defective),
            "mean_defective_parse_score": round(
                sum(c["parse_score"] for c in defective) / len(defective), 1
            ),
            "gap": clean["parse_score"]
            - round(sum(c["parse_score"] for c in defective) / len(defective), 1),
        },
    }


def format_report(report: Dict) -> str:
    """Render the benchmark as a Markdown table."""
    lines = [
        "| fixture | parse | grade | planted defects | detected | spurious |",
        "| --- | ---: | :---: | --- | :---: | :---: |",
    ]
    for case in report["cases"]:
        planted = ", ".join(case["planted"]) or "(none)"
        detected = "n/a" if not case["planted"] else (
            "yes" if not case["missed"] else "NO"
        )
        lines.append(
            f"| {case['fixture']} | {case['parse_score']} | {case['grade']} | "
            f"{planted} | {detected} | {len(case['spurious'])} |"
        )

    totals = report["totals"]
    sep = report["separation"]
    lines += [
        "",
        f"Precision {totals['precision']:.2f}, recall {totals['recall']:.2f}, "
        f"F1 {totals['f1']:.2f} "
        f"({totals['true_positives']} TP, {totals['false_positives']} FP, "
        f"{totals['false_negatives']} FN).",
        f"Clean resume scores {sep['clean_parse_score']}; defective resumes average "
        f"{sep['mean_defective_parse_score']}, a {sep['gap']:.1f} point gap.",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark the ATS defect detector.")
    parser.add_argument("--json", default="benchmark.json")
    args = parser.parse_args(argv)

    report = run_benchmark()
    print(format_report(report))
    Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
