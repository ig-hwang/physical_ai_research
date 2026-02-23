"""
PASIS UI Card Components - Streamlit 렌더링 모듈

신호 카드 구조:
  ┌──────────────────────────────────────────────────────┐
  │  [스코프 배지] [카테고리]              [날짜] [신뢰도] │
  │  제목 (크고 굵게)                         [원문 링크] │
  ├─────────────── 출처 ─────────────────────────────────┤
  │  발행기관  ·  URL                                    │
  ├─────────────── 내용 요약 ────────────────────────────┤
  │  피라미드 원칙 기반 요약문                            │
  ├─────────────── LGU+ 전략 인사이트 ───────────────────┤
  │  전략적 시사점                                       │
  │  • 핵심 인사이트 1                                   │
  │  • 핵심 인사이트 2                                   │
  └──────────────────────────────────────────────────────┘
"""
from __future__ import annotations

from urllib.parse import urlparse

import streamlit as st


_USELESS_URL_PATTERNS = (
    "company=Unknown",       # SEC EDGAR 기업명 미확인 fallback
    "browse-edgar?company=", # SEC EDGAR 일반 검색 (특정 공시 아님)
)


def _is_valid_url(url: str) -> bool:
    """실제 원문으로 연결되는 유효한 URL인지 검사."""
    if not url:
        return False
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.netloc:
            return False
        # 원문 없이 검색 결과로만 연결되는 fallback URL 제외
        if any(pat in url for pat in _USELESS_URL_PATTERNS):
            return False
        return True
    except Exception:
        return False


# ── 스코프별 색상 팔레트 ────────────────────────────────────────────────────────
_SCOPE_COLORS = {
    "Market":  {"bg": "#E4002B", "light": "#FFF0F0", "border": "#E4002B"},
    "Tech":    {"bg": "#1A1AEA", "light": "#F0F0FF", "border": "#1A1AEA"},
    "Case":    {"bg": "#00A651", "light": "#F0FFF5", "border": "#00A651"},
    "Policy":  {"bg": "#F5A623", "light": "#FFFBF0", "border": "#F5A623"},
}

_SCOPE_LABELS_KO = {
    "Market": "시장 신호",
    "Tech": "기술 프론티어",
    "Case": "실제 사례",
    "Policy": "정책/표준",
}

_SCOPE_BADGE_CSS = {
    "Market":  "background:#E4002B;color:white",
    "Tech":    "background:#1A1AEA;color:white",
    "Case":    "background:#00A651;color:white",
    "Policy":  "background:#F5A623;color:white",
}

# ── 카드 공통 CSS (앱 최초 로드 시 1회 주입) ─────────────────────────────────
CARD_CSS = """
<style>
.pasis-card {
  background: #ffffff;
  border: 1px solid #E8ECF0;
  border-radius: 12px;
  padding: 0;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.pasis-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); }

/* 카드 헤더 */
.card-header {
  padding: 14px 18px 10px 18px;
  border-bottom: 1px solid #F0F0F0;
}
.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1A1A2E;
  margin: 6px 0 0 0;
  line-height: 1.4;
}
.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 2px;
}
.scope-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 700;
  white-space: nowrap;
}
.category-tag {
  font-size: 0.78rem;
  color: #555;
  font-weight: 600;
}
.date-tag {
  font-size: 0.75rem;
  color: #888;
  margin-left: auto;
}
.confidence-tag {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 8px;
}

/* 섹션 공통 */
.card-section {
  padding: 12px 18px;
  border-bottom: 1px solid #F5F5F5;
}
.card-section:last-child { border-bottom: none; }
.section-label {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #999;
  margin-bottom: 6px;
}

/* 출처 섹션 */
.source-section { background: #FAFBFC; }
.source-publisher {
  font-size: 0.85rem;
  font-weight: 700;
  color: #333;
}
.source-url {
  font-size: 0.75rem;
  color: #1A1AEA;
  word-break: break-all;
  margin-top: 2px;
}

/* 내용 요약 섹션 */
.summary-text {
  font-size: 0.88rem;
  line-height: 1.65;
  color: #333;
}

/* 인사이트 섹션 */
.insight-section { background: #F8F9FB; }
.implication-text {
  font-size: 0.88rem;
  line-height: 1.6;
  color: #1A1A2E;
  font-weight: 500;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border-left: 3px solid #E4002B;
  margin-bottom: 8px;
}
.insight-item {
  font-size: 0.83rem;
  color: #444;
  padding: 3px 0;
  padding-left: 14px;
  position: relative;
  line-height: 1.5;
}
.insight-item::before {
  content: "▸";
  position: absolute;
  left: 0;
  color: #888;
  font-size: 0.7rem;
}
.source-link-btn {
  display: inline-block;
  padding: 3px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #444;
  text-decoration: none;
  background: white;
  margin-top: 4px;
}
.source-link-btn:hover { background: #f0f0f0; }

/* 분석 없음 뱃지 */
.no-analysis-tag {
  font-size: 0.7rem; color: #999;
  font-style: italic;
}
</style>
"""

