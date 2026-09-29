from datetime import datetime, timedelta, timezone
from pathlib import Path

import main as pipeline
import src.github.enrichment as github_enrichment
from src.models.resume import CandidateProfile
from src.eligibility.hard_filter import meets_hard_eligibility
from src.extraction.resume_extractor import _extract_name, extract_candidate_profile
from src.llm.adapter import LLMAdapter
from src.scoring.engine import score_candidate


def _profile(*, skills=None, ai_evidence=None, python_evidence=None, projects=None, technologies=None, raw_text=''):
    return CandidateProfile(
        candidate_name='Test Candidate',
        email='test@example.com',
        skills=skills or [],
        ai_evidence=ai_evidence or [],
        python_evidence=python_evidence or [],
        projects=projects or [],
        technologies=technologies or [],
        raw_text=raw_text,
    )


def test_python_plus_ai_candidate_is_eligible():
    profile = _profile(
        skills=['Python', 'LangChain', 'FastAPI'],
        ai_evidence=['Built a RAG pipeline with embeddings and vector search', 'Developed tool-calling agent'],
        python_evidence=['Built FastAPI backend', 'Implemented async processing in Python'],
        projects=['RAG assistant with vector search in Python'],
    )
    assert meets_hard_eligibility(profile) is True


def test_python_without_ai_is_rejected():
    profile = _profile(
        skills=['Python', 'Django'],
        ai_evidence=[],
        python_evidence=['Built Django API backend in Python'],
        projects=['Inventory API'],
    )
    assert meets_hard_eligibility(profile) is False


def test_ai_without_python_is_rejected():
    profile = _profile(
        skills=['LangChain', 'OpenAI'],
        ai_evidence=['Built a LLM app'],
        python_evidence=[],
        projects=['OpenAI chatbot'],
    )
    assert meets_hard_eligibility(profile) is False


def test_react_java_only_profile_is_rejected():
    profile = _profile(
        skills=['JavaScript', 'React', 'Java'],
        ai_evidence=[],
        python_evidence=[],
        projects=['React dashboard using Java'],
    )
    assert meets_hard_eligibility(profile) is False


def test_java_react_plus_python_ai_is_eligible():
    profile = _profile(
        skills=['Java', 'React', 'Python', 'LangChain'],
        ai_evidence=['Built agentic workflow with tool calling'],
        python_evidence=['Implemented FastAPI microservice in Python'],
        projects=['Full-stack app and RAG assistant'],
    )
    assert meets_hard_eligibility(profile) is True


def test_shallow_llm_wrapper_gets_penalty():
    profile = _profile(
        skills=['Python', 'OpenAI'],
        ai_evidence=['Prompted ChatGPT API for summary'],
        python_evidence=['Wrote a Python Flask wrapper around OpenAI API'],
        projects=['AI summary generator'],
    )
    score = score_candidate(profile)
    assert 0 <= score["total_score"] <= 100
    assert score["score_breakdown"]["ai_project_depth"] < 20


def test_framework_name_only_is_insufficient_evidence():
    profile = _profile(
        skills=['Python', 'LangChain'],
        ai_evidence=['LangChain project'],
        python_evidence=['Python developer'],
        projects=['LangChain app'],
    )
    score = score_candidate(profile)
    assert score["score_breakdown"]["ai_project_depth"] < 10
    assert meets_hard_eligibility(profile) is False


def test_rag_substring_inside_leverages_does_not_qualify():
    profile = _profile(
        skills=['Python', 'RAG'],
        ai_evidence=['Python-based voice assistant leverages pyttsx3 and speech recognition.'],
        raw_text="Python-based voice assistant leverages pyttsx3 and speech recognition.",
    )
    assert meets_hard_eligibility(profile) is False


def test_rag_substring_inside_storage_does_not_qualify():
    profile = _profile(skills=['Python', 'RAG'], raw_text="Python backend stores records in a relational database.")
    assert meets_hard_eligibility(profile) is False


def test_ordinary_database_retrieval_does_not_qualify_as_ai():
    profile = _profile(raw_text="Python backend designed relational databases for efficient data storage and retrieval.")
    assert meets_hard_eligibility(profile) is False


def test_standalone_rag_term_qualifies_with_python():
    profile = _profile(raw_text="Python project: RAG-based question answering pipeline.")
    assert meets_hard_eligibility(profile) is True


def test_multiword_ai_terms_match_as_complete_phrases():
    profile = _profile(raw_text="Python backend uses vector search for document matching.")
    assert meets_hard_eligibility(profile) is True


def test_meaningful_machine_learning_project_qualifies_with_python():
    profile = _profile(raw_text=(
        "Python project: Machine Learning model trained and evaluated using SVR."
    ))
    assert meets_hard_eligibility(profile) is True


