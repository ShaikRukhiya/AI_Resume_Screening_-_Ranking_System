from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.eligibility.hard_filter import get_hard_eligibility_rejection_reasons, meets_hard_eligibility
from src.github.enrichment import enrich_candidate_github
from src.ingestion.ingest import collect_resume_files, process_resume_batch
from src.models.resume import CandidateProfile
from src.reporting.report import generate_human_report
from src.scoring.engine import score_candidate

load_dotenv()


def _display_name(profile: CandidateProfile) -> str:
    if profile.candidate_name:
        return profile.candidate_name
    stem = Path(profile.source_file).stem or "candidate"
    return f"{stem} (fallback)"


def _unscored_result(profile: CandidateProfile, status: str, reasons: list[str]) -> dict:
    evidence = list(dict.fromkeys(profile.python_evidence + profile.ai_evidence))
    return {
        "candidate_name": _display_name(profile),
        "source_file": profile.source_file,
        "eligible": False,
        "status": status,
        "rejection_reasons": reasons,
        "matched_skills": sorted(set(profile.skills + profile.technologies)),
        "project_summary": ". ".join(profile.projects[:3]) if profile.projects else "No project section found.",
        "evidence": evidence or ["No reliable resume evidence extracted."],
        "python_evidence": profile.python_evidence,
        "ai_evidence": profile.ai_evidence,
        "extraction_warnings": profile.extraction_warnings,
        "duplicate_of": profile.duplicate_of,
    }


def run_pipeline(resume_dir: str = "resumes", output_dir: str = "output", output_file: str | Path | None = None) -> dict:
    resume_path = Path(resume_dir)
    results_file = Path(output_file) if output_file is not None else Path(output_dir) / "results.json"
    output_path = results_file.parent
    output_path.mkdir(parents=True, exist_ok=True)

    parsed_candidates, duplicates, unreadable = process_resume_batch(resume_path)
    eligible_profiles = []
    rejected_results = []
    excluded_results = []
    for profile in parsed_candidates:
        if profile.duplicate_of:
            excluded_results.append(_unscored_result(
                profile,
                "duplicate",
                [f"Duplicate resume; original file: {profile.duplicate_of}."],
            ))
        elif not profile.raw_text.strip():
            excluded_results.append(_unscored_result(
                profile,
                "unreadable",
                ["Resume could not be read or parsed; excluded from scoring."],
            ))
        elif meets_hard_eligibility(profile):
            eligible_profiles.append(profile)
        else:
            rejected_results.append(_unscored_result(
                profile,
                "rejected",
                get_hard_eligibility_rejection_reasons(profile),
            ))

    scored_candidates = []
    for profile in eligible_profiles:
        github_info = enrich_candidate_github(profile)
        candidate_result = score_candidate(profile, github_enrichment=github_info)
        candidate_result["status"] = "eligible"
        scored_candidates.append(candidate_result)

    ranked = sorted(scored_candidates, key=lambda item: item["total_score"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    batch_summary = {
        "total_resumes": len(collect_resume_files(resume_path)),
        "successfully_parsed": len(eligible_profiles) + len(rejected_results),
        "eligible": len(ranked),
        "rejected": len(rejected_results),
        "failed_or_unreadable": unreadable,
        "duplicates": duplicates,
    }

    payload = {
        "candidates": ranked + rejected_results + excluded_results,
        "batch_summary": batch_summary,
    }

    results_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report_file = output_path / "human_report.txt"
    report_file.write_text(generate_human_report(payload), encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser(description="Screen and rank resumes.")
    parser.add_argument("--input", default=os.getenv("RESUME_DIR", "resumes"), help="Resume directory")
    parser.add_argument("--output", default=os.getenv("OUTPUT_DIR", "output"), help="Output directory or results JSON path")
    args = parser.parse_args(argv)
    output_path = Path(args.output)
    if output_path.suffix.lower() == ".json":
        return run_pipeline(resume_dir=args.input, output_file=output_path)
    return run_pipeline(resume_dir=args.input, output_dir=str(output_path))


if __name__ == "__main__":
    main()
