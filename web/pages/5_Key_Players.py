"""
Key Players 페이지
NVIDIA, Google DeepMind, Tesla, Figure AI 등 7대 핵심 플레이어 뉴스 피드
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Key Players | PASIS", layout="wide")

from web.styles import inject_global_css, page_header, section_title, sidebar_brand
inject_global_css()


# ── Key Player 정의 ───────────────────────────────────────────────────────────
KEY_PLAYERS = [
    {"name": "NVIDIA",           "category_label": "Brain & Platform",       "color": "#76B900",
     "must_watch": ["GR00T", "Isaac Lab", "Jetson Thor"]},
    {"name": "Google DeepMind",  "category_label": "Brain & Platform",       "color": "#4285F4",
     "must_watch": ["RT-2", "AutoRT", "PaLM-E"]},
    {"name": "Tesla",            "category_label": "End-to-End AI",          "color": "#CC0000",
     "must_watch": ["Optimus", "FSD", "Dojo"]},
    {"name": "Figure AI",        "category_label": "Hardware & Logic",       "color": "#FF6B00",
     "must_watch": ["Figure 02", "Figure 03", "OpenAI Partnership"]},
    {"name": "Agility Robotics", "category_label": "Industrial / Logistics", "color": "#00875A",
     "must_watch": ["Digit", "Toyota Partnership", "Amazon Partnership"]},
    {"name": "Amazon Robotics",  "category_label": "Infrastructure",         "color": "#FF9900",
     "must_watch": ["Sequoia", "Proteus", "Culper"]},
    {"name": "Sanctuary AI",     "category_label": "Specialized Brain",      "color": "#7B2FBE",
     "must_watch": ["Phoenix", "Carbon OS"]},
]
PLAYER_MAP = {p["name"]: p for p in KEY_PLAYERS}


# ── 데이터 로드 ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_news_feed(company: Optional[str], days_back: int) -> pd.DataFrame:
    from datetime import datetime, timedelta
    from database.init_db import get_session
    from database.models import MarketSignal

    cutoff = datetime.utcnow() - timedelta(days=days_back)
    with get_session() as session:
        q = session.query(MarketSignal).filter(
            MarketSignal.processing_pipeline == "news_feed",
            MarketSignal.published_at >= cutoff,
        )
        if company:
            q = q.filter(MarketSignal.category == company)
        rows = q.order_by(MarketSignal.published_at.desc()).limit(200).all()
        return pd.DataFrame([{
            "title": r.title,
            "source_url": r.source_url,
            "publisher": r.publisher,
            "category": r.category,
            "published_at": r.published_at,
            "confidence_score": r.confidence_score,
            "key_insights": r.key_insights or [],
        } for r in rows])


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand("🏢", "Key Players")
    days_back = st.selectbox("PERIOD", [7, 14, 30], index=1,
                             format_func=lambda x: f"최근 {x}일")
    st.caption("run_pipeline.py 실행 시 자동 갱신됩니다.")


# ── 헤더 ─────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="KEY PLAYERS · COMPETITIVE INTELLIGENCE",
    title="Key Players",
    description="Physical AI 생태계를 주도하는 7개 핵심 기업의 최신 동향을 추적합니다. "
                "각 플레이어의 전략적 행보와 기술 발표를 실시간으로 모니터링하여 경쟁 지형 변화를 포착합니다.",
    tags=["NVIDIA", "Google DeepMind", "Tesla", "Figure AI", "Agility Robotics", "Amazon", "Sanctuary AI"],
)

# ── Key Player 프로필 카드 ────────────────────────────────────────────────────
section_title("플레이어 포트폴리오")
cols = st.columns(len(KEY_PLAYERS))
for col, player in zip(cols, KEY_PLAYERS):
    color = player["color"]
    tags_html = "".join(
        f'<span class="watch-tag">{t}</span>'
        for t in player["must_watch"]
    )
    with col:
        st.markdown(
            f"""
            <div class="player-profile-card" style="border-top-color:{color};">
              <div class="player-name" style="color:{color};">{player["name"]}</div>
              <div class="player-label">{player["category_label"]}</div>
              <div style="margin-top:6px;">{tags_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── 회사 필터 ─────────────────────────────────────────────────────────────────
company_options = ["전체"] + [p["name"] for p in KEY_PLAYERS]
selected_company = st.radio(
    "기업 선택", company_options,
    horizontal=True, label_visibility="collapsed",
)
company_filter: Optional[str] = None if selected_company == "전체" else selected_company

# ── 뉴스 로드 ─────────────────────────────────────────────────────────────────
df = load_news_feed(company_filter, int(days_back))

if df.empty:
    st.info("뉴스 피드 데이터가 없습니다. `python run_pipeline.py --once`를 실행하여 수집하세요.")
    st.stop()

# ── KPI ──────────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("뉴스 수", f"{len(df)}건")
kpi2.metric("출처 수", f"{df['publisher'].nunique()}개")
kpi3.metric("커버 기업", f"{df['category'].nunique()}개")

st.divider()

# ── 뉴스 피드 ─────────────────────────────────────────────────────────────────
section_title(f"뉴스 피드 — {selected_company} ({len(df)}건)")

for _, row in df.iterrows():
    company_name = str(row.get("category", ""))
    player_cfg = PLAYER_MAP.get(company_name, {})
    color = player_cfg.get("color", "#888888")

    published = row.get("published_at")
    try:
        pub_str = pd.to_datetime(published).strftime("%Y-%m-%d") if published is not None else "날짜 미상"
    except Exception:
        pub_str = str(published)[:10]

    publisher  = row.get("publisher") or company_name
    source_url = row.get("source_url", "#")
    title      = row.get("title", "(제목 없음)")
    insights   = row.get("key_insights") or []

    tags_html = "".join(
        f'<span class="watch-tag">{t}</span>' for t in insights
    ) if insights else ""

    st.markdown(
        f"""
        <div class="news-item" style="border-left-color:{color};">
          <span class="news-company-tag" style="background:{color};">{company_name}</span>
          <div class="news-title">{title}</div>
          {f'<div style="margin:4px 0 2px 0;">{tags_html}</div>' if tags_html else ""}
          <div class="news-meta">
            {publisher} &nbsp;·&nbsp; {pub_str}
            &nbsp;·&nbsp;
            <a href="{source_url}" target="_blank">원문 보기 →</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )