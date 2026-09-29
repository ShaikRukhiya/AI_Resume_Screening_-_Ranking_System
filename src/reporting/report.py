from __future__ import annotations

from typing import Any, Dict, List


def format_top_candidates(candidates: List[Dict[str, Any]], limit: int = 5) -> str:
    lines = ["TOP CANDIDATES", ""]
    for idx, candidate in enumerate(candidates[:limit], start=1):
        breakdown = candidate.get("score_breakdown", {})
        lines.append(f"#{idx} {candidate.get('candidate_name', 'Unknown')} — {candidate.get('total_score', 0)}/100")
        lines.append(f"AI Depth: {breakdown.get('ai_project_depth', 0)}/40")
        lines.append(f"Python Backend: {breakdown.get('python_backend', 0)}/30")
        lines.append(f"Cloud: {breakdown.get('cloud_fullstack', 0)}/15")
        lines.append(f"GitHub: {breakdown.get('github', 0)}/10")
        lines.append(f"Engineering: {breakdown.get('engineering_depth', 0)}/5")
        lines.append("Why:")
        for item in candidate.get("strengths", [])[:3]:
            lines.append(f"- {item}")
        if candidate.get("concerns"):
            lines.append("Evidence gaps:")
            for item in candidate.get("concerns", [])[:3]:
                lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def generate_human_report(results: Dict[str, Any]) -> str:
    summary = results.get("batch_summary", {})
    candidates = results.get("candidates", [])
    eligible_candidates = [candidate for candidate in candidates if candidate.get("eligible")]
    rejected_candidates = [candidate for candidate in candidates if candidate.get("status") == "rejected"]
    excluded_candidates = [candidate for candidate in candidates if candidate.get("status") in {"duplicate", "unreadable"}]
    eligible = summary.get("eligible", 0)
    rejected = summary.get("rejected", 0)
    failed = summary.get("failed_or_unreadable", 0)

    lines = [
        "AI RESUME SCREENING REPORT",
        "",
        f"Processed: {summary.get('total_resumes', 0)}",
        f"Eligible: {eligible}",
        f"Rejected: {rejected}",
        f"Failed: {failed}",
        "",
    ]

    if eligible_candidates:
        top = sorted(eligible_candidates, key=lambda item: item.get("total_score", 0), reverse=True)
        lines.append(format_top_candidates(top, limit=5))
    else:
        lines.append("No eligible candidates.")

    if rejected_candidates:
        lines.extend(["", "REJECTED CANDIDATES"])
        for candidate in rejected_candidates:
            source = candidate.get("source_file", "")
            reasons = "; ".join(candidate.get("rejection_reasons", [])) or "Eligibility requirements not met."
            lines.append(f"- {candidate.get('candidate_name', 'Unknown')} ({source}): {reasons}")

    if excluded_candidates:
        lines.extend(["", "EXCLUDED RESUMES"])
        for candidate in excluded_candidates:
            reasons = "; ".join(candidate.get("rejection_reasons", []))
            lines.append(f"- {candidate.get('candidate_name', 'Unknown')} ({candidate.get('source_file', '')}): {reasons}")

    return "\n".join(lines)
