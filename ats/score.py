"""The scorecard.

Two independent numbers, deliberately not averaged into one:

``parse_score``
    Can an ATS read this document at all? Starts at 100 and subtracts each
    finding's penalty. This is the score that matters most, because a resume
    that does not parse is not evaluated on its contents.

``match_score``
    Given what was parsed, how much of the posting's vocabulary is present?
    Zero when no job description is supplied, since there is nothing to match
    against and inventing a number would be worse than admitting that.

Keeping them apart matters: a beautifully keyword-stuffed resume trapped in a
two-column table scores 95 on match and 40 on parse, and the honest advice is
about the table, not the keywords.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .checks import Finding, run_all
from .extract import ExtractionReport, extract
from .keywords import KeywordReport, match

GRADE_BANDS = ((90, "A"), (80, "B"), (70, "C"), (60, "D"), (0, "F"))


@dataclass
class Scorecard:
    """The full result of auditing one resume."""

    parse_score: int
    findings: List[Finding] = field(default_factory=list)
    keywords: Optional[KeywordReport] = None
    extraction: Optional[ExtractionReport] = None
    path: str = ""

    @property
    def match_score(self) -> int:
        if self.keywords is None:
            return 0
        # Weighted coverage dominates: matching the term a posting repeats six
        # times counts for more than matching six one-off terms.
        blended = 0.7 * self.keywords.weighted_coverage + 0.3 * self.keywords.coverage
        return round(100 * blended)

    @property
    def grade(self) -> str:
        for threshold, letter in GRADE_BANDS:
            if self.parse_score >= threshold:
                return letter
        return "F"

    @property
    def critical(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "critical"]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "parse_score": self.parse_score,
            "grade": self.grade,
            "match_score": self.match_score if self.keywords else None,
            "findings": [
                {
                    "check": f.check,
                    "severity": f.severity,
                    "message": f.message,
                    "evidence": f.evidence,
                    "penalty": f.penalty,
                }
                for f in self.findings
            ],
            "keywords": (
                {
                    "coverage": round(self.keywords.coverage, 4),
                    "weighted_coverage": round(self.keywords.weighted_coverage, 4),
                    "matched": [t for t, _ in self.keywords.matched[:30]],
                    "missing": [t for t, _ in self.keywords.missing[:30]],
                    "missing_requirements": self.keywords.missing_requirements,
                }
                if self.keywords else None
            ),
            "extraction": (
                {
                    "body_paragraphs": self.extraction.body_paragraphs,
                    "tables": self.extraction.table_count,
                    "images": self.extraction.image_count,
                    "dropped_snippets": len(self.extraction.dropped_text),
                    "parsed_words": len(self.extraction.ats_text.split()),
                }
                if self.extraction else None
            ),
        }


def score_report(
    report: ExtractionReport, job_description: str | None = None, path: str = ""
) -> Scorecard:
    """Score an already-extracted document."""
    findings = run_all(report)
    parse_score = max(0, 100 - sum(f.penalty for f in findings))
    keywords = (
        match(report.ats_text, job_description) if job_description else None
    )
    return Scorecard(
        parse_score=parse_score,
        findings=findings,
        keywords=keywords,
        extraction=report,
        path=path,
    )


def score_resume(
    resume_path: str | Path, job_description: str | None = None
) -> Scorecard:
    """Audit a DOCX resume, optionally against a job posting."""
    report = extract(resume_path)
    return score_report(report, job_description, path=str(resume_path))


def format_scorecard(card: Scorecard, verbose: bool = False) -> str:
    """Render a scorecard as readable terminal output."""
    lines: List[str] = []
    if card.path:
        lines.append(str(card.path))
    lines.append(f"Parse score: {card.parse_score}/100  (grade {card.grade})")
    if card.keywords is not None:
        lines.append(
            f"Match score: {card.match_score}/100  "
            f"({len(card.keywords.matched)} of "
            f"{len(card.keywords.matched) + len(card.keywords.missing)} terms present)"
        )

    if card.extraction:
        e = card.extraction
        lines.append(
            f"Parsed {len(e.ats_text.split())} words, {e.body_paragraphs} paragraphs, "
            f"{e.table_count} tables, {e.image_count} images"
        )
        if e.dropped_text:
            lines.append(f"Text a parser never sees: {len(e.dropped_text)} snippet(s)")

    if card.findings:
        lines.append("")
        lines.append("Findings:")
        shown = card.findings if verbose else card.findings[:10]
        lines.extend(f"  {finding}" for finding in shown)
        if not verbose and len(card.findings) > len(shown):
            lines.append(f"  ... {len(card.findings) - len(shown)} more (use --verbose)")
    else:
        lines.append("")
        lines.append("No structural problems found.")

    if card.keywords and card.keywords.top_missing:
        lines.append("")
        lines.append("Top missing keywords:")
        lines.append("  " + ", ".join(card.keywords.top_missing))
        if card.keywords.missing_requirements:
            lines.append(
                "  From stated requirements: "
                + ", ".join(card.keywords.missing_requirements[:10])
            )

    return "\n".join(lines)
