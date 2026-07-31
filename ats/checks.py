"""Structural checks against known ATS parser failure modes.

Every check here corresponds to something that actually breaks resume parsing,
and every one is decided from the document itself rather than from a model's
opinion. A check either fires or it does not, and the reason it fired names the
specific text or element responsible so the finding can be verified by hand.

Severity is about consequence, not style:

``critical``
    Content is lost or scrambled before a human reads it. Contact details in a
    header, a two-column table layout, a phone number that only exists inside
    an image.
``warning``
    Content survives but is likely to be misfiled: unrecognized section names,
    dates the parser cannot read, glyphs that mangle on extraction.
``info``
    Worth knowing, not worth failing over.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, List

from .extract import ExtractionReport

SEVERITIES = ("critical", "warning", "info")

# Headings mainstream parsers recognize. A resume that calls its work history
# "Where I've Been" still reads fine to a person and lands in no field at all.
CANONICAL_SECTIONS = {
    "experience": (
        "experience", "work experience", "professional experience",
        "employment", "employment history", "work history", "career history",
    ),
    "education": ("education", "academic background", "academics", "degrees"),
    "skills": (
        "skills", "technical skills", "core competencies", "competencies",
        "technologies", "areas of expertise",
    ),
}

# Date ranges a parser can turn into a duration. "Summer '19" cannot be.
DATE_PATTERNS = (
    r"\b(19|20)\d{2}\s*[-–—]\s*((19|20)\d{2}|present|current)\b",
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(19|20)\d{2}\b",
    r"\b\d{1,2}/(19|20)\d{2}\b",
)

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")

# Glyphs that commonly survive as mojibake or vanish in plain-text extraction.
RISKY_GLYPHS = {
    "•": "bullet",       # • renders, but often extracts as junk
    "▪": "small square bullet",
    "⁃": "hyphen bullet",
    "": "Symbol-font bullet",  # Wingdings private-use area; extracts as garbage
    "–": "en dash",
    "—": "em dash",
    "“": "curly quote",
    "’": "curly apostrophe",
}


@dataclass
class Finding:
    """One detected problem, with the evidence that triggered it."""

    check: str
    severity: str
    message: str
    evidence: str = ""
    penalty: int = 0

    def __str__(self) -> str:
        tail = f"  ({self.evidence})" if self.evidence else ""
        return f"[{self.severity}] {self.check}: {self.message}{tail}"


Check = Callable[[ExtractionReport], List[Finding]]
_REGISTRY: List[Check] = []


def check(func: Check) -> Check:
    """Register a check so :func:`run_all` picks it up."""
    _REGISTRY.append(func)
    return func


@check
def dropped_content(report: ExtractionReport) -> List[Finding]:
    """Text in headers, footers, or text boxes that a parser never sees."""
    findings: List[Finding] = []

    for label, snippets, penalty in (
        ("header", report.header_texts, 12),
        ("footer", report.footer_texts, 8),
        ("text box", report.textbox_texts, 15),
    ):
        for snippet in snippets:
            # Losing contact details is categorically worse than losing a page
            # number, so weight the finding by what the text contains.
            has_contact = bool(EMAIL_RE.search(snippet) or PHONE_RE.search(snippet))
            findings.append(
                Finding(
                    check="dropped_content",
                    severity="critical",
                    message=(
                        f"Contact details sit in the {label} and will not be parsed"
                        if has_contact
                        else f"Text in the {label} is dropped by most parsers"
                    ),
                    evidence=snippet[:80],
                    penalty=penalty + (13 if has_contact else 0),
                )
            )
    return findings


@check
def table_layout(report: ExtractionReport) -> List[Finding]:
    """Tables, which parsers flatten cell by cell and scramble."""
    if not report.has_tables:
        return []

    # One table holding most of the document is a layout grid, not a data
    # table, and it destroys reading order for everything inside it.
    cell_chars = sum(len(t) for t in report.table_cell_texts)
    total_chars = max(len(report.ats_text), 1)
    share = cell_chars / total_chars

    if share > 0.5:
        return [
            Finding(
                check="table_layout",
                severity="critical",
                message=(
                    f"{share:.0%} of the resume sits inside {report.table_count} "
                    "table(s); parsers flatten these row by row and scramble reading order"
                ),
                evidence=f"{len(report.table_cell_texts)} cells",
                penalty=25,
            )
        ]
    return [
        Finding(
            check="table_layout",
            severity="warning",
            message=(
                f"{report.table_count} table(s) present; content is flattened "
                "cell by cell, which can interleave unrelated lines"
            ),
            evidence=f"{share:.0%} of text",
            penalty=8,
        )
    ]


@check
def contact_details(report: ExtractionReport) -> List[Finding]:
    """An email and phone number reachable in the parsed body text."""
    findings: List[Finding] = []
    if not EMAIL_RE.search(report.ats_text):
        in_human = EMAIL_RE.search(report.human_text)
        findings.append(
            Finding(
                check="contact_details",
                severity="critical",
                message=(
                    "Email address exists but not where a parser will find it"
                    if in_human
                    else "No email address found in the parsed text"
                ),
                penalty=20,
            )
        )
    if not PHONE_RE.search(report.ats_text):
        findings.append(
            Finding(
                check="contact_details",
                severity="warning",
                message="No phone number found in the parsed text",
                penalty=8,
            )
        )
    return findings


@check
def image_only_content(report: ExtractionReport) -> List[Finding]:
    """Images, which carry no text at all without OCR."""
    if report.image_count == 0:
        return []
    return [
        Finding(
            check="image_only_content",
            severity="info" if report.image_count == 1 else "warning",
            message=(
                f"{report.image_count} image(s) embedded; ATS parsers do not run OCR, "
                "so any text inside them is invisible"
            ),
            penalty=3 * min(report.image_count, 3),
        )
    ]


@check
def section_headings(report: ExtractionReport) -> List[Finding]:
    """Recognizable Experience, Education, and Skills headings."""
    lowered = report.ats_text.lower()
    findings: List[Finding] = []
    for canonical, variants in CANONICAL_SECTIONS.items():
        if not any(variant in lowered for variant in variants):
            findings.append(
                Finding(
                    check="section_headings",
                    severity="warning",
                    message=(
                        f"No recognizable '{canonical}' heading; parsers map content "
                        "to fields by heading, so this section may not be filed at all"
                    ),
                    evidence=f"expected one of: {', '.join(variants[:3])}",
                    penalty=10,
                )
            )
    return findings


@check
def parseable_dates(report: ExtractionReport) -> List[Finding]:
    """At least one date range a parser can convert into a duration."""
    text = report.ats_text.lower()
    matches = sum(len(re.findall(pattern, text)) for pattern in DATE_PATTERNS)
    if matches == 0:
        return [
            Finding(
                check="parseable_dates",
                severity="warning",
                message=(
                    "No machine-readable date ranges found; without them a parser "
                    "cannot compute years of experience"
                ),
                evidence="try 'Jan 2020 - Present' or '2020 - 2023'",
                penalty=12,
            )
        ]
    if matches < 2:
        return [
            Finding(
                check="parseable_dates",
                severity="info",
                message=f"Only {matches} parseable date range found",
                penalty=3,
            )
        ]
    return []


@check
def risky_characters(report: ExtractionReport) -> List[Finding]:
    """Glyphs that mangle when extracted to plain text."""
    findings: List[Finding] = []
    for glyph, name in RISKY_GLYPHS.items():
        count = report.ats_text.count(glyph)
        if not count:
            continue
        # A private-use Symbol-font bullet is genuinely broken output. A curly
        # apostrophe is merely untidy, and flagging it as critical would be noise.
        severe = glyph == ""
        findings.append(
            Finding(
                check="risky_characters",
                severity="warning" if severe else "info",
                message=(
                    f"{count} {name} character(s); these extract as garbage "
                    "in some parsers"
                    if severe
                    else f"{count} {name} character(s) may not survive plain-text extraction"
                ),
                penalty=6 if severe else 1,
            )
        )
    return findings


@check
def document_length(report: ExtractionReport) -> List[Finding]:
    """Enough parsed text to be a resume at all."""
    words = len(report.ats_text.split())
    if words < 120:
        return [
            Finding(
                check="document_length",
                severity="critical",
                message=(
                    f"Only {words} words survived parsing; the document is likely "
                    "mostly layout, images, or text the parser cannot reach"
                ),
                penalty=25,
            )
        ]
    if words > 1200:
        return [
            Finding(
                check="document_length",
                severity="info",
                message=f"{words} words is long for a resume",
                penalty=2,
            )
        ]
    return []


def run_all(report: ExtractionReport) -> List[Finding]:
    """Run every registered check, worst findings first."""
    findings: List[Finding] = []
    for func in _REGISTRY:
        findings.extend(func(report))
    order = {name: i for i, name in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: (order.get(f.severity, 99), -f.penalty))
    return findings
