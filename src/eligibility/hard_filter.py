from __future__ import annotations

import re

from src.config.settings import AI_KEYWORDS, STRONG_AI_PATTERNS
from src.models.resume import CandidateProfile


_AI_FRAMEWORK_TERMS = {"langchain", "langgraph", "llamaindex", "google adk"}
_GENERIC_RETRIEVAL_TERMS = {"retrieval", "retriever"}
_AI_IMPLEMENTATION_ACTIONS = (
    "built", "build", "developed", "develop", "implemented", "implement",
    "created", "create", "deployed", "deploy", "trained", "train",
    "evaluated", "evaluate", "integrated", "integrate", "fine-tuned",
)
_ML_DOMAIN_TERMS = (
    "machine learning", "deep learning", "neural network", "computer vision",
    "natural language processing", "cnn", "tensorflow", "keras", "pytorch",
    "scikit-learn", "xgboost",
)
_ML_MODEL_WORK_TERMS = (
    "training", "trained", "evaluation", "evaluated", "prediction", "predictive",
    "classifier", "classification", "regression", "inference", "fine-tuned",
)
_ML_MODEL_TERMS = ("model", "models", "classifier", "classification", "regression")
_CUSTOM_AI_ALGORITHM_TERMS = (
    "meta-heuristic algorithm", "metaheuristic algorithm", "evolutionary algorithm",
    "genetic algorithm", "particle swarm optimization", "ant colony optimization",
)
_CUSTOM_AI_ALGORITHM_ACTIONS = (
    "developed", "implemented", "proposed", "evaluated", "benchmarked", "outperformed",
)
_RETRIEVAL_AI_CONTEXT = (
    "retrieval augmented generation", "semantic retrieval", "vector retrieval",
    "retrieval with embeddings", "retrieval using embeddings", "embedding based retrieval",
    "vector based retrieval",
)


def _text_for_candidate(candidate: CandidateProfile) -> str:
    chunks = [candidate.raw_text, " ".join(candidate.skills), " ".join(candidate.projects), " ".join(candidate.ai_evidence), " ".join(candidate.python_evidence)]
    return " ".join(chunk.lower() for chunk in chunks if chunk)


def _text_for_ai_candidate(candidate: CandidateProfile) -> str:
    chunks = [candidate.raw_text, " ".join(candidate.projects), " ".join(candidate.ai_evidence)]
    return " ".join(chunk.lower() for chunk in chunks if chunk)


def _contains_term(text: str, term: str) -> bool:
    words = re.split(r"[\s-]+", term.strip())
    pattern = r"[\s-]+".join(re.escape(word) for word in words)
    return re.search(rf"(?<!\w){pattern}(?!\w)", text, flags=re.IGNORECASE) is not None


def _contains_any(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(_contains_term(text, term) for term in terms)


def _has_meaningful_ml_evidence(text: str) -> bool:
    if not _contains_any(text, _ML_DOMAIN_TERMS):
        return False
    if _contains_any(text, _ML_MODEL_WORK_TERMS):
        return True
    return _contains_any(text, _ML_MODEL_TERMS) and _contains_any(text, _AI_IMPLEMENTATION_ACTIONS)


def _has_custom_ai_algorithm_evidence(text: str) -> bool:
    return _contains_any(text, _CUSTOM_AI_ALGORITHM_TERMS) and _contains_any(text, _CUSTOM_AI_ALGORITHM_ACTIONS)


def _has_meaningful_ai_evidence(text: str) -> bool:
    direct_patterns = tuple(
        pattern for pattern in STRONG_AI_PATTERNS
        if pattern not in _AI_FRAMEWORK_TERMS and pattern not in _GENERIC_RETRIEVAL_TERMS
    )
    if _contains_any(text, direct_patterns) or _contains_any(text, _RETRIEVAL_AI_CONTEXT):
        return True
    if _has_meaningful_ml_evidence(text):
        return True
    if _has_custom_ai_algorithm_evidence(text):
        return True

    application_terms = tuple(
        keyword for keyword in AI_KEYWORDS
        if keyword not in _AI_FRAMEWORK_TERMS and keyword not in _GENERIC_RETRIEVAL_TERMS
    )
    framework_or_ai_application = _contains_any(text, application_terms) or _contains_any(text, tuple(_AI_FRAMEWORK_TERMS))
    return framework_or_ai_application and _contains_any(text, _AI_IMPLEMENTATION_ACTIONS)


def meets_hard_eligibility(candidate: CandidateProfile) -> bool:
    text = _text_for_candidate(candidate)
    python_signal = _contains_any(text, ("python", "fastapi", "flask", "django", "pandas", "pytorch", "numpy", "sqlalchemy", "asyncio"))
    python_project = _contains_any(text, ("python project", "python backend", "python developer", "implemented in python", "built with python", "fastapi", "django", "flask", "backend in python"))
    python_work = _contains_any(text, ("python internship", "python experience", "python development", "worked on python", "python-based", "python api"))
    python_ok = bool(text) and python_signal and (python_project or python_work or _contains_term(text, "python"))
    ai_ok = bool(text) and _has_meaningful_ai_evidence(_text_for_ai_candidate(candidate))
    return python_ok and ai_ok


def get_hard_eligibility_rejection_reasons(candidate: CandidateProfile) -> list[str]:
    text = _text_for_candidate(candidate)
    if not text:
        return ["No readable resume evidence was extracted."]

    reasons = []
    python_signal = _contains_any(text, ("python", "fastapi", "flask", "django", "pandas", "pytorch", "numpy", "sqlalchemy", "asyncio"))
    python_project = _contains_any(text, ("python project", "python backend", "python developer", "implemented in python", "built with python", "fastapi", "django", "flask", "backend in python"))
    python_work = _contains_any(text, ("python internship", "python experience", "python development", "worked on python", "python-based", "python api"))
    if not (python_signal and (python_project or python_work or _contains_term(text, "python"))):
        reasons.append("Missing genuine Python skill, project, or work evidence.")
    if not _has_meaningful_ai_evidence(_text_for_ai_candidate(candidate)):
        reasons.append("Missing meaningful AI/LLM/RAG/agentic/ML project evidence.")
    return reasons
