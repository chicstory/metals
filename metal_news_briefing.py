#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metal_news_briefing.py
--------------------------------------------------------------------------------
주요 7대 금속/원자재(철·철스크랩, 알루미늄, 구리, 팔라듐, 로듐, 백금, 납)의:
  1. Trading Economics 기반 1년 종가 시세 차트 자동 캡처 (렌더링 완료 감지)
  2. 조달청(PPS) 비축물자 판매가격표 자동 캡처
  3. Mining.com 및 글로벌 광물 뉴스 스크래핑
  4. 로컬 Gemma 4 (Ollama) 모델을 통한 시장 분석 및 블로그 가이드 생성

결과 저장 구조:
  thepathlab/resources/YYYY-MM-DD/
    ├── 조달청_원자재_판매가격_YYYY-MM-DD.png
    ├── [철·철스크랩]_1년_시세차트_YYYY-MM-DD.png
    ├── [철·철스크랩] briefing_YYYY-MM-DD.md
    ├── [알루미늄]_1년_시세차트_YYYY-MM-DD.png
    ├── [알루미늄] briefing_YYYY-MM-DD.md
    ├── [구리]_1년_시세차트_YYYY-MM-DD.png
    ├── [구리] briefing_YYYY-MM-DD.md
    ├── [팔라듐]_1년_시세차트_YYYY-MM-DD.png
    ├── [팔라듐] briefing_YYYY-MM-DD.md
    ├── [로듐]_1년_시세차트_YYYY-MM-DD.png
    ├── [로듐] briefing_YYYY-MM-DD.md
    ├── [백금]_1년_시세차트_YYYY-MM-DD.png
    ├── [백금] briefing_YYYY-MM-DD.md
    ├── [납]_1년_시세차트_YYYY-MM-DD.png
    ├── [납] briefing_YYYY-MM-DD.md
    └── [종합요약] briefing_YYYY-MM-DD.md
