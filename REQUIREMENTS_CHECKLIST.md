# Requirements Checklist

| Requirement | Implemented | Location | Tested |
|---|---|---|---|
| Read and use the official assignment as source of truth | ✅ Implemented | README and project logic | ✅ |
| Process every resume in the supplied directory | ✅ Implemented | src/ingestion/ingest.py | ✅ |
| PDF support mandatory | ✅ Implemented | src/parsing/resume_parser.py | ✅ |
| Handle malformed or unreadable resumes without crashing batch | ✅ Implemented | src/ingestion/ingest.py | ✅ |
| Support DOCX/TXT if practical | ✅ Implemented | src/parsing/resume_parser.py | ✅ |
| Handle missing fields | ✅ Implemented | src/extraction/resume_extractor.py | ✅ |
| Handle duplicate files and exclude them from ranking | ✅ Implemented | src/ingestion/ingest.py + main.py | ✅ |
| Extract candidate name, email, phone, skills, projects, technologies, experience, education, GitHub, AI evidence, Python evidence | ✅ Implemented | src/extraction/resume_extractor.py | ✅ |
| Hard eligibility filter with Python + AI both required | ✅ Implemented | src/eligibility/hard_filter.py | ✅ |
| Score and rank eligible candidates only; report rejected candidates with reasons | ✅ Implemented | main.py + src/reporting/report.py | ✅ |
| Do not reject JavaScript/Java/React/Next.js when Python + AI are satisfied | ✅ Implemented | src/eligibility/hard_filter.py | ✅ |
| Required 100-point scoring weights preserved | ✅ Implemented | src/config/settings.py + src/scoring/engine.py | ✅ |
| Project quality penalties for shallow wrappers and framework-only claims | ✅ Implemented | src/scoring/engine.py | ✅ |
| GitHub enrichment with public API and graceful failure | ✅ Implemented | src/github/enrichment.py | ✅ |
| No hard-coded secret tokens | ✅ Implemented | .env.example + src/github/enrichment.py | ✅ |
| Optional structured LLM adapter and provider isolation | ✅ Implemented | src/llm/adapter.py | ✅ |
| No batch crash when LLM call fails | ✅ Implemented | src/llm/adapter.py | ✅ |
| Evidence-backed scoring and AI project depth detector | ✅ Implemented | src/scoring/engine.py | ✅ |
| Evidence strength classification | ✅ Implemented | src/scoring/engine.py | ✅ |
| Strengths and concerns generation | ✅ Implemented | src/scoring/engine.py | ✅ |
| Batch resilience for failures | ✅ Implemented | main.py + src/ingestion/ingest.py | ✅ |
| Lightweight caching | ✅ Implemented | src/github/enrichment.py | ✅ |
| Clean module architecture | ✅ Implemented | src/ | ✅ |
| Machine-readable JSON output | ✅ Implemented | main.py + output/results.json | ✅ |
| Human-readable report generation | ✅ Implemented | src/reporting/report.py + output/human_report.txt | ✅ |
| Tests covering required scenarios | ✅ Implemented | tests/test_resume_screening.py | ✅ |
| README with setup and methodology | ✅ Implemented | README.md | ✅ |
| Final validation checklist | ✅ Implemented | REQUIREMENTS_CHECKLIST.md | ✅ |
