"""
Strategic Analyzer - Claude API 기반 인사이트 추출
strategic-analysis SKILL.md 구현체

분석 프레임워크:
  - Pyramid Principle: Conclusion → Evidence → Actions
  - LGU+ Relevance: Direct Impact / Future Opportunity / Competitive Threat / Partnership
  - Confidence Scoring: Primary source(SEC, arXiv) > Secondary(뉴스)
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_ANALYSIS_MODEL,
    CLAUDE_MAX_TOKENS, CLAUDE_REPORT_MAX_TOKENS, PROCESSED_DIR,
)

log = logging.getLogger(__name__)

# Claude API 분석 프롬프트 (Business Korean, 피라미드 원칙)
_SIGNAL_ANALYSIS_PROMPT = """당신은 LG유플러스 포트폴리오 전략팀의 Physical AI 시장 전략 분석가입니다.
아래 Physical AI 관련 신호(signal)를 분석하여 정형화된 JSON을 반환하십시오.

분석 원칙:
1. 피라미드 원칙: 결론 → 근거 → 액션 순서로 작성
2. LGU+ 관점: Direct Impact / Future Opportunity / Competitive Threat / Partnership Potential 중 가장 관련 있는 것 명시
3. 결론 문장은 반드시 "LGU+ 관점:" 또는 구체적 시사점으로 시작
4. Business Korean 사용 (기술 용어는 영어 유지)

입력 신호:
{signal_json}

다음 JSON 형식으로만 응답하십시오 (다른 텍스트 없이):
{{
  "summary": "결론 우선 요약 (3-5문장, 한국어)",
  "strategic_implication": "LGU+ 관점의 전략적 시사점과 권고 액션 (한국어)",
  "key_insights": [
    "인사이트 1: 기술 성숙도 평가",
    "인사이트 2: 시장 타이밍",
    "인사이트 3: 파트너십/사업 기회"
  ],
  "category": "Investment|M&A|PoC Deployment|Partnership|VLA Models|World Models|Humanoid Locomotion|Regulation|Standard|Industry News",
  "lgu_relevance_type": "Direct Impact|Future Opportunity|Competitive Threat|Partnership Potential"
}}"""

_WEEKLY_REPORT_PROMPT = """당신은 LG유플러스 포트폴리오 전략팀의 Physical AI 수석 인텔리전스 분석가입니다.
임원이 "5분 브리핑"으로 이번 주 Physical AI 시장 전체를 파악할 수 있는 HTML 보고서를 작성하십시오.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[최우선 준수 사항]
▶ 6개 섹션 전부 완성 필수. 섹션 중간 잘림 금지.
▶ 분량 제한 엄수 (초과하면 마지막 섹션이 잘림):
   Section 1: 핵심 포인트 3개, 각 2문장 이내
   Section 2: 최대 4개 기업, 기업당 사실·해석·LGU+ 각 1~2문장
   Section 3: 최대 4개 트렌드, 트렌드당 2문장 이내
   Section 4: 200자 이내 산문 + 불릿 2~3개
   Section 5: 150자 이내 (데이터 없으면 생략)
   Section 6: 타임라인별 액션 1~2개, 각 1문장

[절대 금지 사항]
- 수집 건수, 스코프별 통계 나열 → 금지
- "총 N건이 수집되었습니다" 형식 → 금지
- 신호를 단순 제목 리스트로 나열 → 금지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[신호 데이터 — 이번 주 수집 {total}건 중 주요 신호]
{signals_json}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[필수 HTML 구조 — 6개 섹션, 순서와 제목 그대로]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 1 — 이번 주 핵심 메시지
"이번 주 Physical AI 시장에서 가장 중요한 일은 무엇인가?"에 직접 답하는 1~2문단 서술.
이어서 핵심 포인트 3개 불릿 (각각 수치 또는 기업명 필수 포함).
독자가 이 섹션만 읽어도 이번 주 시장 흐름을 파악할 수 있어야 함.

## SECTION 2 — 기업별 주요 동향 (Company Intelligence)
신호에 등장한 주요 기업별로 소제목을 달고 서술. 데이터에 없는 기업은 포함하지 않음.
각 기업 항목 형식:
  → [사실] 이번 주 해당 기업에서 어떤 결정·발표·공시가 있었는가
  → [해석] 그것이 Physical AI 생태계에서 왜 중요한가
  → [LGU+ 관련성] LGU+ 전략팀 관점에서의 시사점 1문장

## SECTION 3 — 포착된 기술 트렌드 (Tech Trend Radar)
이번 주 신호에서 도출되는 기술 흐름 3~5개를 트렌드 단위로 분석.
"왜 지금 이 트렌드가 중요한가"에 집중. 단순 기술 설명 금지.
각 트렌드: 트렌드 제목 | 근거 신호(논문/발표/사례) | 성숙도 [Early/Emerging/Mainstream] | 향후 전망 1문장

