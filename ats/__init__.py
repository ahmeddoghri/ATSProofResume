"""Deterministic ATS compatibility auditing for resumes.

    >>> from ats import score_resume
    >>> card = score_resume("resume.docx", job_description=posting)
    >>> card.parse_score, card.match_score
"""

from .checks import Finding, run_all
from .extract import ExtractionReport, extract
from .keywords import KeywordReport, match
from .score import Scorecard, format_scorecard, score_report, score_resume

__version__ = "1.1.0"

__all__ = [
    "ExtractionReport", "Finding", "KeywordReport", "Scorecard",
    "extract", "format_scorecard", "match", "run_all",
    "score_report", "score_resume",
]
