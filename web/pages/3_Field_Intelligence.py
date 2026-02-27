"""
Field Intelligence 페이지
PoC, 파트너십, 상용 배포 사례 — 현장 적용 실증 동향
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Field Intelligence | PASIS", layout="wide")

from web.styles import inject_global_css, page_header, section_title, sidebar_brand, plotly_layout, CHART_COLORS
inject_global_css()


@st.cache_data(ttl=300)
def load_case_signals(days_back: int = 90) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope="Case", days_back=days_back)


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand("🏭", "Field Intelligence")
    days_back = st.selectbox("PERIOD", [7, 30, 90, 180], index=2,
                             format_func=lambda x: f"최근 {x}일")
    category_filter = st.multiselect(
        "CATEGORY",
        ["Manufacturing", "Logistics", "PoC Deployment", "Partnership",
         "Investment", "Industry News"],
        default=[],
    )


# ── 헤더 ─────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="CASE SCOPE · PoC / PARTNERSHIP / DEPLOYMENT",
    title="Field Intelligence",
    description="Agility Robotics, Gatik, Amazon Robotics 등의 현장 적용 사례를 추적합니다. "
                "PoC 착수, 파트너십 체결, 상용 배포 이벤트는 시장 진입 타이밍과 전략적 포지셔닝의 핵심 근거입니다.",
    tags=["PoC Deployment", "Partnership", "Commercial Launch", "Agility Robotics", "Amazon", "Gatik"],
)

df = load_case_signals(int(days_back))

if df.empty:
    st.info("Case 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

if category_filter:
    df = df[df["category"].isin(category_filter)]

# ── KPI ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("현장 사례", f"{len(df)}건")
col2.metric("평균 신뢰도", f"{df['confidence_score'].mean():.0%}" if not df.empty else "N/A")
col3.metric("출처 수", f"{df['publisher'].nunique()}개")
col4.metric("카테고리 수", f"{df['category'].nunique()}개")

st.divider()

# ── 차트 ─────────────────────────────────────────────────────────────────────
section_title("산업 섹터 현황")
col_pie, col_timeline = st.columns([1, 2])

with col_pie:
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.pie(
        cat_counts, names="category", values="count",
        hole=0.45,
        color_discrete_sequence=CHART_COLORS,
    )
    plotly_layout(fig, "산업 섹터 분포")
    st.plotly_chart(fig, use_container_width=True)

with col_timeline:
    if "published_at" in df.columns:
        df_time = df.copy()
        df_time["month"] = pd.to_datetime(df_time["published_at"]).dt.to_period("M").dt.start_time
        monthly = df_time.groupby(["month", "category"]).size().reset_index(name="count")
        fig2 = px.bar(
            monthly, x="month", y="count", color="category",
            barmode="stack",
            color_discrete_sequence=CHART_COLORS,
            labels={"month": "월", "count": "건수", "category": "카테고리"},
        )
        plotly_layout(fig2, "사례 누적 추이 (월별)")
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── 신호 상세 ─────────────────────────────────────────────────────────────────
section_title("현장 사례 상세")
st.caption("각 PoC·파트너십 사례의 출처 · 내용 요약 · LGU+ 전략 인사이트를 확인하세요.")

from web.components.cards import signal_card, signal_card_compact
view_mode = st.radio("보기", ["카드", "목록"], horizontal=True, label_visibility="collapsed")

# PoC/파트너십 우선 정렬
priority_cats = ["PoC Deployment", "Partnership", "Manufacturing", "Logistics"]
df_sorted = pd.concat([
    df[df["category"].isin(priority_cats)],
    df[~df["category"].isin(priority_cats)],
])

for _, row in df_sorted.iterrows():
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
                       "field_intelligence.csv", "text/csv")
