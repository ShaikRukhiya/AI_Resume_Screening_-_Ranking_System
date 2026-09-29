from __future__ import annotations

import re
from pathlib import Path
from typing import List

from src.config.settings import AI_KEYWORDS, PYTHON_KEYWORDS, TECH_SKILLS
from src.models.resume import CandidateProfile


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _split_sentences(text: str) -> List[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _extract_name(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    stop_words = {
        "summary", "skills", "experience", "work experience", "education", "projects",
        "linkedin", "github", "phone", "email", "objective", "certifications",
        "technical skills", "professional summary", "profile", "about", "portfolio"
    }
    reject_tokens = {
        "summary", "skills", "experience", "education", "projects", "linkedin",
        "github", "portfolio", "certification", "phone", "email", "mobile", "location",
        "btech", "be", "b.e", "mtech", "engineering", "technology", "college",
        "institute", "university", "student", "intern", "trainee", "portal", "api",
        "server", "design", "system", "management", "vision", "computer", "ml", "ai",
        "nlp", "blockchain", "platform", "dashboard", "tool", "tools", "resume", "profile",
        "software", "developer", "analysis", "engineer", "scientist", "analyst", "manager",
        "researcher", "consultant", "architect", "designer", "founder", "director", "lead",
        "react", "native", "basic", "english", "tamil", "telugu",
        "company", "inc", "ltd", "llc", "corp", "technologies", "solutions", "systems",
        "labs", "university", "college", "institute", "school", "india", "karnataka",
        "bangalore", "bengaluru", "hyderabad", "ahmedabad", "pune", "delhi", "ghaziabad",
        "mathura", "uttar", "pradesh", "dehradun", "uttarakhand", "mumbai", "chennai",
        "noida", "gurugram", "gurgaon", "kolkata", "jaipur", "indore", "bhopal", "lucknow",
    }

    def looks_like_name(line: str) -> bool:
        if not line or len(line) < 3 or len(line) > 80:
            return False
        lowered = line.lower()
        if any(stop in lowered for stop in stop_words):
            return False
        if any(token in lowered for token in ["@", "http", "/", "|", "linkedin", "github", "portfolio", "tools", "skills", "languages", "frameworks", "technologies", "phone", "email", "mobile", "location", ",", ":", "(", ")", "[", "]"]):
            return False
        if re.search(r"\d", line):
            return False
        if re.search(r"\b(19\d{2}|20\d{2})\b", line):
            return False
        if re.search(r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{2,4}\b", lowered):
            return False
        if not re.search(r"[A-Za-z]", line):
            return False
        words = re.findall(r"[A-Za-z]+", line)
        if len(words) < 2 or len(words) > 4:
            return False
        if any(word.lower() in reject_tokens for word in words):
            return False
        if any(word.lower() in {"portal", "server", "api", "ai", "ml", "nlp", "vision", "project", "projects", "design"} for word in words):
            return False
        if any(ch in line for ch in ["-", "•", "*", ";", "_", "=", "/"]):
            return False
        if sum(1 for word in words if word.isupper()) >= 2 and all(word.isalpha() for word in words):
            return True
        if all(word[:1].isupper() or word.isupper() for word in words if word):
            return True
        return False

    location_pattern = re.compile(
        r"\b(?:india|karnataka|bangalore|bengaluru|hyderabad|ahmedabad|pune|delhi|ghaziabad|"
        r"mathura|uttar\s+pradesh|dehradun|uttarakhand|mumbai|chennai|noida|gurugram|gurgaon|"
        r"kolkata|jaipur|indore|bhopal|lucknow)\b",
        flags=re.IGNORECASE,
    )
    contact_pattern = re.compile(r"\b(?:email|phone|mobile|linkedin|github|website|portfolio)\b\s*:?|\bP\s*:", re.IGNORECASE)

    for index, original_line in enumerate(lines[:12]):
        line = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", original_line)
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", line)
        if email_match:
            line = line[:email_match.start()]
        line = contact_pattern.split(line, maxsplit=1)[0]
        line = re.split(r"[|—–]", line, maxsplit=1)[0]
        location_match = location_pattern.search(line)
        if location_match:
            line = line[:location_match.start()]
        line = re.sub(r"\s+", " ", line).strip(" ,|:")
        if looks_like_name(line):
            return line

        if index + 1 < min(len(lines), 12):
            next_line = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", lines[index + 1]).strip()
            if re.fullmatch(r"[A-Z][a-z]+", line) and re.fullmatch(r"[A-Z][a-z]+", next_line):
                combined = f"{line} {next_line}"
                if looks_like_name(combined):
                    return combined
    return ""


def _extract_email(text: str) -> str:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    return match.group(0).strip() if match else ""


def _extract_github_url(text: str) -> str:
    match = re.search(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)|github\.com/([A-Za-z0-9_.-]+)", text, flags=re.IGNORECASE)
    if not match:
        return ""
    user = match.group(1) or match.group(2)
    return f"https://github.com/{user}" if user else ""


def _extract_skills(text: str) -> List[str]:
    lower_text = text.lower()
    found: List[str] = []
    for section_name, values in TECH_SKILLS.items():
        for value in values:
            if value in lower_text:
                found.append(value)
    return list(dict.fromkeys(found))


def _extract_projects(text: str) -> List[str]:
    project_lines = []
    paragraphs = re.split(r"\n\s*\n+", text)
    for block in paragraphs:
        lower = block.lower()
        if "project" in lower or "projects" in lower:
            project_lines.append(_normalize_whitespace(block)[:500])
    if not project_lines:
        for candidate in re.split(r"(?<=[.!?])\s+", text):
            if re.search(r"(build|develop|implement|create|designed|engineered)", candidate, flags=re.IGNORECASE):
                project_lines.append(candidate.strip())
    return project_lines[:10]


def _extract_experience(text: str) -> List[str]:
    experiences: List[str] = []
    for line in text.splitlines():
        if re.search(r"\b(20\d{2}|19\d{2})\b", line) and any(label in line.lower() for label in ["experience", "intern", "work", "developer", "engineer", "internship"]):
            experiences.append(line.strip())
    return experiences[:10]


def _extract_education(text: str) -> List[str]:
    education: List[str] = []
    patterns = ["b.tech", "bachelor", "master", "computer science", "information technology", "engineering", "mca"]
    for line in text.splitlines():
        lower = line.lower()
        if any(pattern in lower for pattern in patterns):
            education.append(line.strip())
    return list(dict.fromkeys(education))[:10]


def extract_candidate_profile(raw_text: str, source_file: str) -> CandidateProfile:
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    name = _extract_name(text)
    email = _extract_email(text)
    phone = _extract_phone(text)
    github_url = _extract_github_url(text)

    skills = _extract_skills(text)
    projects = _extract_projects(text)
    experience = _extract_experience(text)
    education = _extract_education(text)

    ai_evidence = []
    python_evidence = []
    lower_text = text.lower()
    for sentence in _split_sentences(text):
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in AI_KEYWORDS):
            ai_evidence.append(sentence)
        if any(keyword in sentence_lower for keyword in PYTHON_KEYWORDS):
            python_evidence.append(sentence)

    if not skills:
        skills = []

    github_username = ""
    if github_url:
        github_username = github_url.rstrip("/").split("github.com/")[-1]

    fallback_name = ""
    if not name:
        stem = Path(source_file).stem
        fallback_name = re.sub(r"(?i)^candidate[_ -]?(\d+)$", r"Candidate \1", stem)
        name = f"{fallback_name} (fallback)"
    else:
        fallback_name = re.sub(r"(?i)^candidate[_ -]?(\d+)$", r"Candidate \1", Path(source_file).stem)
        lower_name = name.lower()
        if any(token in lower_name for token in ["artificial intelligence", "machine learning", "achievement", "activities", "portal", "server", "management", "tools:", "technical skills", "professional summary", "summary", "profile", "objective", "api design", "dashboard", "system", "skills"]):
            name = f"{fallback_name} (fallback)"
        elif "&" in name or ":" in name or re.search(r"\d", name):
            name = f"{fallback_name} (fallback)"

    candidate_metadata = {"source_text_length": len(text), "name_source": "resume_header" if not (" (fallback)" in name) else "fallback_file_name"}

    return CandidateProfile(
        candidate_name=name,
        email=email,
        phone=phone,
        skills=skills,
        projects=projects,
        technologies=[skill for skill in skills if skill not in ["python", "rag", "llm"]],
        experience=experience,
        education=education,
        github_url=github_url,
        github_username=github_username,
        ai_evidence=list(dict.fromkeys(ai_evidence))[:10],
        python_evidence=list(dict.fromkeys(python_evidence))[:10],
        raw_text=text,
        source_file=source_file,
        metadata=candidate_metadata,
    )
