"""
Physical AI Scout - Data Collection Module
physical-ai-scout SKILL.md 구현체

Sources:
  - arXiv API (cs.RO, cs.AI, cs.CV, cs.LG)
  - SEC EDGAR Full-Text Search API (10-K, 8-K)
  - RSS Feeds (TechCrunch, VentureBeat, IEEE Spectrum 등)
"""
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import arxiv
import feedparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import (
    ARXIV_CATEGORIES,
    ARXIV_MAX_RESULTS,
    ARXIV_RATE_LIMIT_SEC,
    SEC_FORM_TYPES,
    SEC_RATE_LIMIT_SEC,
    NEWS_RSS_FEEDS,
    STRATEGIC_KEYWORDS,
    TARGET_COMPANIES,
    CONFIDENCE_WEIGHTS,
    RAW_DIR,
)

log = logging.getLogger(__name__)

# EDGAR Full-Text Search API (무료, 인증 불필요)
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_HEADERS = {"User-Agent": "PASIS-Research research@lguplus.com"}


def _build_pasis_record(
    scope: str,
    category: str,
    title: str,
    raw_content: str,
    source_url: str,
    publisher: str,
    published_at: datetime,
    confidence_score: float,
    extra_meta: Optional[dict] = None,
) -> dict:
    """PASIS 표준 레코드 생성 (physical-ai-scout SKILL.md Output Schema 준수)."""
    return {
        "event_id": str(uuid.uuid4()),
        "scope": scope,
        "category": category,
        "title": title[:500],  # DB 길이 제한
        "raw_content": raw_content[:5000],
        "source_metadata": {
            "url": source_url,
            "publisher": publisher,
            "published_at": published_at.isoformat(),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "confidence_score": confidence_score,
        },
        **(extra_meta or {}),
    }