_css_injected = False


def _inject_css() -> None:
    global _css_injected
    if not _css_injected:
        st.markdown(CARD_CSS, unsafe_allow_html=True)
        _css_injected = True


def render_scope_badge(scope: str) -> str:
    """scope → HTML 배지 문자열."""
    css = _SCOPE_BADGE_CSS.get(scope, "background:#888;color:white")
    label = _SCOPE_LABELS_KO.get(scope, scope)
    return (
        f'<span class="scope-badge" style="{css}">{label}</span>'
    )


def _confidence_html(score: float | None) -> str:
    if score is None:
        return ""
    pct = int(score * 100)
    if pct >= 90:
        color, bg = "#00A651", "#E8F5E9"
    elif pct >= 70:
        color, bg = "#F5A623", "#FFF8E1"
    else:
        color, bg = "#999", "#F5F5F5"
    return (
        f'<span class="confidence-tag" style="color:{color};background:{bg};">'
        f'신뢰도 {pct}%</span>'
    )


def signal_card(row: dict, expanded: bool = False) -> None:
    """
    개별 신호를 아코디언(st.expander) 방식으로 렌더링.
    - 기본: 접힌 상태 — 제목/스코프/출처/날짜/신뢰도를 한 줄에 표시
    - 클릭 시 펼침: 출처 URL + 원문 버튼 / 내용 요약 / LGU+ 전략 인사이트

    Args:
        row: signal dict
        expanded: True = 기본 펼침
    """
    _inject_css()

    scope       = row.get("scope", "")
    category    = row.get("category") or ""
    title       = row.get("title") or "제목 없음"
    publisher   = row.get("publisher") or ""
    source_url  = row.get("source_url") or ""
    confidence  = row.get("confidence_score")
    summary     = row.get("summary") or ""
    implication = row.get("strategic_implication") or ""
    insights    = row.get("key_insights") or []
    pub_date    = row.get("published_at", "")
    if hasattr(pub_date, "strftime"):
        pub_date = pub_date.strftime("%Y-%m-%d")
    else:
        pub_date = str(pub_date)[:10]

    scope_label = _SCOPE_LABELS_KO.get(scope, scope)
    conf_pct    = f"  신뢰도 {int(confidence * 100)}%" if confidence else ""
    pub_short   = f"  {publisher}" if publisher else ""
    date_short  = f"  {pub_date}" if pub_date else ""

    # expander 헤더: [스코프] 제목 — 출처 | 날짜 | 신뢰도
    header = f"[{scope_label}]  {title[:75]}{'…' if len(title) > 75 else ''}{pub_short}{date_short}{conf_pct}"

    with st.expander(header, expanded=expanded):
        # ── 출처 + 원문 버튼 ─────────────────────────────────────────────────
        col_src, col_btn = st.columns([4, 1])
        url_ok = _is_valid_url(source_url)
        with col_src:
            meta_parts = [p for p in [publisher, category, pub_date] if p]
            st.caption("  ·  ".join(meta_parts))
            if url_ok:
                url_disp = source_url if len(source_url) <= 80 else source_url[:77] + "..."
                st.markdown(
                    f'<a href="{source_url}" target="_blank" '
                    f'style="font-size:0.78rem;color:#1A1AEA;word-break:break-all;">'
                    f'{url_disp}</a>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span style="font-size:0.78rem;color:#999;">원문 URL 없음</span>',
                    unsafe_allow_html=True,
                )
        with col_btn:
            if url_ok:
                st.link_button("원문 보기 →", source_url, use_container_width=True)
            else:
                st.button("URL 없음", disabled=True, use_container_width=True)

        st.divider()

        # ── 내용 요약 ────────────────────────────────────────────────────────
        has_analysis = bool(summary and len(summary) > 20 and "수집된" not in summary)
        st.markdown(
            '<span style="font-size:0.7rem;font-weight:800;letter-spacing:.08em;'
            'text-transform:uppercase;color:#999;">내용 요약</span>',
            unsafe_allow_html=True,
        )
        if has_analysis:
            st.markdown(summary)
        else:
            st.caption("ANTHROPIC_API_KEY 설정 후 자동 생성됩니다.")

        # ── LGU+ 전략 인사이트 ───────────────────────────────────────────────
        has_impl    = bool(implication and implication != "LGU+ 전략팀 분석 필요.")
        has_insights = bool(isinstance(insights, list) and any(insights))
        if has_impl or has_insights:
            st.divider()
            st.markdown(
                '<span style="font-size:0.7rem;font-weight:800;letter-spacing:.08em;'
                'text-transform:uppercase;color:#E4002B;">LGU+ 전략 인사이트</span>',
                unsafe_allow_html=True,
            )
            if has_impl:
                st.info(implication, icon="💡")
            if has_insights:
                for item in insights:
                    if item:
                        st.markdown(f"▸ {item}")


