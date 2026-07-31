"""Matching a resume against a job posting without calling a model.

ATS keyword screening is mechanical: the posting's terms either appear in the
resume or they do not. Reproducing that mechanically, rather than asking a
model whether the resume "feels aligned", gives an answer that is the same
every run and that a candidate can check by reading their own document.

Two ideas do most of the work:

* **Term frequency as importance.** A skill the posting names four times
  matters more than one mentioned in passing, so matches are weighted by how
  often the posting repeats them.
* **Requirement lines are not body text.** Bulleted requirements and lines
  containing "must have" or "required" carry the terms that get screened on,
  and are weighted above prose.

Everything is lowercased, stripped of punctuation, and stop-worded. Multi-word
phrases are matched as phrases so "machine learning" is not credited to a
resume that merely says "learning".
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Set, Tuple

# Common English plus resume and posting boilerplate. Without the second group,
# every posting "matches" on words like "team", "work", and "role".
STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "for", "from", "had", "has", "have", "how", "in", "into", "is", "it",
    "its", "of", "on", "or", "our", "that", "the", "their", "them", "then",
    "there", "these", "they", "this", "to", "was", "we", "were", "what",
    "when", "which", "who", "will", "with", "you", "your", "not", "all",
    "also", "any", "such", "other", "more", "most", "than", "using", "use",
    "used", "including", "include", "includes", "well", "able", "across",
    "within", "while", "about", "over", "through", "after", "before",
    "job", "role", "position", "candidate", "candidates", "applicant",
    "company", "team", "teams", "work", "working", "works", "experience",
    "experiences", "year", "years", "skill", "skills", "ability", "abilities",
    "responsibility", "responsibilities", "requirement", "requirements",
    "qualification", "qualifications", "preferred", "required", "must",
    "plus", "strong", "excellent", "good", "great", "new", "help", "helping",
    "join", "looking", "seeking", "opportunity", "benefits", "salary",
    "please", "apply", "application", "employer", "equal", "etc",
    # Qualifier and connective vocabulary. These words carry the requirement
    # but are never themselves the thing being screened for: no ATS filters on
    # "proficiency". Listing them as missing keywords is how a keyword tool
    # teaches people to ignore it.
    "proficiency", "proficient", "familiarity", "familiar", "knowledge",
    "understanding", "exposure", "comparable", "similar", "particularly",
    "especially", "ideally", "typically", "various", "several", "multiple",
    "relevant", "related", "appropriate", "effective", "effectively",
    "successful", "successfully", "demonstrated", "proven", "track", "record",
    "hands", "deep", "solid", "advanced", "basic", "extensive", "significant",
    "practices", "practice", "tools", "tooling", "technologies", "technology",
    "platform", "platforms", "solutions", "solution", "environment",
    "environments", "based", "level", "senior", "junior", "lead", "staff",
    "principal", "manager", "engineer", "developer", "analyst", "scientist",
    "build", "building", "builds", "develop", "developing", "design",
    "designing", "maintain", "maintaining", "improve", "improving",
    "partner", "partnering", "collaborate", "collaborating", "support",
    "supporting", "ensure", "ensuring", "drive", "driving", "deliver",
    "delivering", "own", "owning", "manage", "managing",
}

# Terms worth catching even though a naive tokenizer splits or drops them.
KNOWN_PHRASES: Tuple[str, ...] = (
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "data science", "data engineering", "data analysis",
    "software engineering", "distributed systems", "version control",
    "continuous integration", "continuous delivery", "unit testing",
    "test driven development", "object oriented", "cloud computing",
    "project management", "product management", "cross functional",
    "problem solving", "time series", "large language models",
    "reinforcement learning", "feature engineering", "a/b testing",
    "ci/cd", "rest api", "web development", "back end", "front end",
    "full stack", "public speaking", "technical writing",
)

REQUIREMENT_MARKERS = (
    "must have", "must-have", "required", "requirements", "you have",
    "you'll need", "qualifications", "we require", "minimum",
    "proficiency in", "proficient in", "expertise in", "experience with",
    "experience in", "knowledge of", "familiarity with",
)

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.\-/]*")


@dataclass
class KeywordReport:
    """What the posting asks for, and what the resume actually says."""

    matched: List[Tuple[str, int]] = field(default_factory=list)
    missing: List[Tuple[str, int]] = field(default_factory=list)
    coverage: float = 0.0
    weighted_coverage: float = 0.0
    requirement_terms: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)

    @property
    def top_missing(self) -> List[str]:
        """The absent terms the posting leaned on hardest."""
        return [term for term, _ in self.missing[:12]]


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace and separators for matching."""
    text = text.lower()
    # Keep +, #, ., -, / so c++, c#, node.js, and ci/cd survive tokenizing.
    text = re.sub(r"[^\w+#./\-\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> List[str]:
    """Split normalized text into meaningful single-word terms.

    Trailing sentence punctuation is stripped so "team." and "team" are one
    term, while inner punctuation survives to keep "node.js" and "ci/cd"
    intact. Tokens opening with a digit are dropped: "5+" and "10x" are
    quantities in a requirement, never the requirement itself.
    """
    terms: List[str] = []
    for raw in TOKEN_RE.findall(normalize(text)):
        token = raw.rstrip(".-/")
        if len(token) < 2 or token in STOPWORDS:
            continue
        if token[0].isdigit():
            continue
        terms.append(token)
    return terms


def find_phrases(text: str) -> List[str]:
    """Detect known multi-word phrases in text."""
    normalized = normalize(text)
    return [phrase for phrase in KNOWN_PHRASES if phrase in normalized]


def requirement_lines(posting: str) -> List[str]:
    """Lines that read as hard requirements rather than prose."""
    lines: List[str] = []
    for raw in posting.splitlines():
        line = raw.strip()
        if not line:
            continue
        lowered = line.lower()
        is_bullet = bool(re.match(r"^[-*•▪‣o]\s+", line))
        if is_bullet or any(marker in lowered for marker in REQUIREMENT_MARKERS):
            lines.append(line)
    return lines


def extract_terms(posting: str, limit: int = 60) -> Counter:
    """Score the posting's terms by frequency, weighting requirement lines.

    Requirement lines count triple. A term named once in a bulleted "must have"
    list is a screening criterion; the same word buried in a paragraph about
    company culture is not.
    """
    counts: Counter = Counter()

    for token in tokenize(posting):
        counts[token] += 1
    for phrase in find_phrases(posting):
        counts[phrase] += normalize(posting).count(phrase)

    requirements = "\n".join(requirement_lines(posting))
    if requirements:
        for token in tokenize(requirements):
            counts[token] += 2  # on top of the base count, so 3x total
        for phrase in find_phrases(requirements):
            counts[phrase] += 2 * normalize(requirements).count(phrase)

    # Drop the long tail: terms appearing once in prose are noise, and
    # reporting them as "missing keywords" is how keyword tools lose trust.
    return Counter(dict(counts.most_common(limit)))


def match(resume_text: str, posting: str, limit: int = 60) -> KeywordReport:
    """Compare a resume against a posting and report coverage."""
    wanted = extract_terms(posting, limit=limit)
    if not wanted:
        return KeywordReport(coverage=1.0, weighted_coverage=1.0)

    resume_normalized = normalize(resume_text)
    resume_tokens = set(tokenize(resume_text))

    def present(term: str) -> bool:
        if " " in term or "/" in term:
            return term in resume_normalized
        return term in resume_tokens

    matched: List[Tuple[str, int]] = []
    missing: List[Tuple[str, int]] = []
    for term, weight in wanted.most_common():
        (matched if present(term) else missing).append((term, weight))

    total_weight = sum(wanted.values())
    matched_weight = sum(weight for _, weight in matched)

    requirement_terms = sorted(
        set(tokenize("\n".join(requirement_lines(posting))))
        & set(wanted)
    )
    missing_requirements = [t for t in requirement_terms if not present(t)]

    return KeywordReport(
        matched=matched,
        missing=missing,
        coverage=len(matched) / len(wanted),
        weighted_coverage=matched_weight / total_weight if total_weight else 0.0,
        requirement_terms=requirement_terms,
        missing_requirements=missing_requirements,
    )