def test_implemented_custom_ai_optimization_algorithm_qualifies():
    profile = _profile(raw_text=(
        "Python project: Developed a novel population-based meta-heuristic algorithm "
        "for job-shop scheduling and evaluated it against genetic algorithms."
    ))
    assert meets_hard_eligibility(profile) is True


def test_python_only_profile_remains_rejected():
    profile = _profile(raw_text="Python backend developer built a REST API.")
    assert meets_hard_eligibility(profile) is False


def test_ai_only_profile_without_python_remains_rejected():
    profile = _profile(raw_text="Built a RAG pipeline with embeddings and vector search.")
    assert meets_hard_eligibility(profile) is False


def test_score_totals_stay_within_0_to_100():
    profile = _profile(
        skills=['Python', 'RAG', 'FastAPI'],
        ai_evidence=['Built RAG retrieval with embeddings and evaluation'],
        python_evidence=['Python backend with PostgreSQL and async tasks'],
        projects=['RAG assistant'],
    )
    score = score_candidate(profile)
    assert 0 <= score["total_score"] <= 100
    assert sum(score["score_breakdown"].values()) == score["total_score"]


def test_score_categories_respect_required_weights():
    profile = _profile(
        skills=['Python', 'RAG', 'FastAPI'],
        ai_evidence=['Built RAG retrieval with embeddings and evaluation'],
        python_evidence=['Python backend with PostgreSQL and async tasks'],
        projects=['RAG assistant'],
    )
    score = score_candidate(profile)
    weights = {
        'ai_project_depth': 40,
        'python_backend': 30,
        'cloud_fullstack': 15,
        'github': 10,
        'engineering_depth': 5,
    }
    for key, weight in weights.items():
        assert score["score_breakdown"][key] <= weight


def test_missing_fields_do_not_crash():
    profile = CandidateProfile(candidate_name='', email='', skills=[], ai_evidence=[], python_evidence=[], projects=[])
    assert meets_hard_eligibility(profile) is False
    score = score_candidate(profile)
    assert score["total_score"] >= 0


def test_duplicate_resume_is_handled():
    profile = CandidateProfile(candidate_name='X', email='x@x.com', source_file='a.pdf', duplicate_of='a.pdf')
    assert profile.duplicate_of == 'a.pdf'


def test_bonus_has_no_api_key_requirement_for_core():
    score = score_candidate(CandidateProfile(candidate_name='Test', email='a@b.com'))
    assert score["github_enrichment_status"] in {"missing", "skipped", "success", "failed"}


def test_result_structure_has_required_keys():
    score = score_candidate(_profile(skills=['Python', 'LangChain'], ai_evidence=['Built vector search RAG app'], python_evidence=['FastAPI backend'], projects=['RAG app']))
    assert set(score.keys()) >= {"candidate_name", "eligible", "rejection_reasons", "total_score", "score_breakdown", "strengths", "concerns"}


def test_name_extraction_accepts_arjun_despite_month_substring():
    assert _extract_name("Arjun Kumar\nSummary\nExperienced Python developer") == "Arjun Kumar"


def test_name_extraction_handles_contact_details_on_header_line():
    assert _extract_name("Vaibhav WakdeEmail: vaibhav@example.com\nEducation") == "Vaibhav Wakde"
    assert _extract_name("Parshuram Kumar P: +91-9798241178\nProfessional Summary") == "Parshuram Kumar"


def test_name_extraction_handles_split_and_layout_joined_header_names():
    assert _extract_name("Prathamesh\nPatil\n+91 73490 41840") == "Prathamesh Patil"
    assert _extract_name("Atul KumarDehradun, Uttarakhand, India\nLinkedIn") == "Atul Kumar"


def test_name_extraction_does_not_search_resume_body_for_name_like_lines():
    assert _extract_name("Professional Summary\nAcme Technologies\nSoftware Engineer") == ""
    assert _extract_name("Harsha A\n- S Q L\n- Python") == "Harsha A"
    assert _extract_name("English\nTamil\nTelugu\nJupyter notebook") == ""


def test_filename_fallback_is_explicit_when_header_is_ambiguous():
    profile = extract_candidate_profile("Professional Summary\nSoftware engineering candidate", "candidate_99.pdf")
    assert profile.candidate_name == "Candidate 99 (fallback)"
    assert profile.metadata["name_source"] == "fallback_file_name"


def test_skill_and_language_lists_do_not_become_candidate_name():
    profile = extract_candidate_profile("English\nTamil\nTelugu\nReact Native Basic", "candidate_20.pdf")
    assert profile.candidate_name == "Candidate 20 (fallback)"
    assert profile.metadata["name_source"] == "fallback_file_name"


def test_llm_adapter_without_api_key_is_non_blocking(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert LLMAdapter().generate_structured("test") is None


def test_llm_adapter_api_and_json_failures_are_non_blocking(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setattr("src.llm.adapter.requests.post", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    assert LLMAdapter().generate_structured("test") is None

    class MalformedResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "not json"}}]}

    monkeypatch.setattr("src.llm.adapter.requests.post", lambda *args, **kwargs: MalformedResponse())
    assert LLMAdapter().generate_structured("test") is None


