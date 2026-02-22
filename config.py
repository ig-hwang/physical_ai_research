"""
PASIS Central Configuration
Physical AI Strategic Intelligence System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARCHIVE_DIR = DATA_DIR / "archive"

# ── Secrets: Streamlit Cloud secrets.toml 우선, 없으면 env var 사용 ──────────
def _get_secret(key: str, default: str = "") -> str:
    """Streamlit Cloud secrets → 환경변수 순으로 조회."""
    # 환경변수(load_dotenv 포함) 우선 적용
    env_val = os.getenv(key, "")
    if env_val:
        return env_val
    # Streamlit Cloud 배포 시 secrets.toml에서 읽기
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default

# ── API Keys ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = _get_secret("ANTHROPIC_API_KEY")
NEWS_API_KEY: str = _get_secret("NEWS_API_KEY")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = _get_secret("DATABASE_URL", f"sqlite:///{BASE_DIR}/pasis.db")

# ── Claude Model ──────────────────────────────────────────────────────────────
CLAUDE_MODEL: str = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS: int = 2048

# ── Research Taxonomy (from CLAUDE.md) ────────────────────────────────────────
SCOPES: list[str] = ["Market", "Tech", "Case", "Policy"]

TARGET_COMPANIES: list[str] = [
    "Tesla", "NVIDIA", "Amazon", "Figure AI", "Boston Dynamics",
    "OpenAI", "Agility Robotics", "Gatik", "Sanctuary AI",
    "1X Technologies", "Apptronik", "Physical Intelligence",
]

STRATEGIC_KEYWORDS: list[str] = [
    # Core Tech
    "Embodied AI", "World Models", "VLA Models", "Foundation Models for Robotics",
    "Vision Language Action", "end-to-end learning",
    # Hardware
    "Humanoid", "Actuator Control", "End-to-End Robotics", "Edge AI Hardware",
    "bipedal robot", "dexterous manipulation",
    # Business
    "Strategic Investment", "M&A", "PoC", "Commercial Deployment",
    "robotics as a service", "robot fleet",
    # Ops
    "Sim-to-Real", "Digital Twins", "Robot Fleet Management",
    "sim2real", "transfer learning robotics",
]

# ── arXiv Config ──────────────────────────────────────────────────────────────
ARXIV_CATEGORIES: list[str] = ["cs.RO", "cs.AI", "cs.CV", "cs.LG"]
ARXIV_MAX_RESULTS: int = 30
ARXIV_RATE_LIMIT_SEC: float = 3.0  # 1 req per 3 seconds

# ── SEC EDGAR Config ──────────────────────────────────────────────────────────
SEC_FORM_TYPES: list[str] = ["10-K", "8-K", "S-1"]
SEC_RATE_LIMIT_SEC: float = 0.1  # max 10 req/sec

# ── News RSS Feeds ────────────────────────────────────────────────────────────
NEWS_RSS_FEEDS: list[dict] = [
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "scope": "Case"},
    {"name": "VentureBeat", "url": "https://venturebeat.com/feed/", "scope": "Case"},
    {"name": "IEEE Spectrum", "url": "https://spectrum.ieee.org/feeds/feed.rss", "scope": "Tech"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "scope": "Tech"},
    {"name": "The Robot Report", "url": "https://www.therobotreport.com/feed/", "scope": "Case"},
]

# ── Scheduler ─────────────────────────────────────────────────────────────────
SCHEDULE_DAY: str = os.getenv("SCHEDULE_DAY", "monday")
SCHEDULE_HOUR: int = int(os.getenv("SCHEDULE_HOUR", "9"))
SCHEDULE_TIMEZONE: str = os.getenv("SCHEDULE_TIMEZONE", "Asia/Seoul")

# ── Quality Thresholds ────────────────────────────────────────────────────────
MIN_QUALITY_SCORE: float = 0.5
MIN_CONFIDENCE_SCORE: float = 0.3

# ── Confidence Scoring (source type weights) ──────────────────────────────────
CONFIDENCE_WEIGHTS: dict[str, float] = {
    "SEC": 0.95,
    "arXiv": 0.90,
    "IEEE": 0.85,
    "Reuters": 0.80,
    "TechCrunch": 0.70,
    "VentureBeat": 0.65,
    "RSS": 0.60,
    "News": 0.60,
}