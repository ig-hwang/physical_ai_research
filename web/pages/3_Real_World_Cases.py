"""
Real-world Cases 페이지
PoC, 파트너십, 상용 배포 사례 · Agility Robotics, Gatik, Amazon
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Real-world Cases | PASIS", layout="wide")

st.markdown("""
<style>
  .scope-header { font-size:1.5rem; font-weight:800; color:#00A651;
                  border-left:5px solid #00A651; padding-left:12px; }
  .deployment-tag {
    background:#E8F5E9; color:#00A651;
    padding:2px 8px; border-radius:8px;
    font-size:0.75rem; font-weight:700;
  }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_case_signals(days_back: int = 90) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope="Case", days_back=days_back)


# ── 사이드바 ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Real-world Cases 필터")
    days_back = st.selectbox("조회 기간", [7, 30, 90, 180], index=2,
                             format_func=lambda x: f"최근 {x}일")
    category_filter = st.multiselect(
        "카테고리",
        ["Manufacturing", "Logistics", "PoC Deployment", "Partnership",
         "Investment", "Industry News"],
        default=[],
    )

# ── 본문 ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="scope-header">Real-world Cases</p>', unsafe_allow_html=True)
st.caption("PoC, 파트너십, 상용 배포 · Agility Robotics, Gatik, Amazon, Figure AI × BMW")

df = load_case_signals(int(days_back))

if df.empty:
    st.info("Case 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

if category_filter:
    df = df[df["category"].isin(category_filter)]

# ── KPI ───────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("사례 신호 수", f"{len(df)}건")
col2.metric("출처 수", f"{df['publisher'].nunique()}개")
col3.metric("카테고리 수", f"{df['category'].nunique()}개")

st.divider()

# ── 배포 섹터별 분포 ───────────────────────────────────────────────────────────
col_pie, col_timeline = st.columns([1, 2])

with col_pie:
    st.markdown("### 산업 섹터 분포")
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.pie(
        cat_counts, names="category", values="count",
        hole=0.45,
        color_discrete_sequence=["#00A651", "#4CAF50", "#81C784",
                                  "#A5D6A7", "#C8E6C9", "#E8F5E9"],
    )
    fig.update_layout(showlegend=True, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_timeline:
    st.markdown("### 사례 누적 추이")
    if "published_at" in df.columns:
        df_time = df.copy()
        df_time["month"] = pd.to_datetime(df_time["published_at"]).dt.to_period("M").dt.start_time
        monthly = df_time.groupby(["month", "category"]).size().reset_index(name="count")
        fig2 = px.bar(
            monthly, x="month", y="count", color="category",
            barmode="stack",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={"month": "월", "count": "건수", "category": "카테고리"},
        )
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── 사례 카드 (출처 / 내용 요약 / 인사이트 3섹션) ─────────────────────────────
from web.components.cards import signal_card, signal_card_compact

st.markdown("### 수집 자료 상세")
st.caption("각 PoC/파트너십 사례의 출처 · 내용 요약 · LGU+ 전략 인사이트를 확인하세요.")

view_mode = st.radio("보기 방식", ["카드 전체", "목록"], horizontal=True, label_visibility="collapsed")

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

# ── 다운로드 ───────────────────────────────────────────────────────────────────
with st.expander("전체 데이터 (CSV)"):
    display_cols = ["title", "category", "publisher", "published_at", "confidence_score", "source_url"]
    display_df = df[[c for c in display_cols if c in df.columns]]
    st.dataframe(display_df, use_container_width=True)
    csv = display_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("CSV 다운로드", csv, "real_world_cases.csv", "text/csv")