def _is_relevant(text: str, keywords: list[str] = STRATEGIC_KEYWORDS) -> bool:
    """텍스트가 전략 키워드를 하나 이상 포함하는지 검증."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


class PhysicalAIScout:
    """
    PASIS 데이터 수집 에이전트.
    Rate limiting, retry, 메타데이터 표준을 자동 적용.
    """

    def __init__(self) -> None:
        self._arxiv_client = arxiv.Client()

    # ── 1. arXiv Paper Tracker ─────────────────────────────────────────────

    def fetch_arxiv_papers(
        self,
        keywords: list[str] = STRATEGIC_KEYWORDS,
        categories: list[str] = ARXIV_CATEGORIES,
        max_results: int = ARXIV_MAX_RESULTS,
        days_back: int = 14,
    ) -> list[dict]:
        """
        arXiv에서 Physical AI 관련 논문 수집.
        Rate limit: 1 req / 3sec (arXiv 정책 준수)
        """
        records: list[dict] = []
        cat_filter = " OR ".join(f"cat:{c}" for c in categories)
        kw_sample = keywords[:6]  # 쿼리 길이 제한
        kw_query = " OR ".join(f'"{kw}"' for kw in kw_sample)
        query = f"({cat_filter}) AND ({kw_query})"

        log.info(f"arXiv 검색 쿼리: {query}")

        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

            for result in self._arxiv_client.results(search):
                if result.published < cutoff:
                    continue

                primary_cat = result.primary_category
                scope = "Tech"
                category = self._classify_arxiv_category(primary_cat)

                record = _build_pasis_record(
                    scope=scope,
                    category=category,
                    title=result.title,
                    raw_content=result.summary,
                    source_url=result.entry_id,
                    publisher=f"arXiv ({primary_cat})",
                    published_at=result.published.replace(tzinfo=timezone.utc)
                    if result.published.tzinfo is None
                    else result.published,
                    confidence_score=CONFIDENCE_WEIGHTS.get("arXiv", 0.90),
                    extra_meta={
                        "authors": [a.name for a in result.authors[:5]],
                        "arxiv_id": result.get_short_id(),
                    },
                )
                records.append(record)
                time.sleep(ARXIV_RATE_LIMIT_SEC)

        except arxiv.HTTPError as e:
            log.error(f"arXiv HTTP 오류: {e}")
        except Exception as e:
            log.error(f"arXiv 수집 오류: {e}", exc_info=True)

        log.info(f"arXiv 수집 완료: {len(records)}건")
        return records

    def _classify_arxiv_category(self, cat: str) -> str:
        mapping = {
            "cs.RO": "Robotics",
            "cs.AI": "AI Research",
            "cs.CV": "Computer Vision",
            "cs.LG": "Machine Learning",
        }
        return mapping.get(cat, "Research Paper")

    # ── 2. SEC EDGAR Filing Monitor ────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def fetch_sec_filings(
        self,
        keywords: list[str] = None,
        companies: list[str] = TARGET_COMPANIES,
        form_types: list[str] = SEC_FORM_TYPES,
        days_back: int = 30,
    ) -> list[dict]:
        """
        SEC EDGAR Full-Text Search API로 공시 수집.
        인증 불필요 (EDGAR 공개 API).
        """
        if keywords is None:
            keywords = ["humanoid robot", "embodied AI", "autonomous robot", "physical AI"]

        records: list[dict] = []
        start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        forms_param = ",".join(form_types)

        for keyword in keywords[:4]:  # API 부하 제한
            params = {
                "q": f'"{keyword}"',
                "forms": forms_param,
                "dateRange": "custom",
                "startdt": start_date,
                "enddt": end_date,
            }
            try:
                resp = requests.get(
                    EDGAR_SEARCH_URL,
                    params=params,
                    headers=EDGAR_HEADERS,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])

                for hit in hits[:5]:  # 키워드당 최대 5건
                    src = hit.get("_source", {})
                    form_type = src.get("form_type", "SEC")
                    entity_name = src.get("entity_name", "Unknown")
                    filing_date = src.get("file_date", datetime.utcnow().strftime("%Y-%m-%d"))
                    filing_url = src.get("file_url", "")
                    if not filing_url:
                        filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={entity_name}"

                    # published_at 파싱
                    try:
                        pub_dt = datetime.strptime(filing_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except ValueError:
                        pub_dt = datetime.now(timezone.utc)

                    record = _build_pasis_record(
                        scope="Market",
                        category=self._classify_sec_form(form_type),
                        title=f"[{form_type}] {entity_name}: {src.get('period_of_report', filing_date)}",
                        raw_content=src.get("file_description", f"{form_type} filing by {entity_name}"),
                        source_url=f"https://www.sec.gov{filing_url}" if filing_url.startswith("/") else filing_url,
                        publisher=f"SEC EDGAR ({form_type})",
                        published_at=pub_dt,
                        confidence_score=CONFIDENCE_WEIGHTS.get("SEC", 0.95),
                    )
                    records.append(record)

                time.sleep(SEC_RATE_LIMIT_SEC)

            except requests.exceptions.RequestException as e:
                log.warning(f"SEC EDGAR API 오류 (keyword={keyword}): {e}")
            except (KeyError, ValueError) as e:
                log.warning(f"SEC 응답 파싱 오류: {e}")

        log.info(f"SEC EDGAR 수집 완료: {len(records)}건")
        return records

    def _classify_sec_form(self, form_type: str) -> str:
        mapping = {
            "10-K": "Annual Report",
            "8-K": "Material Event",
            "S-1": "IPO Filing",
            "10-Q": "Quarterly Report",
        }
        return mapping.get(form_type, "SEC Filing")

    # ── 3. RSS News Aggregator ─────────────────────────────────────────────

    def fetch_rss_news(
        self,
        feeds: list[dict] = None,
        keywords: list[str] = STRATEGIC_KEYWORDS,
        days_back: int = 7,
    ) -> list[dict]:
        """
        RSS 피드에서 Physical AI 관련 뉴스 수집.
        feedparser 기반, API 키 불필요.
        """
        if feeds is None:
            feeds = NEWS_RSS_FEEDS

        records: list[dict] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

        for feed_config in feeds:
            feed_name = feed_config["name"]
            feed_url = feed_config["url"]
            feed_scope = feed_config.get("scope", "Case")

            try:
                parsed = feedparser.parse(feed_url)
                if parsed.bozo and parsed.bozo_exception:
                    log.warning(f"RSS 파싱 경고 ({feed_name}): {parsed.bozo_exception}")

                for entry in parsed.entries:
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                    link = getattr(entry, "link", "")
                    published_parsed = getattr(entry, "published_parsed", None)

                    if not title or not link:
                        continue

                    # 관련성 검증 (키워드 필터)
                    combined_text = f"{title} {summary}"
                    if not _is_relevant(combined_text, keywords):
                        continue

                    # 발행일 파싱
                    if published_parsed:
                        pub_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                    else:
                        pub_dt = datetime.now(timezone.utc)

                    if pub_dt < cutoff:
                        continue

                    confidence = CONFIDENCE_WEIGHTS.get(feed_name, CONFIDENCE_WEIGHTS["RSS"])
                    record = _build_pasis_record(
                        scope=feed_scope,
                        category=self._classify_news_category(combined_text),
                        title=title,
                        raw_content=summary[:2000],
                        source_url=link,
                        publisher=feed_name,
                        published_at=pub_dt,
                        confidence_score=confidence,
                    )
                    records.append(record)

            except Exception as e:
                log.error(f"RSS 수집 오류 ({feed_name}): {e}", exc_info=True)

        log.info(f"RSS 뉴스 수집 완료: {len(records)}건")
        return records

    def _classify_news_category(self, text: str) -> str:
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["investment", "funding", "raise", "series", "m&a", "acqui"]):
            return "Investment"
        if any(kw in text_lower for kw in ["deploy", "factory", "warehouse", "logistics", "poc"]):
            return "PoC Deployment"
        if any(kw in text_lower for kw in ["partner", "collaboration", "joint", "deal"]):
            return "Partnership"
        if any(kw in text_lower for kw in ["regulation", "policy", "standard", "act", "law"]):
            return "Regulation"
        return "Industry News"

    # ── 4. Full Run ────────────────────────────────────────────────────────

    def run_all(
        self,
        days_back: int = 14,
        save_raw: bool = True,
    ) -> list[dict]:
        """
        전체 소스 수집 실행 후 raw 데이터 저장.
        Returns: 통합 레코드 리스트
        """
        log.info("=== PhysicalAIScout 전체 수집 시작 ===")
        all_records: list[dict] = []

        # arXiv
        try:
            arxiv_records = self.fetch_arxiv_papers(days_back=days_back)
            all_records.extend(arxiv_records)
        except Exception as e:
            log.error(f"arXiv 수집 실패: {e}")

        # SEC EDGAR
        try:
            sec_records = self.fetch_sec_filings(days_back=days_back)
            all_records.extend(sec_records)
        except Exception as e:
            log.error(f"SEC EDGAR 수집 실패: {e}")

        # RSS News
        try:
            rss_records = self.fetch_rss_news(days_back=days_back)
            all_records.extend(rss_records)
        except Exception as e:
            log.error(f"RSS 수집 실패: {e}")

        log.info(f"=== 전체 수집 완료: {len(all_records)}건 ===")

        if save_raw and all_records:
            self._save_raw(all_records)

        return all_records

    def _save_raw(self, records: list[dict]) -> None:
        """raw 데이터를 data/raw/{YYYYMMDD}_scout.json 형식으로 저장."""
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_scout.json"
        filepath = RAW_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2, default=str)
        log.info(f"Raw 데이터 저장: {filepath}")