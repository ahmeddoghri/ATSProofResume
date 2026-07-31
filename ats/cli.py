"""Command-line interface for the ATS audit.

Runs entirely offline with no API key. The rewriting features in the web app
need OpenAI; deciding whether a resume parses does not, and pretending
otherwise would put a paywall in front of the part that is just arithmetic.

    ats score resume.docx --job posting.txt
    ats extract resume.docx --show-dropped
    ats compare before.docx after.docx --job posting.txt
    ats fixtures /tmp/corpus
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from docx.opc.exceptions import PackageNotFoundError

from . import __version__
from .extract import extract
from .score import format_scorecard, score_resume


def _read_job(args: argparse.Namespace) -> str | None:
    """Load the posting from --job, treating it as a path if one exists."""
    if not getattr(args, "job", None):
        return None
    candidate = Path(args.job)
    if candidate.exists():
        return candidate.read_text(encoding="utf-8", errors="replace")
    return args.job


def cmd_score(args: argparse.Namespace) -> int:
    card = score_resume(args.resume, _read_job(args))
    if args.json:
        print(json.dumps(card.to_dict(), indent=2))
    else:
        print(format_scorecard(card, verbose=args.verbose))

    # Exit non-zero on a failing resume so this can gate a workflow.
    if args.min_score is not None and card.parse_score < args.min_score:
        print(
            f"\nFAIL: parse score {card.parse_score} is below --min-score {args.min_score}",
            file=sys.stderr,
        )
        return 1
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    report = extract(args.resume)
    print(f"Parsed {len(report.ats_text.split())} words "
          f"from {report.body_paragraphs} paragraphs and {report.table_count} tables")
    if args.show_dropped:
        dropped = report.dropped_text
        if dropped:
            print(f"\nText a parser never receives ({len(dropped)} snippet(s)):")
            for snippet in dropped:
                print(f"  - {snippet[:100]}")
        else:
            print("\nNothing is dropped; the parser sees the whole document.")
    if args.text:
        print("\n--- text as an ATS reads it ---")
        print(report.ats_text)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Score two resumes and report the delta, for before-and-after checks."""
    job = _read_job(args)
    before = score_resume(args.before, job)
    after = score_resume(args.after, job)

    print(f"{'':22} {'before':>8} {'after':>8} {'delta':>8}")
    rows = [("parse score", before.parse_score, after.parse_score)]
    if job:
        rows.append(("match score", before.match_score, after.match_score))
    rows.append(("critical findings", len(before.critical), len(after.critical)))
    rows.append(("warnings", len(before.warnings), len(after.warnings)))

    for label, old, new in rows:
        delta = new - old
        print(f"{label:22} {old:>8} {new:>8} {delta:>+8}")

    if args.json:
        print(json.dumps({"before": before.to_dict(), "after": after.to_dict()}, indent=2))
    return 0


def cmd_fixtures(args: argparse.Namespace) -> int:
    from .fixtures import build_all

    expected = build_all(args.directory)
    print(f"Wrote {len(expected)} fixtures to {args.directory}")
    for name, defects in expected.items():
        print(f"  {name:20} {', '.join(defects) if defects else '(clean)'}")
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    from .bench import format_report, run_benchmark

    report = run_benchmark()
    print(format_report(report))
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {args.json}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ats", description="Audit a resume for ATS compatibility, offline."
    )
    parser.add_argument("--version", action="version", version=f"ats {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    score = sub.add_parser("score", help="audit a resume and print a scorecard")
    score.add_argument("resume", help="path to a .docx resume")
    score.add_argument("-j", "--job", help="job posting text, or a path to it")
    score.add_argument("--json", action="store_true", help="emit JSON")
    score.add_argument("-v", "--verbose", action="store_true", help="show every finding")
    score.add_argument(
        "--min-score", type=int, default=None,
        help="exit non-zero if the parse score falls below this",
    )
    score.set_defaults(func=cmd_score)

    ext = sub.add_parser("extract", help="show what an ATS actually reads")
    ext.add_argument("resume")
    ext.add_argument("--show-dropped", action="store_true", help="list text parsers miss")
    ext.add_argument("--text", action="store_true", help="print the extracted text")
    ext.set_defaults(func=cmd_extract)

    cmp_ = sub.add_parser("compare", help="score two resumes and diff them")
    cmp_.add_argument("before")
    cmp_.add_argument("after")
    cmp_.add_argument("-j", "--job", help="job posting text, or a path to it")
    cmp_.add_argument("--json", action="store_true")
    cmp_.set_defaults(func=cmd_compare)

    fix = sub.add_parser("fixtures", help="generate the test corpus")
    fix.add_argument("directory", nargs="?", default="fixtures")
    fix.set_defaults(func=cmd_fixtures)

    bench = sub.add_parser("bench", help="score the detector against known defects")
    bench.add_argument("--json", default=None, help="also write raw results here")
    bench.set_defaults(func=cmd_bench)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except PackageNotFoundError:
        # What python-docx raises for a missing file, a legacy .doc, or a PDF
        # someone renamed. All three deserve the same plain explanation.
        target = getattr(args, "resume", None) or getattr(args, "before", "the file")
        print(
            f"error: {target} is not a readable .docx file. "
            "Legacy .doc and PDF resumes must be converted to .docx first.",
            file=sys.stderr,
        )
        return 2
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