## SECTION 4 — 시장 & 투자 흐름 (Market Pulse)
"자금이 어디로 향하는가", "어떤 기업군이 강해지고 있는가" 관점으로 서술.
투자·M&A·파트너십·공시 동향 종합 분석. 데이터가 없으면 섹션 생략.

## SECTION 5 — 규제 & 표준 레이더 (Policy Watch)
규제·표준 신호가 있을 경우만 작성. 없으면 섹션 생략.
"이 변화가 시장 참여자에게 미치는 실질적 영향"에 집중.

## SECTION 6 — LGU+ 전략 액션 아이템
모호한 표현("검토 필요", "관심 권고") 금지. 매우 구체적으로.
- 즉시 (1개월 이내): 담당자가 다음 주 당장 할 수 있는 액션 2~3개
- 단기 (3개월): 준비·구축 과제 2~3개
- 중기 (6~12개월): 전략 포지셔닝 방향 1~2개

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[HTML 출력 요건 — 반드시 준수]
① <!DOCTYPE>, <html>, <head>, <body>, <style> 태그 완전 금지 — HTML 조각(fragment)만 반환
② CSS·인라인 스타일 일절 금지 — 아래 지정 클래스만 사용
③ 코드블록 래핑(```html ... ```) 금지 — 순수 HTML 텍스트만 출력

[사용 가능 HTML 구조]
<div class="rpt-section">
  <div class="rpt-section-title">섹션 제목</div>
  <div class="rpt-body">본문 내용 <strong>강조</strong></div>
  <ul class="rpt-bullets"><li>항목</li></ul>
</div>

기업별 동향:
<div class="rpt-company">
  <div class="rpt-company-name"><a href="URL">기업명</a></div>
  <div class="rpt-fact"><strong>사실</strong> 내용</div>
  <div class="rpt-why">해석 내용</div>
  <div class="rpt-lgu">LGU+ 관련성 내용</div>
</div>

기술 트렌드:
<div class="rpt-trend">
  <div class="rpt-trend-title">트렌드명 <span class="rpt-badge">Emerging</span></div>
  <div class="rpt-body">근거 및 전망</div>
</div>

LGU+ 액션:
<div class="rpt-action rpt-action--now">즉시(1개월): 구체적 액션</div>
<div class="rpt-action rpt-action--short">단기(3개월): 준비 과제</div>
<div class="rpt-action rpt-action--mid">중기(6~12개월): 전략 방향</div>

source_url이 있는 경우 기업명·논문명에 반드시 <a href="URL" target="_blank">하이퍼링크</a> 삽입.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


