"""Tests for the deterministic ATS audit engine."""

from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document

from ats import extract, format_scorecard, match, score_resume
from ats.bench import run_benchmark
from ats.checks import run_all
from ats.cli import main as cli_main
from ats.fixtures import JOB_POSTING, build_all
from ats.keywords import extract_terms, requirement_lines, tokenize


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    """Build the fixture corpus once for the whole module."""
    target = tmp_path_factory.mktemp("corpus")
    build_all(target)
    return target


# --- extraction -------------------------------------------------------------

def test_clean_resume_extracts_its_body(corpus):
    report = extract(corpus / "clean.docx")
    assert report.body_paragraphs > 10
    assert "Northwind Analytics" in report.ats_text
    assert report.table_count == 0


def test_header_text_is_absent_from_ats_reading(corpus):
    report = extract(corpus / "header_contact.docx")
    assert "jordan.reyes@example.com" not in report.ats_text
    assert "jordan.reyes@example.com" in report.human_text
    assert report.dropped_text


def test_table_cells_are_flattened_into_the_ats_text(corpus):
    report = extract(corpus / "table_layout.docx")
    assert report.table_count == 1
    assert report.table_cell_texts
    assert "Northwind Analytics" in report.ats_text


def test_reading_order_interleaves_table_columns(corpus):
    """The specific failure that makes two-column resumes unreadable."""
    report = extract(corpus / "table_layout.docx")
    text = report.ats_text
    # Skills live in the left cell and experience in the right, so a row-major
    # read emits the entire skills column before any job history.
    assert text.index("TECHNICAL SKILLS") < text.index("PROFESSIONAL EXPERIENCE")


def test_extraction_of_a_missing_file_raises(tmp_path):
    with pytest.raises(Exception):
        extract(tmp_path / "nope.docx")


# --- checks -----------------------------------------------------------------

def test_clean_resume_produces_no_findings(corpus):
    """No false positives: the property that decides whether anyone trusts it."""
    assert run_all(extract(corpus / "clean.docx")) == []


@pytest.mark.parametrize(
    "fixture,expected",
    [
        ("header_contact", "dropped_content"),
        ("table_layout", "table_layout"),
        ("unlabeled_sections", "section_headings"),
        ("no_dates", "parseable_dates"),
        ("sparse", "document_length"),
    ],
)
def test_each_planted_defect_is_detected(corpus, fixture, expected):
    fired = {f.check for f in run_all(extract(corpus / f"{fixture}.docx"))}
    assert expected in fired


def test_contact_in_header_is_flagged_critical(corpus):
    findings = run_all(extract(corpus / "header_contact.docx"))
    dropped = [f for f in findings if f.check == "dropped_content"]
    assert dropped and dropped[0].severity == "critical"
    # The evidence has to name the offending text, or it cannot be verified.
    assert "jordan.reyes@example.com" in dropped[0].evidence


def test_findings_are_ordered_worst_first(corpus):
    findings = run_all(extract(corpus / "sparse.docx"))
    severities = [f.severity for f in findings]
    assert severities == sorted(severities, key=["critical", "warning", "info"].index)


# --- scoring ----------------------------------------------------------------

def test_clean_resume_scores_full_marks(corpus):
    card = score_resume(corpus / "clean.docx")
    assert card.parse_score == 100
    assert card.grade == "A"


def test_broken_resume_scores_far_below_clean(corpus):
    clean = score_resume(corpus / "clean.docx")
    broken = score_resume(corpus / "header_contact.docx")
    assert clean.parse_score - broken.parse_score > 30


def test_parse_score_is_floored_at_zero(corpus):
    assert score_resume(corpus / "sparse.docx").parse_score >= 0


def test_match_score_is_zero_without_a_posting(corpus):
    """Refusing to invent a number beats inventing one."""
    assert score_resume(corpus / "clean.docx").match_score == 0


def test_match_score_is_reported_with_a_posting(corpus):
    card = score_resume(corpus / "clean.docx", JOB_POSTING)
    assert 0 < card.match_score <= 100


def test_parse_and_match_scores_are_independent(corpus):
    """A table-bound resume can match well and still parse badly."""
    card = score_resume(corpus / "table_layout.docx", JOB_POSTING)
    assert card.match_score > 50
    assert card.parse_score < 90


def test_scorecard_serializes(corpus):
    payload = score_resume(corpus / "clean.docx", JOB_POSTING).to_dict()
    assert payload["parse_score"] == 100
    assert payload["keywords"]["coverage"] > 0
    assert payload["extraction"]["parsed_words"] > 100


def test_formatted_scorecard_mentions_the_score(corpus):
    text = format_scorecard(score_resume(corpus / "header_contact.docx"))
    assert "Parse score" in text
    assert "dropped_content" in text


def test_scoring_is_deterministic(corpus):
    first = score_resume(corpus / "table_layout.docx", JOB_POSTING).to_dict()
    second = score_resume(corpus / "table_layout.docx", JOB_POSTING).to_dict()
    assert first == second


# --- keywords ---------------------------------------------------------------

def test_technical_tokens_survive_normalization():
    tokens = tokenize("Experience with C++, C#, Node.js, and CI/CD pipelines")
    assert "c++" in tokens
    assert "node.js" in tokens
    assert "ci/cd" in tokens


