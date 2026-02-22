# PASIS 시스템 아키텍처

**Physical AI Strategic Intelligence System**
LG Uplus 포트폴리오 전략팀 · Physical AI 리서치 자동화 플랫폼

---

## 1. 시스템 개요

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           PASIS v1.0                                     │
│                    Physical AI Intelligence Platform                     │
├────────────────────────┬─────────────────────────┬───────────────────────┤
│   데이터 수집 레이어    │     분석 레이어          │    서비스 레이어       │
│   (PhysicalAIScout)    │  (StrategicAnalyzer)    │   (Streamlit Web)     │
│                        │                         │                       │
│  arXiv API ──────────► │  Claude claude-sonnet-4-6 ──► │  Main Dashboard  │
│  SEC EDGAR ──────────► │  - 피라미드 요약          │  Market Signals      │
│  RSS Feeds ──────────► │  - LGU+ 전략 시사점      │  Tech Frontier       │
│                        │  - 키 인사이트 추출      │  Real-world Cases    │
│                        │                         │  Policy/Standards    │
│                        │   DataArchivist ──────► │  Weekly Report       │
│                        │  - 스키마 검증           │                       │
│                        │  - 중복 제거             │                       │
│                        │  - 품질 점수 계산        │                       │
│                        │  - DB UPSERT            │                       │
└────────────────────────┴─────────────────────────┴───────────────────────┘
                                      │
                              SQLite (SQLAlchemy)
                              market_signals 테이블
                              weekly_reports 테이블
```

---

## 2. 디렉토리 구조

```
physical_ai_research/
├── CLAUDE.md                    # 프로젝트 가이드라인 (taxonomy, 기술 표준)
├── ARCHITECTURE.md              # 이 파일 - 시스템 설계 문서
├── README.md                    # 사용자 가이드
│
├── config.py                    # 중앙 설정 (API 키, 키워드, 스케줄)
├── requirements.txt             # Python 패키지 의존성
├── .env.example                 # 환경변수 템플릿
├── run_pipeline.py              # 파이프라인 엔트리포인트
├── run.sh                       # 쉘 시작 스크립트
├── pasis.db                     # SQLite DB (자동 생성)
│
├── database/                    # 데이터베이스 레이어
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy ORM (MarketSignal, WeeklyReport)
│   ├── init_db.py               # DB 초기화 + 데모 데이터 시딩
│   └── queries.py               # 분석용 쿼리 헬퍼
│
├── pipeline/                    # 데이터 파이프라인
│   ├── __init__.py
│   ├── scout.py                 # 데이터 수집 (arXiv, SEC EDGAR, RSS)
│   ├── analyzer.py              # Claude API 전략 분석
│   ├── archivist.py             # 검증 + 중복제거 + DB 저장
│   └── scheduler.py             # APScheduler 주간 자동 실행
│
├── web/                         # Streamlit 웹 앱
│   ├── app.py                   # 메인 대시보드
│   ├── pages/
│   │   ├── 1_Market_Signals.py  # SEC 공시, M&A, 투자
│   │   ├── 2_Tech_Frontier.py   # arXiv 논문, VLA, World Models
│   │   ├── 3_Real_World_Cases.py# PoC, 파트너십, 배포 사례
│   │   ├── 4_Policy_Standards.py# EU AI Act, NIST, IFR
│   │   └── 5_Weekly_Report.py   # 주간 전략 브리핑 뷰어
│   └── components/
│       ├── __init__.py
│       ├── charts.py            # Plotly 차트 컴포넌트
│       └── cards.py             # KPI 카드, 신호 카드 UI
│
├── data/
│   ├── raw/                     # 수집 원본 ({YYYYMMDD_HHMMSS}_scout.json)
│   ├── processed/               # 분석 완료 ({YYYYMMDD_HHMMSS}_analyzed.json)
│   └── archive/                 # 장기 보관
│
└── .github/
    └── workflows/
        └── weekly_update.yml    # GitHub Actions 주간 자동 파이프라인
