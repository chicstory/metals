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

    csv_filename = f"9대자원_환산시세_{date_str}.csv"
    csv_path = os.path.join(date_folder, csv_filename)
    if not os.path.exists(csv_path):
        csv_filename = f"7대자원_환산시세_{date_str}.csv"
        csv_path = os.path.join(date_folder, csv_filename)

    md_filename = f"[통합브리핑] 9대_금속원자재_{date_str}.md"
    md_path = os.path.join(date_folder, md_filename)
    if not os.path.exists(md_path):
        md_filename = f"[통합브리핑] 7대_금속원자재_{date_str}.md"
        md_path = os.path.join(date_folder, md_filename)

    html_filename = f"[통합브리핑] 9대_금속원자재_{date_str}.html"
    html_path = os.path.join(date_folder, html_filename)
    if not os.path.exists(html_path):
        html_filename = f"[통합브리핑] 7대_금속원자재_{date_str}.html"
        html_path = os.path.join(date_folder, html_filename)

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

    # 옵션 2: 산업금속 ➡️ 귀금속 순서
    METALS_META = [
        {"key": "copper", "idx": 1, "name_kr": "구리", "name_en": "Copper", "emoji": "🥉", "cat": "nonferrous", "type_label": "비철금속", "unit_krw": "원/kg"},
        {"key": "iron_scrap", "idx": 2, "name_kr": "철·철스크랩", "name_en": "Steel Scrap", "emoji": "🏗️", "cat": "steel", "type_label": "철·스크랩", "unit_krw": "원/kg"},
        {"key": "aluminum", "idx": 3, "name_kr": "알루미늄", "name_en": "Aluminum", "emoji": "🥫", "cat": "nonferrous", "type_label": "비철금속", "unit_krw": "원/kg"},
        {"key": "lead", "idx": 4, "name_kr": "납", "name_en": "Lead", "emoji": "🔋", "cat": "nonferrous", "type_label": "비철금속", "unit_krw": "원/kg"},
        {"key": "gold", "idx": 5, "name_kr": "금", "name_en": "Gold", "emoji": "🥇", "cat": "precious", "type_label": "귀금속", "unit_krw": "원/g"},
        {"key": "silver", "idx": 6, "name_kr": "은", "name_en": "Silver", "emoji": "🥈", "cat": "precious", "type_label": "귀금속", "unit_krw": "원/g"},
        {"key": "platinum", "idx": 7, "name_kr": "백금", "name_en": "Platinum", "emoji": "💍", "cat": "pgm", "type_label": "PGM (백금족)", "unit_krw": "원/g"},
        {"key": "palladium", "idx": 8, "name_kr": "팔라듐", "name_en": "Palladium", "emoji": "🚗", "cat": "pgm", "type_label": "PGM (백금족)", "unit_krw": "원/g"},
        {"key": "rhodium", "idx": 9, "name_kr": "로듐", "name_en": "Rhodium", "emoji": "💎", "cat": "pgm", "type_label": "PGM (백금족)", "unit_krw": "원/g"},
    ]

    # 전일 CSV 로드 (전일대비 가격 변화량 및 환율 변동 동시 반영용)
    prev_csv_rows = []
    all_archived = get_archived_dates()
    if date_str in all_archived:
        c_idx = all_archived.index(date_str)
        if c_idx + 1 < len(all_archived):
            prev_d = all_archived[c_idx + 1]
            prev_csv_file = os.path.join(RESOURCES_DIR, prev_d, f"9대자원_환산시세_{prev_d}.csv")
            if not os.path.exists(prev_csv_file):
                prev_csv_file = os.path.join(RESOURCES_DIR, prev_d, f"7대자원_환산시세_{prev_d}.csv")
            if os.path.exists(prev_csv_file):
                try:
                    with open(prev_csv_file, "r", encoding="utf-8-sig") as pf:
                        prev_csv_rows = list(csv.DictReader(pf))
                except Exception:
                    pass

    for m in METALS_META:
        c_row = next((r for r in csv_rows if r.get("자원명") == m["name_kr"]), None)
        if not c_row:
            continue
        chart_img = f"[{m['name_kr']}]_1년_시세차트_{date_str}.png"
        has_chart = os.path.exists(os.path.join(date_folder, chart_img))

        krw_price = int(float(c_row["원화시장단가(원)"])) if c_row and c_row.get("원화시장단가(원)") not in ["-", ""] else 0
        scrap_70 = int(float(c_row["스크랩추정_70%(원)"])) if c_row and c_row.get("스크랩추정_70%(원)") not in ["-", ""] else 0
        scrap_80 = int(float(c_row["스크랩추정_80%(원)"])) if c_row and c_row.get("스크랩추정_80%(원)") not in ["-", ""] else 0
        raw_price = f"{float(c_row['국제종가']):,.2f} {c_row['국제단위']}" if c_row and c_row.get("국제종가") not in ["-", ""] else "-"

        # 전일 대비 원화단가(원/kg, 원/g) 변화량 및 등락률 계산 (환율 + 국제시세 변동 종합)
        prev_c_row = next((r for r in prev_csv_rows if r.get("자원명") == m["name_kr"]), None)
        prev_krw = int(float(prev_c_row["원화시장단가(원)"])) if prev_c_row and prev_c_row.get("원화시장단가(원)") not in ["-", ""] else None

        diff_krw = None
        diff_pct = None
        diff_badge_html = ""
        if krw_price and prev_krw is not None and prev_krw > 0:
            diff_krw = krw_price - prev_krw
            diff_pct = (diff_krw / prev_krw) * 100
            if diff_krw > 0:
                diff_badge_html = f'<span class="diff-badge diff-up" title="전일 대비 환율·시세 종합 +{diff_krw:,}원 (+{diff_pct:.1f}%) 상승">▲ +{diff_krw:,}원 (+{diff_pct:.1f}%)</span>'
            elif diff_krw < 0:
                diff_badge_html = f'<span class="diff-badge diff-down" title="전일 대비 환율·시세 종합 {diff_krw:,}원 ({diff_pct:.1f}%) 하락">▼ {diff_krw:,}원 ({diff_pct:.1f}%)</span>'
            else:
                diff_badge_html = f'<span class="diff-badge diff-flat" title="전일 대비 보합">- 0원 (0.0%)</span>'

        ai_content = ""
        articles = []
        if md_content:
            sec_pattern = re.compile(rf'## <a id="[^"]+"></a>(?:\d+\.\s*)?[^#\n]*{re.escape(m["name_kr"])}[^\n]*\n(.*?)(?=\n---|\Z)', re.DOTALL)
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
            "diff_krw": diff_krw,
            "diff_pct": diff_pct,
            "diff_badge_html": diff_badge_html,
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
        "csv_path": f"./resources/{date_str}/{urllib.parse.quote(csv_filename)}",
        "html_report_path": f"./resources/{date_str}/{urllib.parse.quote(html_filename)}",
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
        report_filename = f"[통합브리핑] 9대_금속원자재_{d}.html"
        if not os.path.exists(os.path.join(RESOURCES_DIR, d, report_filename)):
            report_filename = f"[통합브리핑] 7대_금속원자재_{d}.html"
        report_url = f"{SITE_URL}/resources/{d}/{urllib.parse.quote(report_filename)}"
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
    """메인 웹사이트 index.html 생성 (대시보드 + 계산기 + 모바일 최적화 카드 + 캘린더/스크롤 아카이브 + 완벽 SEO)"""
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
        u_label = m["unit_krw"]
        if m["key"] == "gold":
            u_label = "원/g (1돈=3.75g)"
        elif m["key"] == "silver":
            u_label = "원/g (1kg=1,000g)"
        calc_metals.append({
            "key": m["key"],
            "name": m["name_kr"],
            "unit": m["unit_krw"].split("/")[1] if "/" in m["unit_krw"] else "kg",
            "unit_label": u_label,
            "price": m["krw_price"],
            "scrap_70": m["scrap_70"],
            "scrap_80": m["scrap_80"],
            "emoji": m["emoji"],
            "cat": m["cat"]
        })
    calc_json = json.dumps(calc_metals, ensure_ascii=False)

    # 1-A. 데스크톱용 9대 자원 테이블 행
    table_rows = []
    for m in data["metals"]:
        badge_div = f"<div style='margin-top:3px;'>{m['diff_badge_html']}</div>" if m.get("diff_badge_html") else ""
        table_rows.append(f"""
        <tr class="table-row" data-cat="{m['cat']}">
            <td class="col-type"><span class="badge badge-{m['cat']}">{m['emoji']} {m['type_label']}</span></td>
            <td class="col-name"><strong>{m['name_kr']}</strong> <span class="text-sub">({m['name_en']})</span></td>
            <td class="col-raw font-mono">{m['raw_price']}</td>
            <td class="col-krw font-bold text-blue">
                <div>{m['krw_price']:,} {m['unit_krw']}</div>
                {badge_div}
            </td>
            <td class="col-scrap font-bold text-amber">
                <span class="scrap-badge">{m['scrap_70']:,} ~ {m['scrap_80']:,} {m['unit_krw']}</span>
            </td>
            <td class="col-action">
                <button class="btn-sm" onclick="setCalculatorTarget('{m['key']}')">🧮 계산</button>
                <a href="#card-{m['key']}" class="btn-sm btn-outline">차트·분석 ↓</a>
            </td>
        </tr>""")

    # 1-B. 모바일 전용 시세 카드 (가로 스크롤 완전 해결!)
    mobile_price_cards = []
    for m in data["metals"]:
        badge_div = f"<div style='margin-top:2px;'>{m['diff_badge_html']}</div>" if m.get("diff_badge_html") else ""
        mobile_price_cards.append(f"""
        <div class="m-price-card" data-cat="{m['cat']}">
            <div class="m-card-top">
                <div class="m-card-title">
                    <span class="m-card-emoji">{m['emoji']}</span>
                    <strong>{m['name_kr']}</strong>
                    <span class="text-sub">({m['name_en']})</span>
                </div>
                <span class="badge badge-{m['cat']}">{m['type_label']}</span>
            </div>
            <div class="m-card-stats">
                <div class="m-stat-row">
                    <span class="m-stat-label">국제 시장 종가</span>
                    <span class="m-stat-val font-mono">{m['raw_price']}</span>
                </div>
                <div class="m-stat-row m-stat-blue">
                    <span class="m-stat-label">원화 환산 시장가</span>
                    <div style="text-align: right;">
                        <span class="m-stat-val font-bold text-blue">{m['krw_price']:,} {m['unit_krw']}</span>
                        {badge_div}
                    </div>
                </div>
                <div class="m-scrap-box">
                    <div class="m-scrap-label">♻️ 스크랩 매입 추정가 (70~80%)</div>
                    <div class="m-scrap-price font-bold text-amber">{m['scrap_70']:,} ~ {m['scrap_80']:,} {m['unit_krw']}</div>
                </div>
            </div>
            <div class="m-card-btns">
                <button class="btn-sm btn-blue-sm" onclick="setCalculatorTarget('{m['key']}')">🧮 계산기에 넣기</button>
                <a href="#card-{m['key']}" class="btn-sm btn-outline">차트 & AI 분석 ↓</a>
            </div>
        </div>""")

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
                        <div style="margin-top:2px;">{m.get('diff_badge_html', '')}</div>
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

    # 3. 아카이브 데이터 구조화 (캘린더 및 스크롤 박스용 - 팔라듐 대신 금 표시)
    archived_data_list = []
    for d in archived_dates:
        c_path = os.path.join(RESOURCES_DIR, d, f"9대자원_환산시세_{d}.csv")
        if not os.path.exists(c_path):
            c_path = os.path.join(RESOURCES_DIR, d, f"7대자원_환산시세_{d}.csv")
        rate_val = 1344.4
        steel_p = "-"
        copper_p = "-"
        gold_p = "-"
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
                        elif cr.get("자원명") == "금":
                            gold_p = f"{int(float(cr['원화시장단가(원)'])):,}원/g"
                        elif cr.get("자원명") == "팔라듐":
                            pd_p = f"{int(float(cr['원화시장단가(원)'])):,}원/g"
        report_filename = f"[통합브리핑] 9대_금속원자재_{d}.html"
        if not os.path.exists(os.path.join(RESOURCES_DIR, d, report_filename)):
            report_filename = f"[통합브리핑] 7대_금속원자재_{d}.html"
        csv_filename = f"9대자원_환산시세_{d}.csv"
        if not os.path.exists(os.path.join(RESOURCES_DIR, d, csv_filename)):
            csv_filename = f"7대자원_환산시세_{d}.csv"

        report_url = f"./resources/{d}/{urllib.parse.quote(report_filename)}"
        csv_url = f"./resources/{d}/{urllib.parse.quote(csv_filename)}"
        archived_data_list.append({
            "date": d,
            "rate": rate_val,
            "steel": steel_p,
            "copper": copper_p,
            "gold": gold_p,
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>더패스랩 9대 금속원자재 & 스크랩 시세 허브 | 실시간 고철·비철·귀금속·PGM 매입 단가</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="매일 업데이트되는 9대 금속원자재(구리, 철스크랩, 알루미늄, 납, 금, 은, 백금, 팔라듐, 로듐)의 국제 시세 및 원화 환산 kg당·g당 단가, 스크랩 매입 추정가 계산기, 조달청 비축물자 판매가격표 종합 허브입니다.">
    <meta name="keywords" content="고철시세, 철스크랩가격, 구리kg가격, 알루미늄시세, 납시세, 금시세, 은시세, 백금시세, 팔라듐시세, 로듐가격, 폐촉매가격, 폐배터리시세, 조달청원자재판매가격, 더패스랩, ThePathLab">
    <meta name="author" content="ThePathLab">
    <link rel="canonical" href="{SITE_URL}/">
    <link rel="alternate" type="application/rss+xml" title="ThePathLab 9대 금속원자재 시황 RSS" href="{SITE_URL}/rss.xml">

    <!-- Open Graph / Social Sharing -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{SITE_URL}/">
    <meta property="og:title" content="더패스랩 9대 금속원자재 & 스크랩 시세 허브">
    <meta property="og:description" content="오늘자 실시간 환산 시장가 및 스크랩(70~80%) 매입 계산기, 조달청 고시표, Trading Economics 1년 시세 차트">
    <meta property="og:image" content="{SITE_URL}/resources/{latest_date}/{urllib.parse.quote(f'조달청_원자재_판매가격_{latest_date}.png')}">

    <!-- Google Structured Data (Schema.org) -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "ThePathLab Metals & Scrap Data Hub",
        "url": "{SITE_URL}/",
        "description": "9대 금속원자재 국제시세 및 스크랩 매입 단가 데이터 허브",
        "publisher": {{
            "@type": "Organization",
            "name": "ThePathLab"
        }}
    }}
    </script>

    <!-- Fonts & Icons -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

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
        html, body {{
            overflow-x: hidden;
            width: 100%;
            background-color: var(--bg);
            color: var(--text-main);
            font-family: var(--font-family);
            line-height: 1.6;
            -webkit-text-size-adjust: 100%;
        }}
        body {{
            padding-bottom: 80px;
        }}
        a {{ color: var(--primary); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            width: 100%;
        }}

        /* TPL Global Unified Navigation Bar & Drawer */
        :root {{
            --tpl-bg-nav: rgba(8, 12, 22, 0.94);
            --tpl-bg-drawer: rgba(11, 15, 25, 0.98);
            --tpl-border: rgba(255, 255, 255, 0.08);
            --tpl-border-glow: rgba(0, 242, 254, 0.35);
            --tpl-cyan: #00f2fe;
            --tpl-blue: #38bdf8;
            --tpl-gold: #ffb800;
            --tpl-red: #f43f5e;
            --tpl-text-main: #f8fafc;
            --tpl-text-sub: #94a3b8;
            --tpl-text-dim: #64748b;
        }}

        .tpl-nav-bar {{
            position: sticky;
            top: 0;
            left: 0;
            right: 0;
            z-index: 10000;
            background: var(--tpl-bg-nav);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--tpl-border);
            padding: 0.65rem 1.25rem;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }}
        .tpl-nav-inner {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }}
        .tpl-nav-brand {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            color: #ffffff;
            font-weight: 800;
            font-size: 1.18rem;
            letter-spacing: -0.4px;
            flex-shrink: 0;
        }}
        .tpl-nav-brand i {{
            color: var(--tpl-gold);
            font-size: 1.3rem;
            filter: drop-shadow(0 0 6px rgba(255, 184, 0, 0.5));
        }}
        .tpl-brand-badge {{
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--tpl-gold);
            background: rgba(255, 184, 0, 0.12);
            border: 1px solid rgba(255, 184, 0, 0.25);
            padding: 2px 7px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        .tpl-nav-links {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .tpl-nav-link {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            color: var(--tpl-text-sub);
            text-decoration: none;
            font-size: 0.88rem;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
            white-space: nowrap;
        }}
        .tpl-nav-link i {{
            font-size: 0.95rem;
            color: var(--tpl-blue);
        }}
        .tpl-nav-link:hover {{
            color: #ffffff;
            background: rgba(255, 255, 255, 0.07);
            text-decoration: none;
        }}
        .tpl-nav-link.active {{
            color: #ffca28;
            background: rgba(255, 184, 0, 0.15);
            border: 1px solid rgba(255, 184, 0, 0.35);
        }}
        .tpl-nav-link.active i {{
            color: #ffca28;
        }}
        .tpl-nav-actions {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-shrink: 0;
        }}
        .tpl-lang-wrap {{
            display: inline-flex;
            align-items: center;
            gap: 3px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--tpl-border);
            padding: 3px 6px;
            border-radius: 8px;
        }}
        .tpl-lang-btn {{
            background: transparent;
            border: none;
            color: var(--tpl-text-sub);
            cursor: pointer;
            font-size: 0.74rem;
            font-weight: 600;
            padding: 3px 5px;
            border-radius: 4px;
            transition: all 0.15s;
        }}
        .tpl-lang-btn:hover {{
            color: #ffffff;
            background: rgba(255, 255, 255, 0.1);
        }}
        .tpl-lang-sep {{
            color: #334155;
            font-size: 0.7rem;
        }}
        .tpl-hamburger-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--tpl-border);
            color: var(--tpl-text-main);
            width: 38px;
            height: 38px;
            border-radius: 10px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
            transition: all 0.2s ease;
        }}
        .tpl-hamburger-btn:hover {{
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
            transform: scale(1.05);
        }}

        /* Off-Canvas Drawer */
        .tpl-drawer-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(5px);
            z-index: 10001;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.25s ease, visibility 0.25s ease;
        }}
        .tpl-drawer-overlay.open {{ opacity: 1; visibility: visible; }}

        .tpl-drawer {{
            position: fixed;
            top: 0;
            right: 0;
            bottom: 0;
            width: 340px;
            max-width: 88vw;
            background: var(--tpl-bg-drawer);
            border-left: 1px solid var(--tpl-border);
            z-index: 10002;
            transform: translateX(100%);
            transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
        }}
        .tpl-drawer.open {{ transform: translateX(0); }}

        .tpl-drawer-header {{
            padding: 1.2rem 1.4rem;
            border-bottom: 1px solid var(--tpl-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(8, 12, 22, 0.95);
        }}
        .tpl-drawer-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            color: #fff;
            font-weight: 800;
            font-size: 1.1rem;
        }}
        .tpl-drawer-brand i {{ color: var(--tpl-gold); font-size: 1.3rem; }}
        .tpl-drawer-title {{ font-size: 1.02rem; font-weight: 800; color: #f8fafc; }}
        .tpl-drawer-sub {{ font-size: 0.72rem; color: var(--tpl-text-dim); }}

        .tpl-drawer-close {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--tpl-border);
            color: var(--tpl-text-sub);
            width: 34px;
            height: 34px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
        }}
        .tpl-drawer-close:hover {{
            background: rgba(255, 255, 255, 0.12);
            color: #fff;
        }}

        .tpl-drawer-body {{
            padding: 1.2rem;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 1.4rem;
        }}
        .tpl-drawer-group-title {{
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--tpl-text-dim);
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .tpl-drawer-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 10px;
            text-decoration: none;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--tpl-border);
            transition: all 0.2s;
            margin-bottom: 6px;
        }}
        .tpl-drawer-item:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 184, 0, 0.35);
            transform: translateX(3px);
            text-decoration: none;
        }}
        .tpl-drawer-icon {{
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
            flex-shrink: 0;
        }}
        .icon-portal {{ background: rgba(0, 242, 254, 0.15); color: var(--tpl-cyan); }}
        .icon-metals {{ background: rgba(255, 184, 0, 0.15); color: var(--tpl-gold); }}
        .icon-engines {{ background: rgba(56, 189, 248, 0.15); color: var(--tpl-blue); }}
        .icon-autoissue {{ background: rgba(244, 63, 94, 0.15); color: var(--tpl-red); }}

        .tpl-drawer-item-title {{ font-size: 0.92rem; font-weight: 700; color: #f1f5f9; margin-bottom: 2px; }}
        .tpl-drawer-item-desc {{ font-size: 0.75rem; color: var(--tpl-text-dim); line-height: 1.35; }}

        .tpl-drawer-chips {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .tpl-chip-link {{
            font-size: 0.8rem;
            font-weight: 600;
            text-decoration: none;
            color: var(--tpl-text-sub);
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--tpl-border);
            padding: 5px 10px;
            border-radius: 8px;
            transition: all 0.2s;
        }}
        .tpl-chip-link:hover {{
            color: #fff;
            background: rgba(0, 242, 254, 0.15);
            border-color: var(--tpl-border-glow);
            text-decoration: none;
        }}

        .tpl-drawer-langs {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }}
        .tpl-drawer-lang-btn {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--tpl-border);
            color: var(--tpl-text-sub);
            padding: 7px 10px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            text-align: left;
            transition: all 0.15s;
        }}
        .tpl-drawer-lang-btn:hover {{ color: #fff; background: rgba(255, 255, 255, 0.1); }}

        .tpl-drawer-sublinks {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .tpl-drawer-sublinks a {{
            color: var(--tpl-text-sub);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 4px 6px;
            border-radius: 6px;
            transition: color 0.15s;
        }}
        .tpl-drawer-sublinks a:hover {{
            color: var(--tpl-cyan);
            text-decoration: none;
        }}

        .tpl-drawer-footer {{
            padding: 1rem 1.4rem;
            border-top: 1px solid var(--tpl-border);
            font-size: 0.78rem;
            color: var(--tpl-text-dim);
            background: rgba(8, 12, 22, 0.95);
            text-align: center;
        }}

        @media (max-width: 920px) {{
            .tpl-nav-links {{ display: none; }}
        }}
        @media (max-width: 480px) {{
            .tpl-lang-wrap {{ display: none; }}
        }}
        .meta-tag {{
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 12.5px;
            color: var(--text-sub);
            white-space: nowrap;
        }}
        .meta-tag strong {{ color: var(--text-main); }}

        /* Hero Banner */
        .hero-banner {{
            background: radial-gradient(circle at top left, #1e3a8a 0%, #1e293b 60%);
            border: 1px solid #3b82f6;
            border-radius: 16px;
            padding: 22px 24px;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 18px;
        }}
        .hero-left h1 {{
            font-size: clamp(18px, 3.5vw, 22px);
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .hero-left p {{
            color: #cbd5e1;
            font-size: 14px;
            max-width: 680px;
            line-height: 1.5;
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
            justify-content: center;
            gap: 6px;
            white-space: nowrap;
        }}
        .btn:hover {{
            background: #2563eb;
            transform: translateY(-1px);
        }}
        .btn-green {{ background: #059669; }}
        .btn-green:hover {{ background: #047857; }}
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
            padding: 6px 12px;
            font-size: 12.5px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--surface);
            color: var(--text-main);
            cursor: pointer;
            transition: background 0.15s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
        }}
        .btn-sm:hover {{ background: var(--surface-hover); }}
        .btn-blue-sm {{
            background: #2563eb;
            color: white;
            border-color: #3b82f6;
            font-weight: 600;
        }}
        .btn-blue-sm:hover {{ background: #1d4ed8; }}
        .btn-sub {{
            background: #334155;
            color: #e2e8f0;
        }}

        /* 🧮 Interactive Calculator Widget */
        .calc-box {{
            background: linear-gradient(145deg, #1e293b 0%, #172554 100%);
            border: 2px solid #3b82f6;
            border-radius: 16px;
            padding: 22px 24px;
            margin-bottom: 32px;
            box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);
        }}
        .calc-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .calc-header h2 {{
            font-size: clamp(17px, 3.2vw, 20px);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .calc-grid {{
            display: grid;
            grid-template-columns: 1.2fr 1fr 1.6fr;
            gap: 16px;
            align-items: center;
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
            padding: 14px 18px;
        }}
        .calc-res-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid #1e293b;
            gap: 10px;
        }}
        .calc-res-row:last-child {{ border-bottom: none; }}
        .calc-res-label {{ font-size: 13px; color: var(--text-sub); }}
        .calc-res-val {{ font-size: 16px; font-weight: 700; }}
        .calc-res-highlight {{
            font-size: clamp(17px, 3.5vw, 21px);
            color: #34d399;
            font-weight: 800;
            text-align: right;
        }}

        /* Price Section Header */
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .section-title {{
            font-size: clamp(18px, 3.2vw, 20px);
            font-weight: 700;
        }}
        .tabs {{
            display: flex;
            gap: 4px;
            background: var(--surface);
            padding: 4px;
            border-radius: 8px;
            border: 1px solid var(--border);
            overflow-x: auto;
            max-width: 100%;
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
            white-space: nowrap;
        }}
        .tab-btn.active {{
            background: var(--primary);
            color: white;
        }}

        /* 🖥️ Desktop Table Wrap */
        .table-wrap {{
            overflow-x: auto;
            background: var(--surface);
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 36px;
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
        tr:hover td {{ background: var(--surface-hover); }}

        /* 📈 Price Diff Badge (전일 대비 환율+시세 변동 뱃지) */
        .diff-badge {{
            display: inline-flex;
            align-items: center;
            gap: 3px;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            letter-spacing: -0.2px;
            font-family: 'JetBrains Mono', monospace;
            white-space: nowrap;
        }}
        .diff-up {{
            color: #34d399;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        .diff-down {{
            color: #f87171;
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}
        .diff-flat {{
            color: #94a3b8;
            background: rgba(148, 163, 184, 0.1);
            border: 1px solid rgba(148, 163, 184, 0.2);
        }}

        /* 🧭 Floating Action Bar (FAB) & Guide Modal */
        .fab-container {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 9999;
            opacity: 0;
            visibility: hidden;
            transform: translateY(15px);
            transition: all 0.25s ease;
        }}
        .fab-container.visible {{
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }}
        .fab-btn {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: 1px solid rgba(255, 255, 255, 0.15);
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            color: #f8fafc;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 17px;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
            transition: all 0.2s ease;
            position: relative;
        }}
        .fab-btn:hover {{
            background: #2563eb;
            color: white;
            border-color: #60a5fa;
            transform: scale(1.08);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
        }}
        .fab-guide {{
            background: rgba(16, 185, 129, 0.2);
            border-color: rgba(16, 185, 129, 0.4);
            color: #34d399;
        }}
        .fab-guide:hover {{
            background: #059669;
            color: white;
            border-color: #34d399;
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        }}
        .fab-guide-tooltip {{
            position: absolute;
            right: 52px;
            white-space: nowrap;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #f8fafc;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            pointer-events: none;
            opacity: 0;
            transform: translateX(6px);
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}
        .fab-guide:hover .fab-guide-tooltip {{
            opacity: 1;
            transform: translateX(0);
        }}

        /* Guide Modal */
        .guide-modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(8, 12, 22, 0.75);
            backdrop-filter: blur(8px);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            opacity: 0;
            visibility: hidden;
            transition: all 0.25s ease;
        }}
        .guide-modal-overlay.open {{
            opacity: 1;
            visibility: visible;
        }}
        .guide-modal {{
            background: #1e293b;
            border: 1px solid #3b82f6;
            border-radius: 16px;
            max-width: 520px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
            overflow: hidden;
            transform: scale(0.95);
            transition: transform 0.25s ease;
        }}
        .guide-modal-overlay.open .guide-modal {{
            transform: scale(1);
        }}
        .guide-modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: #0f172a;
            border-bottom: 1px solid var(--border);
        }}
        .guide-close-btn {{
            background: transparent;
            border: none;
            color: #94a3b8;
            font-size: 24px;
            line-height: 1;
            cursor: pointer;
            padding: 0;
        }}
        .guide-close-btn:hover {{ color: white; }}
        .guide-modal-body {{
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            max-height: 80vh;
            overflow-y: auto;
        }}
        .guide-tip-item {{
            display: flex;
            gap: 12px;
            align-items: flex-start;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            padding: 12px 14px;
        }}
        .guide-tip-icon {{
            font-size: 22px;
            flex-shrink: 0;
        }}
        .guide-tip-content strong {{
            display: block;
            font-size: 13.5px;
            color: #60a5fa;
            margin-bottom: 4px;
        }}
        .guide-tip-content p {{
            font-size: 12.5px;
            color: #cbd5e1;
            line-height: 1.55;
            margin: 0;
        }}
        .guide-tip-footer {{
            margin-top: 6px;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }}

        /* 📱 Mobile Price Cards (가로 스크롤 없는 모바일 완벽 대응 카드형 뷰) */
        .mobile-price-cards {{
            display: none;
            flex-direction: column;
            gap: 14px;
            margin-bottom: 36px;
        }}
        .m-price-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }}
        .m-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #334155;
            padding-bottom: 10px;
            margin-bottom: 12px;
        }}
        .m-card-title {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 16px;
        }}
        .m-card-emoji {{ font-size: 20px; }}
        .m-card-stats {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 14px;
        }}
        .m-stat-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13.5px;
        }}
        .m-stat-label {{ color: var(--text-sub); }}
        .m-stat-val {{ color: var(--text-main); font-weight: 600; }}
        .m-scrap-box {{
            background: rgba(245, 158, 11, 0.12);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 8px;
            padding: 10px 12px;
            margin-top: 4px;
        }}
        .m-scrap-label {{
            font-size: 12px;
            color: #fcd34d;
            font-weight: 600;
            margin-bottom: 2px;
        }}
        .m-scrap-price {{
            font-size: 17px;
            color: #fbbf24;
            font-weight: 800;
        }}
        .m-card-btns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
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
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            white-space: nowrap;
        }}
        .badge-steel {{ background: #334155; color: #cbd5e1; }}
        .badge-nonferrous {{ background: #1e3a8a; color: #93c5fd; }}
        .badge-precious {{ background: #78350f; color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); }}
        .badge-pgm {{ background: #581c87; color: #e9d5ff; }}

        /* PPS Image Section */
        .pps-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 36px;
        }}
        .pps-img-wrap {{
            text-align: center;
            background: #0f172a;
            padding: 12px;
            border-radius: 8px;
            margin-top: 12px;
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
            padding: 22px;
            margin-bottom: 24px;
        }}
        .card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 14px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        .card-title-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .card-icon {{ font-size: 26px; }}
        .card-name {{ font-size: clamp(17px, 3vw, 20px); font-weight: 800; }}
        .card-en {{ font-size: 13px; color: var(--text-sub); font-weight: normal; }}
        .card-price-pills {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .pill {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 12px;
            flex: 1;
            min-width: 140px;
            box-sizing: border-box;
            word-break: break-word;
        }}
        .pill-label {{ font-size: 11px; color: var(--text-muted); display: block; }}
        .pill-val {{ font-size: 14px; font-weight: 700; color: var(--text-main); }}
        .pill-blue .pill-val {{ color: #60a5fa; }}
        .pill-amber .pill-val {{ color: #fbbf24; }}

        .card-chart {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 18px;
            text-align: center;
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            font-size: 12.5px;
            color: var(--text-sub);
            margin-bottom: 8px;
        }}
        .card-chart img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}

        .card-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}
        .card-news, .card-ai {{
            background: #172554;
            border-radius: 10px;
            padding: 16px;
        }}
        .card-ai {{
            background: #1e1b4b;
            border-left: 4px solid #818cf8;
        }}
        .ai-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
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
            margin-left: 16px;
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
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .art-item:last-child {{ border-bottom: none; margin-bottom: 0; }}
        .art-title {{
            font-size: 13.5px;
            font-weight: 600;
            color: #93c5fd;
            line-height: 1.4;
            display: inline-block;
        }}
        .art-meta {{
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 2px;
        }}
        .art-desc {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 4px;
            line-height: 1.4;
        }}

        /* 📅 Archive Section: Mobile-first responsive layout */
        .archive-box {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
            margin-top: 40px;
        }}
        .archive-panes {{
            display: grid;
            grid-template-columns: 340px 1fr;
            gap: 20px;
            margin-top: 16px;
        }}

        /* Calendar Widget */
        .cal-card {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
        }}
        .cal-nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .cal-title {{
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
        }}
        .cal-btn {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-main);
            width: 32px;
            height: 32px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }}
        .cal-btn:hover {{ background: var(--surface-hover); }}
        .cal-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 3px;
            text-align: center;
        }}
        .cal-day-head {{
            font-size: 11.5px;
            color: var(--text-muted);
            font-weight: 600;
            padding: 4px 0;
        }}
        .cal-day-head.sun {{ color: #f87171; }}
        .cal-day-head.sat {{ color: #60a5fa; }}
        .cal-cell {{
            height: 34px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            font-size: 12.5px;
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
            transform: scale(1.04);
        }}
        .cal-cell.selected {{
            background: #059669 !important;
            border-color: #34d399 !important;
            color: white !important;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
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
            padding: 16px;
            display: flex;
            flex-direction: column;
        }}
        .scroll-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            gap: 10px;
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
            max-height: 280px;
            overflow-y: auto;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .scroll-list-wrap::-webkit-scrollbar {{ width: 6px; }}
        .scroll-list-wrap::-webkit-scrollbar-track {{ background: #0f172a; }}
        .scroll-list-wrap::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}

        .scroll-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .scroll-table th {{
            background: #1e293b;
            padding: 8px 10px;
            font-size: 12px;
            color: #94a3b8;
            position: sticky;
            top: 0;
            z-index: 2;
        }}
        .scroll-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid #1e293b;
        }}
        .scroll-table tr:hover td {{ background: #1e293b; }}

        /* Selected Date Preview Bar */
        .date-preview-bar {{
            background: #1e293b;
            border-radius: 8px;
            padding: 12px 14px;
            margin-top: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            border-left: 4px solid #10b981;
        }}
        .preview-left strong {{ font-size: 14.5px; color: white; }}
        .preview-prices {{
            display: flex;
            gap: 12px;
            font-size: 12.5px;
            color: var(--text-sub);
            flex-wrap: wrap;
        }}
        .preview-prices span strong {{ color: #38bdf8; }}

        /* Toast */
        .toast {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            left: 20px;
            max-width: 400px;
            margin: 0 auto;
            background: #10b981;
            color: white;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 13.5px;
            font-weight: 600;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            display: none;
            z-index: 9999;
            text-align: center;
        }}

        footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }}

        /* ==============================================================
           📱 Mobile Breakpoint: @media (max-width: 768px)
           모바일 화면에서 가로 스크롤 완전 제거 & 캘린더 깨짐 완벽 방지
           ============================================================== */
        @media (max-width: 768px) {{
            .container {{
                padding: 0 12px;
            }}
            header {{
                padding: 16px 0 14px 0;
                margin-bottom: 20px;
            }}
            .header-inner {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
            .header-meta {{
                width: 100%;
                justify-content: space-between;
            }}
            .hero-banner {{
                padding: 16px;
                border-radius: 12px;
                margin-bottom: 22px;
            }}
            .hero-actions {{
                width: 100%;
            }}
            .hero-actions .btn {{
                flex: 1;
            }}
            .calc-box {{
                padding: 16px 12px;
                border-radius: 12px;
                margin-bottom: 24px;
                width: 100% !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }}
            .calc-grid {{
                grid-template-columns: 1fr;
                gap: 12px;
            }}
            
            /* 모바일에서는 테이블 숨기고, 전용 카드 뷰 활성화 */
            .table-wrap {{
                display: none !important;
            }}
            .mobile-price-cards {{
                display: flex !important;
                width: 100% !important;
            }}
            .m-price-card {{
                width: 100% !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }}
            .m-stat-row {{
                gap: 8px;
                flex-wrap: wrap;
            }}

            .card-grid {{
                grid-template-columns: 1fr;
                gap: 12px;
            }}
            .card-top {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
            /* 모바일 카드 안 알약 1fr 수직 배치로 카드 밖 삐져나감 완전 방지 */
            .card-price-pills {{
                display: grid !important;
                grid-template-columns: 1fr !important;
                gap: 8px !important;
                width: 100% !important;
            }}
            .pill {{
                width: 100% !important;
                min-width: 0 !important;
                box-sizing: border-box !important;
            }}
            .metal-card {{
                padding: 16px 12px;
                border-radius: 12px;
                margin-bottom: 20px;
                width: 100% !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }}
            .art-title, .art-desc, .ai-bullet, .ai-para, .pill-val {{
                word-break: break-word !important;
                overflow-wrap: break-word !important;
            }}

            /* 아카이브 섹션 모바일 대응 */
            .archive-box {{
                padding: 14px 10px;
                border-radius: 12px;
                margin-top: 30px;
                width: 100% !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }}
            .archive-panes {{
                grid-template-columns: 1fr;
                gap: 14px;
            }}
            .cal-card {{
                padding: 12px 6px;
            }}
            .cal-cell {{
                height: 32px;
                font-size: 12px;
            }}
            .scroll-card {{
                padding: 12px 8px;
            }}
            .scroll-list-wrap {{
                max-height: 240px;
            }}
            .scroll-table th, .scroll-table td {{
                padding: 8px 6px;
                font-size: 11.5px;
            }}
            .date-preview-bar {{
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
                padding: 10px;
            }}
            .preview-prices {{
                flex-direction: column;
                gap: 4px;
                font-size: 12px;
            }}
            .date-preview-bar > div:last-child {{
                width: 100%;
                display: flex;
            }}
            .date-preview-bar > div:last-child .btn-sm {{
                flex: 1;
            }}
        }}
    </style>
</head>
<body>

    <!-- ThePathLab Global Unified Navigation Bar -->
    <nav class="tpl-nav-bar" id="tplNavBar">
      <div class="tpl-nav-inner">
        <a href="https://chicstory.github.io/" class="tpl-nav-brand">
          <i class="bi-bounding-box-circles"></i>
          <span>ThePathLab</span>
          <span class="tpl-brand-badge" id="tplNavBadge">METALS</span>
        </a>

        <div class="tpl-nav-links">
          <a href="https://chicstory.github.io/" class="tpl-nav-link"><i class="bi-house-door"></i> 포털 홈</a>
          <a href="https://chicstory.github.io/autoissue/" class="tpl-nav-link"><i class="bi-bell-fill"></i> 자동차 데일리 이슈</a>
          <a href="https://chicstory.github.io/metals/" class="tpl-nav-link active"><i class="bi-graph-up-arrow"></i> 금속 원자재·스크랩</a>
          <a href="https://chicstory.github.io/engines/hyundai_kia_engine_table.html" class="tpl-nav-link"><i class="bi-table"></i> 제조사별 스펙표</a>
          <a href="https://chicstory.github.io/engines/" class="tpl-nav-link"><i class="bi-cpu"></i> 엔진 전수 백과</a>
          <a href="https://chicstory.github.io/guide.html" class="tpl-nav-link"><i class="bi-compass"></i> 이용 가이드</a>
        </div>

        <div class="tpl-nav-actions">
          <div class="tpl-lang-wrap">
            <button type="button" class="tpl-lang-btn" onclick="tplChangeLang('ko')">KO</button>
            <span class="tpl-lang-sep">|</span>
            <button type="button" class="tpl-lang-btn" onclick="tplChangeLang('en')">EN</button>
            <span class="tpl-lang-sep">|</span>
            <button type="button" class="tpl-lang-btn" onclick="tplChangeLang('ru')">RU</button>
            <span class="tpl-lang-sep">|</span>
            <button type="button" class="tpl-lang-btn" onclick="tplChangeLang('es')">ES</button>
          </div>
          <button type="button" class="tpl-hamburger-btn" id="tplHamburgerBtn" aria-label="전체 메뉴 열기">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block;"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
          </button>
        </div>
      </div>
    </nav>

    <!-- Backdrop Overlay -->
    <div class="tpl-drawer-overlay" id="tplDrawerOverlay"></div>

    <!-- Off-Canvas Drawer (Slide from Right) -->
    <aside class="tpl-drawer" id="tplDrawer" aria-hidden="true">
      <div class="tpl-drawer-header">
        <div class="tpl-drawer-brand">
          <i class="bi-bounding-box-circles"></i>
          <div>
            <div class="tpl-drawer-title">ThePathLab Network</div>
            <div class="tpl-drawer-sub">산업 원자재 & 모빌리티 테크 인텔리전스</div>
          </div>
        </div>
        <button type="button" class="tpl-drawer-close" id="tplDrawerClose" aria-label="메뉴 닫기">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block;"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <div class="tpl-drawer-body">
        <!-- Section 1: Core Hubs -->
        <div class="tpl-drawer-group">
          <div class="tpl-drawer-group-title"><i class="bi-stars"></i> 핵심 서비스 포털</div>
          <a href="https://chicstory.github.io/" class="tpl-drawer-item">
            <div class="tpl-drawer-icon icon-portal"><i class="bi-house-door"></i></div>
            <div class="tpl-drawer-item-text">
              <div class="tpl-drawer-item-title">ThePathLab 포털 메인</div>
              <div class="tpl-drawer-item-desc">통합 인텔리전스 허브 대시보드</div>
            </div>
          </a>
          <a href="https://chicstory.github.io/autoissue/" class="tpl-drawer-item">
            <div class="tpl-drawer-icon" style="background: rgba(244, 63, 94, 0.15); color: #fb7185;"><i class="bi-bell-fill"></i></div>
            <div class="tpl-drawer-item-text">
              <div class="tpl-drawer-item-title">자동차 데일리 이슈 허브</div>
              <div class="tpl-drawer-item-desc">10대 제조사 결함·리콜 & 미국 NHTSA 선제 공고</div>
            </div>
          </a>
          <a href="https://chicstory.github.io/metals/" class="tpl-drawer-item" style="border-color: rgba(255, 184, 0, 0.4); background: rgba(255, 184, 0, 0.08);">
            <div class="tpl-drawer-icon icon-metals"><i class="bi-graph-up-arrow"></i></div>
            <div class="tpl-drawer-item-text">
              <div class="tpl-drawer-item-title" style="color: #ffb800;">9대 금속 원자재 & 스크랩 허브 (현재)</div>
              <div class="tpl-drawer-item-desc">일일 시세 분석 · 1초 즉시 계산기 · 캘린더 아카이브</div>
            </div>
          </a>
          <a href="https://chicstory.github.io/engines/hyundai_kia_engine_table.html" class="tpl-drawer-item">
            <div class="tpl-drawer-icon" style="background: rgba(168, 85, 247, 0.15); color: #c084fc;"><i class="bi-table"></i></div>
            <div class="tpl-drawer-item-text">
              <div class="tpl-drawer-item-title">제조사별 전수 스펙표</div>
              <div class="tpl-drawer-item-desc">6대 제조사 244종 엔진 스펙 전수 비교표</div>
            </div>
          </a>
          <a href="https://chicstory.github.io/engines/" class="tpl-drawer-item">
            <div class="tpl-drawer-icon icon-engines"><i class="bi-cpu"></i></div>
            <div class="tpl-drawer-item-text">
              <div class="tpl-drawer-item-title">자동차 엔진 전수 백과사전</div>
              <div class="tpl-drawer-item-desc">260개 파워트레인 실측 제원 & 다이노 그래프</div>
            </div>
          </a>
        </div>

        <!-- Section 2: Manufacturer Tables Quick Jump -->
        <div class="tpl-drawer-group">
          <div class="tpl-drawer-group-title"><i class="bi-table"></i> 제조사별 전수 스펙 종합비교표</div>
          <div class="tpl-drawer-chips">
            <a href="https://chicstory.github.io/engines/hyundai_kia_engine_table.html" class="tpl-chip-link">현대·기아 (87종)</a>
            <a href="https://chicstory.github.io/engines/bmw_engine_table.html" class="tpl-chip-link">BMW (45종)</a>
            <a href="https://chicstory.github.io/engines/mercedes_benz_engine_table.html" class="tpl-chip-link">메르세데스-벤츠 (40종)</a>
            <a href="https://chicstory.github.io/engines/audi_engine_table.html" class="tpl-chip-link">아우디 (32종)</a>
            <a href="https://chicstory.github.io/engines/volkswagen_engine_table.html" class="tpl-chip-link">폭스바겐 (20종)</a>
            <a href="https://chicstory.github.io/engines/kgm_ssangyong_engine_table.html" class="tpl-chip-link">KGM·쌍용 (20종)</a>
          </div>
        </div>

        <!-- Section 3: Multi-Language Switcher -->
        <div class="tpl-drawer-group">
          <div class="tpl-drawer-group-title"><i class="bi-globe"></i> 언어 선택 (Language)</div>
          <div class="tpl-drawer-langs">
            <button type="button" class="tpl-drawer-lang-btn" onclick="tplChangeLang('ko')">🇰🇷 한국어</button>
            <button type="button" class="tpl-drawer-lang-btn" onclick="tplChangeLang('en')">🇺🇸 English</button>
            <button type="button" class="tpl-drawer-lang-btn" onclick="tplChangeLang('ru')">🇷🇺 Русский</button>
            <button type="button" class="tpl-drawer-lang-btn" onclick="tplChangeLang('es')">🇪🇸 Español</button>
          </div>
        </div>

        <!-- Section 4: Site Info & Links -->
        <div class="tpl-drawer-group">
          <div class="tpl-drawer-group-title"><i class="bi-info-circle"></i> 서비스 정보 & 채널</div>
          <div class="tpl-drawer-sublinks">
            <a href="https://chicstory.github.io/guide.html"><i class="bi-compass"></i> 이용 가이드 & 사이트맵</a>
            <a href="https://chicstory.github.io/about.html"><i class="bi-shield-check"></i> 소개 (About)</a>
            <a href="https://chicstory.github.io/privacy.html"><i class="bi-lock"></i> 개인정보처리방침</a>
            <a href="https://chicstory.github.io/contact.html"><i class="bi-envelope"></i> 문의하기</a>
          </div>
        </div>
      </div>

      <div class="tpl-drawer-footer">
        <div>ThePathLab Data Intelligence Network</div>
        <div style="font-size: 0.72rem; color: #64748b; margin-top: 4px;">© 2026 ThePathLab. All Rights Reserved.</div>
      </div>
    </aside>

    <main class="container">

        <!-- Hero Banner -->
        <section class="hero-banner">
            <div class="hero-left">
                <div class="hero-meta-bar" style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;">
                    <span class="meta-tag"><i class="bi-calendar3"></i> 기준 일시: <strong>{data['date_str']}</strong></span>
                    <span class="meta-tag"><i class="bi-currency-exchange"></i> 적용 환율: <strong style="color: #38bdf8;">1 USD = {data['usd_rate']:,.1f}원</strong></span>
                    <span class="meta-tag" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.35); color: #34d399;"><i class="bi-shield-check"></i> LME · 조달청 공식 검증</span>
                </div>
                <h1>📊 오늘의 9대 금속원자재 & 스크랩 실시간 시황</h1>
                <p>국제 시장 종가(Trading Economics) 및 조달청 공식 판매가격표를 바탕으로, 비철·철스크랩·귀금속(금·은)·PGM(폐촉매)의 원화 환산 단가와 실무 스크랩 매입 추정 시세(70~80%)를 매일 아침 자동 산출합니다.</p>
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
                <span style="font-size: 12.5px; color: #94a3b8;">* 오늘자 공식 시세 대비 감모·정제 마진(70~80%) 자동 적용</span>
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
                    <div style="margin-top:6px; display:flex; gap:6px; flex-wrap:wrap;">
                        <button type="button" class="btn-sm btn-sub" onclick="document.getElementById('calc-qty').value=3.75; calculateScrap();" style="padding:2px 7px; font-size:11px;">1돈(3.75g)</button>
                        <button type="button" class="btn-sm btn-sub" onclick="document.getElementById('calc-qty').value=37.5; calculateScrap();" style="padding:2px 7px; font-size:11px;">10돈(37.5g)</button>
                        <button type="button" class="btn-sm btn-sub" onclick="document.getElementById('calc-qty').value=100; calculateScrap();" style="padding:2px 7px; font-size:11px;">100(g/kg)</button>
                        <button type="button" class="btn-sm btn-sub" onclick="document.getElementById('calc-qty').value=1000; calculateScrap();" style="padding:2px 7px; font-size:11px;">1,000(1kg/1톤)</button>
                    </div>
                </div>
                <div class="calc-result-box">
                    <div class="calc-res-row">
                        <span class="calc-res-label">공식 원자재 시장 가치</span>
                        <span id="res-market" class="calc-res-val">- 원</span>
                    </div>
                    <div class="calc-res-row">
                        <span class="calc-res-label">♻️ 스크랩 매입 예상 (70%~80%)</span>
                        <span id="res-scrap" class="calc-res-highlight">- 원</span>
                    </div>
                </div>
            </div>
        </section>

        <section style="margin-bottom: 30px;">
            <div class="section-header">
                <div>
                    <h2 class="section-title">💰 9대 금속·원자재 원화 환산 시장가 및 스크랩 매입 추정가</h2>
                    <span style="font-size: 13px; color: var(--text-sub);">환율: 1 USD = {data['usd_rate']:,.1f}원 ({data['rate_source']})</span>
                </div>
                <div class="tabs">
                    <button class="tab-btn active" onclick="filterCategory('all', this)">전체보기</button>
                    <button class="tab-btn" onclick="filterCategory('nonferrous', this)">비철금속</button>
                    <button class="tab-btn" onclick="filterCategory('steel', this)">철스크랩</button>
                    <button class="tab-btn" onclick="filterCategory('precious', this)">귀금속(금·은)</button>
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

            <div class="mobile-price-cards">
                {''.join(mobile_price_cards)}
            </div>
        </section>

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

        <section>
            <div class="section-header">
                <h2 class="section-title">📈 9대 자원별 1년 시세 추이 및 AI 시장·스크랩 여파 분석</h2>
                <div class="text-sub" style="font-size: 13px;">Trading Economics 종가 차트 & Gemma 4 로컬 AI 모델 분석</div>
            </div>
            
            <div class="metal-cards">
                {''.join(cards_html)}
            </div>
        </section>

        <section id="archive-calendar" class="archive-box">
            <div class="section-header" style="margin-bottom: 6px;">
                <div>
                    <h2 class="section-title">📅 일자별 브리핑 & 환산 시세 아카이브</h2>
                    <p style="font-size: 13px; color: var(--text-sub); margin-top: 4px;">과거 일자의 일일 통합 브리핑 리포트(HTML) 및 원본 CSV 시세 데이터를 열람·다운로드할 수 있습니다.</p>
                </div>
            </div>

            <div class="archive-panes">
                <div class="cal-card">
                    <div class="cal-nav">
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
                        <span style="font-size: 14px; font-weight: 700; color: #93c5fd;">📋 브리핑 목록 (<span id="arch-count">0</span>건)</span>
                        <input type="text" id="arch-search" class="search-input" placeholder="날짜 검색 (예: 2026-09)" oninput="filterArchiveList()">
                    </div>
                    <div class="scroll-list-wrap">
                        <table class="scroll-table">
                            <thead>
                                <tr>
                                    <th>발행일</th>
                                    <th>철스크랩</th>
                                    <th>구리</th>
                                    <th>금 (Gold)</th>
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
                            <span>금: <strong id="prev-gold">-</strong></span>
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

    <!-- Floating Action Bar (Top + Guide) -->
    <div class="fab-container" id="fab-container">
        <button class="fab-btn fab-guide" id="fab-guide-btn" onclick="openGuideModal()" title="화면 설명서 & 이용 가이드">
            <i class="bi bi-question-lg"></i>
            <span class="fab-guide-tooltip">화면 설명서 💡</span>
        </button>
        <button class="fab-btn fab-top" id="fab-top-btn" onclick="scrollToTop()" title="맨 위로 이동">
            <i class="bi bi-arrow-up"></i>
        </button>
    </div>

    <!-- Guide Modal (화면 설명서 팝업) -->
    <div class="guide-modal-overlay" id="guide-modal-overlay" onclick="closeGuideModal(event)">
        <div class="guide-modal" onclick="event.stopPropagation()">
            <div class="guide-modal-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">💡</span>
                    <h3 style="font-size: 17px; font-weight: 800; color: #fff; margin: 0;">9대 금속 시세 허브 100% 활용 가이드</h3>
                </div>
                <button class="guide-close-btn" onclick="closeGuideModal()">&times;</button>
            </div>
            <div class="guide-modal-body">
                <div class="guide-tip-item">
                    <div class="guide-tip-icon">🧮</div>
                    <div class="guide-tip-content">
                        <strong>원화 환산 시장가 & 전일 대비 변화량</strong>
                        <p>LME·조달청 국제 종가에 <strong>당일 원/달러 환율</strong>을 실시간 반영하여 원/kg 또는 원/g 실거래 단가를 산출합니다. 뱃지(▲/▼)는 환율 변동과 국제시세 변동이 모두 결합된 전일 대비 실질 단가 변동량입니다.</p>
                    </div>
                </div>
                <div class="guide-tip-item">
                    <div class="guide-tip-icon">♻️</div>
                    <div class="guide-tip-content">
                        <strong>스크랩(고물상) 매입 추정가 (70~80%)</strong>
                        <p>원자재 순수 시세에서 정제·가공비 및 감모 마진을 제외하고 고물상·스크랩 수거업체에서 통상 매입하는 실질 기준가입니다. 상단 표의 [계산] 버튼을 누르면 즉시 수량별 추정 정산액을 계산할 수 있습니다.</p>
                    </div>
                </div>
                <div class="guide-tip-item">
                    <div class="guide-tip-icon">🤖</div>
                    <div class="guide-tip-content">
                        <strong>Gemma 4 AI 시장 분석 & 뉴스</strong>
                        <p>해외 원자재 전문 매체 기사를 실시간 크롤링하여 로컬 Gemma 4 AI가 핵심 요약 및 국내 제조·스크랩 시장 향후 여파를 코멘트합니다.</p>
                    </div>
                </div>
                <div class="guide-tip-footer">
                    <a href="https://chicstory.github.io/guide.html" target="_blank" class="btn btn-primary" style="width: 100%; justify-content: center; padding: 12px 16px;">
                        <span>📖 ThePathLab 전체 사이트 통합 가이드 & 사이트맵 보기 ↗</span>
                    </a>
                </div>
            </div>
        </div>
    </div>

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
            
            // Adjust default quantity if Gold/Silver/PGM (g) vs Base Metal (kg)
            const qtyInput = document.getElementById('calc-qty');
            if (metal.key === 'gold') {{
                qtyInput.value = 3.75; // 1돈 기본 추천값
            }} else if ((metal.cat === 'pgm' || metal.cat === 'precious') && (qtyInput.value > 50 || qtyInput.value == 100)) {{
                qtyInput.value = 10;
            }} else if (metal.cat !== 'pgm' && metal.cat !== 'precious' && qtyInput.value < 20) {{
                qtyInput.value = 100;
            }}
            calculateScrap();
        }}

        function setCalculatorTarget(key) {{
            document.getElementById('calc-metal').value = key;
            onMetalChange();
            window.scrollTo({{ top: document.querySelector('.calc-box').offsetTop - 20, behavior: 'smooth' }});
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

        // Category Filter (동시에 모바일 카드도 필터링)
        function filterCategory(cat, btn) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 데스크톱 테이블 필터
            document.querySelectorAll('.table-row').forEach(row => {{
                if (cat === 'all' || row.dataset.cat === cat) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});

            // 모바일 카드 필터
            document.querySelectorAll('.m-price-card').forEach(card => {{
                if (cat === 'all' || card.dataset.cat === cat) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
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
                const goldDisplay = (a.gold && a.gold !== '-') ? a.gold : '-';
                tr.innerHTML = `
                    <td><strong>${{a.date}}</strong> ${{a.is_latest ? '<span style="font-size:10px; background:#059669; color:white; padding:1px 5px; border-radius:3px; margin-left:3px;">최신</span>' : ''}}</td>
                    <td style="color:#60a5fa; font-weight:600;">${{a.steel}}</td>
                    <td style="color:#60a5fa; font-weight:600;">${{a.copper}}</td>
                    <td style="color:#fbbf24; font-weight:600;">${{goldDisplay}}</td>
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
            const goldDisplay = (found.gold && found.gold !== '-') ? found.gold : '-';
            const goldElem = document.getElementById('prev-gold');
            if (goldElem) goldElem.innerText = goldDisplay;
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

            // FAB Scroll listener
            window.addEventListener('scroll', function() {{
                var fab = document.getElementById('fab-container');
                if (fab) {{
                    if (window.scrollY > 300) {{
                        fab.classList.add('visible');
                    }} else {{
                        fab.classList.remove('visible');
                    }}
                }}
            }}, {{passive: true}});
        }});

        function scrollToTop() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        function openGuideModal() {{
            var overlay = document.getElementById('guide-modal-overlay');
            if (overlay) {{
                overlay.classList.add('open');
                document.body.style.overflow = 'hidden';
            }}
        }}

        function closeGuideModal(e) {{
            var overlay = document.getElementById('guide-modal-overlay');
            if (overlay) {{
                overlay.classList.remove('open');
                document.body.style.overflow = '';
            }}
        }}

        /* Off-Canvas Drawer Toggle & Language Scripts */
        (function() {{
            var btn = document.getElementById('tplHamburgerBtn');
            var drawer = document.getElementById('tplDrawer');
            var overlay = document.getElementById('tplDrawerOverlay');
            var closeBtn = document.getElementById('tplDrawerClose');

            function openDrawer() {{
                if (drawer && overlay) {{
                    drawer.classList.add('open');
                    overlay.classList.add('open');
                    drawer.setAttribute('aria-hidden', 'false');
                    document.body.style.overflow = 'hidden';
                }}
            }}

            function closeDrawer() {{
                if (drawer && overlay) {{
                    drawer.classList.remove('open');
                    overlay.classList.remove('open');
                    drawer.setAttribute('aria-hidden', 'true');
                    document.body.style.overflow = '';
                }}
            }}

            if (btn) btn.addEventListener('click', openDrawer);
            if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
            if (overlay) overlay.addEventListener('click', closeDrawer);

            var links = drawer ? drawer.querySelectorAll('a') : [];
            for (var i = 0; i < links.length; i++) {{
                links[i].addEventListener('click', closeDrawer);
            }}

            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') closeDrawer();
            }});
        }})();

        // Google Translate & tplChangeLang
        function googleTranslateElementInit() {{
            new google.translate.TranslateElement({{
                pageLanguage: 'ko',
                includedLanguages: 'ko,en,ru,es,ja,zh-CN,de,fr',
                autoDisplay: false
            }}, 'google_translate_element');
        }}

        function tplChangeLang(lang) {{
            document.cookie = 'googtrans=/ko/' + lang + '; path=/; SameSite=Lax; Secure';
            document.cookie = 'googtrans=/ko/' + lang + '; path=/; domain=' + location.hostname + '; SameSite=Lax; Secure';
            var select = document.querySelector('.goog-te-combo');
            if (select) {{
                select.value = lang;
                select.dispatchEvent(new Event('change'));
                return;
            }}
            loadGoogleTranslate(function() {{
                var attempts = 0;
                var checkInterval = setInterval(function() {{
                    attempts++;
                    var sel = document.querySelector('.goog-te-combo');
                    if (sel) {{
                        clearInterval(checkInterval);
                        sel.value = lang;
                        sel.dispatchEvent(new Event('change'));
                    }} else if (attempts > 15) {{
                        clearInterval(checkInterval);
                        location.reload();
                    }}
                }}, 100);
            }});
        }}
        window.changeLanguage = tplChangeLang;
        window.tplChangeLang = tplChangeLang;

        function loadGoogleTranslate(cb) {{
            if (window.gtLoaded) {{ if (cb && typeof cb === 'function') cb(); return; }}
            window.gtLoaded = true;
            var s = document.createElement('script');
            s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
            if (cb && typeof cb === 'function') s.onload = cb;
            document.body.appendChild(s);
        }}
        ['scroll', 'mousemove', 'touchstart'].forEach(function(ev) {{
            window.addEventListener(ev, function() {{ loadGoogleTranslate(); }}, {{once: true, passive: true}});
        }});
        if (document.cookie.indexOf('googtrans') !== -1 && document.cookie.indexOf('googtrans=/ko/ko') === -1) {{
            loadGoogleTranslate();
        }}
    </script>
    <!-- Google Translate Container (Hidden) -->
    <div id="google_translate_element" style="display:none;"></div>
</body>
</html>
"""

    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"    -> [웹사이트 완료] 메인 대시보드 생성: index.html ({len(index_html):,} bytes)", flush=True)

    # 7. 전체 네트워크(포털, metals, autoissue, engines) Sitemap & RSS 일괄 갱신
    try:
        from generate_network_seo import run_unified_seo_sync
        run_unified_seo_sync()
    except Exception as e:
        print(f"    -> [경고] 통합 SEO 동기화 실패 ({e}), 로컬 사이트맵으로 폴백", flush=True)
        generate_sitemap(archived_dates)

    # 8. latest.json 생성 (메인 포털 및 외부 클라이언트 실시간 연동용)
    try:
        latest_json_data = {
            "latest_date": latest_date,
            "formatted_date": f"{latest_date} 발행",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
            "usd_rate": data.get("usd_rate", 1338.7),
            "rate_source": data.get("rate_source", "네이버 금융"),
            "recent_dates": archived_dates[:5],
            "metals": [
                {
                    "name": m["name_kr"],
                    "key": m["key"],
                    "krw_price": m["krw_price"],
                    "unit": m["unit_krw"],
                    "diff_krw": m["diff_krw"],
                    "diff_pct": round(m["diff_pct"], 2) if m.get("diff_pct") is not None else None,
                    "scrap_70": m["scrap_70"],
                    "scrap_80": m["scrap_80"]
                }
                for m in data.get("metals", [])
            ]
        }
        latest_json_path = os.path.join(BASE_DIR, "latest.json")
        with open(latest_json_path, "w", encoding="utf-8") as f:
            json.dump(latest_json_data, f, ensure_ascii=False, indent=2)
        print(f"    -> [API 생성 완료] 메인 포털 실시간 연동용 latest.json 생성", flush=True)
    except Exception as e:
        print(f"    -> [경고] latest.json 생성 실패: {e}", flush=True)

    # 9. 메인 포털(chicstory.github.io) 정적 HTML 동기화
    sync_portal_index(latest_date, archived_dates)

    return index_path


def sync_portal_index(latest_date: str, archived_dates: List[str]):
    portal_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "chicstory.github.io"))
    portal_index = os.path.join(portal_dir, "index.html")
    if not os.path.exists(portal_index):
        return
    try:
        with open(portal_index, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Update live status badge
        content = re.sub(
            r'<span class="live-status-badge gold"[^>]*><span class="pulse-dot gold"></span>\d{4}-\d{2}-\d{2} 발행</span>',
            f'<span class="live-status-badge gold" id="metalsLiveBadge"><span class="pulse-dot gold"></span>{latest_date} 발행</span>',
            content
        )

        # 2. Update card update items
        if len(archived_dates) >= 2:
            d0 = archived_dates[0][5:]
            d1 = archived_dates[1][5:]
            content = re.sub(
                r'(<span class="card-update-date"[^>]*>)\d{2}-\d{2}(</span>\s*<span class="card-update-title"[^>]*>[79]대 금속 일일 시세 & 스크랩 추정가</span>)',
                rf'\g<1>{d0}\g<2>',
                content
            )
            content = re.sub(
                r'(<span class="card-update-date"[^>]*>)\d{2}-\d{2}(</span>\s*<span class="card-update-title"[^>]*>[79]대 금속 일일 시황 & 조달청 고시가</span>)',
                rf'\g<1>{d1}\g<2>',
                content
            )

        # 3. Update timeline activity date
        content = re.sub(
            r'(<span class="activity-date"[^>]*>)\d{4}-\d{2}-\d{2}(</span>\s*<span class="activity-cat cat-metals">금속원자재</span>)',
            rf'\g<1>{latest_date}\g<2>',
            content
        )

        with open(portal_index, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"    -> [포털 연동 완료] chicstory.github.io/index.html 정적 태그 동기화 ({latest_date})", flush=True)
    except Exception as e:
        print(f"    -> [경고] 포털 index.html 동기화 실패: {e}", flush=True)


if __name__ == "__main__":
    build_website_index()

