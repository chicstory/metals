# 🌐 ThePathLab 커스텀 도메인 연결 및 검색엔진·애널리틱스 설정 가이드

본 문서는 **독립 도메인(예: `thepathlab.kr` 또는 `thepathlab.com`)을 구매한 후**, GitHub Pages 연결부터 **Google Search Console, Google Analytics 4, 네이버 서치어드바이저, 구글 애드센스**에 신규 등록하고 세팅하는 전 과정을 정리한 종합 가이드입니다.

---

## 📌 한눈에 보는 전환 절차 체크리스트

| 단계 | 항목 | 필수 여부 | 소요 시간 | 비고 |
| :--- | :--- | :---: | :---: | :--- |
| **Step 1** | 도메인 구매 및 DNS 설정 (A 레코드 & CNAME) | **필수** | 5분 | 도메인 등록업체(가비아 등)에서 설정 |
| **Step 2** | GitHub Pages CNAME 등록 & Enforce HTTPS | **필수** | 1분 | GitHub 레포 Settings에서 활성화 |
| **Step 3** | Google Search Console 신규 속성 추가 | **필수** | 3분 | **도메인 속성(DNS TXT 인증)** 강력 권장 |
| **Step 4** | 새 도메인 사이트맵 & RSS 제출 | **필수** | 2분 | `sitemap.xml` 및 `rss.xml` 제출 |
| **Step 5** | Google Analytics 4(GA4) 웹 스트림 URL 갱신 | **필수** | 1분 | 측정 ID(`G-K3PFHN6VW7`) 유지, URL만 변경 |
| **Step 6** | 네이버 서치어드바이저 사이트 등록 | **권장** | 3분 | 국내 네이버 검색 유입 필수 코스 |
| **Step 7** | Google AdSense 사이트 추가 & 심사 신청 | **목표** | 2분 | 새 도메인으로 승인 신청 |

---

## 1️⃣ 도메인 구매 및 DNS / GitHub Pages 연결

### ① DNS 레코드 설정 (도메인 등록업체: 가비아, 호스팅케이알 등)
도메인 관리자 페이지의 **[DNS 레코드 설정]**에서 아래 레코드를 추가합니다:

1. **A 레코드 4개 추가 (루트 도메인용: `@`)**:
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
2. **CNAME 레코드 1개 추가 (`www` 서브도메인용)**:
   - 호스트 이름: `www`
   - 값/목적지: `chicstory.github.io.` (끝에 점 주의)

