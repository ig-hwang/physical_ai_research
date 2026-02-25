"""
Key Player News Feed 페이지
NVIDIA, Google DeepMind, Tesla, Figure AI, Agility Robotics, Amazon Robotics, Sanctuary AI
Claude 분석 없이 수집 즉시 표시하는 빠른 피드.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Key Player News Feed | PASIS", layout="wide")

st.markdown("""
<style>
  .feed-header {
    font-size:1.5rem; font-weight:800; color:#1A1A2E;
    border-left:5px solid #1A1A2E; padding-left:12px;
  }
  .player-card {
    border-radius:10px; padding:12px 14px;
    margin-bottom:6px; border:1px solid #e0e0e0;
  }
  .player-name { font-size:0.95rem; font-weight:800; }
  .player-label { font-size:0.72rem; color:#666; margin-top:2px; }
  .must-watch-tag {
    display:inline-block;
    background:#F0F4FF; color:#3B5BDB;
    padding:1px 7px; border-radius:6px;
    font-size:0.68rem; font-weight:600; margin:2px 2px 0 0;
  }
  .news-card {
    border-left:4px solid; border-radius:6px;
    padding:10px 14px; margin-bottom:8px;
    background:#FAFAFA;
  }
  .news-title { font-size:0.92rem; font-weight:700; color:#1A1A2E; }
  .news-meta { font-size:0.75rem; color:#888; margin-top:4px; }
  .company-badge {
    display:inline-block;
    padding:2px 9px; border-radius:8px;
    font-size:0.72rem; font-weight:700;
    color:#fff; margin-right:6px;
  }
</style>
""", unsafe_allow_html=True)


# ── Key Player 정의 (config에서 로드) ─────────────────────────────────────────
from config import KEY_PLAYERS

PLAYER_MAP: dict[str, dict] = {p["name"]: p for p in KEY_PLAYERS}


# ── 데이터 로드 ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_news_feed(company: str | None, days_back: int) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_news_feed_df
    with get_session() as session:
        return get_news_feed_df(session, company=company, days_back=days_back)


# ── 사이드바 ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### News Feed 필터")
    days_back = st.selectbox(
        "조회 기간",
        [7, 14, 30],
        index=1,
        format_func=lambda x: f"최근 {x}일",
    )
    st.caption("데이터는 run_pipeline.py 실행 시 자동 갱신됩니다.")

# ── 헤더 ───────────────────────────────────────────────────────────────────────
st.markdown('<p class="feed-header">Key Player News Feed</p>', unsafe_allow_html=True)
st.caption("7대 핵심 플레이어의 최신 뉴스 · Claude 분석 없이 수집 즉시 표시")

st.divider()

# ── Key Player 프로필 카드 그리드 ─────────────────────────────────────────────
st.markdown("#### Key Players 개요")
cols = st.columns(len(KEY_PLAYERS))
for col, player in zip(cols, KEY_PLAYERS):
    color = player["color"]
    tags_html = "".join(
        f'<span class="must-watch-tag">{t}</span>'
        for t in player["must_watch"]
    )
    with col:
        st.markdown(
            f"""
            <div class="player-card" style="border-top:3px solid {color};">
              <div class="player-name" style="color:{color};">{player["name"]}</div>
              <div class="player-label">{player["category_label"]}</div>
              <div style="margin-top:6px;">{tags_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── 회사 필터 버튼 ─────────────────────────────────────────────────────────────
st.markdown("#### 필터")
company_options = ["전체"] + [p["name"] for p in KEY_PLAYERS]

selected_company = st.radio(
    "회사 선택",
    company_options,
    horizontal=True,
    label_visibility="collapsed",
)
company_filter = None if selected_company == "전체" else selected_company

st.divider()

# ── 뉴스 로드 ─────────────────────────────────────────────────────────────────
df = load_news_feed(company_filter, int(days_back))

if df.empty:
    st.info(
        "뉴스 피드 데이터가 없습니다. `python run_pipeline.py --once` 를 실행하여 수집하세요.",
        icon="ℹ️",
    )
    st.stop()

# ── KPI ───────────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("뉴스 수", f"{len(df)}건")
kpi2.metric("출처 수", f"{df['publisher'].nunique()}개")
kpi3.metric("커버 기업", f"{df['category'].nunique()}개")

st.divider()

# ── 뉴스 피드 목록 ─────────────────────────────────────────────────────────────
st.markdown(f"#### 뉴스 피드 — {selected_company} ({len(df)}건)")

for _, row in df.iterrows():
    company_name: str = row.get("category", "")
    player_cfg = PLAYER_MAP.get(company_name, {})
    color = player_cfg.get("color", "#888888")

    published = row.get("published_at")
    if published is not None:
        try:
            pub_str = pd.to_datetime(published).strftime("%Y-%m-%d")
        except Exception:
            pub_str = str(published)[:10]
    else:
        pub_str = "날짜 미상"

    publisher = row.get("publisher") or company_name
    source_url = row.get("source_url", "#")
    title = row.get("title", "(제목 없음)")

    # Must-Watch 태그 매칭 (key_insights 필드)
    insights = row.get("key_insights") or []
    tags_html = "".join(
        f'<span class="must-watch-tag">{t}</span>'
        for t in insights
    ) if insights else ""

    st.markdown(
        f"""
        <div class="news-card" style="border-left-color:{color};">
          <span class="company-badge" style="background:{color};">{company_name}</span>
          <span class="news-title">{title}</span>
          {f'<div style="margin-top:4px;">{tags_html}</div>' if tags_html else ""}
          <div class="news-meta">
            {publisher} &nbsp;·&nbsp; {pub_str}
            &nbsp;·&nbsp;
            <a href="{source_url}" target="_blank" style="color:#3B5BDB;">원문 보기 →</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
