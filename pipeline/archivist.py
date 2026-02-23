"""
Data Archivist - 스키마 검증, 중복 제거, DB 저장
data-archivist SKILL.md 구현체

품질 평가 기준:
  - Metadata completeness: 40%
  - Source authority: 30%
  - Content richness: 20%
  - Timeliness: 10%
"""
import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CONFIDENCE_WEIGHTS, MIN_QUALITY_SCORE
from database.init_db import get_session
from database.queries import upsert_signal

log = logging.getLogger(__name__)

REQUIRED_FIELDS = ["title", "scope", "source_metadata"]
VALID_SCOPES = {"Market", "Tech", "Case", "Policy"}


def _is_valid_url(url: str) -> bool:
    """URL이 유효한 http/https 형식인지 검증."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


class DataArchivist:
    """
    PASIS 데이터 영속성 에이전트.
    검증 → 중복제거 → 품질 점수 → DB UPSERT 파이프라인.
    """

    def __init__(self) -> None:
        self._seen_hashes: set[str] = set()

    # ── 1. Schema Validation ───────────────────────────────────────────────

    def validate_schema(self, record: dict) -> tuple[bool, list[str]]:
        """
        PASIS 스키마 검증.
        Returns: (is_valid, error_messages)
        """
        errors: list[str] = []

        # 필수 필드 존재 검증
        for field in REQUIRED_FIELDS:
            if not record.get(field):
                errors.append(f"필수 필드 누락: {field}")

        # scope 값 검증
        scope = record.get("scope", "")
        if scope not in VALID_SCOPES:
            errors.append(f"유효하지 않은 scope: '{scope}'. 허용값: {VALID_SCOPES}")

        # source_metadata 검증
        meta = record.get("source_metadata", {})
        if not isinstance(meta, dict):
            errors.append("source_metadata는 dict 타입이어야 합니다.")
        else:
            if not meta.get("url"):
                errors.append("source_metadata.url 누락")
            if not meta.get("published_at"):
                errors.append("source_metadata.published_at 누락")

            # URL 형식 검증
            url = meta.get("url", "")
            if url and not _is_valid_url(url):
                errors.append(f"유효하지 않은 URL 형식: '{url[:80]}'")

            # confidence_score 범위 검증
            score = meta.get("confidence_score")
            if score is not None and not (0.0 <= float(score) <= 1.0):
                errors.append(f"confidence_score 범위 초과: {score}")

        is_valid = len(errors) == 0
        return is_valid, errors

    # ── 2. Deduplication ───────────────────────────────────────────────────

    def deduplicate_records(self, records: list[dict]) -> list[dict]:
        """
        SHA-256 기반 중복 제거.
        전략: title + source_url 해시 매칭.
        """
        unique: list[dict] = []
        for record in records:
            content_hash = self._compute_hash(record)
            if content_hash in self._seen_hashes:
                log.debug(f"중복 제거: {record.get('title', '')[:50]}")
                continue
            self._seen_hashes.add(content_hash)
            record["content_hash"] = content_hash
            unique.append(record)

        removed = len(records) - len(unique)
        if removed > 0:
            log.info(f"중복 제거: {removed}건 제거, {len(unique)}건 유지")
        return unique

    def _compute_hash(self, record: dict) -> str:
        title = record.get("title", "")
        url = record.get("source_metadata", {}).get("url", "")
        raw = f"{title}|{url}".lower().strip()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ── 3. Quality Scoring ─────────────────────────────────────────────────

    def calculate_quality_score(self, record: dict) -> float:
        """
        데이터 품질 점수 산정 (0.0-1.0).
        Metadata(40%) + Authority(30%) + Content(20%) + Timeliness(10%)
        """
        score = 0.0
        meta = record.get("source_metadata", {})

        # 1. Metadata completeness (40%)
        meta_fields = ["url", "publisher", "published_at", "scraped_at", "confidence_score"]
        completeness = sum(1 for f in meta_fields if meta.get(f)) / len(meta_fields)
        score += completeness * 0.40

        # 2. Source authority (30%)
        publisher = meta.get("publisher", "")
        authority = CONFIDENCE_WEIGHTS.get("RSS", 0.60)
        for source_key, weight in CONFIDENCE_WEIGHTS.items():
            if source_key.lower() in publisher.lower():
                authority = weight
                break
        score += authority * 0.30

        # 3. Content richness (20%)
        title_len = len(record.get("title", ""))
        content_len = len(record.get("raw_content", "") or record.get("summary", ""))
        richness = min((title_len / 50) * 0.3 + (content_len / 500) * 0.7, 1.0)
        score += richness * 0.20

        # 4. Timeliness (10%)
        try:
            pub_str = meta.get("published_at", "")
            if isinstance(pub_str, str):
                pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            else:
                pub_dt = pub_str
            days_old = (datetime.now(timezone.utc) - pub_dt.replace(tzinfo=timezone.utc)
                        if pub_dt.tzinfo is None else
                        datetime.now(timezone.utc) - pub_dt).days
            timeliness = max(0.0, 1.0 - days_old / 60)  # 60일 기준 선형 감쇠
        except (ValueError, TypeError, AttributeError):
            timeliness = 0.5
        score += timeliness * 0.10

        return round(min(score, 1.0), 3)

    # ── 4. DB Ingestion ────────────────────────────────────────────────────

    def ingest_batch(self, records: list[dict]) -> dict:
        """
        배치 UPSERT to DB.
        Returns: {"rows_inserted": int, "rows_updated": int, "errors": list}
        """
        inserted = 0
        updated = 0
        errors: list[str] = []

        # 전처리
        validated = []
        for record in records:
            is_valid, errs = self.validate_schema(record)
            if not is_valid:
                log.warning(f"스키마 검증 실패 (title={record.get('title','')[:40]}): {errs}")
                errors.append(f"{record.get('title','')[:40]}: {errs}")
                continue
            validated.append(record)

        deduplicated = self.deduplicate_records(validated)

        # DB 저장
        try:
            with get_session() as session:
                for record in deduplicated:
                    meta = record.get("source_metadata", {})
                    quality_score = self.calculate_quality_score(record)

                    if quality_score < MIN_QUALITY_SCORE:
                        log.debug(f"품질 점수 미달 (score={quality_score}): {record.get('title','')[:40]}")
                        continue

                    # published_at 파싱
                    pub_str = meta.get("published_at", "")
                    try:
                        if isinstance(pub_str, str):
                            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                            if pub_dt.tzinfo is not None:
                                pub_dt = pub_dt.replace(tzinfo=None)
                        else:
                            pub_dt = pub_str
                    except (ValueError, TypeError):
                        pub_dt = datetime.utcnow()

                    scraped_str = meta.get("scraped_at", "")
                    try:
                        if isinstance(scraped_str, str) and scraped_str:
                            scraped_dt = datetime.fromisoformat(scraped_str.replace("Z", "+00:00"))
                            if scraped_dt.tzinfo is not None:
                                scraped_dt = scraped_dt.replace(tzinfo=None)
                        else:
                            scraped_dt = datetime.utcnow()
                    except (ValueError, TypeError):
                        scraped_dt = datetime.utcnow()

                    signal_data = {
                        "event_id": record.get("event_id", str(uuid.uuid4())),
                        "scope": record.get("scope"),
                        "category": record.get("category"),
                        "title": record.get("title"),
                        "summary": record.get("summary"),
                        "strategic_implication": record.get("strategic_implication"),
                        "key_insights": record.get("key_insights", []),
                        "source_url": meta.get("url", ""),
                        "publisher": meta.get("publisher"),
                        "published_at": pub_dt,
                        "scraped_at": scraped_dt,
                        "confidence_score": meta.get("confidence_score"),
                        "data_quality_score": quality_score,
                        "processing_pipeline": "scout->analysis->archivist",
                        "schema_version": "v1.0",
                    }

                    was_inserted, event_id = upsert_signal(session, signal_data)
                    if was_inserted:
                        inserted += 1
                    else:
                        updated += 1

        except Exception as e:
            log.error(f"DB 저장 오류: {e}", exc_info=True)
            errors.append(str(e))

        result = {"rows_inserted": inserted, "rows_updated": updated, "errors": errors}
        log.info(f"DB 저장 결과: 신규={inserted}, 갱신={updated}, 오류={len(errors)}")
        return result

    def run_pipeline(self, raw_records: list[dict]) -> dict:
        """
        검증 → 중복제거 → 품질점수 → DB 저장 전체 파이프라인 실행.
        """
        log.info(f"=== DataArchivist 파이프라인 시작: {len(raw_records)}건 ===")
        result = self.ingest_batch(raw_records)
        log.info(f"=== DataArchivist 파이프라인 완료 ===")
        return result