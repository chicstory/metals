import os
import sys
import re
import csv
import json
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
SITE_URL = "https://chicstory.github.io/metals"

def get_archived_dates() -> List[str]:
    """resources/ 폴더 안의 YYYY-MM-DD 폴더 목록을 최신순으로 반환"""
    if not os.path.exists(RESOURCES_DIR):
        return []
    dates = []
    for name in os.listdir(RESOURCES_DIR):
        p = os.path.join(RESOURCES_DIR, name)
        if os.path.isdir(p) and re.match(r"^\d{4}-\d{2}-\d{2}$", name):
            dates.append(name)
    dates.sort(reverse=True)
    return dates

def load_date_data(date_str: str) -> Optional[Dict[str, Any]]:
    """지정된 날짜 폴더에서 CSV, MD, 이미지 정보를 읽어 구조화된 딕셔너리로 반환"""
    date_folder = os.path.join(RESOURCES_DIR, date_str)
    if not os.path.exists(date_folder):
        return None

    csv_path = os.path.join(date_folder, f"7대자원_환산시세_{date_str}.csv")
    md_path = os.path.join(date_folder, f"[통합브리핑] 7대_금속원자재_{date_str}.md")

    csv_rows = []
    usd_rate = 1344.4
    rate_source = "네이버 금융"
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
        if csv_rows:
            try:
                usd_rate = float(csv_rows[0].get("적용환율(원/달러)", 1344.4))
                rate_source = csv_rows[0].get("환율출처", "네이버 금융")
            except Exception:
                pass

    pps_img = f"조달청_원자재_판매가격_{date_str}.png"
    has_pps = os.path.exists(os.path.join(date_folder, pps_img))

    metals_info = []
    md_content = ""
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

    METALS_META = [
        {"key": "steel_scrap", "idx": 1, "name_kr": "철·철스크랩", "name_en": "Steel Scrap", "emoji": "🔩", "cat": "steel", "type_label": "철·스크랩", "unit_krw": "원/kg"},
        {"key": "aluminum", "idx": 2, "name_kr": "알루미늄", "name_en": "Aluminum", "emoji": "🥫", "cat": "nonferrous", "type_label": "비철금속", "unit_krw": "원/kg"},
        {"key": "copper", "idx": 3, "name_kr": "구리", "name_en": "Copper", "emoji": "🔌", "cat": "nonferrous", "type_label": "비철금속", "unit_krw": "원/kg"},
        {"key": "lead", "idx": 4, "name_kr": "납", "name_en": "Lead", "emoji": "🔋", "cat": "nonferrous", "type_label": "비철금속", "unit_krw": "원/kg"},
        {"key": "palladium", "idx": 5, "name_kr": "팔라듐", "name_en": "Palladium", "emoji": "🚗", "cat": "pgm", "type_label": "PGM (백금족)", "unit_krw": "원/g"},
        {"key": "rhodium", "idx": 6, "name_kr": "로듐", "name_en": "Rhodium", "emoji": "💎", "cat": "pgm", "type_label": "PGM (백금족)", "unit_krw": "원/g"},
        {"key": "platinum", "idx": 7, "name_kr": "백금", "name_en": "Platinum", "emoji": "💍", "cat": "pgm", "type_label": "PGM (백금족)", "unit_krw": "원/g"},
    ]

    for m in METALS_META:
        c_row = next((r for r in csv_rows if r.get("자원명") == m["name_kr"]), None)
        chart_img = f"[{m['name_kr']}]_1년_시세차트_{date_str}.png"
        has_chart = os.path.exists(os.path.join(date_folder, chart_img))

        krw_price = int(float(c_row["원화시장단가(원)"])) if c_row and c_row.get("원화시장단가(원)") not in ["-", ""] else 0
        scrap_70 = int(float(c_row["스크랩추정_70%(원)"])) if c_row and c_row.get("스크랩추정_70%(원)") not in ["-", ""] else 0
        scrap_80 = int(float(c_row["스크랩추정_80%(원)"])) if c_row and c_row.get("스크랩추정_80%(원)") not in ["-", ""] else 0
        raw_price = f"{float(c_row['국제종가']):,.2f} {c_row['국제단위']}" if c_row and c_row.get("국제종가") not in ["-", ""] else "-"

        ai_content = ""
        articles = []
        if md_content:
            sec_pattern = re.compile(rf'## <a id="[^"]+"></a>{m["idx"]}\. [^\n]+\n(.*?)(?=\n---|\Z)', re.DOTALL)
            sec_match = sec_pattern.search(md_content)
            if sec_match:
                sec_body = sec_match.group(1)
                ai_match = re.search(r'### 🔍 시장 분석 및 향후 여파 코멘트 \(Gemma 4\)\n\n(.*?)(?=\n---|\Z)', sec_body, re.DOTALL)
                if ai_match:
                    ai_content = ai_match.group(1).strip()
                art_matches = re.findall(r'- \*\*\[(.*?)\]\((.*?)\)\*\*\n\s+- \*\*출처\*\*: (.*?) \| \*\*일시\*\*: (.*?)(?:\n\s+- \*\*요약\*\*: (.*?))?(?=\n-|\n###|\Z)', sec_body, re.DOTALL)
                for am in art_matches:
                    articles.append({
                        "title": am[0].strip(),
                        "link": am[1].strip(),
                        "source": am[2].strip(),
                        "pub_str": am[3].strip(),
                        "description": am[4].strip() if len(am) > 4 else ""
                    })

        metals_info.append({
            **m,
            "raw_price": raw_price,
            "krw_price": krw_price,
            "scrap_70": scrap_70,
            "scrap_80": scrap_80,
            "chart_img_path": f"./resources/{date_str}/{urllib.parse.quote(chart_img)}" if has_chart else None,
            "ai_content": ai_content,
            "articles": articles,
        })

    return {
        "date_str": date_str,
        "usd_rate": usd_rate,
        "rate_source": rate_source,
        "pps_img_path": f"./resources/{date_str}/{urllib.parse.quote(pps_img)}" if has_pps else None,
        "csv_path": f"./resources/{date_str}/7대자원_환산시세_{date_str}.csv",
        "html_report_path": f"./resources/{date_str}/[통합브리핑] 7대_금속원자재_{date_str}.html",
        "metals": metals_info
    }