def signal_card_compact(row: dict) -> None:
    """
    테이블 행 스타일 압축 카드 — 목록 뷰 전용.
    제목 + 출처 + 날짜만 표시, 클릭 시 상세 모달 없음.
    """
    _inject_css()
    scope      = row.get("scope", "")
    title      = (row.get("title") or "")[:90]
    publisher  = row.get("publisher") or ""
    pub_date   = row.get("published_at", "")
    confidence = row.get("confidence_score")
    source_url = row.get("source_url") or ""

    if hasattr(pub_date, "strftime"):
        pub_date = pub_date.strftime("%Y-%m-%d")
    else:
        pub_date = str(pub_date)[:10]

    badge  = render_scope_badge(scope)
    conf_h = _confidence_html(confidence)
    link   = f'<a href="{source_url}" target="_blank" style="color:#1A1AEA;font-size:0.78rem;">원문</a>' if source_url else ""

    st.markdown(f"""
    <div style="padding:10px 14px;border-bottom:1px solid #F0F0F0;
                display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
      {badge}
      <span style="flex:1;font-size:0.88rem;font-weight:600;color:#1A1A2E;">{title}</span>
      <span style="font-size:0.78rem;color:#666;">{publisher}</span>
      <span style="font-size:0.75rem;color:#999;">{pub_date}</span>
      {conf_h}
      {link}
    </div>
    """, unsafe_allow_html=True)


def kpi_row(metrics: dict) -> None:
    """KPI 메트릭 행."""
    cols = st.columns(6)
    kpis = [
        ("전체 신호",     metrics.get("total_signals", 0),                           "건"),
        ("이번 주 신규",  metrics.get("this_week", 0),                               "건"),
        ("평균 신뢰도",   f"{metrics.get('avg_confidence', 0):.0%}",                 ""),
        ("Market",       metrics.get("market", 0),                                  "건"),
        ("Tech",         metrics.get("tech", 0),                                    "건"),
        ("Case + Policy",metrics.get("case", 0) + metrics.get("policy", 0),         "건"),
    ]
    for col, (label, value, suffix) in zip(cols, kpis):
        with col:
            st.metric(label=label, value=f"{value}{suffix}")


def scope_filter_sidebar() -> list[str]:
    """사이드바 스코프 필터."""
    st.sidebar.markdown("### 스코프 필터")
    all_scopes = ["Market", "Tech", "Case", "Policy"]
    selected = [
        s for s in all_scopes
        if st.sidebar.checkbox(_SCOPE_LABELS_KO[s], value=True, key=f"sf_{s}")
    ]
    return selected if selected else all_scopes


def render_no_data_message(scope: str = "") -> None:
    msg = f"{scope} 스코프의 " if scope else ""
    st.info(
        f"{msg}수집된 데이터가 없습니다.\n\n"
        "**파이프라인을 실행하세요:**\n```bash\npython run_pipeline.py --once\n```"
    )
