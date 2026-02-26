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
CLAUDE_MODEL: str = "claude-sonnet-4-6"          # 주간 리포트 전용
CLAUDE_ANALYSIS_MODEL: str = "claude-haiku-4-5-20251001"  # 개별 신호 분석
CLAUDE_MAX_TOKENS: int = 500                      # 신호 분석 JSON 출력 상한
CLAUDE_REPORT_MAX_TOKENS: int = 8192             # 주간 리포트 출력 상한

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
ARXIV_MAX_RESULTS: int = 15
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

# ── Key Players (News Feed) ───────────────────────────────────────────────────
KEY_PLAYERS: list[dict] = [
    {"name": "NVIDIA",            "category_label": "Brain & Platform",       "color": "#76B900",
     "must_watch": ["GR00T", "Isaac Lab", "Jetson Thor"],
     "feeds": [
         {"url": "https://news.google.com/rss/search?q=NVIDIA+GR00T+%22Isaac+Lab%22+robot&hl=en-US&gl=US&ceid=US:en"},
         {"url": "https://nvidianews.nvidia.com/rss"},
     ]},
    {"name": "Google DeepMind",   "category_label": "Brain & Platform",       "color": "#4285F4",
     "must_watch": ["RT-2", "AutoRT", "PaLM-E"],
     "feeds": [
         {"url": "https://news.google.com/rss/search?q=%22Google+DeepMind%22+RT-2+robotics&hl=en-US&gl=US&ceid=US:en"},
         {"url": "https://deepmind.google/blog/rss.xml"},
     ]},
    {"name": "Tesla",             "category_label": "End-to-End AI",          "color": "#CC0000",
     "must_watch": ["Optimus", "FSD", "Dojo"],
     "feeds": [
         {"url": "https://news.google.com/rss/search?q=Tesla+Optimus+humanoid+robot&hl=en-US&gl=US&ceid=US:en"},
     ]},
    {"name": "Figure AI",         "category_label": "Hardware & Logic",       "color": "#FF6B00",
     "must_watch": ["Figure 02", "Figure 03", "OpenAI Partnership"],
     "feeds": [
         {"url": "https://news.google.com/rss/search?q=%22Figure+AI%22+humanoid+robot&hl=en-US&gl=US&ceid=US:en"},
     ]},
    {"name": "Agility Robotics",  "category_label": "Industrial / Logistics", "color": "#00875A",
     "must_watch": ["Digit", "Toyota Partnership", "Amazon Partnership"],
     "feeds": [
         {"url": "https://news.google.com/rss/search?q=%22Agility+Robotics%22+Digit+robot&hl=en-US&gl=US&ceid=US:en"},
     ]},
    {"name": "Amazon Robotics",   "category_label": "Infrastructure",         "color": "#FF9900",
     "must_watch": ["Sequoia", "Proteus", "Culper"],
     "feeds": [
         {"url": "https://news.google.com/rss/search?q=Amazon+%22Amazon+Robotics%22+Sequoia+Proteus&hl=en-US&gl=US&ceid=US:en"},
         {"url": "https://www.amazon.science/latest-news.rss"},
     ]},
    {"name": "Sanctuary AI",      "category_label": "Specialized Brain",      "color": "#7B2FBE",
     "must_watch": ["Phoenix", "Carbon OS"],
     "feeds": [
         {"url": "https://news.google.com/rss/search?q=%22Sanctuary+AI%22+Phoenix+humanoid&hl=en-US&gl=US&ceid=US:en"},
     ]},
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