--------------------------------------------------------------------------------
"""

import os
import sys
import time
import json
import re
import html
import csv
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Dict, List, Any, Optional, Tuple

# PIL 이미지 처리 라이브러리
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Selenium 브라우저 자동화
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

# Windows 콘솔 utf-8 출력 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 기본 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(SCRIPT_DIR, "resources")
os.makedirs(RESOURCES_DIR, exist_ok=True)

# Ollama 설정
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma4:12b-it-qat"

# HTTP 요청 헤더 (Mining.com / TradingEconomics 차단 방지용 브라우저 헤더)
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 7대 자원 정의 및 키워드/TradingEconomics/단위 환산 매핑
TARGET_METALS = {
    "iron_scrap": {
        "name_kr": "철·철스크랩",
        "name_en": "Steel Scrap",
        "emoji": "🏗️",
        "te_slug": "scrap-steel",
        "category": "metal",           # USD/T -> 원/kg
        "type_label": "철·스크랩",
        "unit_raw": "USD/T",
        "unit_krw": "원/kg",
        "keywords": ["steel scrap", "scrap steel", "ferrous scrap", "shredded scrap", "heavy melt", "iron ore", "steelmaking", "steel price", "rebar", "hrc", "baowu", "posco"],
        "primary_query": '("steel scrap" OR "scrap steel" OR "ferrous scrap" OR "steel prices" OR "steel demand")',
        "broad_query": '("steel scrap" OR "scrap steel" OR "ferrous scrap")',
    },
    "aluminum": {
        "name_kr": "알루미늄",
        "name_en": "Aluminum",
        "emoji": "🥫",
        "te_slug": "aluminum",
        "category": "metal",           # USD/T -> 원/kg
        "type_label": "비철금속",
        "unit_raw": "USD/T",
        "unit_krw": "원/kg",
        "keywords": ["aluminum", "aluminium", "bauxite", "alumina", "aluminum smelter", "aluminum price"],
        "primary_query": '(aluminum OR aluminium OR bauxite OR alumina)',
        "broad_query": '(aluminum OR aluminium) (price OR market OR smelter)',
    },
    "copper": {
        "name_kr": "구리",
        "name_en": "Copper",
        "emoji": "🥉",
        "te_slug": "copper",
        "category": "copper_lbs",       # USD/Lbs -> 원/kg (1 lb = 0.45359237 kg)
        "type_label": "비철금속",
        "unit_raw": "USD/Lbs",
        "unit_krw": "원/kg",
        "keywords": ["copper", "codelco", "freeport", "escondida", "copper cathode"],
        "primary_query": 'copper (price OR mine OR supply OR deficit OR surplus OR lme)',
        "broad_query": 'copper (market OR price OR mining)',
    },
    "lead": {
        "name_kr": "납",
        "name_en": "Lead",
        "emoji": "🔋",
        "te_slug": "lead",
        "category": "metal",           # USD/T -> 원/kg
        "type_label": "비철금속",
        "unit_raw": "USD/T",
        "unit_krw": "원/kg",
        "keywords": [
            "lead metal", "lead price", "lead market", "lead smelter",
            "lead battery", "lead zinc", "lead concentrate", "lead scrap",
            "refined lead", "lme lead"
        ],
        "primary_query": '("lead metal" OR "lead price" OR "lead smelter" OR "lead battery" OR "lead and zinc")',
        "broad_query": '("lead metal" OR "lead smelter" OR "refined lead")',
    },
    "palladium": {
        "name_kr": "팔라듐",
        "name_en": "Palladium",
        "emoji": "🪙",
        "te_slug": "palladium",
        "category": "pgm",             # USD/t.oz -> 원/g (1 t.oz = 31.1034768 g)
        "type_label": "PGM (백금족)",
        "unit_raw": "USD/t.oz",
        "unit_krw": "원/g",
        "keywords": ["palladium", "norilsk", "catalytic converter"],
        "primary_query": 'palladium (price OR supply OR market OR auto)',
        "broad_query": 'palladium metal price',
    },
    "rhodium": {
        "name_kr": "로듐",
        "name_en": "Rhodium",
        "emoji": "✨",
        "te_slug": "rhodium",
        "category": "pgm",             # USD/t.oz -> 원/g
        "type_label": "PGM (백금족)",
        "unit_raw": "USD/t.oz",
        "unit_krw": "원/g",
        "keywords": ["rhodium"],
        "primary_query": 'rhodium (price OR market OR pgm)',
        "broad_query": 'rhodium precious metal',
    },
    "platinum": {
        "name_kr": "백금",
        "name_en": "Platinum",
        "emoji": "💍",
        "te_slug": "platinum",
        "category": "pgm",             # USD/t.oz -> 원/g
        "type_label": "PGM (백금족)",
        "unit_raw": "USD/t.oz",
        "unit_krw": "원/g",
        "keywords": ["platinum", "pgm", "pgms", "anglo american platinum", "impala"],
        "primary_query": 'platinum (price OR pgm OR hydrogen OR jewelry OR market)',
        "broad_query": 'platinum metal (price OR supply)',
    },
}


def fetch_usd_krw_rate() -> Tuple[float, str]:
    """네이버 금융 및 금융 API를 통해 최신 USD/KRW 환율 및 출처 조회"""
    # 1. 네이버 금융 시장지표 (하나은행 고시환율)
    try:
        url = "https://m.stock.naver.com/front-api/marketIndex/prices?category=exchange&reutersCode=FX_USDKRW"
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rate_str = data["result"][0]["closePrice"]
            rate = float(rate_str.replace(",", ""))
            return rate, "네이버 금융 (하나은행 고시환율)"
    except Exception:
        pass

    # 2. 야후 파이낸스 백업
    try:
        y_url = "https://query1.finance.yahoo.com/v8/finance/chart/USDKRW=X"
        y_req = urllib.request.Request(y_url, headers={"User-Agent": BROWSER_HEADERS["User-Agent"]})
        with urllib.request.urlopen(y_req, timeout=5) as y_resp:
            y_data = json.loads(y_resp.read().decode("utf-8"))
            rate = y_data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(rate), "야후 파이낸스 (Yahoo Finance 실시간)"
    except Exception:
        pass

    # 3. 기본값 폴백
    return 1340.0, "기준 환율 (추정)"


def clean_html(raw_html: str) -> str:
    """HTML 태그 제거 및 텍스트 정리"""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def create_headless_browser():
    """Selenium 헤드리스 브라우저 인스턴스 생성"""
    if not HAS_SELENIUM:
        return None
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--window-size=1280,2200")
        options.add_argument(f"user-agent={BROWSER_HEADERS['User-Agent']}")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"[경고] 브라우저 드라이버 시작 실패 ({e})", flush=True)
        return None


def capture_pps_price_table(driver, date_folder: str, today_str: str) -> Optional[str]:
    """조달청 비축물자 웹사이트에서 원자재 판매가격표 영역 캡처"""
    if not driver:
        return None

    pps_url = "https://www.pps.go.kr/bichuk/index.do"
    temp_full_path = os.path.join(date_folder, "_temp_pps_full.png")
    final_img_name = f"조달청_원자재_판매가격_{today_str}.png"
    final_img_path = os.path.join(date_folder, final_img_name)

    print(f"[*] 🏛️ 조달청(PPS) 비축물자 가격표 캡처 진행 중...", flush=True)

    try:
        driver.set_window_size(1280, 2200)
        driver.get(pps_url)
        # 테이블 컨테이너 대기
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".con_box2, .tableB")))
        time.sleep(1.5)

        driver.save_screenshot(temp_full_path)
        if os.path.exists(temp_full_path):
            if HAS_PIL:
                img = Image.open(temp_full_path)
                # 원자재 판매가격 표 영역 크롭
                cropped = img.crop((25, 850, 1255, 1660))
                cropped.save(final_img_path)
                os.remove(temp_full_path)
            else:
                os.rename(temp_full_path, final_img_path)

            print(f"    -> [완료] 조달청 가격표 저장: {final_img_name}", flush=True)
            return final_img_name
    except Exception as e:
        print(f"[경고] 조달청 캡처 중 오류: {e}", file=sys.stderr, flush=True)
        if os.path.exists(temp_full_path):
            try:
                os.remove(temp_full_path)
            except Exception:
                pass
    return None


def capture_tradingeconomics_chart(driver, metal_kr: str, te_slug: str, date_folder: str, today_str: str) -> Tuple[Optional[str], Optional[float]]:
    """Trading Economics에서 로딩 완료를 감지하여 1년 종가 차트 영역 캡처 및 최종 종가 추출"""
    if not driver:
        return None, None

    te_url = f"https://tradingeconomics.com/commodity/{te_slug}"
    final_img_name = f"[{metal_kr}]_1년_시세차트_{today_str}.png"
    final_img_path = os.path.join(date_folder, final_img_name)
    latest_price = None

    try:
        driver.set_window_size(1280, 1400)
        driver.get(te_url)

        # 핵심: 차트 데이터(SVG/Highcharts 시리즈) 렌더링이 완료될 때까지 명시적 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#chart .highcharts-series, #chart svg"))
        )
        # 애니메이션 안착을 위해 2초 대기
        time.sleep(2)

        # Highcharts 차트 데이터에서 최종 종가 수치 추출
        try:
            extracted_price = driver.execute_script("""
                try {
                    var c = Highcharts.charts.find(function(x) { return x && x.series && x.series[0] && x.series[0].points; });
                    if (c && c.series[0].points.length > 0) {
                        return c.series[0].points.slice(-1)[0].y;
                    }
                    return null;
                } catch(e) {
                    return null;
                }
            """)
            if extracted_price is not None:
                latest_price = float(extracted_price)
        except Exception:
            pass

        # 상단 네비게이션/헤더/배너 등 고정(sticky) 요소가 차트 상단을 가리는 현상 제거
        driver.execute_script("""
            var elements = document.querySelectorAll('header, nav, .navbar, .header, [class*="navbar"], [class*="sticky"], .ad, [id*="banner"], [class*="banner"], a[href*="join"]');
            elements.forEach(function(e) { e.remove(); });
        """)
        time.sleep(0.5)

        chart_el = driver.find_element(By.CSS_SELECTOR, "#chart")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chart_el)
        time.sleep(1)
        chart_el.screenshot(final_img_path)

        price_disp = f" (최종종가: {latest_price})" if latest_price is not None else ""
        print(f"    -> [차트 완료] 1년 시세 차트 캡처 성공: {final_img_name}{price_disp}", flush=True)
        return final_img_name, latest_price
    except Exception as e:
        print(f"    [경고] {metal_kr} 차트 캡처 실패 ({e})", file=sys.stderr, flush=True)
    return None, None


def fetch_mining_com_feed() -> List[Dict[str, Any]]:
    """Mining.com 공식 RSS 피드 수집"""
    url = "https://www.mining.com/feed/"
    articles = []
    try:
        req = urllib.request.Request(url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pubdate_elem = item.find("pubDate")
                desc_elem = item.find("description")
                categories = [cat.text.strip().lower() for cat in item.findall("category") if cat.text]

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_str = pubdate_elem.text.strip() if pubdate_elem is not None and pubdate_elem.text else ""
                desc = clean_html(desc_elem.text) if desc_elem is not None and desc_elem.text else ""

                pub_dt = None
                if pub_str:
                    try:
                        pub_dt = parsedate_to_datetime(pub_str)
                    except Exception:
                        pass

                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "pub_date": pub_dt,
                        "pub_str": pub_str,
                        "description": desc,
                        "categories": categories,
                        "source": "Mining.com (공식 피드)",
                    })
        print(f"    -> 총 {len(articles)}개 기사 확보", flush=True)
    except Exception as e:
        print(f"[경고] Mining.com 피드 수집 중 오류: {e}", file=sys.stderr, flush=True)
    return articles


def fetch_google_news_rss(query: str, days: int = 2, source_filter: str = "") -> List[Dict[str, Any]]:
    """Google News RSS를 통해 추가 기사 검색"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}+when:{days}d&hl=en-US&gl=US&ceid=US:en"
    articles = []

    try:
        req = urllib.request.Request(url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pubdate_elem = item.find("pubDate")
                desc_elem = item.find("description")
                source_elem = item.find("source")

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_str = pubdate_elem.text.strip() if pubdate_elem is not None and pubdate_elem.text else ""
                source_name = source_elem.text.strip() if source_elem is not None and source_elem.text else "Google News"
                desc = clean_html(desc_elem.text) if desc_elem is not None and desc_elem.text else ""

                if source_filter and source_filter.lower() not in source_name.lower() and source_filter.lower() not in link.lower():
                    continue

                pub_dt = None
                if pub_str:
                    try:
                        pub_dt = parsedate_to_datetime(pub_str)
                    except Exception:
                        pass

                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "pub_date": pub_dt,
                        "pub_str": pub_str,
                        "description": desc,
                        "categories": [],
                        "source": f"{source_name} (검색 수집)",
                    })
    except Exception as e:
        print(f"[경고] Google News 수집 실패 ({query}): {e}", file=sys.stderr, flush=True)

    return articles