def generate_sitemap(archived_dates: List[str]):
    """구글/네이버 SEO용 sitemap.xml 생성"""
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        f'    <loc>{SITE_URL}/</loc>',
        f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
    ]
    for d in archived_dates:
        report_url = f"{SITE_URL}/resources/{d}/{urllib.parse.quote(f'[통합브리핑] 7대_금속원자재_{d}.html')}"
        sitemap_lines.extend([
            '  <url>',
            f'    <loc>{report_url}</loc>',
            f'    <lastmod>{d}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>',
        ])
    sitemap_lines.append('</urlset>')

    sitemap_path = os.path.join(BASE_DIR, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_lines))
    print("    -> [Sitemap 완료] sitemap.xml 생성", flush=True)


def build_website_index() -> str:
    """메인 웹사이트 index.html 생성 (대시보드 + 계산기 + 캘린더/스크롤 아카이브 + 완벽 SEO)"""
    archived_dates = get_archived_dates()
    if not archived_dates:
        print("[경고] resources 폴더에 브리핑 데이터가 없습니다.")
        return ""

    latest_date = archived_dates[0]
    data = load_date_data(latest_date)
    if not data:
        print(f"[경고] {latest_date} 데이터 로드 실패")
        return ""

    # JSON 데이터 주입 (계산기용)
    calc_metals = []
    for m in data["metals"]:
        calc_metals.append({
            "key": m["key"],
            "name": m["name_kr"],
            "unit": m["unit_krw"].split("/")[1] if "/" in m["unit_krw"] else "kg",
            "unit_label": m["unit_krw"],
            "price": m["krw_price"],
            "scrap_70": m["scrap_70"],
            "scrap_80": m["scrap_80"],
            "emoji": m["emoji"],
            "cat": m["cat"]
        })
    calc_json = json.dumps(calc_metals, ensure_ascii=False)

    # 1. 7대 자원 테이블 행
    table_rows = []
    for m in data["metals"]:
        table_rows.append(f"""
        <tr class="table-row" data-cat="{m['cat']}">
            <td class="col-type"><span class="badge badge-{m['cat']}">{m['emoji']} {m['type_label']}</span></td>
            <td class="col-name"><strong>{m['name_kr']}</strong> <span class="text-sub">({m['name_en']})</span></td>
            <td class="col-raw font-mono">{m['raw_price']}</td>
            <td class="col-krw font-bold text-blue">{m['krw_price']:,} {m['unit_krw']}</td>
            <td class="col-scrap font-bold text-amber">
                <span class="scrap-badge">{m['scrap_70']:,} ~ {m['scrap_80']:,} {m['unit_krw']}</span>
            </td>
            <td class="col-action">
                <button class="btn-sm" onclick="setCalculatorTarget('{m['key']}')">🧮 계산</button>
                <a href="#card-{m['key']}" class="btn-sm btn-outline">차트·분석 ↓</a>
            </td>
        </tr>""")

    # 2. 7대 자원별 상세 카드 (차트 & 뉴스 & AI 분석)
    cards_html = []
    for m in data["metals"]:
        articles_li = []
        if m["articles"]:
            for a in m["articles"][:4]:
                desc = f"<p class='art-desc'>{a['description'][:180]}...</p>" if a.get("description") else ""
                articles_li.append(f"""
                <li class="art-item">
                    <a href="{a['link']}" target="_blank" rel="noopener" class="art-title">{a['title']} ↗</a>
                    <div class="art-meta">출처: <span>{a['source']}</span> | 일시: {a['pub_str']}</div>
                    {desc}
                </li>""")
        else:
            articles_li.append("<li class='text-muted'>최근 주요 시장 교란 뉴스나 특이 동향이 없습니다.</li>")

        # Format AI text
        ai_p = []
        for line in m["ai_content"].split("\n"):
            ls = line.strip()
            if not ls:
                continue
            ls = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", ls)
            if ls.startswith("- "):
                ai_p.append(f"<li class='ai-bullet'>{ls[2:]}</li>")
            else:
                ai_p.append(f"<p class='ai-para'>{ls}</p>")

        chart_html = ""
        if m["chart_img_path"]:
            chart_html = f"""
            <div class="card-chart">
                <div class="chart-header">
                    <span>📈 1년 시세 추이 차트 (Trading Economics 종가)</span>
                    <a href="{m['chart_img_path']}" target="_blank" class="text-sub">크게보기 ↗</a>
                </div>
                <img src="{m['chart_img_path']}" alt="{m['name_kr']} 1년 시세 차트" loading="lazy">
            </div>"""

        cards_html.append(f"""
        <article id="card-{m['key']}" class="metal-card" data-cat="{m['cat']}">
            <div class="card-top">
                <div class="card-title-group">
                    <span class="card-icon">{m['emoji']}</span>
                    <div>
                        <h3 class="card-name">{m['idx']}. {m['name_kr']} <span class="card-en">{m['name_en']}</span></h3>
                        <span class="badge badge-{m['cat']}">{m['type_label']}</span>
                    </div>
                </div>
                <div class="card-price-pills">
                    <div class="pill">
                        <span class="pill-label">국제 종가</span>
                        <span class="pill-val">{m['raw_price']}</span>
                    </div>
                    <div class="pill pill-blue">
                        <span class="pill-label">원화 환산 시장가</span>
                        <span class="pill-val">{m['krw_price']:,} {m['unit_krw']}</span>
                    </div>
                    <div class="pill pill-amber">
                        <span class="pill-label">♻️ 스크랩 추정가(70~80%)</span>
                        <span class="pill-val">{m['scrap_70']:,} ~ {m['scrap_80']:,} {m['unit_krw']}</span>
                    </div>
                </div>
            </div>

            {chart_html}

            <div class="card-grid">
                <div class="card-news">
                    <h4>📰 최근 주요 뉴스 ({len(m['articles'])}건)</h4>
                    <ul class="art-list">
                        {''.join(articles_li)}
                    </ul>
                </div>
                <div class="card-ai">
                    <div class="ai-header">
                        <h4>🔍 AI 시장 및 스크랩 여파 분석</h4>
                        <span class="ai-tag">Gemma 4</span>
                    </div>
                    <div class="ai-body">
                        {''.join(ai_p)}
                    </div>
                </div>
            </div>
        </article>""")

    # 3. 아카이브 데이터 구조화 (캘린더 및 스크롤 박스용)
    archived_data_list = []
    for d in archived_dates:
        c_path = os.path.join(RESOURCES_DIR, d, f"7대자원_환산시세_{d}.csv")
        rate_val = 1344.4
        steel_p = "-"
        copper_p = "-"
        pd_p = "-"
        if os.path.exists(c_path):
            with open(c_path, "r", encoding="utf-8-sig") as cf:
                c_rows = list(csv.DictReader(cf))
                if c_rows:
                    try:
                        rate_val = float(c_rows[0].get("적용환율(원/달러)", 1344.4))
                    except Exception:
                        pass
                    for cr in c_rows:
                        if cr.get("자원명") == "철·철스크랩":
                            steel_p = f"{int(float(cr['원화시장단가(원)'])):,}원/kg"
                        elif cr.get("자원명") == "구리":
                            copper_p = f"{int(float(cr['원화시장단가(원)'])):,}원/kg"
                        elif cr.get("자원명") == "팔라듐":
                            pd_p = f"{int(float(cr['원화시장단가(원)'])):,}원/g"
        report_url = f"./resources/{d}/{urllib.parse.quote(f'[통합브리핑] 7대_금속원자재_{d}.html')}"
        csv_url = f"./resources/{d}/{urllib.parse.quote(f'7대자원_환산시세_{d}.csv')}"
        archived_data_list.append({
            "date": d,
            "rate": rate_val,
            "steel": steel_p,
            "copper": copper_p,
            "palladium": pd_p,
            "report_url": report_url,
            "csv_url": csv_url,
            "is_latest": (d == latest_date)
        })

    archive_json = json.dumps(archived_data_list, ensure_ascii=False)

    # 4. 전체 HTML 빌드
    index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>더패스랩 7대 금속원자재 & 스크랩 시세 허브 | 실시간 고철·비철·PGM 매입 단가</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="매일 업데이트되는 7대 금속원자재(철스크랩, 알루미늄, 구리, 납, 팔라듐, 로듐, 백금)의 국제 시세 및 원화 환산 kg당·g당 단가, 스크랩 매입 추정가 계산기, 조달청 비축물자 판매가격표 종합 허브입니다.">
    <meta name="keywords" content="고철시세, 철스크랩가격, 구리kg가격, 알루미늄시세, 납시세, 팔라듐시세, 로듐가격, 백금시세, 폐촉매가격, 폐배터리시세, 조달청원자재판매가격, 더패스랩, ThePathLab">
    <meta name="author" content="ThePathLab">
    <link rel="canonical" href="{SITE_URL}/">

    <!-- Open Graph / Social Sharing -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{SITE_URL}/">
    <meta property="og:title" content="더패스랩 7대 금속원자재 & 스크랩 시세 허브">
    <meta property="og:description" content="오늘자 실시간 환산 시장가 및 스크랩(70~80%) 매입 계산기, 조달청 고시표, Trading Economics 1년 시세 차트">
    <meta property="og:image" content="{SITE_URL}/resources/{latest_date}/{urllib.parse.quote(f'조달청_원자재_판매가격_{latest_date}.png')}">

    <!-- Google Structured Data (Schema.org) -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "ThePathLab Metals & Scrap Data Hub",
        "url": "{SITE_URL}/",
        "description": "7대 금속원자재 국제시세 및 스크랩 매입 단가 데이터 허브",
        "publisher": {{
            "@type": "Organization",
            "name": "ThePathLab"
        }}
    }}
    </script>

    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-card: #243248;
            --surface-hover: #334155;
            --border: #334155;
            --border-light: #475569;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --text-muted: #64748b;
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.25);
            --green: #10b981;
            --green-glow: rgba(16, 185, 129, 0.2);
            --amber: #f59e0b;
            --amber-glow: rgba(245, 158, 11, 0.2);
            --font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", Roboto, "Apple SD Gothic Neo", sans-serif;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg);
            color: var(--text-main);
            font-family: var(--font-family);
            line-height: 1.6;
            padding-bottom: 80px;
        }}
        a {{ color: var(--primary); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        /* Header */
        header {{
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border);
            padding: 32px 0 24px 0;
            margin-bottom: 32px;
        }}
        .header-inner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .brand-title {{
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(90deg, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .brand-sub {{
            font-size: 13.5px;
            color: var(--text-sub);
            margin-top: 4px;
        }}
        .header-meta {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .meta-tag {{
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 13px;
            color: var(--text-sub);
        }}
        .meta-tag strong {{ color: var(--text-main); }}

        /* Hero Banner */
        .hero-banner {{
            background: radial-gradient(circle at top left, #1e3a8a 0%, #1e293b 60%);
            border: 1px solid #3b82f6;
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 32px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .hero-left h1 {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .hero-left p {{
            color: #cbd5e1;
            font-size: 14.5px;
            max-width: 680px;
        }}
        .hero-actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        /* Buttons */
        .btn {{
            background: var(--primary);
            color: white;
            font-weight: 600;
            padding: 10px 18px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn:hover {{
            background: #2563eb;
            transform: translateY(-1px);
        }}
        .btn-green {{
            background: #059669;
        }}
        .btn-green:hover {{
            background: #047857;
        }}
        .btn-outline {{
            background: transparent;
            border: 1px solid var(--border-light);
            color: var(--text-sub);
        }}
        .btn-outline:hover {{
            background: var(--surface);
            color: var(--text-main);
        }}
        .btn-sm {{
            padding: 5px 10px;
            font-size: 12.5px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--surface);
            color: var(--text-main);
            cursor: pointer;
            transition: background 0.15s;
        }}
        .btn-sm:hover {{
            background: var(--surface-hover);
        }}
        .btn-sub {{
            background: #334155;
            color: #e2e8f0;
        }}

        /* 🧮 Interactive Calculator Widget */
        .calc-box {{
            background: linear-gradient(145deg, #1e293b 0%, #172554 100%);
            border: 2px solid #3b82f6;
            border-radius: 16px;
            padding: 26px;
            margin-bottom: 36px;
            box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);
        }}
        .calc-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .calc-header h2 {{
            font-size: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .calc-grid {{
            display: grid;
            grid-template-columns: 1.2fr 1fr 1.6fr;
            gap: 20px;
            align-items: center;
        }}
        @media (max-width: 900px) {{
            .calc-grid {{ grid-template-columns: 1fr; }}
        }}
        .calc-field label {{
            display: block;
            font-size: 13px;
            color: var(--text-sub);
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .calc-select, .calc-input {{
            width: 100%;
            padding: 12px 14px;
            background: #0f172a;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            outline: none;
        }}
        .calc-select:focus, .calc-input:focus {{
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px var(--primary-glow);
        }}
        .calc-result-box {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 16px 20px;
        }}
        .calc-res-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid #1e293b;
        }}
        .calc-res-row:last-child {{ border-bottom: none; }}
        .calc-res-label {{ font-size: 13px; color: var(--text-sub); }}
        .calc-res-val {{ font-size: 17px; font-weight: 700; }}
        .calc-res-highlight {{
            font-size: 22px;
            color: #34d399;
            font-weight: 800;
        }}

        /* Table Section */
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 700;
        }}
        .tabs {{
            display: flex;
            gap: 6px;
            background: var(--surface);
            padding: 4px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-sub);
            padding: 6px 12px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
        }}
        .tab-btn.active {{
            background: var(--primary);
            color: white;
        }}

        .table-wrap {{
            overflow-x: auto;
            background: var(--surface);
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 40px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14.5px;
            text-align: left;
        }}
        th {{
            background: #172554;
            color: #93c5fd;
            padding: 14px 16px;
            font-weight: 600;
            border-bottom: 2px solid var(--border);
            white-space: nowrap;
        }}
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }}
        tr:hover td {{
            background: var(--surface-hover);
        }}
        .font-mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
        .font-bold {{ font-weight: 700; }}
        .text-blue {{ color: #60a5fa; }}
        .text-amber {{ color: #fbbf24; }}
        .scrap-badge {{
            background: rgba(245, 158, 11, 0.15);
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid rgba(245, 158, 11, 0.3);
            white-space: nowrap;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            font-size: 11.5px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
        }}
        .badge-steel {{ background: #334155; color: #cbd5e1; }}
        .badge-nonferrous {{ background: #1e3a8a; color: #93c5fd; }}
        .badge-pgm {{ background: #581c87; color: #e9d5ff; }}

        /* PPS Image Section */
        .pps-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 40px;
        }}
        .pps-img-wrap {{
            text-align: center;
            background: #0f172a;
            padding: 16px;
            border-radius: 8px;
            margin-top: 14px;
        }}
        .pps-img-wrap img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}

        /* 7 Commodity Detail Cards */
        .metal-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 28px;
            transition: border-color 0.2s;
        }}
        .metal-card:hover {{
            border-color: var(--border-light);
        }}
        .card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 18px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border);
        }}
        .card-title-group {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .card-icon {{ font-size: 28px; }}
        .card-name {{ font-size: 20px; font-weight: 800; }}
        .card-en {{ font-size: 14px; color: var(--text-sub); font-weight: normal; }}
        .card-price-pills {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .pill {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 6px 12px;
        }}
        .pill-label {{ font-size: 11px; color: var(--text-muted); display: block; }}
        .pill-val {{ font-size: 14.5px; font-weight: 700; color: var(--text-main); }}
        .pill-blue .pill-val {{ color: #60a5fa; }}
        .pill-amber .pill-val {{ color: #fbbf24; }}

        .card-chart {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: var(--text-sub);
            margin-bottom: 10px;
        }}
        .card-chart img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}

        .card-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 800px) {{
            .card-grid {{ grid-template-columns: 1fr; }}
        }}
        .card-news, .card-ai {{
            background: #172554;
            border-radius: 10px;
            padding: 18px;
        }}
        .card-ai {{
            background: #1e1b4b;
            border-left: 4px solid #818cf8;
        }}
        .ai-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .ai-tag {{
            background: #4338ca;
            color: #e0e7ff;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .ai-bullet {{
            margin-left: 18px;
            font-size: 13.5px;
            color: #cbd5e1;
            margin-bottom: 6px;
        }}
        .ai-para {{
            font-size: 13.5px;
            color: #cbd5e1;
            margin-bottom: 8px;
        }}
        .art-list {{ list-style: none; }}
        .art-item {{
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .art-item:last-child {{ border-bottom: none; margin-bottom: 0; }}
        .art-title {{
            font-size: 14px;
            font-weight: 600;
            color: #93c5fd;
            line-height: 1.4;
            display: inline-block;
        }}
        .art-meta {{
            font-size: 11.5px;
            color: var(--text-muted);
            margin-top: 3px;
        }}
        .art-desc {{
            font-size: 12.5px;
            color: #94a3b8;
            margin-top: 4px;
            line-height: 1.4;
        }}

        /* 📅 New Archive Section: Calendar + Scrollbox */
        .archive-box {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-top: 50px;
        }}
        .archive-panes {{
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 24px;
            margin-top: 20px;
        }}
        @media (max-width: 950px) {{
            .archive-panes {{ grid-template-columns: 1fr; }}
        }}

        /* Calendar Widget */
        .cal-card {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
        }}
        .cal-nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }}
        .cal-title {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
        }}
        .cal-btn {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-main);
            width: 30px;
            height: 30px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .cal-btn:hover {{ background: var(--surface-hover); }}
        .cal-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            text-align: center;
        }}
        .cal-day-head {{
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 600;
            padding: 6px 0;
        }}
        .cal-day-head.sun {{ color: #f87171; }}
        .cal-day-head.sat {{ color: #60a5fa; }}
        .cal-cell {{
            height: 38px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            font-size: 13.5px;
            position: relative;
            cursor: default;
            color: #64748b;
        }}
        .cal-cell.empty {{ background: transparent; }}
        .cal-cell.has-data {{
            color: var(--text-main);
            font-weight: 700;
            background: #1e293b;
            border: 1px solid #3b82f6;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .cal-cell.has-data:hover {{
            background: #2563eb;
            color: white;
            transform: scale(1.05);
        }}
        .cal-cell.selected {{
            background: #059669 !important;
            border-color: #34d399 !important;
            color: white !important;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
        }}
        .cal-dot {{
            width: 4px;
            height: 4px;
            background: #34d399;
            border-radius: 50%;
            margin-top: 1px;
        }}

        /* Scroll Box List Widget */
        .scroll-card {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
            display: flex;
            flex-direction: column;
        }}
        .scroll-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .search-input {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
            width: 180px;
        }}
        .search-input:focus {{ border-color: var(--primary); }}
        
        .scroll-list-wrap {{
            max-height: 310px;
            overflow-y: auto;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        /* Custom Scrollbar */
        .scroll-list-wrap::-webkit-scrollbar {{
            width: 8px;
        }}
        .scroll-list-wrap::-webkit-scrollbar-track {{
            background: #0f172a;
        }}
        .scroll-list-wrap::-webkit-scrollbar-thumb {{
            background: #334155;
            border-radius: 4px;
        }}
        .scroll-list-wrap::-webkit-scrollbar-thumb:hover {{
            background: #475569;
        }}

        .scroll-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }}
        .scroll-table th {{
            background: #1e293b;
            padding: 10px 12px;
            font-size: 12.5px;
            color: #94a3b8;
            position: sticky;
            top: 0;
            z-index: 2;
        }}
        .scroll-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #1e293b;
        }}
        .scroll-table tr:hover td {{
            background: #1e293b;
        }}

        /* Selected Date Preview Bar */
        .date-preview-bar {{
            background: #1e293b;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            border-left: 4px solid #10b981;
        }}
        .preview-left strong {{ font-size: 15px; color: white; }}
        .preview-prices {{
            display: flex;
            gap: 14px;
            font-size: 13px;
            color: var(--text-sub);
            flex-wrap: wrap;
        }}
        .preview-prices span strong {{ color: #38bdf8; }}

        /* Toast */
        .toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            display: none;
            z-index: 9999;
        }}

        footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 60px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
        }}
    </style>
</head>
<body>

    <!-- Header (GitHub link removed, replaced with official Blog link) -->
    <header>
        <div class="container header-inner">
            <div>
                <a href="./" class="brand-title">THEPATHLAB METALS & SCRAP HUB</a>
                <div class="brand-sub">7대 금속·원자재 실시간 환산 시세 및 스크랩 매입 단가 데이터 허브</div>
            </div>
            <div class="header-meta">
                <div class="meta-tag">기준 일시: <strong>{data['date_str']}</strong></div>
                <div class="meta-tag">적용 환율: <strong style="color: #38bdf8;">1 USD = {data['usd_rate']:,.1f}원</strong></div>
                <a href="https://blog.naver.com/thepathlab" target="_blank" rel="noopener" class="btn-sm btn-outline">더패스랩 공식 블로그 ↗</a>
            </div>
        </div>
    </header>

    <main class="container">

        <!-- Hero Banner -->
        <section class="hero-banner">
            <div class="hero-left">
                <h1>📊 오늘의 7대 금속원자재 & 스크랩 실시간 시황</h1>
                <p>국제 시장 종가(Trading Economics) 및 조달청 공식 판매가격표를 바탕으로, 고철·비철·PGM(폐촉매)의 원화 환산 단가와 실무 스크랩 매입 추정 시세(70~80%)를 매일 아침 자동 산출합니다.</p>
            </div>
            <div class="hero-actions">
                <button onclick="copyNaverTable()" class="btn btn-green">📋 네이버 블로그용 표 복사</button>
                <a href="{data['csv_path']}" download class="btn btn-outline">📥 오늘자 CSV</a>
            </div>
        </section>

        <!-- 🧮 실시간 스크랩 계산기 위젯 -->
        <section class="calc-box">
            <div class="calc-header">
                <h2>🧮 실시간 스크랩 매입 예상 견적 계산기</h2>
                <span style="font-size: 13px; color: #94a3b8;">* 오늘자 공식 시세 대비 감모·정제 마진(70~80%) 자동 적용</span>
            </div>
            <div class="calc-grid">
                <div class="calc-field">
                    <label for="calc-metal">품목 선택</label>
                    <select id="calc-metal" class="calc-select" onchange="onMetalChange()">
                        <!-- JS injected -->
                    </select>
                </div>
                <div class="calc-field">
                    <label for="calc-qty">수량 (<span id="calc-unit-label">kg</span>)</label>
                    <input type="number" id="calc-qty" class="calc-input" value="100" min="0.1" step="any" oninput="calculateScrap()">
                </div>
                <div class="calc-result-box">
                    <div class="calc-res-row">
                        <span class="calc-res-label">공식 원자재 시장 가치</span>
                        <span id="res-market" class="calc-res-val">- 원</span>
                    </div>
                    <div class="calc-res-row">
                        <span class="calc-res-label">♻️ 스크랩 매입 예상 범위 (70%~80%)</span>
                        <span id="res-scrap" class="calc-res-highlight">- 원</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- 💰 7대 금속·원자재 오늘의 시세표 -->
        <section style="margin-bottom: 36px;">
            <div class="section-header">
                <div>
                    <h2 class="section-title">💰 7대 금속·원자재 원화 환산 시장가 및 스크랩 매입 추정가</h2>
                    <span style="font-size: 13px; color: var(--text-sub);">환율: 1 USD = {data['usd_rate']:,.1f}원 ({data['rate_source']})</span>
                </div>
                <div class="tabs">
                    <button class="tab-btn active" onclick="filterCategory('all', this)">전체보기</button>
                    <button class="tab-btn" onclick="filterCategory('steel', this)">철스크랩</button>
                    <button class="tab-btn" onclick="filterCategory('nonferrous', this)">비철금속</button>
                    <button class="tab-btn" onclick="filterCategory('pgm', this)">백금족(PGM)</button>
                </div>
            </div>

            <div class="table-wrap">
                <table id="main-price-table">
                    <thead>
                        <tr>
                            <th>구분</th>
                            <th>자원명</th>
                            <th>국제 종가</th>
                            <th>원화 환산 시장가</th>
                            <th>♻️ 스크랩 매입 추정가 (70~80%)</th>
                            <th>빠른 도구</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </section>

        <!-- 🏛️ 오늘자 조달청 판매가격표 -->
        {f'''
        <section class="pps-card">
            <div class="section-header">
                <h2 class="section-title">🏛️ 오늘자 조달청(PPS) 원자재 판매가격 고시표</h2>
                <a href="https://www.pps.go.kr/bichuk/index.do" target="_blank" class="btn-sm btn-outline">조달청 비축물자 누리집 ↗</a>
            </div>
            <div class="pps-img-wrap">
                <img src="{data['pps_img_path']}" alt="조달청 판매가격표" loading="lazy">
            </div>
        </section>
        ''' if data['pps_img_path'] else ""}

        <!-- 📈 7대 자원별 상세 차트 & AI 시황 분석 -->
        <section>
            <div class="section-header">
                <h2 class="section-title">📈 7대 자원별 1년 시세 추이 및 AI 시장·스크랩 여파 분석</h2>
                <span style="font-size: 13px; color: var(--text-sub);">차트 출처: Trading Economics | AI 분석: Gemma 4</span>
            </div>

            {''.join(cards_html)}
        </section>

        <!-- 📅 일자별 아카이브: 월간 캘린더 & 스크롤 박스 -->
        <section class="archive-box">
            <div class="section-header" style="margin-bottom: 8px;">
                <div>
                    <h2 class="section-title">📅 일자별 시황 브리핑 아카이브</h2>
                    <span style="font-size: 13px; color: var(--text-sub);">날짜를 클릭하거나 스크롤 박스에서 과거 브리핑과 CSV를 손쉽게 열람하세요.</span>
                </div>
            </div>

            <div class="archive-panes">
                <!-- 좌측: 월간 캘린더 -->
                <div class="cal-card">
                    <div class="cal-nav">
                        <button class="cal-btn" onclick="prevMonth()">◀</button>
                        <span id="cal-month-title" class="cal-title">2026년 9월</span>
                        <button class="cal-btn" onclick="nextMonth()">▶</button>
                    </div>
                    <div class="cal-grid" id="cal-grid">
                        <!-- JS injected days -->
                    </div>
                </div>

                <!-- 우측: 콤팩트 스크롤 박스 -->
                <div class="scroll-card">
                    <div class="scroll-top">
                        <span style="font-size: 14.5px; font-weight: 700; color: #93c5fd;">📋 브리핑 목록 (<span id="arch-count">0</span>건)</span>
                        <input type="text" id="arch-search" class="search-input" placeholder="날짜 검색 (예: 2026-09)" oninput="filterArchiveList()">
                    </div>
                    <div class="scroll-list-wrap">
                        <table class="scroll-table">
                            <thead>
                                <tr>
                                    <th>발행일</th>
                                    <th>철스크랩</th>
                                    <th>구리</th>
                                    <th>팔라듐</th>
                                    <th>도구</th>
                                </tr>
                            </thead>
                            <tbody id="scroll-tbody">
                                <!-- JS injected rows -->
                            </tbody>
                        </table>
                    </div>

                    <!-- 선택된 날짜 상세 프리뷰 바 -->
                    <div id="date-preview-bar" class="date-preview-bar">
                        <div class="preview-left">
                            <strong id="prev-date-label">-</strong>
                            <span id="prev-badge" style="font-size: 11px; background: #059669; padding: 2px 6px; border-radius: 4px; margin-left: 6px; color: white;"></span>
                        </div>
                        <div class="preview-prices">
                            <span>철스크랩: <strong id="prev-steel">-</strong></span>
                            <span>구리: <strong id="prev-copper">-</strong></span>
                            <span>팔라듐: <strong id="prev-pd">-</strong></span>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <a id="prev-report-btn" href="#" target="_blank" class="btn-sm btn-outline">리포트 열람 ↗</a>
                            <a id="prev-csv-btn" href="#" download class="btn-sm btn-sub">CSV</a>
                        </div>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <footer>
        <div class="container">
            <p><strong>THEPATHLAB METALS & SCRAP INTELLIGENCE</strong> | Automated Market Intelligence Platform</p>
            <p style="margin-top: 6px; font-size: 12px; color: #64748b;">
                Data Sources: Trading Economics, Mining.com, Public Procurement Service(조달청), Naver Finance.<br>
                본 데이터는 정보 제공용이며, 실제 매입·매매 거래 시 품위, 운송비, 제련 감모율에 따라 변동될 수 있습니다.
            </p>
        </div>
    </footer>

    <div id="toast" class="toast"></div>

    <script>
        const METALS = {calc_json};
        const ARCHIVES = {archive_json};

        // Current calendar view state
        let currentYear = 2026;
        let currentMonth = 9; // 1-indexed
        let selectedDate = "{latest_date}";

        if (ARCHIVES.length > 0) {{
            const p = ARCHIVES[0].date.split("-");
            currentYear = parseInt(p[0]);
            currentMonth = parseInt(p[1]);
            selectedDate = ARCHIVES[0].date;
        }}

        // Initialize Calculator
        function initCalculator() {{
            const sel = document.getElementById('calc-metal');
            sel.innerHTML = '';
            METALS.forEach(m => {{
                const opt = document.createElement('option');
                opt.value = m.key;
                opt.innerText = `${{m.emoji}} ${{m.name}} (${{m.unit_label}})`;
                sel.appendChild(opt);
            }});
            onMetalChange();
        }}

        function onMetalChange() {{
            const key = document.getElementById('calc-metal').value;
            const metal = METALS.find(m => m.key === key);
            if (!metal) return;
            document.getElementById('calc-unit-label').innerText = metal.unit;
            
            // Adjust default quantity if PGM (g) vs Base Metal (kg)
            const qtyInput = document.getElementById('calc-qty');
            if (metal.cat === 'pgm' && qtyInput.value > 50) {{
                qtyInput.value = 10;
            }} else if (metal.cat !== 'pgm' && qtyInput.value < 20) {{
                qtyInput.value = 100;
            }}
            calculateScrap();
        }}

        function setCalculatorTarget(key) {{
            document.getElementById('calc-metal').value = key;
            onMetalChange();
            window.scrollTo({{ top: document.querySelector('.calc-box').offsetTop - 30, behavior: 'smooth' }});
        }}

        function calculateScrap() {{
            const key = document.getElementById('calc-metal').value;
            const qty = parseFloat(document.getElementById('calc-qty').value) || 0;
            const metal = METALS.find(m => m.key === key);
            if (!metal) return;

            const marketTotal = Math.round(metal.price * qty);
            const scrap70Total = Math.round(metal.scrap_70 * qty);
            const scrap80Total = Math.round(metal.scrap_80 * qty);

            document.getElementById('res-market').innerText = `${{marketTotal.toLocaleString()}} 원`;
            document.getElementById('res-scrap').innerText = `${{scrap70Total.toLocaleString()}} 원 ~ ${{scrap80Total.toLocaleString()}} 원`;
        }}

        // Category Filter
        function filterCategory(cat, btn) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            document.querySelectorAll('.table-row').forEach(row => {{
                if (cat === 'all' || row.dataset.cat === cat) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}

        // Calendar Logic
        function renderCalendar() {{
            document.getElementById('cal-month-title').innerText = `${{currentYear}}년 ${{currentMonth}}월`;
            const grid = document.getElementById('cal-grid');
            grid.innerHTML = '';

            const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
            dayNames.forEach((d, idx) => {{
                const h = document.createElement('div');
                h.className = 'cal-day-head' + (idx === 0 ? ' sun' : idx === 6 ? ' sat' : '');
                h.innerText = d;
                grid.appendChild(h);
            }});

            const firstDay = new Date(currentYear, currentMonth - 1, 1).getDay();
            const totalDays = new Date(currentYear, currentMonth, 0).getDate();

            // Leading blanks
            for (let i = 0; i < firstDay; i++) {{
                const blank = document.createElement('div');
                blank.className = 'cal-cell empty';
                grid.appendChild(blank);
            }}

            // Days
            for (let d = 1; d <= totalDays; d++) {{
                const cell = document.createElement('div');
                cell.className = 'cal-cell';
                const dateStr = `${{currentYear}}-${{String(currentMonth).padStart(2, '0')}}-${{String(d).padStart(2, '0')}}`;
                cell.innerText = d;

                const found = ARCHIVES.find(a => a.date === dateStr);
                if (found) {{
                    cell.classList.add('has-data');
                    const dot = document.createElement('div');
                    dot.className = 'cal-dot';
                    cell.appendChild(dot);
                    if (dateStr === selectedDate) {{
                        cell.classList.add('selected');
                    }}
                    cell.onclick = () => selectDate(dateStr);
                }}

                grid.appendChild(cell);
            }}
        }}

        function prevMonth() {{
            currentMonth--;
            if (currentMonth < 1) {{
                currentMonth = 12;
                currentYear--;
            }}
            renderCalendar();
        }}

        function nextMonth() {{
            currentMonth++;
            if (currentMonth > 12) {{
                currentMonth = 1;
                currentYear++;
            }}
            renderCalendar();
        }}

        // Scroll Box Logic
        function renderScrollList(filterText = '') {{
            const tbody = document.getElementById('scroll-tbody');
            tbody.innerHTML = '';
            const filtered = ARCHIVES.filter(a => a.date.includes(filterText.trim()));
            document.getElementById('arch-count').innerText = filtered.length;

            if (filtered.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#64748b; padding:20px;">일치하는 브리핑 일자가 없습니다.</td></tr>';
                return;
            }}

            filtered.forEach(a => {{
                const tr = document.createElement('tr');
                tr.style.cursor = 'pointer';
                tr.innerHTML = `
                    <td><strong>${{a.date}}</strong> ${{a.is_latest ? '<span style="font-size:10px; background:#059669; color:white; padding:1px 5px; border-radius:3px; margin-left:3px;">최신</span>' : ''}}</td>
                    <td style="color:#60a5fa; font-weight:600;">${{a.steel}}</td>
                    <td style="color:#60a5fa; font-weight:600;">${{a.copper}}</td>
                    <td style="color:#fbbf24; font-weight:600;">${{a.palladium}}</td>
                    <td>
                        <a href="${{a.report_url}}" target="_blank" class="btn-sm btn-outline" style="padding:2px 6px; font-size:11.5px;">열람 ↗</a>
                        <a href="${{a.csv_url}}" download class="btn-sm btn-sub" style="padding:2px 6px; font-size:11.5px;">CSV</a>
                    </td>
                `;
                tr.onclick = (e) => {{
                    if (e.target.tagName !== 'A') {{
                        selectDate(a.date);
                    }}
                }};
                tbody.appendChild(tr);
            }});
        }}

        function filterArchiveList() {{
            const val = document.getElementById('arch-search').value;
            renderScrollList(val);
        }}

        function selectDate(dateStr) {{
            selectedDate = dateStr;
            const found = ARCHIVES.find(a => a.date === dateStr);
            if (!found) return;

            // Update preview bar
            document.getElementById('prev-date-label').innerText = `📅 ${{found.date}} 브리핑`;
            document.getElementById('prev-badge').innerText = found.is_latest ? '오늘자 최신' : '과거 아카이브';
            document.getElementById('prev-steel').innerText = found.steel;
            document.getElementById('prev-copper').innerText = found.copper;
            document.getElementById('prev-pd').innerText = found.palladium;
            document.getElementById('prev-report-btn').href = found.report_url;
            document.getElementById('prev-csv-btn').href = found.csv_url;

            // Sync calendar month if needed
            const p = dateStr.split("-");
            currentYear = parseInt(p[0]);
            currentMonth = parseInt(p[1]);
            renderCalendar();
        }}

        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => {{ t.style.display = 'none'; }}, 3000);
        }}

        // Copy Naver Blog Table (Clean HTML)
        function copyNaverTable() {{
            const table = document.getElementById('main-price-table');
            const range = document.createRange();
            range.selectNode(table);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            try {{
                document.execCommand('copy');
                window.getSelection().removeAllRanges();
                showToast('✅ 네이버 블로그용 표가 복사되었습니다! 에디터에 Ctrl+V 하세요.');
            }} catch(e) {{
                alert('복사 실패: 표를 직접 마우스로 드래그하여 복사해 주세요.');
            }}
        }}

        window.addEventListener('DOMContentLoaded', () => {{
            initCalculator();
            renderCalendar();
            renderScrollList();
            if (ARCHIVES.length > 0) {{
                selectDate(ARCHIVES[0].date);
            }}
        }});
    </script>
</body>
</html>
"""

    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"    -> [웹사이트 완료] 메인 대시보드 생성: index.html ({len(index_html):,} bytes)", flush=True)

    generate_sitemap(archived_dates)
    return index_path


if __name__ == "__main__":
    build_website_index()
