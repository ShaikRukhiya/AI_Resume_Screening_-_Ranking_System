from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Tuple

from src.extraction.resume_extractor import extract_candidate_profile
from src.models.resume import CandidateProfile
from src.parsing.resume_parser import extract_text_from_file

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def collect_resume_files(resume_dir: str | Path) -> List[Path]:
    directory = Path(resume_dir)
    if not directory.exists():
        return []
    files = [path for path in sorted(directory.iterdir()) if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS]
    return files


def process_resume_batch(resume_dir: str | Path) -> Tuple[List[CandidateProfile], int, int]:
    files = collect_resume_files(resume_dir)
    seen_hashes: dict[str, str] = {}
    parsed_candidates: List[CandidateProfile] = []
    duplicates = 0
    unreadable = 0

    for file_path in files:
        digest = _hash_file(file_path)
        if digest in seen_hashes:
            duplicate = CandidateProfile(
                candidate_name="",
                email="",
                source_file=str(file_path),
                duplicate_of=seen_hashes[digest],
                extraction_warnings=["Duplicate resume detected."],
            )
            parsed_candidates.append(duplicate)
            duplicates += 1
            continue

        seen_hashes[digest] = str(file_path)
        try:
            raw_text = extract_text_from_file(file_path)
            if not raw_text or not raw_text.strip():
                raise ValueError("Empty or unreadable resume content.")
            profile = extract_candidate_profile(raw_text, str(file_path))
            if profile is None:
                raise ValueError("Could not parse resume.")
            parsed_candidates.append(profile)
        except Exception:
            unreadable += 1
            fallback = CandidateProfile(
                candidate_name="",
                email="",
                source_file=str(file_path),
                extraction_warnings=["Failed to parse resume. Marked unreadable."],
            )
            parsed_candidates.append(fallback)

    return parsed_candidates, duplicates, unreadable
