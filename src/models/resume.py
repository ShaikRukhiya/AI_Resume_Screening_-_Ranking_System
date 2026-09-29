"""Resume-related models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CandidateProfile:
    candidate_name: str = ""
    email: str = ""
    phone: str = ""
    skills: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    experience: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    github_url: str = ""
    github_username: str = ""
    ai_evidence: List[str] = field(default_factory=list)
    python_evidence: List[str] = field(default_factory=list)
    raw_text: str = ""
    source_file: str = ""
    duplicate_of: Optional[str] = None
    extraction_warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "projects": self.projects,
            "technologies": self.technologies,
            "experience": self.experience,
            "education": self.education,
            "github_url": self.github_url,
            "github_username": self.github_username,
            "ai_evidence": self.ai_evidence,
            "python_evidence": self.python_evidence,
            "source_file": self.source_file,
            "duplicate_of": self.duplicate_of,
            "extraction_warnings": self.extraction_warnings,
            "metadata": self.metadata,
        }