def is_article_relevant(article: Dict[str, Any], metal_key: str) -> bool:
    """기사가 해당 금속 자원과 직접적으로 관련되어 있는지 검증"""
    metal_info = TARGET_METALS[metal_key]
    keywords = metal_info["keywords"]

    text_to_check = f"{article['title']} {article['description']} {' '.join(article.get('categories', []))}".lower()

    if metal_key == "lead":
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_to_check):
                return True
        return False

    for kw in keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text_to_check):
            return True

    return False


def collect_metal_news(days: int = 2) -> Dict[str, List[Dict[str, Any]]]:
    """Mining.com 및 Google News에서 7개 자원 뉴스 수집 및 분류"""
    classified: Dict[str, List[Dict[str, Any]]] = {k: [] for k in TARGET_METALS}
    seen_titles = {k: set() for k in TARGET_METALS}

    def add_if_unique(m_key: str, art: Dict[str, Any]):
        t_clean = re.sub(r"[^a-zA-Z0-9가-힣]", "", art["title"]).lower()
        if t_clean not in seen_titles[m_key]:
            seen_titles[m_key].add(t_clean)
            classified[m_key].append(art)

    # 1. Mining.com 공식 RSS 피드 수집
    print(f"[*] Mining.com 최신 뉴스 피드 가져오는 중...", flush=True)
    mining_feed = fetch_mining_com_feed()

    threshold = datetime.now(timezone.utc) - timedelta(days=days)
    for art in mining_feed:
        if art["pub_date"] and art["pub_date"] < threshold:
            continue
        for metal_key in TARGET_METALS:
            if is_article_relevant(art, metal_key):
                add_if_unique(metal_key, art)

    # 2. 추가 뉴스 검색
    for metal_key in TARGET_METALS:
        query = TARGET_METALS[metal_key]["primary_query"]
        extra = fetch_google_news_rss(query, days=days)
        for art in extra:
            if is_article_relevant(art, metal_key):
                add_if_unique(metal_key, art)

    return classified


