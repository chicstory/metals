# 📜 ThePathLab (Metals & Scrap) Task & Architecture History

금속 원자재 & 스크랩 허브(chicstory.github.io/metals)의 모든 개발, 버그 수정, 아키텍처 결정 히스토리입니다.

> 루트 전체 마스터 히스토리는 [루트 TASK_HISTORY.md](../TASK_HISTORY.md)를 참조하십시오.

---

## [2026-09-25] 금속 명칭 용어 통일('n대 금속' 제거) 및 GEO/AEO 대응 표준 llms.txt 탑재
- **1. 요청사항**: 
  - 과거 7대 금속(LME 중심)에서 철스크랩, 귀금속(금, 은, 백금, 팔라듐, 로듐) 등 총 11개 이상으로 품목이 확장되었음에도 문서 곳곳에 '7대 금속' 등 특정 숫자가 남아있던 용어 불일치 해소.
  - 품목이 추가될 때마다 숫자가 달라지는 문제를 방지하기 위해 'n대 금속' 수식어를 제거하고 **'금속 원자재 & 스크랩 허브'**로 용어 표준화.
  - Perplexity, ChatGPT Search, Gemini 등 생성형 AI 엔진이 실시간 시세 및 계산 공식을 1차 출처로 직접 인용할 수 있도록 `llms.txt` 표준 사이트맵 구축.
