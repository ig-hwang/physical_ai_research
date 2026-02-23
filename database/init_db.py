"""
Database initialization and connection management
"""
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_URL
from database.models import Base, MarketSignal

log = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        log.error(f"DB session error: {e}")
        raise
    finally:
        session.close()


def init_db(seed_demo_data: bool = True) -> None:
    """Create all tables and optionally seed demo data."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    log.info("Database tables created.")

    if seed_demo_data:
        _seed_demo_data()


def _fix_demo_urls() -> None:
    """기존 데모 데이터의 잘못된 URL을 올바른 URL로 패치."""
    broken_to_fixed = {
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=figure+ai":
            "https://techcrunch.com/2024/02/29/figure-ai-raises-675m-from-microsoft-openai-nvidia-and-others/",
        "https://www.sec.gov/Archives/edgar/data/1045810/000104581024000005/":
            "https://nvidianews.nvidia.com/news/nvidia-to-acquire-runai",
        "https://techcrunch.com/2024/01/18/figure-bmw-partnership/":
            "https://techcrunch.com/2024/01/18/figure-lands-a-commercial-deal-with-bmw-manufacturing/",
        "https://www.reuters.com/technology/amazon-robots-fulfillment/":
            "https://www.aboutamazon.com/news/transportation/amazon-proteus-robot",
    }
    try:
        with get_session() as session:
            updated = 0
            for old_url, new_url in broken_to_fixed.items():
                rows = session.query(MarketSignal).filter_by(source_url=old_url).all()
                for row in rows:
                    row.source_url = new_url
                    updated += 1
            if updated:
                log.info(f"데모 URL 패치 완료: {updated}건 수정")
    except Exception as e:
        log.warning(f"데모 URL 패치 실패 (무시): {e}")


def _seed_demo_data() -> None:
    """Seed realistic Physical AI demo signals so the dashboard is immediately usable."""
    # ── URL 수정 마이그레이션: 기존 데모 데이터의 broken URL 교체 ──────────────
    _fix_demo_urls()

    with get_session() as session:
        existing = session.query(MarketSignal).count()
        if existing > 0:
            log.info(f"Demo data already present ({existing} records). Skipping seed.")
            return

    demo_signals: list[dict] = [
        # ── Market Signals ────────────────────────────────────────────────────
        {
            "scope": "Market", "category": "Investment",
            "title": "Figure AI Raises $675M Series B at $2.6B Valuation",
            "summary": "Figure AI가 675M 달러 규모 Series B 투자를 유치하며 기업가치 26억 달러를 확정. "
                       "BMW, Microsoft, NVIDIA, OpenAI 등이 공동 참여. 2025년 상업 배포 가속화 목적.",
            "strategic_implication": "LGU+ 관점: Humanoid Robotics-as-a-Service 시장 진입 검토 시급. "
                                     "5G 기반 로봇 플릿 관제 서비스 개발 기회. Figure AI Korea 파트너십 타진 권고.",
            "key_insights": [
                "투자 규모 기준 Humanoid 로보틱스 역대 최대 Series B",
                "BMW 공장 내 Figure 01 실제 배포로 상업 검증 완료",
                "5G 연결 기반 실시간 로봇 제어 수요 확인"
            ],
            "source_url": "https://techcrunch.com/2024/02/29/figure-ai-raises-675m-from-microsoft-openai-nvidia-and-others/",
            "publisher": "TechCrunch",
            "confidence_score": 0.92,
            "published_at": datetime.utcnow() - timedelta(days=7),
        },
        {
            "scope": "Market", "category": "M&A",
            "title": "NVIDIA acquires Run:ai for $700M to dominate AI infrastructure",
            "summary": "NVIDIA가 AI 워크로드 오케스트레이션 플랫폼 Run:ai를 7억 달러에 인수. "
                       "데이터센터 GPU 활용 효율화 및 Physical AI 훈련 인프라 강화 목적.",
            "strategic_implication": "LGU+ 관점: AI 인프라 파트너십 전략 재검토 필요. "
                                     "NVIDIA 중심의 수직 통합 가속화로 Edge AI Hardware 공급망 영향 모니터링.",
            "key_insights": [
                "NVIDIA의 소프트웨어 레이어 확장 전략 명확화",
                "AI 훈련 비용 절감이 Physical AI 상용화 임계점 낮춤",
                "국내 AI 인프라 업체 경쟁력 점검 필요"
            ],
            "source_url": "https://nvidianews.nvidia.com/news/nvidia-to-acquire-runai",
            "publisher": "NVIDIA Newsroom",
            "confidence_score": 0.95,
            "published_at": datetime.utcnow() - timedelta(days=14),
        },
        {
            "scope": "Market", "category": "PoC Deployment",
            "title": "Tesla Optimus Gen 2 begins limited factory deployment at Fremont",
            "summary": "Tesla Optimus Gen 2 휴머노이드 로봇이 Fremont 공장 내 배터리 셀 분류 작업에 투입. "
                       "일 500개 부품 처리 속도 달성. Elon Musk, 2025년 1,000대 규모 확장 언급.",
            "strategic_implication": "LGU+ 관점: Tesla B2B 로봇 리스 모델이 국내 제조업 도입 선례 창출. "
                                     "5G 제어망 + AI 로봇 통합 솔루션 개발 로드맵 수립 권고.",
            "key_insights": [
                "End-to-End 신경망 기반 제어로 프로그래밍 없는 Task 학습 검증",
                "공장 내 5G 연결 필수 인프라로 부상",
                "국내 스마트팩토리 업체 대상 로봇 연동 솔루션 기회"
            ],
            "source_url": "https://ir.tesla.com/sec-filings/annual-reports",
            "publisher": "Tesla IR (10-K 2024)",
            "confidence_score": 0.90,
            "published_at": datetime.utcnow() - timedelta(days=3),
        },
        # ── Tech Frontier ─────────────────────────────────────────────────────
        {
            "scope": "Tech", "category": "VLA Models",
            "title": "π0: A Vision-Language-Action Flow Model for General Robot Control",
            "summary": "Physical Intelligence(π)가 발표한 π0 모델은 다양한 로봇 형태(embodiment)에 "
                       "범용 적용 가능한 VLA Flow 모델. 7개 로봇, 68개 태스크에서 SOTA 달성.",
            "strategic_implication": "LGU+ 관점: Foundation Model for Robotics의 상용화 임박 신호. "
                                     "엣지 AI 하드웨어 수요 급증 예상. 국내 엣지 AI 솔루션 파트너십 기회.",
            "key_insights": [
                "단일 모델로 다양한 로봇 플랫폼 제어 가능성 실증",
                "Sim-to-Real 갭 20% 이하로 감소 (ICRA 2024 기준)",
                "VLA 모델이 Embodied AI 표준 아키텍처로 수렴 중"
            ],
            "source_url": "https://arxiv.org/abs/2410.24164",
            "publisher": "arXiv (cs.RO)",
            "confidence_score": 0.93,
            "published_at": datetime.utcnow() - timedelta(days=5),
        },
        {
            "scope": "Tech", "category": "World Models",
            "title": "UniSim: A Neural Closed-Loop Sensor Simulator for Autonomous Driving and Robotics",
            "summary": "NVIDIA UniSim은 실제 센서 데이터를 기반으로 폐루프 시뮬레이션 환경을 생성하는 "
                       "World Model. 자율주행 및 로보틱스 데이터 증강에 활용, Sim-to-Real 갭 35% 축소.",
            "strategic_implication": "LGU+ 관점: Digital Twin + 5G 네트워크 슬라이싱 결합 서비스 개발 가능. "
                                     "스마트시티/물류센터 대상 로봇 시뮬레이션 서비스 BM 검토.",
            "key_insights": [
                "World Model 기반 데이터 증강이 Physical AI 훈련 비용 50% 절감 가능",
                "Digital Twin 시장과 World Model 기술의 융합 가속",
                "통신사 5G 인프라가 실시간 시뮬레이션 동기화 핵심 역할"
            ],
            "source_url": "https://arxiv.org/abs/2308.01661",
            "publisher": "arXiv (cs.CV)",
            "confidence_score": 0.91,
            "published_at": datetime.utcnow() - timedelta(days=10),
        },
        {
            "scope": "Tech", "category": "Humanoid Locomotion",
            "title": "Agility Robotics Digit achieves 4.5km/h stable bipedal locomotion on unstructured terrain",
            "summary": "Agility Robotics의 Digit V3가 비정형 지형에서 시속 4.5km 안정적 이족 보행 달성. "
                       "강화학습 기반 locomotion policy가 실내외 환경 전환 없이 적응.",
            "strategic_implication": "LGU+ 관점: 물류 라스트마일 로봇 서비스 수요 증가 대응. "
                                     "Amazon-Agility 파트너십 모델 분석 후 국내 물류 업체 연계 검토.",
            "key_insights": [
                "이족 보행 로봇의 실외 환경 적응성 상업 수준 도달",
                "Amazon Fulfillment Center 내 실증으로 물류 자동화 검증",
                "통신 기반 로봇 모니터링 수요 창출"
            ],
            "source_url": "https://arxiv.org/abs/2304.09266",
            "publisher": "arXiv (cs.RO)",
            "confidence_score": 0.88,
            "published_at": datetime.utcnow() - timedelta(days=18),
        },
        # ── Real-world Cases ──────────────────────────────────────────────────
        {
            "scope": "Case", "category": "Manufacturing",
            "title": "BMW x Figure AI: Humanoid robots handle automotive sub-assembly at Spartanburg",
            "summary": "Figure 01 로봇이 BMW Spartanburg 공장에서 자동차 서브어셈블리 작업 수행. "
                       "일 200회 이상 반복 조립 작업에서 95% 이상 성공률 달성. RaaS 계약 구조.",
            "strategic_implication": "LGU+ 관점: RaaS(Robotics-as-a-Service) 모델이 국내 제조업 진출 교두보. "
                                     "5G 네트워크 SLA 보장 기반 로봇 제어 서비스 패키지화 기회.",
            "key_insights": [
                "RaaS 모델 상업 검증 완료 - 국내 제조업 적용 선례",
                "초저지연 5G 필수 인프라로 통신사 협력 니즈 확인",
                "국내 현대차/기아 대상 유사 모델 적용 타당성 검토 권고"
            ],
            "source_url": "https://techcrunch.com/2024/01/18/figure-lands-a-commercial-deal-with-bmw-manufacturing/",
            "publisher": "TechCrunch",
            "confidence_score": 0.78,
            "published_at": datetime.utcnow() - timedelta(days=21),
        },
        {
            "scope": "Case", "category": "Logistics",
            "title": "Amazon deploys 1,000+ Proteus AMRs across 6 fulfillment centers",
            "summary": "Amazon이 Proteus 자율이동로봇(AMR) 1,000대 이상을 6개 물류센터에 배포. "
                       "작업자 이동 거리 25% 감소, 처리량 30% 향상. 2025년 확장 계획 발표.",
            "strategic_implication": "LGU+ 관점: 물류센터 자동화 솔루션 + 5G 사설망 패키지 수주 기회. "
                                     "국내 쿠팡/CJ대한통운 대상 레퍼런스 케이스 활용 가능.",
            "key_insights": [
                "AMR 시장 국내 진입 타이밍: 2025-2026년이 최적 진입점",
                "5G 사설망 기반 AMR 제어가 핵심 솔루션 요소",
                "안전/보안 규제 대응 컨설팅 니즈 동반 성장"
            ],
            "source_url": "https://www.aboutamazon.com/news/transportation/amazon-proteus-robot",
            "publisher": "About Amazon",
            "confidence_score": 0.82,
            "published_at": datetime.utcnow() - timedelta(days=30),
        },
        # ── Policy/Standard ───────────────────────────────────────────────────
        {
            "scope": "Policy", "category": "Regulation",
            "title": "EU AI Act final text: Physical AI classified as High-Risk (Annex III)",
            "summary": "EU AI Act 최종안에서 제조/물류/의료 환경 내 Physical AI가 고위험 AI로 분류. "
                       "2025년 8월부터 적합성 평가 의무화. CE 마킹 및 기술 문서화 요구.",
            "strategic_implication": "LGU+ 관점: 국내 Physical AI 서비스 수출 시 EU 규제 대응 비용 내재화 필요. "
                                     "규제 컴플라이언스 컨설팅 서비스 BM 개발 검토.",
            "key_insights": [
                "EU 시장 진출 기업 대상 규제 준수 비용 20-30% 증가 예상",
                "국내 규제 선제 대응으로 글로벌 경쟁 우위 확보 가능",
                "ISO/IEC 42001 AI 경영시스템 인증 수요 증가"
            ],
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
            "publisher": "EU Official Journal",
            "confidence_score": 0.97,
            "published_at": datetime.utcnow() - timedelta(days=45),
        },
        {
            "scope": "Policy", "category": "Standard",
            "title": "NIST AI RMF 1.0: Robotics Addendum publishes voluntary framework",
            "summary": "NIST AI Risk Management Framework 1.0 Robotics Addendum 발표. "
                       "Physical AI 안전성, 신뢰성, 설명가능성 평가 기준 제시. 자발적 채택 권고.",
            "strategic_implication": "LGU+ 관점: NIST 프레임워크 조기 채택으로 B2G(정부) 시장 진출 우위 확보. "
                                     "국내 로봇 안전 인증 체계 수립에 기여하는 포지셔닝 가능.",
            "key_insights": [
                "자발적 프레임워크지만 정부 조달 요건으로 사실상 의무화 전망",
                "국내 과기부 AI 안전 가이드라인과 NIST 프레임워크 정합성 확인 필요",
                "LGU+ AI 서비스 전반 NIST 프레임워크 적용 검토"
            ],
            "source_url": "https://airc.nist.gov/RMF",
            "publisher": "NIST",
            "confidence_score": 0.94,
            "published_at": datetime.utcnow() - timedelta(days=60),
        },
    ]

    with get_session() as session:
        for idx, data in enumerate(demo_signals):
            signal = MarketSignal(
                event_id=str(uuid.uuid4()),
                scope=data["scope"],
                category=data["category"],
                title=data["title"],
                summary=data["summary"],
                strategic_implication=data["strategic_implication"],
                key_insights=data["key_insights"],
                source_url=data["source_url"],
                publisher=data["publisher"],
                confidence_score=data["confidence_score"],
                data_quality_score=round(data["confidence_score"] * 0.95, 2),
                published_at=data["published_at"],
                scraped_at=datetime.utcnow(),
                processing_pipeline="demo_seed",
                schema_version="v1.0",
            )
            session.add(signal)

        log.info(f"Seeded {len(demo_signals)} demo signals.")