class StrategicAnalyzer:
    """Claude API 기반 전략 분석 에이전트."""

    def __init__(self) -> None:
        self._client: Optional[object] = None
        self._available = bool(ANTHROPIC_API_KEY)

        if self._available:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                log.info(f"Claude API 연결 완료 (모델: {CLAUDE_MODEL})")
            except ImportError:
                log.warning("anthropic 패키지 미설치. pip install anthropic")
                self._available = False
        else:
            log.warning("ANTHROPIC_API_KEY 미설정. 분석 없이 기본 메타데이터만 저장됩니다.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
    )
    def analyze_signal(self, signal: dict) -> dict:
        """
        단일 신호를 Claude로 분석하여 summary, strategic_implication 추가.
        API 키 미설정 시 fallback 처리.
        """
        if not self._available:
            return self._fallback_analysis(signal)

        try:
            import anthropic

            signal_json = json.dumps(
                {
                    "title": signal.get("title", ""),
                    "raw_content": signal.get("raw_content", "")[:600],
                    "scope": signal.get("scope", ""),
                    "publisher": signal.get("source_metadata", {}).get("publisher", ""),
                    "published_at": signal.get("source_metadata", {}).get("published_at", ""),
                },
                ensure_ascii=False,
            )

            message = self._client.messages.create(
                model=CLAUDE_ANALYSIS_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": _SIGNAL_ANALYSIS_PROMPT.format(signal_json=signal_json),
                    }
                ],
            )

            content = message.content[0].text.strip()
            # JSON 파싱 (마크다운 펜스 제거 방어 처리)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            parsed = json.loads(content)

            signal["summary"] = parsed.get("summary", "")
            signal["strategic_implication"] = parsed.get("strategic_implication", "")
            signal["key_insights"] = parsed.get("key_insights", [])
            signal["category"] = parsed.get("category", signal.get("category", ""))
            signal["lgu_relevance_type"] = parsed.get("lgu_relevance_type", "")
            signal["analyzed_by"] = CLAUDE_MODEL

        except json.JSONDecodeError as e:
            log.warning(f"Claude 응답 JSON 파싱 실패: {e}. Fallback 처리.")
            return self._fallback_analysis(signal)
        except Exception as e:
            log.error(f"Claude API 호출 오류: {e}")
            return self._fallback_analysis(signal)

        return signal

    def analyze_batch(
        self,
        signals: list[dict],
        save_processed: bool = True,
    ) -> list[dict]:
        """
        신호 배치 분석. 처리된 데이터를 data/processed/에 저장.
        """
        log.info(f"=== 배치 분석 시작: {len(signals)}건 ===")
        analyzed: list[dict] = []

        for i, signal in enumerate(signals):
            try:
                result = self.analyze_signal(signal)
                analyzed.append(result)
                if (i + 1) % 10 == 0:
                    log.info(f"진행률: {i+1}/{len(signals)}")
            except Exception as e:
                log.error(f"신호 분석 오류 (event_id={signal.get('event_id')}): {e}")
                analyzed.append(self._fallback_analysis(signal))

        log.info(f"=== 배치 분석 완료: {len(analyzed)}건 ===")

        if save_processed and analyzed:
            self._save_processed(analyzed)

        return analyzed

    def generate_weekly_report(self, signals: list[dict]) -> str:
        """
        주간 전략 브리핑 HTML 리포트 생성.
        API 미설정 시 기본 HTML 반환.
        """
        if not self._available or not signals:
            return self._fallback_weekly_report(signals)

        # 신뢰도 기준 정렬 후 스코프별 상위 신호 선택 (각 5건씩, 최대 20건)
        # 8192 토큰 출력 한도 내 6개 섹션 완성을 위해 입력 신호 수 최적화
        def _sort_key(s: dict) -> float:
            return float(s.get("confidence_score") or s.get("data_quality_score") or 0.5)

        top_signals = []
        for scope in ["Market", "Tech", "Case", "Policy"]:
            scope_sigs = sorted(
                [s for s in signals if s.get("scope") == scope],
                key=_sort_key,
                reverse=True,
            )
            top_signals.extend(scope_sigs[:5])

        signals_summary = json.dumps(
            [
                {
                    "scope": s.get("scope"),
                    "category": s.get("category"),
                    "title": s.get("title", ""),
                    "content": (
                        s.get("summary")
                        or s.get("raw_content", "")
                    )[:500],
                    "strategic_implication": s.get("strategic_implication", ""),
                    "key_insights": s.get("key_insights", []),
                    "publisher": (
                        s.get("publisher")
                        or s.get("source_metadata", {}).get("publisher", "")
                    ),
                    "source_url": s.get("source_url") or s.get("source_metadata", {}).get("url", ""),
                    "published_at": str(
                        s.get("published_at")
                        or s.get("source_metadata", {}).get("published_at", "")
                    )[:10],
                    "confidence": round(_sort_key(s), 2),
                }
                for s in top_signals
            ],
            ensure_ascii=False,
        )

        try:
            message = self._client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_REPORT_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": _WEEKLY_REPORT_PROMPT.format(
                            total=len(signals),
                            signals_json=signals_summary,
                        ),
                    }
                ],
            )
            html = message.content[0].text.strip()
            if html.startswith("```"):
                html = html.split("```")[1]
                if html.startswith("html"):
                    html = html[4:]
            return html

        except Exception as e:
            log.error(f"주간 리포트 생성 오류: {e}")
            return self._fallback_weekly_report(signals)

    # ── Fallbacks ──────────────────────────────────────────────────────────

    def _fallback_analysis(self, signal: dict) -> dict:
        """Claude API 미사용 시 기본 메타데이터 채움."""
        title = signal.get("title", "")
        publisher = signal.get("source_metadata", {}).get("publisher", "")
        signal.setdefault("summary", f"{title} — {publisher}에서 수집된 Physical AI 관련 신호.")
        signal.setdefault("strategic_implication", "LGU+ 전략팀 분석 필요.")
        signal.setdefault("key_insights", [])
        signal.setdefault("analyzed_by", "fallback")
        return signal

    def _fallback_weekly_report(self, signals: list[dict]) -> str:
        """Claude API 미설정 시 기본 주간 리포트 HTML."""
        from collections import Counter
        scope_counts = Counter(s.get("scope", "Unknown") for s in signals)
        items = "".join(
            f"<li><strong>[{s.get('scope')}]</strong> {s.get('title', '')}</li>"
            for s in signals[:20]
        )
        return f"""
<div class="weekly-report-fallback">
  <h2>PASIS 주간 Physical AI 인텔리전스 브리핑</h2>
  <p>생성일: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}</p>
  <h3>이번 주 수집 현황</h3>
  <ul>
    {''.join(f'<li>{scope}: {cnt}건</li>' for scope, cnt in scope_counts.items())}
  </ul>
  <p>총 {len(signals)}건의 신호 수집.</p>
  <p><em>상세 전략 분석은 ANTHROPIC_API_KEY 설정 후 자동 생성됩니다.</em></p>
  <h3>수집 신호 목록</h3>
  <ul>{items}</ul>
</div>"""

    def _save_processed(self, records: list[dict]) -> None:
        """분석 완료 데이터를 data/processed/에 저장."""
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_analyzed.json"
        filepath = PROCESSED_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"분석 데이터 저장: {filepath}")