def call_gemma_analysis(metal_name: str, articles: List[Dict[str, Any]]) -> str:
    """로컬 Gemma 4 (Ollama)를 호출하여 기사 요약 및 향후 시장 여파 분석 코멘트 생성"""
    if not articles:
        return (
            "**1. 이슈 판정**: **[특이 이슈 없음]**\n\n"
            "- 최근 24~48시간 동안 글로벌 시장을 흔드는 특이 뉴스나 급변 동향이 없습니다.\n"
            "- **향후 여파 코멘트**: 현재 글로벌 수급과 가격이 비교적 안정적인 보합세를 유지하고 있어, 국내 자동차 부품 및 스크랩 유통 시장에서도 단기적인 가격 급변보다는 기존 재고 순환 위주의 안정적 흐름이 이어질 것으로 판단됩니다."
        )

    articles_text = ""
    for idx, art in enumerate(articles[:3], 1):
        articles_text += f"[기사 {idx}]\n"
        articles_text += f"- 제목: {art['title']}\n"
        articles_text += f"- 출처: {art.get('source', 'Mining.com')}\n"
        if art.get('description'):
            articles_text += f"- 내용 요약: {art['description'][:250]}\n"
        articles_text += f"- 링크: {art['link']}\n\n"

    prompt = f"""당신은 원자재/비철금속 시장 및 자동차 부품(촉매, 알터네이터, 배터리, 휠, 차체 등)·고철·비철 유통 전문 수석 애널리스트입니다.
아래는 [{metal_name}] 관련 최근 글로벌 주요 뉴스입니다:

{articles_text}

이 뉴스들을 종합 분석하여, 실무자(블로그 작성자)가 시장을 파악하고 향후 글을 작성할 때 참고할 수 있도록 [핵심 뉴스 요약 및 향후 여파 코멘트]를 한국어로 작성해 주세요.
불필요한 인사말이나 상투적인 블로그용 서두/제목 추천/해시태그는 완전히 배제하고, 철저히 '객관적 팩트 요약'과 '향후 시장 및 부품·스크랩 업계에 미칠 실무적 영향 코멘트'에 집중해 주세요.

반드시 아래 형식에 맞춰 명확하게 작성해 주세요:

**1. 이슈 판정**: [중요 이슈 발생 / 단순 시황 / 특이 이슈 없음] 중 택1 (한 줄 사유)
**2. 핵심 내용 요약**: 기사들의 핵심 사건과 수급 변화를 1~3개 글머리 기호로 명료하게 요약
**3. 향후 시장 여파 및 전망 코멘트**:
   - **원자재 가격 및 글로벌 수급 여파**: (단기/중기 가격 전망, 글로벌 공급망 및 광산/제련소 동향)
   - **자동차 부품 및 스크랩 유통 영향**: (국내 고철/비철 유통 단가, 폐차 부품 매입·매매가, 재생/재활용 시장에 미칠 실무적 파급 효과)
"""

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
        }
    }

    try:
        req = urllib.request.Request(
            OLLAMA_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
    except Exception as e:
        return f"[오류] 로컬 Gemma 4 모델 호출 실패 ({e})\n(Ollama가 켜져 있는지 확인해 주세요.)"


def markdown_to_html_simple(md_text: str) -> str:
    """간단한 마크다운 문법(굵게, 기울임, 불릿 리스트, 줄바꿈)을 깔끔한 HTML로 변환"""
    if not md_text:
        return ""
    lines = md_text.split("\n")
    html_lines = []
    in_ul = False
    for line in lines:
        line_s = line.strip()
        if not line_s:
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            continue
        line_s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_s)
        line_s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_s)

        if line_s.startswith("- ") or line_s.startswith("* "):
            if not in_ul:
                html_lines.append('<ul style="margin: 8px 0 12px 0; padding-left: 22px; line-height: 1.7; color: #374151;">')
                in_ul = True
            item_text = line_s[2:].strip()
            html_lines.append(f"<li style='margin-bottom: 4px;'>{item_text}</li>")
        else:
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f'<p style="margin: 8px 0; line-height: 1.7; color: #374151;">{line_s}</p>')
    if in_ul:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def build_html_report(
    today_str: str,
    now_kst: str,
    usd_krw_rate: float,
    exchange_source: str,
    pps_img_name: Optional[str],
    price_table_items: List[Dict[str, Any]],
    metal_detail_objs: List[Dict[str, Any]],
    csv_filename: str,
    output_html_path: str
):
    """네이버 블로그 복사 100% 호환 표 및 대시보드를 갖춘 단일 통합 HTML 브리핑 보고서 생성"""

    # 1. 네이버 블로그에 복사해서 붙여넣어도 절대 깨지지 않는 인라인 스타일의 Table HTML
    price_rows_html = []
    for p in price_table_items:
        price_rows_html.append(f"""
        <tr style="border-bottom: 1px solid #e5e7eb; transition: background-color 0.2s;">
            <td style="padding: 12px 8px; border: 1px solid #dee2e6; text-align: center; background-color: #f9fafb; font-weight: 600;">{p['emoji']} {p['type_label']}</td>
            <td style="padding: 12px 8px; border: 1px solid #dee2e6; text-align: center; font-weight: bold; color: #111827;">{p['name_kr']}</td>
            <td style="padding: 12px 8px; border: 1px solid #dee2e6; text-align: center; color: #6b7280; font-size: 13px;">{p['name_en']}</td>
            <td style="padding: 12px 8px; border: 1px solid #dee2e6; text-align: center; font-family: monospace; font-size: 14px;">{p['price_raw']}</td>
            <td style="padding: 12px 8px; border: 1px solid #dee2e6; text-align: center; font-weight: bold; color: #1d4ed8; font-size: 15px; background-color: #eff6ff;">{p['krw_price']}</td>
            <td style="padding: 12px 8px; border: 1px solid #dee2e6; text-align: center; font-weight: bold; color: #b45309; font-size: 15px; background-color: #fffbeb;">{p['scrap_range']}</td>
            <td style="padding: 12px 8px; border: 1px solid #dee2e6; text-align: center; color: #4b5563; font-weight: 500;">{p['unit_krw']}</td>
        </tr>""")

    price_table_html = f"""
    <table id="naver-copy-table" style="border-collapse: collapse; width: 100%; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; font-size: 14px; text-align: center; margin: 16px 0; border: 2px solid #9ca3af; background-color: #ffffff;">
        <thead>
            <tr style="background-color: #f3f4f6; border-bottom: 2px solid #4b5563;">
                <th style="padding: 12px 8px; border: 1px solid #dee2e6; font-weight: bold; color: #1f2937;">구분</th>
                <th style="padding: 12px 8px; border: 1px solid #dee2e6; font-weight: bold; color: #1f2937;">자원명</th>
                <th style="padding: 12px 8px; border: 1px solid #dee2e6; font-weight: bold; color: #1f2937;">영문명</th>
                <th style="padding: 12px 8px; border: 1px solid #dee2e6; font-weight: bold; color: #1f2937;">국제 종가</th>
                <th style="padding: 12px 8px; border: 1px solid #dee2e6; font-weight: bold; color: #1d4ed8;">원화 환산 시장가</th>
                <th style="padding: 12px 8px; border: 1px solid #dee2e6; font-weight: bold; color: #b45309;">♻️ 스크랩 매입 추정가 (70~80%)</th>
                <th style="padding: 12px 8px; border: 1px solid #dee2e6; font-weight: bold; color: #1f2937;">단위</th>
            </tr>
        </thead>
        <tbody>
            {''.join(price_rows_html)}
        </tbody>
    </table>
    """

    # 2. 7대 자원별 상세 섹션 HTML
    metal_cards_html = []
    for m in metal_detail_objs:
        anchor_id = f"metal-{m['idx']}"
        articles_html = []
        if m["articles"]:
            for art in m["articles"][:5]:
                articles_html.append(f"""
                <li style="margin-bottom: 12px;">
                    <a href="{art['link']}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: bold; font-size: 15px; display: inline-block;">{art['title']} ↗</a>
                    <div style="font-size: 13px; color: #6b7280; margin: 3px 0;">출처: <span style="color: #4b5563; font-weight: 500;">{art.get('source', 'Mining.com')}</span> | 일시: {art.get('pub_str', '-')}</div>
                    {f'<div style="font-size: 13.5px; color: #4b5563; line-height: 1.5; background: #f9fafb; padding: 6px 10px; border-radius: 4px; margin-top: 4px;">{art["description"][:220]}...</div>' if art.get("description") else ""}
                </li>""")
        else:
            articles_html.append("<li style='color: #6b7280;'>최근 24~48시간 이내에 보도된 직접적인 특이 기사가 없습니다.</li>")

        chart_block = ""
        if m.get("chart_img_name"):
            chart_block = f"""
            <div style="margin: 18px 0; text-align: center; background: #ffffff; padding: 14px; border-radius: 8px; border: 1px solid #e5e7eb;">
                <div style="font-weight: 600; font-size: 14px; color: #4b5563; margin-bottom: 8px; text-align: left;">📈 Trading Economics 1년 종가 시세 차트</div>
                <img src="./{urllib.parse.quote(m['chart_img_name'])}" alt="{m['name_kr']} 차트" style="max-width: 100%; height: auto; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                <div style="font-size: 12px; color: #9ca3af; margin-top: 6px; text-align: right;"><a href="https://tradingeconomics.com/commodity/{m['te_slug']}" target="_blank" style="color: #9ca3af;">Trading Economics 바로가기 ↗</a></div>
            </div>"""

        ai_formatted = markdown_to_html_simple(m.get("ai_content", ""))

        card_html = f"""
        <div id="{anchor_id}" class="metal-card" style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 28px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f3f4f6; padding-bottom: 12px; margin-bottom: 16px;">
                <h2 style="margin: 0; font-size: 22px; color: #111827;">{m['emoji']} {m['idx']}. {m['name_kr']} <span style="font-size: 16px; color: #6b7280; font-weight: normal;">({m['name_en']})</span></h2>
                <span style="background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">{m['type_label']}</span>
            </div>

            <!-- 단가 뱃지 -->
            <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 18px;">
                <div style="background: #f3f4f6; padding: 10px 14px; border-radius: 8px; flex: 1; min-width: 160px;">
                    <div style="font-size: 12px; color: #6b7280;">국제 종가</div>
                    <div style="font-size: 16px; font-weight: bold; color: #111827; margin-top: 2px;">{m['price_raw_str']}</div>
                </div>
                <div style="background: #eff6ff; padding: 10px 14px; border-radius: 8px; flex: 1; min-width: 180px; border: 1px solid #bfdbfe;">
                    <div style="font-size: 12px; color: #1d4ed8; font-weight: 500;">원화 환산 시장가</div>
                    <div style="font-size: 17px; font-weight: bold; color: #1e40af; margin-top: 2px;">{f"{int(round(m['krw_unit_price'])):,} {m['unit_krw']}" if m.get('krw_unit_price') else "-"}</div>
                </div>
                <div style="background: #fffbeb; padding: 10px 14px; border-radius: 8px; flex: 1; min-width: 200px; border: 1px solid #fde68a;">
                    <div style="font-size: 12px; color: #b45309; font-weight: 500;">♻️ 스크랩 매입 추정가 (70~80%)</div>
                    <div style="font-size: 17px; font-weight: bold; color: #92400e; margin-top: 2px;">{f"{int(round(m['scrap_70'])):,} ~ {int(round(m['scrap_80'])):,} {m['unit_krw']}" if m.get('scrap_70') else "-"}</div>
                </div>
            </div>

            <!-- 차트 -->
            {chart_block}

            <!-- 뉴스 목록 -->
            <div style="margin: 18px 0;">
                <h3 style="font-size: 16px; color: #1f2937; margin-bottom: 10px;">📰 최근 주요 뉴스 요약 및 출처 ({len(m['articles'])}건)</h3>
                <ul style="padding-left: 20px; margin: 0;">
                    {''.join(articles_html)}
                </ul>
            </div>

            <!-- Gemma 4 분석 -->
            <div style="margin-top: 20px; background: #f8fafc; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 0 8px 8px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h3 style="font-size: 16px; color: #1e3a8a; margin: 0;">🔍 시장 분석 및 향후 여파 코멘트 (Gemma 4)</h3>
                    <button onclick="copySectionText('{anchor_id}-analysis')" style="padding: 4px 10px; font-size: 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">📋 분석 텍스트 복사</button>
                </div>
                <div id="{anchor_id}-analysis">
                    {ai_formatted}
                </div>
            </div>
        </div>"""
        metal_cards_html.append(card_html)

    # 3. 종합 네비게이션 목차 행
    nav_rows_html = []
    for m in metal_detail_objs:
        nav_rows_html.append(f"""
        <tr style="border-bottom: 1px solid #f3f4f6;">
            <td style="padding: 10px; text-align: center; color: #6b7280;">{m['idx']}</td>
            <td style="padding: 10px; font-weight: bold;"><a href="#metal-{m['idx']}" style="color: #111827; text-decoration: none;">{m['emoji']} {m['name_kr']}</a></td>
            <td style="padding: 10px; color: #6b7280; font-size: 13px;">{m['name_en']}</td>
            <td style="padding: 10px; text-align: center; font-weight: 600; color: #1d4ed8;">{f"{int(round(m['krw_unit_price'])):,} {m['unit_krw']}" if m.get('krw_unit_price') else "-"}</td>
            <td style="padding: 10px; text-align: center; font-weight: 600; color: #b45309;">{f"{int(round(m['scrap_70'])):,} ~ {int(round(m['scrap_80'])):,} {m['unit_krw']}" if m.get('scrap_70') else "-"}</td>
            <td style="padding: 10px; text-align: center; color: #4b5563;">{len(m['articles'])}건</td>
            <td style="padding: 10px; text-align: center;"><a href="#metal-{m['idx']}" style="color: #2563eb; font-weight: 500; text-decoration: none;">이동 ↓</a></td>
        </tr>""")

    # 4. 전체 HTML 템플릿 완성
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>7대 금속·원자재 일일 통합 브리핑 ({today_str})</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 24px 16px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 1020px;
            width: 100%;
        }}
        .btn-copy-main {{
            background: linear-gradient(135deg, #03c75a 0%, #02b04f 100%);
            color: white;
            border: none;
            padding: 12px 22px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(3, 199, 90, 0.3);
            transition: transform 0.1s, box-shadow 0.1s;
        }}
        .btn-copy-main:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(3, 199, 90, 0.4);
        }}
        .btn-copy-main:active {{
            transform: translateY(0);
        }}
        .toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1e293b;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: none;
            z-index: 9999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 메인 헤더 -->
        <header style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h1 style="margin: 0; font-size: 26px; color: #0f172a;">📊 7대 금속·원자재 일일 통합 브리핑</h1>
                    <div style="margin-top: 6px; color: #64748b; font-size: 14px;">발행일시: <strong>{today_str} ({now_kst})</strong> | 위치: <code>thepathlab/resources/{today_str}/</code></div>
                </div>
                <div style="background: #f1f5f9; padding: 8px 14px; border-radius: 8px; font-size: 13px; color: #334155; text-align: right;">
                    <div>기준 환율: <strong style="color: #0284c7;">1 USD = {usd_krw_rate:,.1f}원</strong></div>
                    <div style="font-size: 11px; color: #64748b;">출처: {exchange_source}</div>
                </div>
            </div>
            <div style="margin-top: 14px; padding-top: 14px; border-top: 1px solid #f1f5f9; font-size: 13.5px; color: #475569; display: flex; justify-content: space-between; align-items: center;">
                <span>💡 블로그 글 작성 시 아래 표나 각 자원별 분석 텍스트를 복사하여 활용하세요.</span>
                <a href="./{urllib.parse.quote(csv_filename)}" download style="color: #0284c7; text-decoration: none; font-weight: 500;">📥 원본 시세 CSV 다운로드</a>
            </div>
        </header>

        <!-- 조달청 가격표 섹션 -->
        {f'''
        <section style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <h2 style="margin: 0; font-size: 18px; color: #1e293b;">🏛️ 오늘자 조달청(PPS) 원자재 판매가격 고시표</h2>
                <a href="https://www.pps.go.kr/bichuk/index.do" target="_blank" style="font-size: 13px; color: #2563eb; text-decoration: none; font-weight: 500;">조달청 비축물자 누리집 바로가기 ↗</a>
            </div>
            <div style="text-align: center; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;">
                <img src="./{urllib.parse.quote(pps_img_name)}" alt="조달청 판매가격표" style="max-width: 100%; height: auto; border-radius: 6px;">
            </div>
        </section>
        ''' if pps_img_name else ""}

        <!-- 💰 복사용 네이버 블로그 표 섹션 -->
        <section style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 1px solid #e2e8f0; border-top: 4px solid #03c75a;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;">
                <div>
                    <h2 style="margin: 0; font-size: 20px; color: #0f172a;">💰 7대 금속·원자재 원화 환산 시장가 및 스크랩 매입 추정가</h2>
                    <div style="color: #64748b; font-size: 13px; margin-top: 4px;">네이버 블로그 스마트에디터에 100% 호환되는 표준 HTML 테이블입니다.</div>
                </div>
                <button onclick="copyPriceTable()" class="btn-copy-main">📋 네이버 블로그용 표 클립보드 복사</button>
            </div>

            <!-- 안내 배너 -->
            <div style="background: #f8fafc; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; font-size: 13px; line-height: 1.6; color: #475569; border: 1px solid #e2e8f0;">
                • <strong>환산 기준</strong>: PGM(팔라듐·로듐·백금)은 <strong>g당 원화 단가(원/g)</strong>, 일반 금속(철스크랩·알루미늄·구리·납)은 <strong>kg당 원화 단가(원/kg)</strong> 환산<br>
                • <strong>♻️ 스크랩 매입 추정가 (70~80%)</strong>: 원자재 순수 시세 대비 가공·정제 마진 및 감모율을 감안하여 통상 시장 시세의 <strong>70% ~ 80% 수준</strong>으로 형성됩니다.<br>
                • <strong>복사 방법</strong>: 위 초록색 <strong>[표 클립보드 복사]</strong> 버튼을 누르거나, 표 전체를 마우스로 드래그(Ctrl+C)한 뒤 네이버 블로그에 Ctrl+V 하시면 깨짐 없이 깔끔하게 표로 붙여넣어집니다.
            </div>

            <!-- 실제 복사 대상 테이블 -->
            <div style="overflow-x: auto;">
                {price_table_html}
            </div>
            <div style="font-size: 12px; color: #94a3b8; text-align: right; margin-top: 6px;">* 본 환산 단가는 국제 종가 기준 이론가이며, 실제 스크랩 거래 시 품위(순도), 운송비, 제련비 등에 따라 차이가 발생할 수 있습니다.</div>
        </section>

        <!-- 📋 빠른 목차 네비게이션 -->
        <section style="background: white; border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
            <h2 style="margin: 0 0 14px 0; font-size: 17px; color: #1e293b;">📋 오늘자 7대 자원별 시황 요약 목차</h2>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="border-bottom: 2px solid #e2e8f0; color: #64748b; font-size: 13px;">
                            <th style="padding: 8px; text-align: center;">번호</th>
                            <th style="padding: 8px; text-align: left;">자원명</th>
                            <th style="padding: 8px; text-align: left;">영문명</th>
                            <th style="padding: 8px; text-align: center;">원화 환산 시장가</th>
                            <th style="padding: 8px; text-align: center;">스크랩 추정가 (70~80%)</th>
                            <th style="padding: 8px; text-align: center;">수집 기사</th>
                            <th style="padding: 8px; text-align: center;">바로가기</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(nav_rows_html)}
                    </tbody>
                </table>
            </div>
        </section>

        <!-- 7대 자원별 상세 카드 리스트 -->
        {''.join(metal_cards_html)}

        <footer style="text-align: center; color: #94a3b8; font-size: 13px; margin: 40px 0 20px 0;">
            ThePathLab Metal News Briefing System | Data Sources: Trading Economics, Mining.com, Naver Finance
        </footer>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => {{ t.style.display = 'none'; }}, 3000);
        }}

        function copyPriceTable() {{
            const table = document.getElementById('naver-copy-table');
            const range = document.createRange();
            range.selectNode(table);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            try {{
                document.execCommand('copy');
                window.getSelection().removeAllRanges();
                showToast('✅ 네이버 블로그용 표가 복사되었습니다! 네이버 글쓰기 화면에 Ctrl+V로 붙여넣으세요.');
            }} catch(e) {{
                alert('복사 실패: 표를 직접 마우스로 드래그하여 Ctrl+C 로 복사해 주세요.');
            }}
        }}

        function copySectionText(elementId) {{
            const el = document.getElementById(elementId);
            if (!el) return;
            const text = el.innerText;
            navigator.clipboard.writeText(text).then(() => {{
                showToast('📋 분석 코멘트 텍스트가 복사되었습니다!');
            }}).catch(() => {{
                const range = document.createRange();
                range.selectNode(el);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                document.execCommand('copy');
                window.getSelection().removeAllRanges();
                showToast('📋 분석 코멘트 텍스트가 복사되었습니다!');
            }});
        }}
    </script>