def test_trailing_punctuation_is_stripped():
    tokens = tokenize("we deploy on kubernetes.")
    assert "kubernetes" in tokens
    assert "kubernetes." not in tokens


def test_quantities_are_not_keywords():
    assert not [t for t in tokenize("5+ years and 10x growth") if t[0].isdigit()]


def test_boilerplate_is_not_reported_as_a_keyword():
    terms = extract_terms(JOB_POSTING)
    for noise in ("proficiency", "familiarity", "experience", "requirements"):
        assert noise not in terms


def test_requirement_lines_are_isolated():
    lines = requirement_lines(JOB_POSTING)
    assert any("Python and SQL" in line for line in lines)
    assert not any("We are seeking" in line for line in lines)


def test_requirement_terms_outweigh_prose_terms():
    terms = extract_terms(JOB_POSTING)
    # "spark" is a bulleted requirement; "reliability" only appears in prose.
    assert terms["spark"] > terms.get("reliability", 0)


def test_matching_finds_present_and_absent_terms():
    report = match("Python, SQL, and Apache Spark experience", JOB_POSTING)
    matched = {t for t, _ in report.matched}
    missing = {t for t, _ in report.missing}
    assert "python" in matched
    assert "kubernetes" in missing


def test_phrases_are_matched_as_phrases():
    """'machine learning' must not be credited to a resume that says 'learning'."""
    posting = "Requirements:\n- machine learning experience required"
    assert "machine learning" in {t for t, _ in match("I enjoy learning", posting).missing}
    assert "machine learning" in {
        t for t, _ in match("machine learning pipelines", posting).matched
    }


def test_empty_posting_yields_full_coverage():
    assert match("anything at all", "").coverage == 1.0


# --- benchmark --------------------------------------------------------------

def test_benchmark_detects_every_planted_defect():
    totals = run_benchmark()["totals"]
    assert totals["recall"] == 1.0
    assert totals["false_negatives"] == 0


def test_benchmark_reports_no_false_positives():
    assert run_benchmark()["totals"]["false_positives"] == 0


def test_benchmark_separates_clean_from_broken():
    separation = run_benchmark()["separation"]
    assert separation["clean_parse_score"] == 100
    assert separation["gap"] > 25


def test_benchmark_is_reproducible():
    assert run_benchmark()["totals"] == run_benchmark()["totals"]


# --- CLI --------------------------------------------------------------------

def test_cli_score_runs(corpus, capsys):
    assert cli_main(["score", str(corpus / "clean.docx")]) == 0
    assert "Parse score: 100" in capsys.readouterr().out


def test_cli_score_emits_json(corpus, capsys):
    import json

    assert cli_main(["score", str(corpus / "clean.docx"), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["grade"] == "A"


def test_cli_min_score_gates_a_bad_resume(corpus):
    """Non-zero exit is what makes this usable in a workflow."""
    assert cli_main(["score", str(corpus / "header_contact.docx"), "--min-score", "80"]) == 1
    assert cli_main(["score", str(corpus / "clean.docx"), "--min-score", "80"]) == 0


def test_cli_accepts_a_posting_file(corpus, capsys):
    args = ["score", str(corpus / "clean.docx"), "-j", str(corpus / "job_posting.txt")]
    assert cli_main(args) == 0
    assert "Match score" in capsys.readouterr().out


def test_cli_extract_lists_dropped_text(corpus, capsys):
    cli_main(["extract", str(corpus / "header_contact.docx"), "--show-dropped"])
    assert "jordan.reyes@example.com" in capsys.readouterr().out


def test_cli_compare_reports_a_delta(corpus, capsys):
    args = ["compare", str(corpus / "header_contact.docx"), str(corpus / "clean.docx")]
    assert cli_main(args) == 0
    out = capsys.readouterr().out
    assert "parse score" in out
    assert "+" in out


def test_cli_reports_a_missing_file_cleanly(tmp_path, capsys):
    assert cli_main(["score", str(tmp_path / "absent.docx")]) == 2


# --- app integration --------------------------------------------------------

def test_audit_endpoint_scores_an_upload(corpus):
    from fastapi.testclient import TestClient

    from app.main import app

    with open(corpus / "clean.docx", "rb") as handle:
        response = TestClient(app).post("/audit/", files={"file": ("clean.docx", handle)})
    payload = response.json()
    assert response.status_code == 200
    assert payload["parse_score"] == 100


def test_audit_endpoint_rejects_a_non_docx():
    from fastapi.testclient import TestClient

    from app.main import app

    response = TestClient(app).post("/audit/", files={"file": ("resume.pdf", b"%PDF-1.4")})
    assert response.status_code == 400
    assert "docx" in response.json()["error"].lower()


def test_audit_report_writer_records_an_improvement(corpus, tmp_path):
    from app.tasks import write_ats_audit

    result = write_ats_audit(
        corpus / "header_contact.docx", corpus / "clean.docx", JOB_POSTING, str(tmp_path)
    )
    assert result["after"] > result["before"]
    report = (tmp_path / "ats_report.txt").read_text()
    assert "ATS COMPATIBILITY REPORT" in report
    assert (tmp_path / "ats_report.json").exists()


def test_audit_report_writer_survives_a_bad_path(tmp_path):
    """A failed audit must not cost the user their rewritten resume."""
    from app.tasks import write_ats_audit

    assert write_ats_audit("nope.docx", "also-nope.docx", "", str(tmp_path)) is None
