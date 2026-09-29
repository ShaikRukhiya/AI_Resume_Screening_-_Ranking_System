from __future__ import annotations

import re
from typing import Any, Dict, List

from src.config.settings import REQUIRED_SCORE_KEYS, SCORING_WEIGHTS
from src.eligibility.hard_filter import get_hard_eligibility_rejection_reasons, meets_hard_eligibility
from src.models.resume import CandidateProfile


def _candidate_text(profile: CandidateProfile) -> str:
    chunks = [profile.raw_text, " ".join(profile.skills), " ".join(profile.projects), " ".join(profile.ai_evidence), " ".join(profile.python_evidence)]
    return " ".join(chunks).lower()


def _contains_any(text: str, values: List[str]) -> bool:
    return any(value.lower() in text for value in values)


def _derive_ai_depth(profile: CandidateProfile) -> tuple[int, str, List[str], List[str]]:
    text = _candidate_text(profile)
    evidence = []
    penalties = []
    if "rag" in text or "retrieval" in text:
        evidence.append("Implemented retrieval/RAG workflow")
    if "embeddings" in text or "vector search" in text:
        evidence.append("Used embeddings/vector search")
    if "tool calling" in text or "agent" in text or "multi-agent" in text:
        evidence.append("Implemented tool-calling or agentic workflow")
    if "langchain" in text or "langgraph" in text or "llamaindex" in text:
        evidence.append("Used LLM framework or orchestration library")
    if "evaluation" in text or "benchmark" in text:
        evidence.append("Included evaluation or testing workflow")

    if not evidence:
        if "llm" in text or "openai" in text or "chatgpt" in text:
            evidence.append("Used LLM API")
            penalties.append("Simple LLM/API wrapper without deeper implementation evidence")
        else:
            evidence.append("Limited AI implementation evidence")
            penalties.append("Insufficient AI implementation evidence")

    if any(value in text for value in ["prompt -> response", "prompt and response", "simple wrapper", "api wrapper"]) or "chatgpt" in text and "wrapper" in text:
        penalties.append("Shallow LLM wrapper pattern")

    if "langchain" in text and not any(value in text for value in ["retrieval", "agent", "vector search", "embeddings", "evaluation"]):
        penalties.append("Framework-name-only AI claim")

    if not evidence or ("framework" in text and not any(value in text for value in ["rag", "embeddings", "agent", "retrieval", "vector search"])):
        score = 4
    elif any(value in text for value in ["rag", "retrieval", "embeddings", "vector search", "agentic", "multi-agent"]):
        score = 33
    elif "langchain" in text and not any(value in text for value in ["rag", "retrieval", "embeddings", "vector search", "tool calling", "agentic", "multi-agent", "evaluation", "retriever"]):
        score = 6
    elif "llm" in text or "openai" in text:
        score = 18
    else:
        score = 8

    score = min(score, 40)
    return score, "HIGH" if score >= 25 else "MEDIUM" if score >= 10 else "LOW", evidence, penalties


def _derive_python_backend(profile: CandidateProfile) -> tuple[int, List[str], List[str]]:
    text = _candidate_text(profile)
    evidence = []
    strengths = []
    if "fastapi" in text or "flask" in text or "django" in text:
        evidence.append("Built API or backend in Python")
        strengths.append("Python backend evidence")
    if "postgresql" in text or "mysql" in text or "mongodb" in text:
        evidence.append("Used database systems in backend work")
    if "asyncio" in text or "celery" in text or "redis" in text:
        evidence.append("Built asynchronous or scalable backend processing")
    if "docker" in text or "aws" in text or "azure" in text:
        evidence.append("Deployment or cloud knowledge")

    score = 0
    if "fastapi" in text or "flask" in text or "django" in text:
        score += 12
    if "postgresql" in text or "mysql" in text or "mongodb" in text:
        score += 6
    if "asyncio" in text or "celery" in text or "redis" in text:
        score += 4
    if "python" in text:
        score += 6
    score = min(score, 30)
    return score, evidence, strengths


def _derive_cloud_score(profile: CandidateProfile) -> tuple[int, List[str]]:
    text = _candidate_text(profile)
    evidence = []
    score = 0
    if "docker" in text:
        score += 5
        evidence.append("Docker deployment experience")
    if "aws" in text or "gcp" in text or "azure" in text:
        score += 5
        evidence.append("Cloud platform experience")
    if "next.js" in text or "react" in text or "node.js" in text or "express" in text:
        score += 5
        evidence.append("Full-stack or front-end integration")
    return min(score, 15), evidence


