"""
Technology Radar 페이지
arXiv 논문, ICRA/IROS/CVPR 학회, Embodied AI·VLA·World Models 기술 동향
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from config import STRATEGIC_KEYWORDS

st.set_page_config(page_title="Technology Radar | PASIS", layout="wide")

from web.styles import inject_global_css, page_header, section_title, sidebar_brand, plotly_layout, CHART_COLORS
inject_global_css()


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


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand("🔬", "Technology Radar")
    days_back = st.selectbox("PERIOD", [7, 30, 90, 180], index=2,
                             format_func=lambda x: f"최근 {x}일")
    category_filter = st.multiselect(
        "CATEGORY",
        ["Robotics", "AI Research", "VLA Models", "World Models",
         "Humanoid Locomotion", "Computer Vision", "Machine Learning"],
        default=[],
    )


# ── 헤더 ─────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="TECH SCOPE · arXiv / ICRA / IROS / CVPR",
    title="Technology Radar",
    description="arXiv (cs.RO·cs.AI·cs.CV), ICRA, IROS, CVPR 등 핵심 학술 채널의 최신 연구를 모니터링합니다. "
                "Embodied AI, VLA Models, World Models 등 핵심 기술의 성숙도와 트렌드 방향성을 추적합니다.",
    tags=["arXiv cs.RO", "ICRA · IROS", "CVPR", "VLA Models", "World Models", "Embodied AI"],
)

df = load_tech_signals(int(days_back))

if df.empty:
    st.info("Tech 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

if category_filter:
    df = df[df["category"].isin(category_filter)]

# ── KPI ──────────────────────────────────────────────────────────────────────
kw_df = compute_keyword_freq(df)
top_kw = kw_df.iloc[0]["keyword"] if not kw_df.empty else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("논문/기술 신호", f"{len(df)}건")
col2.metric("평균 신뢰도", f"{df['confidence_score'].mean():.0%}" if not df.empty else "N/A")
col3.metric("카테고리 수", f"{df['category'].nunique()}개")
col4.metric("최다 키워드", top_kw)

st.divider()

# ── 키워드 + 카테고리 차트 ────────────────────────────────────────────────────
section_title("기술 키워드 분석")
col_kw, col_cat = st.columns(2)

with col_kw:
    from web.components.charts import keyword_frequency_chart
    fig_kw = keyword_frequency_chart(kw_df, top_n=12)
    plotly_layout(fig_kw, "전략 키워드 빈도 (Top 12)")
    st.plotly_chart(fig_kw, use_container_width=True)

with col_cat:
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(
        cat_counts, x="category", y="count",
        color="category",
        color_discrete_sequence=CHART_COLORS,
    )
    plotly_layout(fig, "기술 카테고리 분포")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── 트렌드 타임라인 ────────────────────────────────────────────────────────────
section_title("기술 발표 타임라인")
if "published_at" in df.columns:
    df_time = df.copy()
    df_time["week"] = pd.to_datetime(df_time["published_at"]).dt.to_period("W").dt.start_time
    weekly = df_time.groupby(["week", "category"]).size().reset_index(name="count")
    fig_tl = px.line(
        weekly, x="week", y="count", color="category",
        markers=True,
        color_discrete_sequence=CHART_COLORS,
    )
    plotly_layout(fig_tl, "카테고리별 주간 발표 추이")
    fig_tl.update_xaxes(tickformat="%Y-%m-%d")
    st.plotly_chart(fig_tl, use_container_width=True)

st.divider()

# ── 신호 상세 ─────────────────────────────────────────────────────────────────
section_title("수집 자료 상세")
st.caption("각 논문·기술 신호의 출처 · 내용 요약 · LGU+ 전략 인사이트를 확인하세요.")

from web.components.cards import signal_card, signal_card_compact
view_mode = st.radio("보기", ["카드", "목록"], horizontal=True, label_visibility="collapsed")

for _, row in df.iterrows():
    if "카드" in view_mode:
        signal_card(row.to_dict())
    else:
        signal_card_compact(row.to_dict())

st.divider()
with st.expander("전체 데이터 (CSV 다운로드)"):
    cols = ["title", "category", "publisher", "published_at", "confidence_score", "source_url"]
    display_df = df[[c for c in cols if c in df.columns]]
    st.dataframe(display_df, use_container_width=True)
    st.download_button("CSV 다운로드", display_df.to_csv(index=False, encoding="utf-8-sig"),
                       "technology_radar.csv", "text/csv")