def test_pipeline_scores_only_eligible_candidates_and_reports_all_inputs(tmp_path, monkeypatch):
    resume_dir = tmp_path / "resumes"
    resume_dir.mkdir()
    for filename in ("candidate_01.pdf", "candidate_02.pdf", "candidate_03.pdf", "candidate_04.pdf"):
        (resume_dir / filename).touch()

    eligible = _profile(raw_text="Python project built with a RAG pipeline.")
    eligible.source_file = str(resume_dir / "candidate_01.pdf")
    rejected = _profile(raw_text="Python backend built a REST API.")
    rejected.source_file = str(resume_dir / "candidate_02.pdf")
    duplicate = CandidateProfile(
        source_file=str(resume_dir / "candidate_03.pdf"),
        duplicate_of=str(resume_dir / "candidate_01.pdf"),
        extraction_warnings=["Duplicate resume detected."],
    )
    unreadable = CandidateProfile(
        source_file=str(resume_dir / "candidate_04.pdf"),
        extraction_warnings=["Failed to parse resume. Marked unreadable."],
    )

    enrichment_calls = []
    monkeypatch.setattr(pipeline, "process_resume_batch", lambda path: ([eligible, rejected, duplicate, unreadable], 1, 1))
    monkeypatch.setattr(
        pipeline,
        "enrich_candidate_github",
        lambda profile: enrichment_calls.append(profile) or {"score": 0, "status": "missing", "summary": "GitHub not provided."},
    )

    payload = pipeline.run_pipeline(str(resume_dir), str(tmp_path / "output"))
    by_source = {Path(candidate["source_file"]).name: candidate for candidate in payload["candidates"]}
    assert payload["batch_summary"] == {
        "total_resumes": 4,
        "successfully_parsed": 2,
        "eligible": 1,
        "rejected": 1,
        "failed_or_unreadable": 1,
        "duplicates": 1,
    }
    assert enrichment_calls == [eligible]
    assert by_source["candidate_01.pdf"]["eligible"] is True
    assert "rank" in by_source["candidate_01.pdf"]
    assert "score_breakdown" in by_source["candidate_01.pdf"]
    for filename in ("candidate_02.pdf", "candidate_03.pdf", "candidate_04.pdf"):
        record = by_source[filename]
        assert record["rejection_reasons"]
        assert "rank" not in record
        assert "score_breakdown" not in record
        assert "total_score" not in record


def test_cli_accepts_documented_input_and_json_output_paths(tmp_path, monkeypatch):
    call = {}
    monkeypatch.setattr(pipeline, "run_pipeline", lambda **kwargs: call.update(kwargs) or {})
    output_file = tmp_path / "results.json"
    pipeline.main(["--input", "custom-resumes", "--output", str(output_file)])
    assert call == {"resume_dir": "custom-resumes", "output_file": output_file}


def test_github_recent_activity_is_limited_to_last_180_days():
    now = datetime(2026, 9, 29, tzinfo=timezone.utc)
    assert github_enrichment._is_recently_updated((now - timedelta(days=30)).isoformat(), now)
    assert not github_enrichment._is_recently_updated((now - timedelta(days=181)).isoformat(), now)
    assert not github_enrichment._is_recently_updated("not-a-date", now)


def test_github_score_uses_recent_pushes_and_invalidates_old_cache(monkeypatch):
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=20)).isoformat()
    old = (now - timedelta(days=400)).isoformat()
    repos = [
        {"name": "python-rag", "description": "RAG pipeline", "language": "Python", "pushed_at": recent, "updated_at": recent, "archived": False},
        {"name": "legacy-repo", "description": "Old project", "language": "Java", "pushed_at": old, "updated_at": old, "archived": False},
    ]

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    responses = iter((FakeResponse({"login": "sample-dev"}), FakeResponse(repos)))
    requested_urls = []
    monkeypatch.setattr(github_enrichment, "_load_cache", lambda: {"sample-dev": {"score": 10, "status": "success"}})
    saved_cache = {}
    monkeypatch.setattr(github_enrichment, "_save_cache", lambda cache: saved_cache.update(cache))
    monkeypatch.setattr(
        github_enrichment.requests,
        "get",
        lambda url, **kwargs: requested_urls.append(url) or next(responses),
    )

    result = github_enrichment.enrich_candidate_github(CandidateProfile(github_username="sample-dev"))
    assert result["status"] == "success"
    assert result["score"] == 5
    assert "1 repositories pushed within 180 days" in result["summary"]
    assert "sort=updated" in requested_urls[1]
    assert saved_cache["sample-dev"]["version"] == github_enrichment.CACHE_VERSION
