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

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, PROCESSED_DIR

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

_WEEKLY_REPORT_PROMPT = """당신은 LG유플러스 포트폴리오 전략팀의 Physical AI 시장 수석 분석가입니다.
수집된 Physical AI 신호 {total}건을 종합하여 아래 구조의 전략 브리핑 HTML을 생성하십시오.

[분석 원칙]
- 피라미드 원칙: 핵심 결론 → 근거·데이터 → 액션
- 데이터 기반: 구체적 수치·기업명·날짜 반드시 포함
- Business Korean (기술 용어 영어 유지)
- 각 섹션을 충실하게 작성 (단순 나열 금지, 해석·시사점 필수)

[신호 데이터]
{signals_json}

[필수 HTML 섹션 구조 — 이 순서와 제목 그대로 사용]

1. Executive Summary
   - 이번 주 Physical AI 시장의 핵심 결론 3가지 (불릿)
   - 각 결론은 수치 또는 기업명 포함

2. 이번 주 주요 트렌드
   - 수집 신호에서 도출한 3~5개 거시 트렌드
   - 각 트렌드: 제목 + 2~3문장 해설 + 관련 기업/기술 명시

3. 리서치 내용
   - Market Signals: 주요 투자·M&A·IR 동향 (각 항목: 제목, 핵심 내용, 의미)
   - Tech Frontier: 주목할 arXiv 논문·기술 발전 (각 항목: 제목, 기술 요점, 성숙도 평가)
   - Real-world Cases: PoC·파트너십·상업 배포 사례 (각 항목: 사례, 결과 수치, 확산 가능성)
   - Policy/Standards: 규제·표준 동향 (각 항목: 규정명, 주요 내용, 국내 영향)

4. 전략 참고사항
   - 경쟁 환경 변화: 글로벌 플레이어 포지셔닝 변화 분석
   - 주목 기업/기술: 이번 주 임계점에 도달한 기술·기업
   - 시장 타이밍: 진입·투자·파트너십 최적 시점 평가

5. LGU+ 인사이트 & 권고 액션
   - 즉시 검토 (1개월 이내): 구체적 액션 2~3개
   - 중기 대응 (3~6개월): 준비 과제 2~3개
   - 장기 전략 (1년+): 포지셔닝 방향 1~2개

HTML만 반환하십시오 (마크다운 펜스·주석 없이).
스타일은 인라인 CSS로 깔끔하게 작성하십시오."""


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
                    "raw_content": signal.get("raw_content", "")[:1500],
                    "scope": signal.get("scope", ""),
                    "publisher": signal.get("source_metadata", {}).get("publisher", ""),
                    "published_at": signal.get("source_metadata", {}).get("published_at", ""),
                },
                ensure_ascii=False,
            )

            message = self._client.messages.create(
                model=CLAUDE_MODEL,
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

        # 스코프별 상위 신호 포함 (각 5건씩, 최대 20건)
        top_signals = []
        for scope in ["Market", "Tech", "Case", "Policy"]:
            scope_sigs = [s for s in signals if s.get("scope") == scope]
            top_signals.extend(scope_sigs[:5])

        signals_summary = json.dumps(
            [
                {
                    "scope": s.get("scope"),
                    "category": s.get("category"),
                    "title": s.get("title", ""),
                    "summary": (
                        s.get("summary")
                        or s.get("raw_content", "")
                    )[:400],
                    "strategic_implication": s.get("strategic_implication", ""),
                    "key_insights": s.get("key_insights", []),
                    "publisher": (
                        s.get("publisher")
                        or s.get("source_metadata", {}).get("publisher", "")
                    ),
                    "published_at": str(
                        s.get("published_at")
                        or s.get("source_metadata", {}).get("published_at", "")
                    )[:10],
                }
                for s in top_signals
            ],
            ensure_ascii=False,
        )

        try:
            message = self._client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=8192,
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