```

---

## 3. 핵심 컴포넌트 설명

### 3.1 PhysicalAIScout (`pipeline/scout.py`)
- **목적**: 1차 데이터 소스에서 Physical AI 신호 수집
- **소스**:
  | 소스 | API | 인증 | 주요 데이터 |
  |------|-----|------|------------|
  | arXiv | arXiv API v2 | 불필요 | cs.RO, cs.AI, cs.CV 논문 |
  | SEC EDGAR | EDGAR Full-Text Search | 불필요 | 10-K, 8-K, S-1 공시 |
  | RSS Feeds | feedparser | 불필요 | TechCrunch, VentureBeat, IEEE |
- **출력**: PASIS 표준 레코드 (event_id, scope, source_metadata 포함)
- **Rate Limiting**: arXiv 3초/req, EDGAR 0.1초/req

### 3.2 StrategicAnalyzer (`pipeline/analyzer.py`)
- **목적**: Claude API로 원시 신호를 전략 인사이트로 변환
- **모델**: `claude-sonnet-4-6`
- **분석 프레임워크**:
  - 피라미드 원칙: 결론 → 근거 → 액션
  - LGU+ 관련성: Direct Impact / Future Opportunity / Competitive Threat / Partnership
- **Fallback**: API 키 미설정 시 기본 메타데이터 보존

### 3.3 DataArchivist (`pipeline/archivist.py`)
- **목적**: 스키마 검증 → 중복 제거 → 품질 점수 → DB UPSERT
- **품질 점수 산정**:
  ```
  Quality = Metadata(40%) + Authority(30%) + Content(20%) + Timeliness(10%)
  ```
- **중복 제거**: SHA-256(title + source_url) 해시 기반
- **DB 저장**: event_id 기반 UPSERT (멱등성 보장)

### 3.4 Streamlit 웹 앱 (`web/`)
- **메인 대시보드**: KPI, 스코프 분포, 주간 추이, 최신 신호 피드
- **스코프별 상세 페이지**: 필터링, 시각화, CSV 다운로드
- **주간 리포트**: Claude 생성 HTML 브리핑 뷰어
- **데이터 캐싱**: `@st.cache_data(ttl=300)` — 5분 캐시

---

## 4. 데이터 흐름

```
[arXiv / SEC / RSS]
        │
        ▼ (scout.py)
  raw JSON (data/raw/)
        │
        ▼ (analyzer.py)
  analyzed JSON (data/processed/)
  + Claude summary + strategic_implication
        │
        ▼ (archivist.py)
  [validate] → [deduplicate] → [quality_score] → [DB UPSERT]
        │
        ▼
  SQLite: market_signals 테이블
        │
        ├──► weekly_reports 테이블 (주간 HTML 리포트)
        │
        ▼
  Streamlit 웹 대시보드 (캐시 TTL 5분)
```

---

## 5. 데이터 스키마

### market_signals 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| event_id | VARCHAR(36) | UUID, UNIQUE — 멱등성 키 |
| scope | VARCHAR(20) | Market / Tech / Case / Policy |
| category | VARCHAR(100) | 세부 분류 (Investment, VLA Models 등) |
| title | TEXT | 원문 제목 |
| summary | TEXT | 피라미드 원칙 요약 (Claude 생성) |
| strategic_implication | TEXT | LGU+ 전략 시사점 |
| key_insights | JSON | 핵심 인사이트 리스트 |
| source_url | TEXT | 원문 URL (필수) |
| publisher | VARCHAR(200) | 발행 기관 |
| published_at | DATETIME | 발행일시 (필수) |
| scraped_at | DATETIME | 수집일시 |
| confidence_score | FLOAT | 신뢰도 점수 (0.0-1.0) |
| data_quality_score | FLOAT | 품질 점수 (0.0-1.0) |

### weekly_reports 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| iso_week | VARCHAR(10) | e.g. "2026-W08" — UNIQUE |
| total_signals | INT | 이번 주 수집 건수 |
| full_report_html | TEXT | Claude 생성 HTML 브리핑 |
| generated_at | DATETIME | 리포트 생성일시 |
| model_used | VARCHAR(50) | 사용 Claude 모델 |

---

## 6. 주간 자동 업데이트 메커니즘

### 옵션 A: Python 스케줄러 (로컬/서버)
```bash
python run_pipeline.py --daemon
# 매주 월요일 09:00 KST 자동 실행
```

### 옵션 B: 시스템 Cron
```bash
# crontab -e
0 9 * * 1 cd /path/to/physical_ai_research && python run_pipeline.py --once >> cron.log 2>&1
# 매주 월요일 09:00 실행
```

### 옵션 C: GitHub Actions (클라우드)
```
.github/workflows/weekly_update.yml
매주 월요일 00:00 UTC = 09:00 KST 자동 트리거
```

---

## 7. 빠른 시작 가이드

### 초기 설정
```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env에 ANTHROPIC_API_KEY 입력

# 3. DB 초기화 (데모 데이터 포함)
./run.sh init
```

### 웹 대시보드 실행
```bash
./run.sh web
# → http://localhost:8501
```

### 파이프라인 즉시 실행
```bash
./run.sh pipeline
# arXiv + SEC + RSS 수집 → Claude 분석 → DB 저장 → 주간 리포트
```

### 스케줄러 데몬
```bash
./run.sh daemon
# 매주 월요일 09:00 KST 자동 실행
```

---

## 8. 기술 스택

| 레이어 | 기술 | 버전 |
|--------|------|------|
| 언어 | Python | 3.10+ |
| 웹 프레임워크 | Streamlit | 1.40+ |
| 시각화 | Plotly | 5.24+ |
| DB ORM | SQLAlchemy | 2.0+ |
| DB | SQLite → PostgreSQL | — |
| AI 분석 | Anthropic Claude | claude-sonnet-4-6 |
| 데이터 수집 | arxiv, requests, feedparser | — |
| 스케줄러 | APScheduler | 3.10+ |
| CI/CD | GitHub Actions | — |

---

## 9. 확장 로드맵

- [ ] PostgreSQL 마이그레이션 (대용량 데이터)
- [ ] BigQuery 연동 (CLAUDE.md 계획)
- [ ] Apache Airflow DAG 전환
- [ ] Slack/이메일 주간 리포트 발송
- [ ] 경쟁사 비교 분석 대시보드
- [ ] 한국어 키워드 확장 (국내 Physical AI)
- [ ] 사용자 알림 (키워드 히트 시 즉시 알림)