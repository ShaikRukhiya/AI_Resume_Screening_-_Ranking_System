from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"
CACHE_DIR = PROJECT_ROOT / ".cache"

SCORING_WEIGHTS = {
    "ai_project_depth": 40,
    "python_backend": 30,
    "cloud_fullstack": 15,
    "github": 10,
    "engineering_depth": 5,
}

PYTHON_KEYWORDS = [
    "python",
    "fastapi",
    "flask",
    "django",
    "pandas",
    "numpy",
    "pytorch",
    "tensorflow",
    "sqlalchemy",
    "asyncio",
    "opencv",
    "scikit",
    "airflow",
    "celery",
    "redis",
    "postgresql",
    "mysql",
    "sqlite",
    "gunicorn",
    "uvicorn",
]

AI_KEYWORDS = [
    "rag",
    "retrieval",
    "embeddings",
    "vector search",
    "langchain",
    "langgraph",
    "llamaindex",
    "google adk",
    "agent",
    "agentic",
    "tool calling",
    "multi-agent",
    "prompt engineering",
    "llm",
    "large language model",
    "openai",
    "anthropic",
    "huggingface",
    "evaluation pipeline",
    "retriever",
    "chunking",
    "fine-tuning",
    "vector db",
    "pinecone",
    "weaviate",
    "faiss",
    "qdrant",
    "ollama",
]

PROJECT_REASONS = [
    "Built RAG pipeline",
    "Implemented embeddings and vector search",
    "Developed tool-calling agent",
    "Created multi-agent orchestration workflow",
    "Built retrieval pipeline",
    "Created evaluation and benchmarking workflow",
]

STRONG_AI_PATTERNS = [
    "rag",
    "retrieval",
    "embeddings",
    "vector search",
    "tool calling",
    "multi-agent",
    "agentic workflow",
    "langchain",
    "langgraph",
    "llamaindex",
    "vector db",
    "evaluation pipeline",
]

TECH_SKILLS = {
    "python": ["python", "fastapi", "flask", "django", "pandas", "numpy", "pytorch", "tensorflow"],
    "ai": ["rag", "llm", "langchain", "langgraph", "llamaindex", "vector search", "embeddings", "agent", "tool calling"],
    "cloud": ["docker", "aws", "gcp", "azure", "kubernetes", "terraform", "ci/cd", "github actions"],
    "frontend": ["react", "next.js", "javascript", "typescript", "node.js", "express", "tailwind"],
    "data": ["sql", "postgresql", "mysql", "mongodb", "redis", "spark", "pandas"],
}

REQUIRED_SCORE_KEYS = [
    "ai_project_depth",
    "python_backend",
    "cloud_fullstack",
    "github",
    "engineering_depth",
]