</body>
</html>
    """

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_all_metal_briefings(days: Optional[int] = None) -> str:
    """7대 자원 시세 차트 + 종가 수집 및 원화 환산(CSV) + 조달청 가격표 + 뉴스 요약 및 여파 코멘트를 HTML 대시보드와 마크다운으로 동시 생성"""
    now = datetime.now()
    if days is None:
        days = 3 if now.weekday() == 0 else 2

    today_str = now.strftime("%Y-%m-%d")
    now_kst = now.strftime("%Y-%m-%d %H:%M:%S")

    # 1. 날짜별 전용 서브폴더 생성: thepathlab/resources/YYYY-MM-DD/
    date_folder = os.path.join(RESOURCES_DIR, today_str)
    os.makedirs(date_folder, exist_ok=True)

    # 2. 최신 환율 정보 가져오기
    usd_krw_rate, exchange_source = fetch_usd_krw_rate()

    print(f"\n" + "=" * 68, flush=True)
    print(f"  🏭 7대 금속/원자재 일일 통합 브리핑 리포트 생성기", flush=True)
    print(f"  - 저장 폴더: thepathlab/resources/{today_str}/", flush=True)
    print(f"  - 기준 일시: {now_kst} (최근 {days}일 이내 기사)", flush=True)
    print(f"  - 적용 환율: 1 USD = {usd_krw_rate:,.1f}원 ({exchange_source})", flush=True)
    print(f"  - AI 분석  : {DEFAULT_MODEL} (Local Ollama)", flush=True)
    print(f"  - 차트 소스: Trading Economics (1년 종가)", flush=True)
    print(f"  - 국내 가격: 조달청(PPS) 비축물자 누리집", flush=True)
    print(f"  - 산출 방식: 네이버 블로그 복사용 HTML 대시보드 + 마크다운 + CSV 저장", flush=True)
    print(f"=" * 68 + "\n", flush=True)

    # 3. 브라우저 시작 (조달청 및 7개 차트 캡처에 공통 사용)
    driver = create_headless_browser()

    pps_img_name = None
    if driver:
        # 조달청 원자재 판매가격표 캡처
        pps_img_name = capture_pps_price_table(driver, date_folder, today_str)

    # 4. 뉴스 수집
    classified = collect_metal_news(days=days)

    total_metals = len(TARGET_METALS)
    metal_sections = []
    summary_table_rows = []
    price_table_items = []
    metal_detail_objs = []
    csv_rows = []

    # 5. 각 자원별 1년 차트 캡처 + 종가 추출 + 원화 환산 + Gemma 4 분석
    for idx, (key, info) in enumerate(TARGET_METALS.items(), 1):
        metal_kr = info["name_kr"]
        metal_en = info["name_en"]
        emoji = info.get("emoji", "📌")
        te_slug = info.get("te_slug", key)
        cat = info.get("category", "metal")
        unit_raw = info.get("unit_raw", "USD/T")
        unit_krw = info.get("unit_krw", "원/kg")
        type_label = info.get("type_label", "금속")
        articles = classified[key]

        print(f"\n[{idx}/{total_metals}] {emoji} [{metal_kr}] 데이터 정리 중...", flush=True)

        # 5-1. Trading Economics 1년 시세 차트 캡처 및 최종 종가 추출
        chart_img_name, latest_price = None, None
        if driver:
            chart_img_name, latest_price = capture_tradingeconomics_chart(driver, metal_kr, te_slug, date_folder, today_str)

        # 5-2. 원화 및 스크랩(70~80%) 단가 환산 계산
        if latest_price is not None:
            if cat == "metal":
                # USD/T -> 1T = 1,000kg
                krw_unit_price = (latest_price * usd_krw_rate) / 1000.0
                price_raw_str = f"${latest_price:,.2f} / T"
            elif cat == "copper_lbs":
                # USD/Lbs -> 1 lb = 0.45359237 kg
                krw_unit_price = (latest_price * usd_krw_rate) / 0.45359237
                price_raw_str = f"${latest_price:,.4f} / Lb"
            elif cat == "pgm":
                # USD/t.oz -> 1 t.oz = 31.1034768 g
                krw_unit_price = (latest_price * usd_krw_rate) / 31.1034768
                price_raw_str = f"${latest_price:,.2f} / oz"
            else:
                krw_unit_price = (latest_price * usd_krw_rate) / 1000.0
                price_raw_str = f"${latest_price:,.2f}"

            scrap_70 = krw_unit_price * 0.70
            scrap_80 = krw_unit_price * 0.80
            krw_price_disp = f"**{int(round(krw_unit_price)):,}원**"
            scrap_range_disp = f"**{int(round(scrap_70)):,}원 ~ {int(round(scrap_80)):,}원**"

            csv_rows.append([
                today_str, type_label, metal_kr, metal_en,
                latest_price, unit_raw, round(usd_krw_rate, 2), exchange_source,
                unit_krw, int(round(krw_unit_price)), int(round(scrap_70)), int(round(scrap_80))
            ])
        else:
            krw_unit_price = None
            scrap_70 = None
            scrap_80 = None
            price_raw_str = "-"
            krw_price_disp = "-"
            scrap_range_disp = "-"
            csv_rows.append([
                today_str, type_label, metal_kr, metal_en,
                "-", unit_raw, round(usd_krw_rate, 2), exchange_source,
                unit_krw, "-", "-", "-"
            ])

        price_table_items.append({
            "idx": idx,
            "key": key,
            "name_kr": metal_kr,
            "name_en": metal_en,
            "emoji": emoji,
            "type_label": type_label,
            "price_raw": price_raw_str,
            "krw_price": krw_price_disp,
            "scrap_range": scrap_range_disp,
            "unit_krw": unit_krw,
            "latest_price": latest_price,
        })

        # 5-3. Gemma 4 분석 (핵심 요약 + 향후 여파 코멘트)
        print(f"    -> AI 팩트 요약 및 향후 여파 코멘트 분석 중...", flush=True)
        if articles:
            ai_content = call_gemma_analysis(metal_kr, articles)
        else:
            ai_content = (
                "**1. 이슈 판정**: **[특이 이슈 없음]**\n\n"
                f"- 최근 {days}일 동안 주요 시장 교란 요인이나 대형 이슈 기사가 없습니다.\n"
                "- **향후 여파 코멘트**: 현재 수급과 가격이 비교적 안정적인 보합 흐름을 유지하고 있어, 국내 자동차 부품 및 스크랩 유통 시장에서도 단기적인 가격 급변보다는 기존 재고 순환 위주의 안정적 흐름이 이어질 것으로 전망됩니다."
            )

        # 목차 테이블 행 데이터
        section_anchor = f"{idx}-{metal_kr.replace('·', '').replace(' ', '-')}-{metal_en.lower().replace(' ', '-')}"
        chart_link = f"[차트보기](#차트-{idx})" if chart_img_name else "-"
        summary_table_rows.append(
            f"| {idx} | {emoji} **{metal_kr}** | {metal_en} | {krw_price_disp} ({unit_krw}) | {scrap_range_disp} | {len(articles)}건 | {chart_link} | [상세 분석](#{section_anchor}) |"
        )

        # 5-4. 각 자원별 상세 섹션 마크다운 구성
        sec_lines = [
            f"---",
            f"",
            f"## <a id=\"{section_anchor}\"></a>{idx}. {emoji} {metal_kr} ({metal_en})",
            f"",
            f"### 💵 원화 환산 시세 및 스크랩 추정 단가",
            f"- **국제 시장 종가**: `{price_raw_str}`",
            f"- **원화 환산 시장가**: **{int(round(krw_unit_price)):,} {unit_krw}** *(적용 환율: {usd_krw_rate:,.1f}원 | 출처: {exchange_source})*" if krw_unit_price else f"- **원화 환산 시장가**: -",
            f"- **♻️ 스크랩 매입 추정가 (70~80%)**: **{int(round(scrap_70)):,} ~ {int(round(scrap_80)):,} {unit_krw}**" if scrap_70 else f"- **♻️ 스크랩 매입 추정가 (70~80%)**: -",
            f"",
        ]

        # 1년 시세 차트 이미지 임베드
        if chart_img_name:
            sec_lines.extend([
                f"### <a id=\"차트-{idx}\"></a>📈 1년 시세 추이 및 전일 종가 (Trading Economics)",
                f"",
                f"![{metal_kr} 1년 시세 차트](./{urllib.parse.quote(chart_img_name)})",
                f"",
                f"*데이터 출처: [Trading Economics - {metal_kr}](https://tradingeconomics.com/commodity/{te_slug})*",
                f"",
            ])

        # 수집된 기사 목록 및 원문 링크
        sec_lines.extend([
            f"### 📰 수집된 최근 주요 기사 및 출처 ({len(articles)}건)",
            f"",
        ])

        if articles:
            for art in articles[:5]:
                sec_lines.append(f"- **[{art['title']}]({art['link']})**")
                sec_lines.append(f"  - **출처**: {art.get('source', 'Mining.com')} | **일시**: {art.get('pub_str', '-')}")
                if art.get('description'):
                    sec_lines.append(f"  - **요약**: {art['description'][:220]}...")
                sec_lines.append(f"")
        else:
            sec_lines.append(f"- 최근 24~48시간 이내에 보도된 직접적인 특이 기사가 없습니다.\n")

        # Gemma 4 시장 분석 및 향후 여파 코멘트
        sec_lines.extend([
            f"### 🔍 시장 분석 및 향후 여파 코멘트 (Gemma 4)",
            f"",
            f"{ai_content}",
            f"",
        ])

        metal_sections.append("\n".join(sec_lines))

        metal_detail_objs.append({
            "idx": idx,
            "key": key,
            "name_kr": metal_kr,
            "name_en": metal_en,
            "emoji": emoji,
            "te_slug": te_slug,
            "type_label": type_label,
            "chart_img_name": chart_img_name,
            "price_raw_str": price_raw_str,
            "krw_unit_price": krw_unit_price,
            "scrap_70": scrap_70,
            "scrap_80": scrap_80,
            "unit_krw": unit_krw,
            "articles": articles,
            "ai_content": ai_content,
        })

    # 브라우저 종료
    if driver:
        try:
            driver.quit()
        except Exception:
            pass

    # 6. CSV 파일 저장: 7대자원_환산시세_YYYY-MM-DD.csv
    csv_filename = f"7대자원_환산시세_{today_str}.csv"
    csv_path = os.path.join(date_folder, csv_filename)
    try:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "날짜", "구분", "자원명", "영문명", "국제종가", "국제단위",
                "적용환율(원/달러)", "환율출처", "환산단위", "원화시장단가(원)",
                "스크랩추정_70%(원)", "스크랩추정_80%(원)"
            ])
            for r in csv_rows:
                writer.writerow(r)
        print(f"    -> [CSV 완료] 시세 환산 데이터 저장: {csv_filename}", flush=True)
    except Exception as e:
        print(f"[경고] CSV 저장 실패: {e}", file=sys.stderr, flush=True)

    # 7. 단일 통합 브리핑 마크다운 파일 조립
    doc_lines = [
        f"# 📊 7대 금속·원자재 일일 통합 브리핑 ({today_str})",
        f"",
        f"> **발행일시**: {today_str} ({now_kst})  ",
        f"> **문서 목적**: 블로그 포스팅 작성 참고용 원자재 시황·뉴스 요약 & 여파 분석 리포트  ",
        f"> **저장 위치**: `thepathlab/resources/{today_str}/`  ",
        f"",
        f"---",
        f"",
    ]

    # 조달청 판매가격표 상단 배치
    if pps_img_name:
        doc_lines.extend([
            f"## 🏛️ 오늘자 조달청(PPS) 원자재 판매가격 고시표",
            f"",
            f"![조달청 비축물자 판매가격표](./{urllib.parse.quote(pps_img_name)})",
            f"",
            f"*실시간 확인: [조달청 비축물자 누리집 바로가기](https://www.pps.go.kr/bichuk/index.do)*",
            f"",
            f"---",
            f"",
        ])

    # 💰 원화 환산 시장가 및 스크랩 매입 추정가 테이블 (복사용)
    doc_lines.extend([
        f"## 💰 7대 금속·원자재 원화 환산 시장가 및 스크랩 매입 추정가 (복사용)",
        f"",
        f"> **적용 환율**: **1 USD = {usd_krw_rate:,.1f}원** (출처: {exchange_source})  ",
        f"> **환산 기준 안내**:  ",
        f"> - **PGM(팔라듐·로듐·백금)**: **g당 원화 단가(원/g)** 기준 환산 (1 troy oz = 31.1035g)  ",
        f"> - **일반 금속(철스크랩·알루미늄·구리·납)**: **kg당 원화 단가(원/kg)** 기준 환산  ",
        f"> - **♻️ 스크랩 매입 추정 시세**: 원자재 순수 시세 대비 가공·정제 마진 및 감모율을 감안하여 **통상 시장 시세의 70% ~ 80% 수준**으로 형성됩니다.  ",
        f"> - *💡 블로그 글 작성 시 아래 표 영역을 드래그하여 그대로 복사(Ctrl+C)해 붙여넣으실 수 있습니다.*  ",
        f"",
        f"| 구분 | 자원명 | 영문명 | 국제 종가 | 원화 환산 시장가 | ♻️ 스크랩 매입 추정가 (70~80%) | 단위 |",
        f"| :---: | :--- | :--- | :---: | :---: | :---: | :---: |",
    ])

    for p in price_table_items:
        doc_lines.append(
            f"| {p['emoji']} {p['type_label']} | **{p['name_kr']}** | {p['name_en']} | {p['price_raw']} | {p['krw_price']} | {p['scrap_range']} | {p['unit_krw']} |"
        )

    doc_lines.extend([
        f"",
        f"*※ 본 환산 단가는 국제 종가 기준 이론가이며, 실제 스크랩 거래 시 품위(순도), 운송비, 제련·가공비 등에 따라 차이가 발생할 수 있습니다.*  ",
        f"*※ 전체 데이터 CSV 저장 파일: [`{csv_filename}`](./{urllib.parse.quote(csv_filename)})*",
        f"",
        f"---",
        f"",
    ])

    # 7대 자원 목차 네비게이션 테이블
    doc_lines.extend([
        f"## 📋 7대 자원별 시황 요약 목차",
        f"",
        f"| 번호 | 자원명 | 영문명 | 원화 환산 시장가 | 스크랩 추정가 (70~80%) | 수집 기사 | 1년 차트 | 바로가기 |",
        f"| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |",
    ])
    doc_lines.extend(summary_table_rows)
    doc_lines.append("")

    # 7개 자원 상세 섹션 합치기
    doc_lines.extend(metal_sections)

    # 단일 통합 파일 저장: [통합브리핑] 7대_금속원자재_YYYY-MM-DD.md
    consolidated_filename = f"[통합브리핑] 7대_금속원자재_{today_str}.md"
    consolidated_path = os.path.join(date_folder, consolidated_filename)

    with open(consolidated_path, "w", encoding="utf-8") as f:
        f.write("\n".join(doc_lines))

    # 8. 단일 통합 브리핑 HTML 대시보드 파일 생성 (네이버 블로그 복사용)
    consolidated_html_filename = f"[통합브리핑] 7대_금속원자재_{today_str}.html"
    consolidated_html_path = os.path.join(date_folder, consolidated_html_filename)
    try:
        build_html_report(
            today_str=today_str,
            now_kst=now_kst,
            usd_krw_rate=usd_krw_rate,
            exchange_source=exchange_source,
            pps_img_name=pps_img_name,
            price_table_items=price_table_items,
            metal_detail_objs=metal_detail_objs,
            csv_filename=csv_filename,
            output_html_path=consolidated_html_path,
        )
    except Exception as e:
        print(f"[경고] HTML 브리핑 생성 실패: {e}", file=sys.stderr, flush=True)

    # 9. 메인 웹사이트(index.html & sitemap.xml) 최신화
    try:
        from site_generator import build_website_index
        build_website_index()
    except Exception as e:
        print(f"[경고] 메인 웹사이트 index.html 생성 실패: {e}", file=sys.stderr, flush=True)

    print(f"\n" + "=" * 68, flush=True)
    print(f" ✨ 7대 금속·원자재 단일 통합 브리핑 파일 생성 완료!", flush=True)
    print(f" 저장 폴더: {date_folder}", flush=True)
    print(f"   - 🌐 {consolidated_html_filename} (★네이버 블로그 표 복사용 HTML 대시보드)", flush=True)
    print(f"   - 📄 {consolidated_filename} (마크다운 원문)", flush=True)
    print(f"   - 📊 {csv_filename} (엑셀용 환산 시세)", flush=True)
    if pps_img_name:
        print(f"   - 🏛️ {pps_img_name}", flush=True)
    for key, info in TARGET_METALS.items():
        chart_name = f"[{info['name_kr']}]_1년_시세차트_{today_str}.png"
        print(f"   - 📈 {chart_name}", flush=True)
    print(f"=" * 68 + "\n", flush=True)

    return date_folder


if __name__ == "__main__":
    days_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("--days="):
            try:
                days_arg = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)

    generate_all_metal_briefings(days=days_arg)