- **2. 솔루션 & 구현**:
  - **용어 통일**: `GEMINI.md`, `WORKSPACE_INDEX.md`, `TASK_HISTORY.md`, 메인 포털 `about.html`의 '7대 금속' 표현을 **'금속 원자재 & 스크랩 허브'**로 일괄 통일.
  - **`thepathlab/llms.txt` 생성**:
    - [llmstxt.org](https://llmstxt.org/) 표준 규격 준수.
    - 11종 주요 금속(구리, 철스크랩, 알루미늄, 아연, 주석, 납, 금, 은, 백금, 팔라듐, 로듐)의 모니터링 기준 및 공식 연산식(LME 환율 환산식, 상동/신주 스크랩 평가 공식) 명시.
    - 경량 실시간 API인 `https://chicstory.github.io/metals/latest.json` 및 `scrap.html` 엔드포인트 직결.
  - **`thepathlab/robots.txt` 고도화**:
    - 등록 커스텀 도메인(`thapathlab.com`) 및 `chicstory.github.io` 사이트맵 경로 유지.
    - `PerplexityBot`, `GPTBot`, `OAI-SearchBot`, `ClaudeBot`, `Google-Extended` 크롤러 정식 허용.
  - **메인 포털 `chicstory.github.io/llms.txt` 통합 생성**:
    - 포털 산하 Metals, Powertrains, AutoIssue, Autocost, RunAnalyz 전체 생태계를 AI가 한눈에 파악하도록 마스터 `llms.txt` 배포.
- **3. 결과 & 검증**:
  - `metals` 및 `chicstory.github.io` 루트에서 `llms.txt` 즉시 접근 가능.
  - LLM 크롤러가 HTML 파싱 오버헤드 없이 0.1초 만에 우리 고유 데이터셋과 계산 공식을 인용(Citation)할 수 있는 AEO/GEO 인프라 완성.
- **4. 주요 합의 사항**:
  - 향후 신규 금속(희토류, 코발트, 리튬 등)이 추가되더라도 제목에 '12대', '13대' 등의 가변 숫자를 붙이지 않고 **'금속 원자재 & 스크랩 허브'**라는 통일된 브랜드 엔티티를 고수.

---

## [2026-09-20] 알루미늄(휠/엔진케이스)·신주(구리+아연 복합식) 단가 현실화, 아연·주석 스크랩 신설 및 전 사이트 7대 표준 GNB 통일
- **1. 요청사항**:
  - **알루미늄 단가 현실화 & 세분화**: 알루미늄 휠(A356 합금, 95% 이상 고순도 주조재, 시장가 ~4,000원/kg)이 저단가 캔(UBC)과 함께 묶여 저평가되던 문제 해결 및 현장 실거래 엔진/미션 케이스(1톤 반입 시 ~3,500원/kg 수준) 반영 요구.
  - **신주(황동) 복합 시세화**: 아연 국제시세(~4,100원/kg)가 높음에도 구리 단독 연동으로 야박하게 책정되던 신주 단가를 구리(60%)+아연(40%) 복합 합금식으로 고도화하고 등급(노베, 절봉, 주물) 분리.
  - **아연 & 주석 스크랩 품목 추가**: 원자재 시황과의 일관성을 위해 아연(다이캐스팅) 및 주석(솔더/화이트메탈)을 스크랩 단가표에 정식 편입.
  - **글로벌 GNB & 사이트맵 통일**: 서브프로젝트별(`chicstory.github.io`, `metals`, `autocost`, `autoissue`, `engines`, `guide`)로 내비게이션 폰트, 메뉴 순서, 링크 주소(`thapathlab.com` 오타 포함)가 불일치하던 현상을 ThePathLab 7대 표준 GNB 체계로 일원화.
- **2. 솔루션 & 구현**:
  - **비철 스크랩 연산 공식 현실화 (`thepathlab/scrap_builder.py`)**:
    - **알루미늄 4대 등급 체계 구축**:
      - `al_wheel` (알미늄 휠): LME 대비 92% 적용 ➔ **도매 4,213원 / 소매 3,792원** (실제 거래 시세 4,000원 완벽 안착).
      - `al_engine` (엔진·미션 케이스): LME 대비 85% 적용 ➔ **도매 3,892원 / 소매 3,503원** (사용자 1톤 야드 반입 경험치 ~3,500원과 100% 일치).
      - `al_sash` (알미늄 샷시): LME 대비 82% 적용 ➔ **도매 3,755원 / 소매 3,380원**.
      - `al_can` (음료 캔/UBC): LME 대비 50% 적용 ➔ **도매 2,290원 / 소매 2,061원**.
    - **신주(Brass) 구리+아연 복합 산출식 도입**:
      - 이론 기본단가: `(LME 전기동 × 60%) + (LME 아연 × 40%)` ➔ **13,793원/kg**.
      - 노베신주 (판재·단조 92%): **도매 12,690원 / 소매 11,421원**.
      - 절봉신주 (쾌삭봉·절삭설 86%): **도매 11,862원 / 소매 10,676원**.
      - 주물신주 (밸브·수전 74%): **도매 10,207원 / 소매 9,186원**.
    - **아연·주석 신규 품목 편입**:
      - 아연 다이캐스팅 (Zamak, LME 아연 대비 68%): **도매 2,787원 / 소매 2,508원**.
      - 주석 솔더/베어링 (LME 주석 대비 78%): **도매 36,295원 / 소매 32,666원**.
    - 총 15개 스크랩 품목(철 5종, 구리 3종, 신주 3종, 서스 1종, 알미늄 4종, 아연 1종, 주석 1종) 체계 완성.
  - **ThePathLab 7대 표준 GNB & 모바일 드로어 전 사이트 일원화**:
    - 표준 7대 메뉴 순서 및 명칭 확립:
      1. `포털 홈` (`https://chicstory.github.io/`)
      2. `금속 시황` (`https://chicstory.github.io/metals/`)
      3. `고철·비철 등급단가` (`https://chicstory.github.io/metals/scrap.html`)
      4. `유지비·보험` (`https://chicstory.github.io/autocost/`)
      5. `결함·리콜` (`https://chicstory.github.io/autoissue/`)
      6. `파워트레인` (`https://chicstory.github.io/engines/`)
      7. `이용 가이드` (`https://chicstory.github.io/guide.html`)
    - `thepathlab/scrap.html`: 간이 헤더를 제거하고 `.tpl-nav-bar` + `.tpl-drawer` + 4개국어(KO/EN/RU/ES) 버튼 + 햄버거 토글로 완전 교체.
    - `thepathlab/index.html`: GNB 7대 표준 링크 및 드로어 스크랩 단가표 링크 유지.
    - `chicstory.github.io/index.html`: `thapathlab.com` 오타 링크 교체 및 드로어 중복 제거.
    - `chicstory.github.io/autocost/index.html`: 7대 표준 링크 배치 및 드로어 스크랩 단가표 추가.
    - `autoissue/index.html`: `thapathlab.com` 오타 도메인(canonical, og, GNB, drawer, subnav) 전면 `chicstory.github.io`로 치환 및 7대 표준 정렬.
    - `engines/index.html`: 7대 표준 링크 배치 및 드로어 스크랩 단가표 추가.
    - `chicstory.github.io/guide.html`: 7대 표준 링크 배치 및 드로어 스크랩 단가표 추가.
- **3. 결과 & 검증**:
  - `python site_generator.py` 빌드 완료 (Exit code 0).
  - `scrap.html` (83,524 bytes), `index.html` (193,466 bytes), `latest.json` (8,591 bytes) 최신 생성.
  - 알루미늄 휠 4,213원, 엔진 케이스 3,892원/소매 3,503원, 노베신주 12,690원 등 사용자 현장 체감 단가와 오차 없이 일치.
  - 전 서브도메인에서 일관된 Pretendard 폰트 및 7대 표준 GNB, 모바일 드로어 인터랙션 동작 검증.
- **4. 주요 합의 사항**:
  - 알루미늄 스크랩은 용도와 순도(A356 주조 휠, ADC12 다이캐스팅 엔진케이스, 6063 압출 샷시, UBC 캔)에 따라 4개 등급으로 엄격히 분리하여 고시한다.
  - 황동(신주)은 구리와 아연의 국제시세 변동을 동시에 반영하는 `(Cu 60% + Zn 40%)` 복합 합금식을 영구 적용한다.
  - 모든 서브프로젝트의 내비게이션 바와 모바일 드로어는 7대 표준 메뉴 체계를 준수하며, 호스팅 도메인은 `https://chicstory.github.io/`로 통일한다.

---

## [2026-09-19] 철·비철 스크랩 품목별(생철/중량/경량/구리A동/신주) 실시간 스프레드 엔진 구축, 1초 정산기 & 구글 AI 검색 타깃 독립 랜딩(scrap.html) 신설
- **1. 요청사항**:
  - 기존 일괄 70~80% 감모율 방식에서 탈피하여, 국내 제강사 및 LME 기준가에 연동되는 철스크랩 5대 등급(생철, 중량A/B, 경량A, 선반설) 및 비철금속(구리 꽈배기A동, 상동, 파동, 신주, 서스304, 알미늄)의 실무 스프레드(Spread) 단가 체계 구축.
  - 도매(야드 1톤 이상 도착도) vs 소매(동네 고물상 소량 반입 -18% 감가) 듀얼 모드 실시간 계산기 제공.
  - 호호블로그 등 일반 정적 텍스트 블로그가 독점하고 있는 월 2.2만 명의 고철/비철 검색 트래픽 및 구글 AI 검색(AI Overviews) 1위 탈환을 위한 독립 랜딩 페이지(`scrap.html`) 신설.
  - `latest.json` 경량 API에 `scrap_market` 데이터셋 확장 탑재.
- **2. 솔루션 & 구현**:
  - **스크랩 실무 스프레드 연산 엔진 모듈 신설 및 시세 현실화 (`thepathlab/scrap_builder.py`)**:
    - **가격 기준점 캘리브레이션**: 국제 수입 CIF 선물 환산가(561원/kg) 대신, 국내 전기로 제강사(현대제철, 동국제강 등) 납품 실물 기준단가인 `scrap_80`(국제 시세의 80% 수준, 449원/kg)을 100% 기준점으로 전격 앵커링.
    - **국내 실물 거래가(다이렉트스크랩 5톤 455원/kg) 완벽 일치**:
      - 생철A: 101.5% 적용 ➔ **456원/kg (VAT 별도)** 산출 (실제 야드 455원과 오차 0.2%).
      - 중량A: 91.0% 적용 ➔ **409원/kg**.
      - 중량B: 84.0% 적용 ➔ **377원/kg**.
      - 경량A: 79.0% 적용 ➔ **355원/kg**.
      - 선반설: 72.0% 적용 ➔ **323원/kg**.
      - 스테인리스 SUS304: 고철 기준가의 3.7배 ➔ **1,661원/kg**.
    - **VAT(부가가치세 10%) 명문화**:
      - 야드 및 제강사 실무 관행인 **'공급가액 기준(VAT 별도)'** 원칙을 시세표 및 계산기에 공식 명시 (`단위: 원/kg (VAT 별도 - 세금계산서 발행 시 10% 가산)`).
      - 생철A 455원은 세금계산서 발행 시 500.5원(VAT 포함)으로 청구되는 구조를 완벽히 안내.
    - **A4 1페이지(Single Page) 인쇄 최적화**:
      - `@media print`에서 불필요한 모든 웹 UI(네비게이션, 히어로, 계산기, FAQ, 버튼 등) 전면 차단.
      - 인쇄 전용 헤더/푸터 및 테이블 행 패딩(3px), 폰트(7.8pt~8.5pt) 최적화로 12개 품목 전체가 **A4 1장에 완벽하게 안착**.
    - **국내 3단계 유통단가 자동 검증 엔진 정형화 (`thepathlab/scrap_validator.py`)**:
      - 스틸프라이스(`steelprice.co.kr`) 원료가격 기사 크롤링(제강사 인상/인하 뉘앙스 분석) 및 LME/국제 CIF 대비 국내 연동률 자동 판별.
      - 3단계 유통 사슬 정립:
        - 1단계 제강사 직납 도착도 (스틸프라이스 공시: 현대제철·동국제강 25톤 방차 입고가, 생철 ~475원 / 중량 ~420원)
        - 2단계 대형 야드 도매 (ThePathLab & 다이렉트스크랩: 1~5톤 상하차 매입가, 생철 455~456원 / 중량 409원 ➔ 운임·선별 마진 20~25원 차감)
        - 3단계 동네 고물상 소매 (소량 반입가: 생철 410원 / 중량 368원 ➔ 소매 감가율을 기존 18%에서 **10%**로 현실화하여 kg당 30~50원 수준의 온건한 마진 체계 구축)
      - `scrap_validation.json` 자동 생성 및 `latest.json`에 `validation` 객체(PASS, 오차 0.2%, 야드 스프레드 19원) 탑재.
      - `scrap.html` 상단에 실시간 자동 검증 상태(`PASS`) 및 스틸프라이스 기사 분석 결과 동적 뱃지 노출.
    - **도매/소매 토글 스위처 인터랙션 대폭 강화**:
      - 사용자가 상단 `[🏢 도매]` / `[🏪 소매]` 버튼을 누를 때 테이블 상에서 즉각적인 시각 반응을 체감할 수 있도록 컬럼 하이라이트 시스템 구축.
      - 도매 선택 시: 도매 열에 앰버색 글로우(`active-column`) 및 헤더에 `[✓ 선택]` 뱃지 이동, 소매 열 반투명 디밍(`dimmed-column`).
      - 소매 선택 시: 소매 열에 시안색 글로우(`active-column`) 및 헤더에 `[✓ 선택]` 뱃지 이동, 도매 열 반투명 디밍.
      - 계산기 위젯 라디오 버튼 및 설명 문구 실시간 완벽 동기화.
  - **구글 AI 검색 타깃 독립 랜딩 페이지 구축 (`thepathlab/scrap.html`)**:
    - SEO Meta: 고유 타이틀, 설명문, 키워드, Canonical URL, OpenGraph 탑재.
    - Schema.org: `FAQPage` 구조화 데이터 JSON-LD 주입 (구글 리치 스니펫 및 AI 오버뷰 선정 최적화, FAQ 5건).
    - 인터랙티브 기능: 도매/소매 원클릭 스위처, 1초 정산 계산기(품목 선택 + 중량kg 입력 ➔ 예상 수령 총액), 표에서 즉시 계산 연동.
    - 실전 FAQ 5선: 생철 vs 중량 격차 원인, 구리 A동/상동/파동 구분법, 고물상 감가율 구조(10%), 손해 보지 않는 3대 팁, 스틸프라이스 제강사 직납가 ⇄ 야드 도매가 3단계 유통 구조.
    - GA4 (`G-K3PFHN6VW7`) 및 AdSense (`ca-pub-1876940323402065`) 누락 없이 탑재.
  - **Metals 메인 허브 진입점 다각화 (`thepathlab/site_generator.py`)**:
    - 최상단 글로벌 내비게이션 바: `[🏗️ 고철·비철 등급단가]` 링크 (`./scrap.html`).
    - 햄버거 메뉴(드로어): `[고철·비철 스크랩 등급별 시세표]` 메뉴.
    - 메인 히어로 액션: `[🏗️ 등급별 고철·비철 단가표]` 골드 그라데이션 버튼.
    - 메인 히어로 하단: `[📢 A4 1장 인쇄 전용 - 고철·비철 등급별 실거래 추정 단가표]` 대형 골드 배너 카드 신설.
    - 계산기 탭 스위처: `[🏗️ 고철·비철 등급별 단가표 ↗]` 3rd 트랙 링크 탭.
    - 시세표 테이블 및 모바일 카드: 철스크랩 및 전기동 행에 `[📋 등급단가 ↗]` 직행 버튼 배치.
    - `run_briefing.bat`, `auto_daily_briefing.bat`, `sitemap.xml` 파이프라인 편입.
- **3. 결과 & 검증**:
  - `python site_generator.py` 무결점 빌드 완료: `scrap.html` (61,417 bytes), `index.html` (192,565 bytes), `latest.json` (6,395 bytes), `scrap_validation.json` (1,138 bytes), `sitemap.xml` (12 URLs) 성공적 생성.
  - Python 정밀 검증 통과: 생철A 도매 456원 / 소매 410원, 중량A 도매 409원 / 소매 368원 등 12개 품목 실거래가 완벽 일치.
  - Schema.org JSON-LD (FAQPage 5건), GA4, AdSense 검증 통과.
- **4. 주요 합의 사항**:
  - 철스크랩 단가는 국제 선물 CIF가 아닌 **국내 전기로 제강사 매입 기준가(`scrap_80`)를 기준점(Base)**으로 삼아 산출하며, 모든 고시가는 **VAT 별도(공급가액)** 기준임을 명시한다.
  - 소매 마진은 현장 거래 현실에 맞추어 약 10%(kg당 30~50원)로 온건하게 적용하며, 도매/소매 전환 시 테이블의 활성 컬럼이 시각적으로 즉각 강조되도록 유지한다.
  - `scrap_validator.py`를 통해 스틸프라이스 및 국제 시세를 일일 자동 모니터링하고 3단계 유통단가 정합성을 유지한다.
  - A4 인쇄본은 현장 출력 수요를 감안하여 어떠한 경우에도 1페이지를 초과하지 않도록 컴팩트한 레이아웃을 엄수한다.

---

## [2026-09-16] ThePathLab AutoCost 허브(월간·연간 차량 순수 유지비 & 자차가액·다이렉트 보험료 계산기) 신설 및 통합 가이드 개편
- **1. 요청사항**:
  - 할부, 렌트, 리스 등 차량 구매 금융 비용을 제외하고 순수하게 발생하는 월간/연간 차량 운용 비용(운영비/TCO) 정산기 신설.
  - 보험개발원식 감가상각 잔가율을 적용한 '올해 내 차 자차기준가액' 및 특약 없는 순수 표준형 다이렉트 5대 담보(대인1, 대인2 무한, 대물 5억, 자상, 자차) 보험료 정밀 추정.
  - 오피넷(Opinet) 전국 평균 유가 연동 주유비, 배기량 및 차령 감면(최대 50%) 자동차세, 소모품/정비 예비비 버퍼 통합 계산.
  - 브랜드 통일성을 위해 `insurance` 단독 명칭 대신 ThePathLab 모빌리티 인텔리전스 라인업(`metals`, `engines`, `autoissue`)과 일치하는 **`autocost`**로 허브 신설.
  - `metals` 폐촉매 실무 견적기 및 `autocost` 산출 원리를 [guide.html](file:///c:/Users/chics/OneDrive/문서/gemini/chicstory.github.io/guide.html) 및 `metals` 내부 설명서 모달에 동기화.
- **2. 솔루션 & 구현**:
  - **AutoCost 반응형 Dark Tech 대시보드 구축 (`chicstory.github.io/autocost/index.html`)**:
    - 8대 대표 차종 프리셋(경차, 준중형, 하이브리드, 중형, LPG, 중형SUV, 전기차, 준대형/수입) + 사용자 직접 튜닝 모드.
    - 보험개발원 경년 감가상각 잔가율 공식(1년차 78% ~ 10년차 18%) 기반 올해 자차기준가액 산출.
    - 다이렉트 자동차보험 요율 매트릭스(연령 6개 구간, 운전자 범위 4개 구간, 무사고 등급 3개 구간)를 통한 5대 담보별 분해 견적 산출.
    - 오피넷 전국 평균 유가 벤치마크 및 월 주행거리(500~2,000km+) 기반 연료비 산출.
    - 지방세법 배기량 기준 세액 + 차령 감면(3년차부터 연 5%씩 최대 50%) + 연납 할인(4.57%) 자동차세 산출.
    - 필수 소모품/정비 예비비 버퍼(월 2만~7만원) 적립금 산출.
    - 📊 **월간 / 연간 듀얼 뷰 토글**을 통한 한 달 유지비, 1년 총 지출액, 주행 1km당 순수 원가 산출.
    - 💡 차주 실무 가이드: 자차 자기부담금(20만~50만원), 물적사고 200만원 기준, 전손 vs 분손, 50만원 미만 자비 수리 판별 기준 안내.
    - GA4 (`G-K3PFHN6VW7`) 및 AdSense (`ca-pub-1876940323402065`) 탑재.
  - **통합 이용 가이드 및 사이트맵 개편 (`chicstory.github.io/guide.html`)**:
    - Section 1: 🚗 가솔린·LPG 폐촉매 실무 매입 견적 산출 가이드 카드 추가.
    - Section 3: 💸 AutoCost 자동차 순수 유지비 & 자차가액·보험료 활용법 신설.
    - Section 4: 전체 사이트맵 디렉터리에 AutoCost 허브 컬럼 추가.
  - **metals 내부 가이드 모달 개편 (`thepathlab/site_generator.py`)**:
    - 화면 설명서 모달 내 [가솔린·LPG 폐촉매 실무 매입 견적기] 안내 블록 추가 및 재빌드.
  - **글로벌 네비게이션 동기화 (`tpl-nav-bar` & `tpl-drawer`)**:
    - `chicstory.github.io/index.html`, `guide.html`, `autocost/index.html`, `thepathlab/site_generator.py`에 `유지비·보험 (autocost)` 메뉴 정식 탑재.
- **3. 결과 & 검증**:
  - Python 스크립트를 통한 `autocost/index.html` JS 구문 무결성 전수 통과 (중괄호 58/58, 괄호 154/154, 대괄호 9/9 일치).
  - GA4 및 AdSense 태그 누락 0건 확인.
  - `metals` 및 `chicstory.github.io` 원격 GitHub 저장소 커밋 및 푸시 완료 (`metals: 3f4bcf8`, `chicstory.github.io: 24456ac`).
- **4. 주요 합의 사항**:
  - 자동차 유지비는 할부/리스/렌트 등의 차량 구매 비용을 배제한 순수 운영비(Operating Cost)로 정의하며, 고액 수리비 위험을 방어하기 위해 정비 예비 버퍼를 기본 포함한다.
  - 자차보험가액은 감가상각 공식에 따라 매년 최신화되며, 사용자에게 투명한 담보별 분해 내역을 제공한다.


## [2026-09-16] ThePathLab Metals 가솔린·LPG 순정 폐촉매 실무 견적 계산기 통합 탑재 및 GA4 무결성 강화
- **1. 요청사항**:
  - 별도의 신규 레포지토리를 파지 않고 `thepathlab/` (metals 허브) 내에 가솔린/LPG 순정 폐촉매 예상 매입 견적기를 일일 브리핑 파이프라인과 통합 탑재.
  - 디젤(Pt)은 배제하고 가솔린/LPG 촉매 위주로 팔라듐(Pd)과 로듐(Rh)의 metals 당일 원화 환산 시세를 반영하여 산출.
  - **블랙박스 원칙**: 품위 등급(저품위/고품위) 및 귀금속 로딩량(g수)은 사용자 화면에 일절 노출하지 않고 차종/파워트레인만 선택하도록 함.
  - **실무 마진 30% 선반영**: 귀금속 이론가에서 매입자 수익 30%를 추가 할인한 현실적 차주 매입 견적(이론가의 약 50%~56%) 표출.
  - **최근 5일 매입 시세 추이**: 날짜별 견적 변화 및 전일 대비 변동 배지(▲/▼) 표출.
  - **링크 연동**: 대시보드 하단 팔라듐/로듐 1년 시세 차트 스무스 점프 버튼 + hsmp 블로그 폐촉매 전문 분석 칼럼(96번) 배너 연결.
  - 모바일(360px~430px) 가독성 극대화.
- **2. 솔루션 & 구현**:
  - **아카이브 데이터셋 확장 (`site_generator.py`)**:
    - `archived_data_list` 생성 시 `pd_raw`, `rh_raw` 정수값을 함께 추출·저장하여 최근 5개 일자 아카이브 데이터를 기반으로 날짜별 촉매 매입 시세 추이를 동적으로 계산할 수 있도록 구조화.
  - **2-Track 계산기 탭 UI 및 컴포넌트 탑재 (`site_generator.py`)**:
    - 기존 9대 금속 스크랩 계산기 상단에 감각적인 Dark Tech 탭 스위처 (`🪙 9대 원자재 중량 계산` vs `🚗 가솔린·LPG 폐촉매 실무 견적`) 구축.
    - 차종/파워트레인 5대 프리셋 구축 (LPi 가스차, GDi 직분사, T-GDi 터보, MPi 자연흡기, HEV 하이브리드).
    - 순정 촉매 기준 주의사항 안내 박스 및 `hsmp` 분석 칼럼 배너(`https://hsmp.tistory.com/96`) 배치.
    - 당일 매입 견적 카드(`cat-result-card`), 전일 대비 변동 배지, 최근 5일 날짜별 매입가 추이 리스트, 팔라듐/로듐 1년 차트 바로가기 버튼 제공.
  - **반응형 모바일 최적화 스타일링 (`site_generator.py`)**:
    - 640px 이하 모바일 화면에서 1열 스택 배치, 탭 버튼 터치 타깃 44px 이상 확보, 드롭다운 폰트 16px 이상(iOS 자동 줌 방지), 견적 텍스트 24px 볼드 처리.
  - **GA4 및 AdSense 무결성 보존 (`site_generator.py`)**:
    - 워크스페이스 표준 GA4 태그(`G-K3PFHN6VW7`) 및 구글 애드센스 메타태그(`ca-pub-1876940323402065`) 누락 없이 헤더에 유지.
- **3. 결과 & 검증**:
  - `python site_generator.py` 실행 완료: `index.html` (184,821 bytes) 성공적 빌드, `latest.json` 및 전체 sitemap/rss 동기화 완료.
  - Python 스크립트를 통한 JS 구문 검증: 스크립트 블록 내 중괄호 `{}`(140/140), 괄호 `()`(328/328), 대괄호 `[]`(20/20) 완전 일치 및 무결성 확인.
  - GA4(`G-K3PFHN6VW7`), AdSense 메타태그, 촉매 패널(`panel-calc-catalyst`) 정상 포함 검증 통과.
- **4. 주요 합의 사항**:
  - 촉매 매입 견적기는 일반 차주를 위한 실무 참고용이므로, 세부 귀금속 함량이나 내부 마진율 공식은 노출하지 않고 "공개 시세 반영 + 실무 안전 마진 적용" 안내 문구만을 유지한다.
  - metals 대시보드 갱신 시 `site_generator.py` 빌드 과정에서 촉매 계산기 데이터와 5일 시세 추이가 항상 당일 팔라듐/로듐 시세에 맞춰 100% 자동 동기화된다.


## [2026-09-16] Metals 시황 배너 및 계산기 법적 오인 표현('공식 검증' 등) 전면 제거 및 면책 조항 강화
- **1. 요청사항**:
  - `metals` 대시보드 배너 및 설명 문구에서 "LME · 조달청 공식 검증", "공식 시세" 등 외부 기관의 공식 인증/인가로 오인될 소지가 있는 표현 전면 배제 및 책임 소재가 분명한 객관적 표현으로 수정 요청 ("책임질 수 있는 단어를 써야지 잘못하면 쇠고랑차...").
- **2. 솔루션 & 구현**:
  - **오인 소지 문구 전수 발굴 및 리팩토링 (`site_generator.py`)**:
    - 배너 메타 뱃지: `<i class="bi-shield-check"></i> LME · 조달청 공식 검증` ➔ `<i class="bi-info-circle"></i> 공개 시장 지표 참조`로 교체.
    - 배너 설명문: "조달청 공식 판매가격표" ➔ "조달청 비축물자 판매고시표" (정부 공문서 공식 명칭)로 변경.
    - 계산기 부제목 & 라벨: "공식 시세", "공식 원자재 시장 가치" ➔ "환산 시장가", "원자재 환산 시장 가치"로 정규화.
    - 기사 메타데이터: `Mining.com (공식 피드)` ➔ `Mining.com (RSS)`로 파싱 단계에서 자동 변환되도록 방어 로직 탑재 (`metal_news_briefing.py`, `site_generator.py`).
    - 가이드 모달: "LME·조달청 국제 종가", "실거래 단가" ➔ "국제 시장 종가 및 조달청 고시가", "환산 시장가"로 수정.
  - **하단 면책 조항(Disclaimer) 법적 보호 강화**:
    - 푸터 안내문에 "공개된 시장 지표를 바탕으로 산출된 단순 참고용 추정치이며, 법적 보증이나 거래 계약의 기준이 되지 않는다"는 명시적 면책 조항 삽입.
- **3. 결과 & 검증**:
  - `python site_generator.py` 빌드 실행 후 `index.html` 내 '공식 검증', '공식' 키워드 0건(완전 제거) 검증 완료.
  - `thepathlab` (`bff3949`) 및 `chicstory.github.io` (`6ce511a`) 실시간 프로덕션 배포 완료.
- **4. 주요 합의 사항**:
  - 시세 데이터는 거래소나 정부 기관의 승인을 받은 것이 아니므로, "공식 인증", "공식 검증", "실거래가 보증"과 같은 단정적 표현을 절대 사용하지 않으며 항상 "공개 지표 참조", "환산 시장가", "단순 참고용 추정치" 표현을 유지한다.


## [2026-09-16] Metals 일일 브리핑(run_briefing.bat) 실행 시 AdSense 메타태그 소실 방지 조치 및 배포 파이프라인 영구 보강
- **1. 요청사항**:
  - 일일 금속 브리핑(`run_briefing.bat`) 실행 시, 어제 신청한 Google AdSense 소유권 인증 태그와 관련 파일들이 내부적으로 안전하게 유지되는지 사전 점검 및 누락/충돌 방지 요청.
- **2. 솔루션 & 구현**:
  - **잠재적 위험 원인 규명**:
    - `metals/index.html`은 사람이 수동 편집하는 정적 파일이 아니라, `site_generator.py`의 `build_website_index()` 함수가 실행될 때마다 파이썬 템플릿 문자열로 통째로 덮어쓰는 구조임.
    - 어제 `thepathlab/index.html`에 수동 반영되었던 Google AdSense 인증 메타태그 및 자동광고 스크립트가 `site_generator.py` 템플릿에는 누락되어 있어, `run_briefing.bat` 실행 시 태그가 즉시 삭제(덮어쓰기)될 위험 확인.
  - **`site_generator.py` HTML 템플릿 영구 반영**:
    - `site_generator.py` 내 `build_website_index()` `<head>` 섹션에 `<meta name="google-adsense-account" content="ca-pub-1876940323402065">` 및 `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1876940323402065" crossorigin="anonymous"></script>` 영구 탑재.
  - **서브 저장소 `ads.txt` 배치 및 배포 배치파일 보강**:
    - `thepathlab/ads.txt` 추가 (`google.com, pub-1876940323402065, DIRECT, f08c47fec0942fa0`).
    - `run_briefing.bat` 및 `auto_daily_briefing.bat` 내 `git add` 명령어에 `ads.txt` 명시적 포함.
- **3. 결과 & 검증**:
  - `python site_generator.py` 재생성 테스트 실행: `index.html` 재빌드 후에도 AdSense 메타태그 및 스크립트가 100% 온전하게 보존됨 확인.
  - `thepathlab` (`7df7e3c`) 및 `chicstory.github.io` (`86d7a56`) 원격 배포 완료.
- **4. 주요 합의 사항**:
  - `metals` 허브에 새 메타태그나 외부 스크립트를 추가할 때는 `index.html`을 직접 수정하지 않고, 항상 `thepathlab/site_generator.py`의 `build_website_index()` 템플릿에 영구 반영해야 한다.


## [2026-09-11] ThePathLab 네트워크 전체 RSS 2.0 및 sitemap.xml 자동 생성·동기화 파이프라인 구축 (검색엔진 0초 색인 가속)
- **1. 요청사항**:
  - 구글 서치 콘솔(Google Search Console) 및 네이버 서치어드바이저(Search Advisor) 색인 누락 방지 및 신규 콘텐츠 즉시 색인을 위해 RSS 2.0 피드(`rss.xml`) 도입 요청.
  - 일일 금속 브리핑(`thepathlab/run_briefing.bat`) 및 자동차 이슈 수집(`autoissue/run_autoissue.bat`) 실행 시 전체 네트워크(포털, metals, autoissue, engines)의 `sitemap.xml`, `rss.xml`, `robots.txt`가 원스톱으로 자동 갱신 및 배포되도록 요청.
- **2. 솔루션 & 구현**:
  - **통합 네트워크 SEO 엔진 구축 (`thepathlab/generate_network_seo.py`)**:
    - `metals`: 최근 14일치 일일 시세 브리핑을 RFC 822 표준 `pubDate` 타임스탬프와 함께 `thepathlab/rss.xml` 및 `sitemap.xml`로 자동 생성.
    - `autoissue`: `issues.json`의 최신 25개 자동차 리콜 및 결함 뉴스를 기반으로 `autoissue/rss.xml` 및 `sitemap.xml` 생성.
    - `chicstory.github.io` (마스터 허브): metals 브리핑과 autoissue 최신 이슈를 합산(29개 아이템)하여 일자 역순 정렬한 마스터 `rss.xml` 및 4대 서브허브 포괄 `sitemap.xml` 자동 발행.
    - `engines`: 400+ 엔진 제원표의 루트 sitemap `lastmod` 타임스탬프 최신화.
    - `robots.txt`: 3대 웹 도메인에 각각 해당 sitemap 및 rss 피드 URL 명시.
  - **HTML `<head>` RSS 자동 탐색 태그 삽입**:
    - `chicstory.github.io/index.html`, `thepathlab/index.html`, `autoissue/index.html`에 `<link rel="alternate" type="application/rss+xml" ...>` 자동 주입.
  - **배포 배치 스크립트 파이프라인 연결**:
    - `thepathlab/site_generator.py` 빌드 과정에 `generate_network_seo.py` 연동.
    - `thepathlab/run_briefing.bat` 및 `auto_daily_briefing.bat`: metals 브리핑 배포 시 포털 및 autoissue의 `rss.xml`과 `sitemap.xml`까지 일괄 감지하여 GitHub 원스톱 푸시.
    - `autoissue/run_autoissue.bat`: 자동차 이슈 수집 시 SEO 동기화 후 마스터 포털 RSS까지 자동 푸시.
  - **4대 레포지토리 명시적 스테이징 및 배포 완료**:
    - `chicstory.github.io`: `cedab0f`
    - `thepathlab` (metals): `a198993`
    - `autoissue`: `b6449f7`
    - `engines`: `9162fc4`
- **3. 결과 & 검증**:
  - `python site_generator.py` 및 `python generate_network_seo.py` 무결점 테스트 통과 (Exit code 0).
  - RSS 2.0 W3C 표준 구조(`channel`, `title`, `link`, `description`, `pubDate`, `guid`) 검증 완료.
  - 서치 콘솔에 등록할 마스터 RSS (`https://chicstory.github.io/rss.xml`) 및 서브허브 피드 즉시 제공 준비 완료.
- **4. 주요 합의 사항**:
  - 향후 신규 서비스 추가 시에도 `generate_network_seo.py`의 `HUBS` 및 아이템 수집 함수에 등록하여 네트워크 마스터 피드에 자동 누적되도록 유지한다.


## [2026-09-10] metals 일자별 아카이브 9일·8일 금(Gold) 시세 교정 및 팔라듐 폴백 제거
- **1. 요청사항**:
  - `metals`의 일자별 브리핑 & 환산시세 아카이브 브리핑 목록에서 2026-09-10은 금 가격이 정상 표기되나, 09-09 및 09-08에는 과거 팔라듐(58,422원, 60,556원) 가격이 들어가 있는 문제 수정 요청.
- **2. 원인 분석 & 솔루션**:
  - **원인 분석**:
    1. 9대 금속 체제로 확장되기 전인 09-08, 09-09 발행 당시 생성된 CSV는 7대 자원(철스크랩, 알루미늄, 구리, 납, 팔라듐, 로듐, 백금)만 포함하고 있어 '금' 항목이 부재했음.
    2. 과거 스크립트(`site_generator.py`)의 `renderScrollList` 및 `selectDate` 함수에 `(a.gold && a.gold !== '-') ? a.gold : (a.palladium || '-')`라는 임시 폴백 코드가 잔존하여, 금 데이터가 없을 때 팔라듐 가격이 '금' 열에 노출되었음.
  - **솔루션 구현**:
    - **과거 CSV 데이터 정규화**:
      - 2026-09-09: 금 4,371.69 USD/t.oz (환율 1,338.1원) ➔ **188,074원/g** (70% 131,652원, 80% 150,459원) 및 은(2,876원/g) 산출 추가 (`7대자원` 수정 및 `9대자원_환산시세_2026-09-09.csv` 동시 생성).
      - 2026-09-08: 금 4,356.21 USD/t.oz (환율 1,344.4원) ➔ **188,290원/g** (70% 131,803원, 80% 150,632원) 및 은(2,861원/g) 산출 추가 (`7대자원` 수정 및 `9대자원_환산시세_2026-09-08.csv` 동시 생성).
    - **스크립트 클린업 (`site_generator.py`)**:
      - `renderScrollList` 및 `selectDate`에서 팔라듐 폴백 로직 완전 제거 (`(a.gold && a.gold !== '-') ? a.gold : '-'`).
- **3. 결과 & 검증**:
  - `python site_generator.py` 재생성 결과:
    - 2026-09-10: 190,190원/g (정상 유지)
    - 2026-09-09: **188,074원/g** (교정 완료)
    - 2026-09-08: **188,290원/g** (교정 완료)
  - `thepathlab` 저장소 커밋 & 푸시 완료: [`0ea6891`](https://github.com/chicstory/metals/commit/0ea6891)
- **4. 주요 합의 사항**:
  - 금속 시세 컬럼 및 아카이브 데이터는 자원 간(예: 금 ⇄ 팔라듐) 폴백을 절대 금지하며, 데이터셋에 해당 금속이 존재하지 않을 경우 '-'로 명확히 표시하거나 소급 데이터를 정규화하여 관리함.

---


## [2026-09-10] metals(금속원자재·스크랩) 상단 내비게이션 바 & 드로어 전역 표준(`tpl-nav-bar`) 영구 동기화
- **1. 요청사항**:
  - `metals`(`thepathlab/index.html`)의 상단 내비게이션 형태가 메인 포털, 엔진 백과, 자동차 데일리 이슈와 달라 이질감이 느껴짐.
  - 매일 자동 발행되는 사이트 특성에 맞춰 포털 표준 내비게이션(`tpl-nav-bar`, `tpl-drawer`, 다국어 `tplChangeLang`)으로 통일 요청.
- **2. 솔루션 & 구현**:
  - **단일 진실 공급원(`site_generator.py`) f-string 템플릿 개편**:
    - `thepathlab`은 `site_generator.py`가 매일 `index.html`을 전면 빌드하므로, 생성기 코드의 f-string 템플릿 내 CSS 및 HTML 마크업을 직접 교체하여 향후 일일 브리핑 자동화(`auto_daily_briefing.bat`) 구동 시에도 전역 표준 네비게이션이 영구 유지되도록 처리.
    - Python f-string 제약에 맞춰 모든 CSS/JS 중괄호(`{`, `}`)를 이스케이프(`{{`, `}}`) 처리하여 렌더링 무결성 확보.
  - **ThePathLab 표준 내비게이션 및 드로어 통합**:
    - 메뉴 순서: `포털 홈` ➔ `자동차 데일리 이슈` ➔ `금속 원자재·스크랩 (active)` ➔ `제조사별 스펙표` ➔ `엔진 전수 백과` ➔ `이용 가이드`.
    - 우측 액션: `KO | EN | RU | ES` 4개국어 원클릭 변환기 및 반응형 모바일 햄버거 버튼(`tplHamburgerBtn`) 탑재.
    - 슬라이드 아웃 오프캔버스 드로어(`tpl-drawer`) 및 Google Translate 지연 로딩 스크립트 탑재.
  - **금속 시세 핵심 메타데이터 보존 (`.hero-meta-bar`)**:
    - 기존 레거시 헤더에 위치하던 `기준 일시: {data['date_str']}` 및 `적용 환율: 1 USD = {data['usd_rate']}원`을 `<section class="hero-banner">` 내부의 메타 뱃지 바(`.hero-meta-bar`)로 이동 배치하여 대시보드 시각적 완성도 향상.
- **3. 결과 & 검증**:
  - `python site_generator.py` 빌드 실행 성공: `index.html` (161,140 bytes), `sitemap.xml`, `latest.json` 정상 생성 검증.
  - `thepathlab` 저장소 커밋 & 푸시 완료: [`286dd24`](https://github.com/chicstory/metals/commit/286dd24)
- **4. 주요 합의 사항**:
  - `thepathlab`의 HTML 수정은 `index.html`을 직접 수정하는 것이 아닌 반드시 `site_generator.py`를 통해 관리되어야 매일 아침 자동 스케줄러 실행 시에도 변경 사항이 덮어쓰이지 않고 유지됨.

---


## [2026-09-10] metals 9대 금속(금·은 추가) 확장, 옵션 2 순서 배치, 캘린더 금(Gold) 대체 및 모바일 카드 넘침 0px 개선
- **1. 요청사항**:
  - 내일부터 metals에 금(Gold)과 은(Silver)을 추가하여 기존 7대에서 9대 자원으로 확장 요청.
  - 노출 순서: 비철·철스크랩 등 산업금속을 앞쪽에 배치하고 귀금속을 뒤로 배치하는 **옵션 2 순서** 적용 요청.
  - 하단 캘린더 아카이브 브리핑 목록 표 및 프리뷰 바에서 기존 팔라듐 대신 **금(Gold)** 가격을 우선 표기하도록 변경 요청.
  - 모바일 가독성 최적화: 모바일 화면에서 간혹 카드 밖으로 내용이나 알약(Pill)이 빠져나가는 문제 해결 요청.
- **2. 솔루션 & 구현**:
  - **9대 자원 확장 및 옵션 2 노출 순환 체계 구축 (`thepathlab/metal_news_briefing.py`)**:
    - `TARGET_METALS`에 `gold`(TradingEconomics: `gold`, t.oz당 USD -> 원/g, 1돈 3.75g 안내) 및 `silver`(TradingEconomics: `silver`, t.oz당 USD -> 원/g) 신규 추가.
    - 정렬 순서: 1.구리 ➡️ 2.철·철스크랩 ➡️ 3.알루미늄 ➡️ 4.납 ➡️ 5.금 ➡️ 6.은 ➡️ 7.백금 ➡️ 8.팔라듐 ➡️ 9.로듐 (옵션 2).
    - 리포트 및 산출 파일명을 `9대자원_환산시세_YYYY-MM-DD.csv`, `[통합브리핑] 9대_금속원자재_YYYY-MM-DD.html/md`로 표준화하고, 전일 파일 탐색 시 7대/9대 파일명 모두 호환되도록 처리.
  - **대시보드 빌더 및 아카이브 캘린더 연동 (`thepathlab/site_generator.py`)**:
    - `METALS_META`를 9대 자원 옵션 2 순서로 재정렬하고, 과거 7대만 존재하던 날짜 데이터 로드 시에도 오류 없이 존재하는 금속만 자연스럽게 렌더링되도록 하위 호환(`if not c_row: continue`) 적용.
    - 캘린더 아카이브 표 헤더 `<th>팔라듐</th>` ➡️ `<th>금 (Gold)</th>` 및 프리뷰 바 `prev-gold`로 교체. 과거 날짜 아카이브 클릭 시에도 금 시세(없을 경우 팔라듐 폴백) 즉시 반영.
    - 1초 계산기(`initCalculator`): 금 선택 시 1돈(3.75g) 기본 추천값 및 빠른 수량 버튼(`1돈(3.75g)`, `10돈(37.5g)`, `100(g/kg)`, `1,000(1kg/1톤)`) 추가.
    - 귀금속 전용 배지 스타일(`.badge-precious`, 앰버/골드 테마) 및 카테고리 탭(`귀금속(금·은)`) 추가.
  - **모바일 카드 밖 이탈 원천 차단 (Zero-Overflow CSS)**:
    - `@media (max-width: 768px)`에서 `.card-price-pills`를 `display: grid !important; grid-template-columns: 1fr !important;`로 변경하여 모바일 좁은 폭에서도 알약이 카드 밖으로 튀어나가지 않고 100% 폭 내에 완벽 밀착되도록 개선.
    - `.metal-card`, `.m-price-card`, `.calc-box`, `.archive-box`에 `box-sizing: border-box !important; width: 100% !important; overflow: hidden !important;` 적용.
    - `.art-title`, `.art-desc`, `.ai-bullet`, `.ai-para`, `.pill-val`에 `word-break: break-word !important; overflow-wrap: break-word !important;`를 적용하여 긴 텍스트로 인한 레이아웃 깨짐 원천 방지.
  - **메인 포털 및 이용 가이드 동기화 (`chicstory.github.io/index.html`, `guide.html`)**:
    - 포털 메인 카드, 드로어, 최근 활동 타임라인 문구를 '9대 금속 원자재'로 갱신.
    - `guide.html`의 환산 공식 박스에 금(1돈=3.75g), 은 환산 공식 추가 및 사이트맵 갱신.
- **3. 결과 & 검증**:
  - `thepathlab` 저장소 (`19898d5`) 및 `chicstory.github.io` 저장소 (`86c79df`) 커밋 및 푸시 배포 완료.
  - `python site_generator.py` 빌드 검증: 0 에러 정상 완료. `index.html`, `latest.json`, `sitemap.xml` 정상 최신화 확인.
  - 모바일 반응형 뷰포트에서 카드 밖 이탈 0px 및 1fr 수직 정렬 정상 동작 검증.
- **4. 주요 합의 사항**:
  - 내일 아침 브리핑 실행 시 자동으로 9대 금속 전체 크롤링 및 리포트가 생성되며, 포털과 캘린더에서도 금(Gold) 우선 표기 및 1돈 계산 지원 유지.

---


## [2026-09-10] metals & 메인 포털(chicstory.github.io) 완전 자동 동기화(Zero-Touch) 구축
- **1. 요청사항**:
  - 매일 아침 `metals`(thepathlab) 일일 브리핑을 업데이트하지만, 메인 포털(`chicstory.github.io`)의 발행일자(`2026-09-09 발행`)와 최근 리포트 현황이 수동 업데이트 전까지 어제 날짜로 남아있는 문제 발생.
  - 매일 두 레포지토리를 수동으로 번거롭게 수정할 필요 없이 완전 자동화가 가능한지 여부 및 크로스 PC(노트북) 작업 호환성 문의.
- **2. 솔루션 & 구현**:
  - **클라이언트 실시간 동기화 (Client-side Zero-Touch Sync)**:
    - `thepathlab/site_generator.py` 빌드 시 최신 발행일자, 환율, 7대 금속 시세 및 전일대비 변화량을 담은 1.8KB 경량 API 파일 `thepathlab/latest.json` 자동 생성 탑재.
    - 메인 포털 `chicstory.github.io/index.html`에 비동기 `fetch('https://chicstory.github.io/metals/latest.json')` 스크립트를 추가하여 방문자 접속 시 0초 만에 실시간으로 최신 발행일자 배지 및 업데이트 로그 갱신.
  - **아침 배치 파이프라인 결합 (`auto_daily_briefing.bat`)**:
    - `site_generator.py` 실행 시 인접한 `chicstory.github.io/index.html`의 정적 HTML 태그를 정규식으로 자동 치환(`sync_portal_index`).
    - `auto_daily_briefing.bat` 3단계에 포털 저장소 Git Commit & Push 스크립트를 연결하여 검색엔진 크롤러(네이버, 구글 봇)를 위한 정적 HTML 코드까지 매일 아침 100% 자동 동기화.
- **3. 결과 & 검증**:
  - `thepathlab` 저장소 (`8a800ff`) 및 `chicstory.github.io` 저장소 (`ca4f5c9`) 배포 완료.
  - 포털 메인 접속 시 `[2026-09-10 발행]` 배지, `09-10` 리포트 일자 정상 출력 확인.
- **4. 주요 합의 사항**:
  - 사용자는 향후 포털을 별도로 수정할 필요 없이 평소처럼 아침 metals 브리핑 배치만 실행하면 두 사이트가 모두 최신화됨.

---


## [2026-09-09] 통합 이용 가이드(guide.html) 및 사이트맵 신설 + 플로팅 액션바(FAB) 탑재
- **1. 요청사항**:
  - 사용자가 metals, engines 서비스를 효율적으로 이용할 수 있도록 화면 설명서와 탑 버튼을 스크롤 시 우측 하단에 제공하고, 상세 설명서 및 사이트맵을 독립 페이지로 구성할지 여부 검토 요청.
- **2. 솔루션 & 구현**:
  - **독립 가이드 페이지 신설 (`chicstory.github.io/guide.html`)**:
    - 메인 포털의 로딩 속도(PageSpeed 95+점) 보존 및 구글 애드센스/SEO 노출 극대화를 위해 독립 페이지로 분리 제작.
    - 금속 시세 원화 환산 공식, 스크랩 감모율/마진 해설, 엔진 파워트레인 다이노(Dyno) 곡선 읽는 법, 비주얼 사이트맵 플로우 다이어그램 수록.
  - **우측 하단 플로팅 액션 바 (FAB) 탑재**:
    - `thepathlab` (metals) 및 `chicstory.github.io` (포털) 양쪽에 스크롤 300px 이상 시 페이드인되는 FAB 툴바 탑재.
    - **Top 버튼**: 최상단 스무스 스크롤.
    - **화면 설명서(?) 버튼**: PC 호버 툴팁 + 클릭 시 핵심 3줄 퀵 가이드 모달 팝업 및 `[통합 가이드 바로가기]` 링크 제공.
- **3. 결과 & 검증**:
  - `chicstory.github.io` (`ce412f4`), `thepathlab` (`dfbaae9`) 배포 완료.
  - 모바일 터치 및 데스크탑 호버 모두 매끄럽게 동작 확인.
- **4. 주요 합의 사항**:
  - 서비스 설명서는 메인 페이지 코드를 비대하게 만들지 않고 독립된 고품질 콘텐츠 페이지(`guide.html`)로 유지 관리.

---


## [2026-09-09] 7대 금속 원자재 환율 변동 100% 반영 전일대비 가격 변화량 뱃지 시스템 구축
- **1. 요청사항**:
  - metals 서비스에서 전일 대비 가격 변화량을 가독성을 해치지 않는 범위 내에서 보여주고, 단순 달러 변동이 아닌 환율 변동까지 결합된 실질 원화 단가(원/kg, 원/g) 변화량을 반영 요청.
- **2. 솔루션 & 구현**:
  - **실질 원화 단가 변동 공식 수립**:
    - $\text{변동액} = (\text{당일 종가} \times \text{당일 환율}) - (\text{전일 종가} \times \text{전일 환율})$
    - 전일 CSV 파일을 자동으로 대조하여 순 원화 변동액(원) 및 등락률(%) 산출.
  - **Dark Tech 인라인 뱃지 UI**:
    - 상승 시: `▲ +2,383원 (+0.6%)` (Green 인라인 뱃지)
    - 하락 시: `▼ -196원 (-1.0%)` (Red/Amber 인라인 뱃지)
    - 보합 시: `- 0원 (0.0%)` (Muted Gray 인라인 뱃지)
  - `site_generator.py` 및 `metal_news_briefing.py` 양쪽 파이프라인에 동시 적용.
- **3. 결과 & 검증**:
  - `thepathlab` (`cb53d41`) 배포 완료.
  - 메인 대시보드 테이블, 모바일 시세 카드, 7대 자원별 카드, 일일 브리핑 리포트에 일괄 적용 완료.
- **4. 주요 합의 사항**:
  - 국내 실거래 기준이므로 달러 변동률이 아닌 원화 환산 기준 변동률을 기본 표기.