### ② GitHub Pages 커스텀 도메인 등록
1. `chicstory.github.io` 레포지토리의 **Settings ➡️ Pages** 접속.
2. **Custom domain** 입력창에 구매한 도메인(예: `thepathlab.kr`) 입력 후 **Save**.
3. DNS가 전파되면 (약 5~30분 소요) **[Enforce HTTPS]** 체크박스를 반드시 활성화.
   *(GitHub가 Let's Encrypt SSL 보안 인증서를 무료 자동 발급함)*

---

## 2️⃣ Google Search Console (GSC) 신규 등록 & 사이트맵 제출

> ⚠️ **중요**: 구글 서치콘솔은 도메인이 바뀌면 **완전히 새로운 웹사이트**로 취급합니다. 기존 `chicstory.github.io` 속성과 별개로 새 도메인 속성을 반드시 추가해야 합니다.

### ① '도메인' 속성 추가 (가장 강력 추천)
1. [Google Search Console](https://search.google.com/search-console) 접속.
2. 좌측 상단 속성 드롭다운 ➡️ **[+ 속성 추가]**.
3. 왼쪽의 **[도메인]** 카드 선택 (URL 접두사가 아닌 **도메인** 선택).
4. `thepathlab.kr` (프로토콜 없이 도메인만) 입력.
5. 구글이 제시하는 **TXT 레코드 값**(예: `google-site-verification=...`)을 복사하여, 도메인 등록업체(가비아 등) DNS 설정에 **TXT 레코드**로 등록 후 **[확인]** 클릭.
   - **장점**: `https`, `http`, `www`, 서브도메인이 일괄 통합 관리되어 가장 정확한 색인 분석 가능.

### ② 사이트맵 및 RSS 제출
새 속성이 인증되면 좌측 메뉴 **[Sitemaps]**로 이동하여 아래 4개를 각각 제출합니다:
- `sitemap.xml`
- `rss.xml`
- `metals/sitemap.xml`
- `engines/sitemap.xml`
- `autoissue/sitemap.xml`
*(앞에 슬래시 없이 파일명/상대경로로 입력)*

### ③ (선택) 기존 속성에서 '주소 변경(Change of Address)' 신청
기존 `https://chicstory.github.io` 속성으로 들어가 **설정 ➡️ 주소 변경** 메뉴에서 새 도메인으로 이전 신청을 해두면 구글이 기존 평가 점수를 새 도메인으로 더 빨리 넘겨줍니다.

---

## 3️⃣ Google Analytics 4 (GA4) 설정 갱신

> 💡 **GA4 추적 코드(`G-K3PFHN6VW7`)를 바꿀 필요는 전혀 없습니다!** 
> 기존 GA4 속성을 그대로 사용하면서 URL 설정만 업데이트하면 방문자 히스토리가 끊기지 않고 누적됩니다.

1. [Google Analytics](https://analytics.google.com/) 접속.
2. 좌측 하단 **[관리(톱니바퀴)] ➡️ [데이터 스트림] ➡️ 기존 Web 스트림 클릭**.
3. **스트림 세부정보** 상단의 **연필(수정) 아이콘** 클릭:
   - **스트림 URL**: `https://chicstory.github.io` ➡️ **`https://thepathlab.kr`** 로 변경.
   - **스트림 이름**: (원하는 경우) `ThePathLab Network`로 변경.
4. **저장** 클릭.

---

## 4️⃣ 네이버 서치어드바이저 등록 (국내 유입 극대화)

국내 포털 검색(네이버) 유입을 위해 네이버 등록도 필수입니다:

1. [네이버 서치어드바이저](https://searchadvisor.naver.com/) 접속 ➡️ **웹마스터 도구**.
2. **사이트 등록**에 `https://thepathlab.kr` 입력.
3. **사이트 소유확인**:
   - `HTML 메타 태그` 방식 선택 ➡️ 제공되는 `<meta name="naver-site-verification" content="..." />` 태그 복사.
   - 메인 포털 `index.html`의 `<head>` 영역에 삽입하여 배포 후 소유확인 클릭.
4. 좌측 메뉴 **[요청] ➡️ [사이트맵 제출]**: `sitemap.xml` 제출.
5. 좌측 메뉴 **[요청] ➡️ [RSS 제출]**: `rss.xml` 제출.

---

## 5️⃣ Google AdSense 사이트 추가 및 승인 심사 신청

독립 도메인이 연결되고 HTTPS가 활성화되면 바로 애드센스 심사에 들어갑니다:

1. [Google AdSense](https://adsense.google.com/) 접속 ➡️ 좌측 메뉴 **[사이트]**.
2. **[+ 새 사이트 추가]** 클릭 ➡️ 구매한 도메인(예: `thepathlab.kr`) 입력.
3. 구글이 발급하는 **애드센스 검수 스크립트 코드** 복사:
   ```html
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
   ```
4. 이 코드를 알려주시면 제가 사이트 전수 메인 `<head>`에 탑재하여 배포합니다.
5. 애드센스 화면에서 **[검토 요청]** 버튼을 클릭하면 심사가 시작됩니다 (통상 1~7일 소요).
6. **`ads.txt` 배치**:
   - 애드센스에서 제공하는 `ads.txt` 문구(예: `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`)를 루트 디렉토리에 파일로 생성해 두면 크롤링 에러 없이 100% 안전합니다.

---

## 6️⃣ 코드베이스 내부 URL 일괄 자동 전환 (AI 일괄 대행)

도메인이 확정되면, 아래 작업은 AI 어시스턴트(Antigravity)에게 **"도메인 `XXX.com`으로 연결 완료했으니 코드베이스 전체 치환해줘"**라고 요청하시면 1초 만에 자동 완료됩니다:

1. 루트 디렉토리에 `CNAME` 파일 생성 (새 도메인 기록).
2. 전 페이지 `<link rel="canonical" href="...">` 및 OpenGraph(`og:url`)를 새 도메인으로 치환.
3. `sitemap.xml`, `rss.xml`, `robots.txt` 내부 절대 경로 일괄 갱신.
4. GNB 및 드로어 내부 링크 통일.