def _derive_github_score(profile: CandidateProfile, github_enrichment: dict | None) -> tuple[int, str, str]:
    if not github_enrichment:
        return 0, "missing", "GitHub unavailable or not provided."
    status = github_enrichment.get("status", "missing")
    score = int(github_enrichment.get("score", 0))
    summary = github_enrichment.get("summary", "GitHub enrichment unavailable.")
    return min(score, 10), status, summary


def _derive_engineering_score(profile: CandidateProfile) -> tuple[int, List[str]]:
    text = _candidate_text(profile)
    evidence = []
    score = 0
    if "testing" in text or "pytest" in text or "unit tests" in text:
        score += 2
        evidence.append("Testing evidence")
    if "data structures" in text or "algorithm" in text or "system design" in text:
        score += 2
        evidence.append("Computer science foundations")
    if "ci/cd" in text or "github actions" in text or "docker" in text:
        score += 1
        evidence.append("DevOps or deployment workflow")
    return min(score, 5), evidence


def _derive_strengths(profile: CandidateProfile, ai_score: int, py_score: int, cloud_score: int, github_score: int, eng_score: int) -> List[str]:
    strengths: List[str] = []
    text = _candidate_text(profile)
    if ai_score >= 20:
        strengths.append("Strong AI project")
    if py_score >= 15:
        strengths.append("Strong Python backend")
    if cloud_score >= 5:
        strengths.append("Deployment experience")
    if github_score > 0:
        strengths.append("Active GitHub")
    if eng_score > 0:
        strengths.append("Engineering depth")
    if not strengths and "python" in text:
        strengths.append("Python background")
    return strengths[:5]


def _derive_concerns(profile: CandidateProfile) -> List[str]:
    concerns: List[str] = []
    text = _candidate_text(profile)
    if "redis" not in text and "caching" not in text:
        concerns.append("Limited Redis evidence")
    if "test" not in text and "pytest" not in text and "unit" not in text:
        concerns.append("No clear testing evidence")
    if not profile.github_url:
        concerns.append("GitHub unavailable")
    if "docker" not in text and "aws" not in text and "azure" not in text and "gcp" not in text:
        concerns.append("Limited cloud evidence")
    return concerns[:5]


def score_candidate(profile: CandidateProfile, github_enrichment: dict | None = None) -> Dict[str, Any]:
    eligible = meets_hard_eligibility(profile)
    rejection_reasons = get_hard_eligibility_rejection_reasons(profile) if not eligible else []

    ai_score, ai_level, ai_evidence, ai_penalties = _derive_ai_depth(profile)
    python_score, python_evidence, python_strengths = _derive_python_backend(profile)
    cloud_score, cloud_evidence = _derive_cloud_score(profile)
    github_score, github_status, github_summary = _derive_github_score(profile, github_enrichment)
    engineering_score, engineering_evidence = _derive_engineering_score(profile)

    total_score = min(100, ai_score + python_score + cloud_score + github_score + engineering_score)
    score_breakdown = {
        "ai_project_depth": ai_score,
        "python_backend": python_score,
        "cloud_fullstack": cloud_score,
        "github": github_score,
        "engineering_depth": engineering_score,
    }

    strength_list = _derive_strengths(profile, ai_score, python_score, cloud_score, github_score, engineering_score)
    concern_list = _derive_concerns(profile)
    if ai_penalties:
        concern_list.extend(ai_penalties)
    concern_list = list(dict.fromkeys(concern_list))[:5]

    evidence = list(dict.fromkeys(ai_evidence + python_evidence + cloud_evidence + engineering_evidence))
    if not evidence:
        evidence = ["No strong implementation evidence found in resume."]

    result = {
        "candidate_name": profile.candidate_name or "Unknown Candidate",
        "source_file": profile.source_file,
        "eligible": eligible,
        "rejection_reasons": rejection_reasons,
        "total_score": total_score,
        "score_breakdown": score_breakdown,
        "matched_skills": sorted(set(profile.skills + profile.technologies)),
        "project_summary": ". ".join(profile.projects[:3]) if profile.projects else "No project section found.",
        "github_summary": github_summary,
        "strengths": strength_list,
        "concerns": concern_list,
        "evidence": evidence,
        "evidence_strength": "HIGH" if ai_score >= 25 or python_score >= 20 else "MEDIUM" if evidence else "LOW",
        "ai_project_depth_analysis": {
            "level": ai_level,
            "score": ai_score,
            "evidence": ai_evidence,
            "penalties": ai_penalties,
        },
        "github_enrichment_status": github_status,
        "python_evidence": profile.python_evidence,
        "ai_evidence": profile.ai_evidence,
    }
    return result
