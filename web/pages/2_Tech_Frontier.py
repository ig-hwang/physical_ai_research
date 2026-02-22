"""
Tech Frontier 페이지
arXiv 논문, 학회(ICRA, IROS, CVPR), 기술 트렌드
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from config import STRATEGIC_KEYWORDS

st.set_page_config(page_title="Tech Frontier | PASIS", layout="wide")

st.markdown("""
<style>
  .scope-header { font-size:1.5rem; font-weight:800; color:#1A1AEA;
                  border-left:5px solid #1A1AEA; padding-left:12px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_tech_signals(days_back: int = 90) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope="Tech", days_back=days_back)


def compute_keyword_freq(df: pd.DataFrame) -> pd.DataFrame:
    """제목+요약 텍스트에서 전략 키워드 빈도 계산."""
    if df.empty:
        return pd.DataFrame(columns=["keyword", "count"])

    text_corpus = " ".join(
        (str(r.get("title", "")) + " " + str(r.get("summary", "")))
        for _, r in df.iterrows()
    ).lower()

    rows = []
    for kw in STRATEGIC_KEYWORDS:
        count = text_corpus.count(kw.lower())
        if count > 0:
            rows.append({"keyword": kw, "count": count})
    return pd.DataFrame(rows).sort_values("count", ascending=False)


# ── 사이드바 ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Tech Frontier 필터")
    days_back = st.selectbox("조회 기간", [7, 30, 90, 180], index=2,
                             format_func=lambda x: f"최근 {x}일")
    category_filter = st.multiselect(
        "카테고리",
        ["Robotics", "AI Research", "VLA Models", "World Models",
         "Humanoid Locomotion", "Computer Vision", "Machine Learning"],
        default=[],
    )

# ── 본문 ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="scope-header">Tech Frontier</p>', unsafe_allow_html=True)
st.caption("arXiv (cs.RO, cs.AI, cs.CV), ICRA, IROS, CVPR · Embodied AI, VLA, World Models")

df = load_tech_signals(int(days_back))

if df.empty:
    st.info("Tech 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

if category_filter:
    df = df[df["category"].isin(category_filter)]

# ── KPI ───────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("논문/기술 신호", f"{len(df)}건")
col2.metric("평균 신뢰도", f"{df['confidence_score'].mean():.0%}" if not df.empty else "N/A")
col3.metric("카테고리 수", f"{df['category'].nunique()}개")
kw_df = compute_keyword_freq(df)
top_kw = kw_df.iloc[0]["keyword"] if not kw_df.empty else "N/A"
col4.metric("최다 키워드", top_kw)

st.divider()

# ── 키워드 빈도 + 카테고리 분포 ───────────────────────────────────────────────
col_kw, col_cat = st.columns(2)

with col_kw:
    st.markdown("### 전략 키워드 빈도")
    from web.components.charts import keyword_frequency_chart
    st.plotly_chart(keyword_frequency_chart(kw_df, top_n=12), use_container_width=True)

with col_cat:
    st.markdown("### 기술 카테고리 분포")
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(
        cat_counts, x="category", y="count",
        color="category",
        color_discrete_sequence=px.colors.qualitative.Bold,
        title="카테고리별 논문 수",
    )
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── 타임라인 (출판일 기준) ─────────────────────────────────────────────────────
st.markdown("### 기술 트렌드 타임라인")
if "published_at" in df.columns:
    df_time = df.copy()
    df_time["week"] = pd.to_datetime(df_time["published_at"]).dt.to_period("W").dt.start_time
    weekly = df_time.groupby(["week", "category"]).size().reset_index(name="count")
    fig_timeline = px.line(
        weekly, x="week", y="count", color="category",
        markers=True, title="카테고리별 주간 논문 발표 추이",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig_timeline.update_xaxes(tickformat="%Y-%m-%d")
    fig_timeline.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_timeline, use_container_width=True)

st.divider()

# ── 신호 카드 (출처 / 내용 요약 / 인사이트 3섹션) ─────────────────────────────
from web.components.cards import signal_card, signal_card_compact

st.markdown("### 수집 자료 상세")
st.caption("각 논문/기술 신호의 출처 · 내용 요약 · LGU+ 전략 인사이트를 확인하세요.")

view_mode = st.radio("보기 방식", ["카드 전체", "목록"], horizontal=True, label_visibility="collapsed")

for _, row in df.iterrows():
    if "카드" in view_mode:
        signal_card(row.to_dict())
    else:
        signal_card_compact(row.to_dict())

# ── CSV 다운로드 ───────────────────────────────────────────────────────────────
with st.expander("전체 데이터 (CSV)"):
    display_cols = ["title", "category", "publisher", "published_at", "confidence_score", "source_url"]
    display_df = df[[c for c in display_cols if c in df.columns]]
    st.dataframe(display_df, use_container_width=True)
    csv = display_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("CSV 다운로드", csv, "tech_frontier.csv", "text/csv")