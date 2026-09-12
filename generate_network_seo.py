#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ThePathLab Network Unified SEO & RSS Feed Engine
================================================
포털(chicstory.github.io), 금속시황(metals), 자동차이슈(autoissue), 엔진백과(engines)의
사이트맵(sitemap.xml) 및 실시간 색인용 RSS 피드(rss.xml)를 원스톱으로 생성·동기화합니다.

구글 서치 콘솔 및 네이버 서치어드바이저의 초고속 인덱싱(Fast-track Indexing)을 지원합니다.
"""

import os
import sys
import re
import csv
import json
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from typing import List, Dict, Any

# Windows 콘솔 utf-8 출력 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# KST 표준 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))

# 기본 디렉토리 상대 경로 설정 (크로스 PC 호환)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
PORTAL_DIR = os.path.join(ROOT_DIR, "chicstory.github.io")
AUTOISSUE_DIR = os.path.join(ROOT_DIR, "autoissue")
ENGINES_DIR = os.path.join(ROOT_DIR, "engines")
METALS_DIR = BASE_DIR
RESOURCES_DIR = os.path.join(METALS_DIR, "resources")


def xml_escape(text: str) -> str:
    """XML 특수문자 안전 이스케이프"""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def get_rfc822_date(date_str: str, hour: int = 9, minute: int = 0) -> str:
    """YYYY-MM-DD 문자열을 RFC 822 RSS 표준 포맷으로 변환"""
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d").replace(
            hour=hour, minute=minute, second=0, tzinfo=KST
        )
        return format_datetime(dt)
    except Exception:
        now = datetime.now(KST)
        return format_datetime(now)


# ==============================================================================
# 1. METALS (thepathlab) SEO & RSS 생성
# ==============================================================================
def generate_metals_seo() -> List[Dict[str, Any]]:
    """metals sitemap.xml 및 rss.xml 생성"""
    if not os.path.exists(RESOURCES_DIR):
        return []

    # 아카이브 날짜 목록 추출
    dates = []
    for name in os.listdir(RESOURCES_DIR):
        p = os.path.join(RESOURCES_DIR, name)
        if os.path.isdir(p) and re.match(r"^\d{4}-\d{2}-\d{2}$", name):
            dates.append(name)
    dates.sort(reverse=True)

    if not dates:
        return []

    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    latest_date = dates[0]
    site_url = "https://thapathlab.com/metals"

    # 1-1. sitemap.xml 생성
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        f'    <loc>{site_url}/</loc>',
        f'    <lastmod>{today_str}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
    ]

    rss_items = []
    for d in dates:
        # 리포트 파일명 결정
        report_filename = f"[통합브리핑] 9대_금속원자재_{d}.html"
        if not os.path.exists(os.path.join(RESOURCES_DIR, d, report_filename)):
            report_filename = f"[통합브리핑] 7대_금속원자재_{d}.html"
        
        encoded_report = urllib.parse.quote(report_filename)
        report_url = f"{site_url}/resources/{d}/{encoded_report}"

        sitemap_lines.extend([
            '  <url>',
            f'    <loc>{report_url}</loc>',
            f'    <lastmod>{d}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>',
        ])

        # CSV 요약 정보 로드 (RSS description용)
        desc_parts = []
        c_path = os.path.join(RESOURCES_DIR, d, f"9대자원_환산시세_{d}.csv")
        if not os.path.exists(c_path):
            c_path = os.path.join(RESOURCES_DIR, d, f"7대자원_환산시세_{d}.csv")
        if os.path.exists(c_path):
            try:
                with open(c_path, "r", encoding="utf-8-sig") as cf:
                    reader = csv.DictReader(cf)
                    for row in reader:
                        m_name = row.get("자원명", "")
                        price = row.get("원화시장단가(원)", "")
                        unit = row.get("환산단위", "")
                        if m_name in ["구리", "철·철스크랩", "알루미늄", "금", "은", "팔라듐"]:
                            try:
                                desc_parts.append(f"{m_name} {int(float(price)):,}{unit}")
                            except Exception:
                                pass
            except Exception:
                pass

        summary_text = " | ".join(desc_parts) if desc_parts else "9대 금속원자재 일일 시세 및 스크랩 매입 추정가 분석"

        # 최근 14일치만 RSS 아이템으로 포함 (RSS 피드 경량화 최적화)
        if len(rss_items) < 14:
            rss_items.append({
                "title": f"[{d}] ThePathLab 9대 금속원자재 일일 시황 & 스크랩 매입 추정가 리포트",
                "link": report_url,
                "guid": f"metals-{d}",
                "pubDate": get_rfc822_date(d, hour=10, minute=0),
                "description": f"[{d} 기준] LME·조달청 국제 시세 및 원화 환산 단가: {summary_text}. 실무 스크랩(70~80%) 매입 견적 계산기 포함.",
                "category": "금속원자재·스크랩",
                "date": d
            })

    sitemap_lines.append('</urlset>')

    sitemap_path = os.path.join(METALS_DIR, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_lines))

    # 1-2. metals/rss.xml 생성
    now_rfc = format_datetime(datetime.now(KST))
    metals_rss = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        '    <title>ThePathLab 9대 금속원자재 &amp; 스크랩 시황</title>',
        f'    <link>{site_url}/</link>',
        '    <description>매일 업데이트되는 9대 금속원자재(구리, 철스크랩, 알루미늄, 납, 금, 은, 백금, 팔라듐, 로듐)의 국제 시세 및 원화 환산 단가, 스크랩 매입 추정가 리포트</description>',
        '    <language>ko-kr</language>',
        f'    <pubDate>{now_rfc}</pubDate>',
        f'    <lastBuildDate>{now_rfc}</lastBuildDate>',
        f'    <atom:link href="{site_url}/rss.xml" rel="self" type="application/rss+xml" />',
    ]

    for itm in rss_items:
        metals_rss.extend([
            '    <item>',
            f'      <title>{xml_escape(itm["title"])}</title>',
            f'      <link>{xml_escape(itm["link"])}</link>',
            f'      <guid isPermaLink="false">{xml_escape(itm["guid"])}</guid>',
            f'      <pubDate>{itm["pubDate"]}</pubDate>',
            f'      <description>{xml_escape(itm["description"])}</description>',
            f'      <category>{xml_escape(itm["category"])}</category>',
            '    </item>',
        ])

    metals_rss.extend(['  </channel>', '</rss>'])

    metals_rss_path = os.path.join(METALS_DIR, "rss.xml")
    with open(metals_rss_path, "w", encoding="utf-8") as f:
        f.write("\n".join(metals_rss))

    print(f"    -> [metals SEO 완료] sitemap.xml ({len(dates)+1} URLs), rss.xml ({len(rss_items)} items)", flush=True)
    return rss_items


# ==============================================================================
# 2. AUTOISSUE SEO & RSS 생성
# ==============================================================================
def generate_autoissue_seo() -> List[Dict[str, Any]]:
    """autoissue sitemap.xml 및 rss.xml 생성"""
    issues_json_path = os.path.join(AUTOISSUE_DIR, "data", "issues.json")
    if not os.path.exists(issues_json_path):
        return []

    try:
        with open(issues_json_path, "r", encoding="utf-8") as f:
            issues = json.load(f)
    except Exception as e:
        print(f"    [경고] autoissue issues.json 로드 실패: {e}", flush=True)
        return []

    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    site_url = "https://thapathlab.com/autoissue"

    # 2-1. sitemap.xml 생성
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{site_url}/</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    with open(os.path.join(AUTOISSUE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    # 2-2. rss.xml 생성 (최신 25건 이슈)
    now_rfc = format_datetime(datetime.now(KST))
    rss_items = []

    auto_rss = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        '    <title>ThePathLab 자동차 데일리 이슈 - 10대 제조사 결함·리콜 &amp; 신차</title>',
        f'    <link>{site_url}/</link>',
        '    <description>현대기아, BMW, 벤츠, 아우디 등 10대 글로벌 제조사의 실시간 결함·리콜 공고, 미국 NHTSA 선제 공고 및 신차 파워트레인 뉴스</description>',
        '    <language>ko-kr</language>',
        f'    <pubDate>{now_rfc}</pubDate>',
        f'    <lastBuildDate>{now_rfc}</lastBuildDate>',
        f'    <atom:link href="{site_url}/rss.xml" rel="self" type="application/rss+xml" />',
    ]

    for iss in issues[:25]:
        iss_date = iss.get("date", today_str)
        cat_label = iss.get("category_label", "이슈")
        brand_name = iss.get("brand_name", "")
        title = f"[{brand_name}] {iss.get('title', '')}"
        desc = iss.get("summary", "")
        # 구글 서치콘솔 RSS 색인 규정: 타 도메인(외부 링크) 포함 시 색인 거부되므로 내부 앵커 링크로 정규화
        link = f"{site_url}/#{iss.get('id', '')}"
        pub_date = get_rfc822_date(iss_date, hour=11, minute=0)

        rss_obj = {
            "title": title,
            "link": link,
            "guid": f"autoissue-{iss.get('id', '')}",
            "pubDate": pub_date,
            "description": f"[{cat_label}] {desc}",
            "category": "자동차 데일리 이슈",
            "date": iss_date
        }
        rss_items.append(rss_obj)

        auto_rss.extend([
            '    <item>',
            f'      <title>{xml_escape(rss_obj["title"])}</title>',
            f'      <link>{xml_escape(rss_obj["link"])}</link>',
            f'      <guid isPermaLink="false">{xml_escape(rss_obj["guid"])}</guid>',
            f'      <pubDate>{rss_obj["pubDate"]}</pubDate>',
            f'      <description>{xml_escape(rss_obj["description"])}</description>',
            f'      <category>{xml_escape(rss_obj["category"])}</category>',
            '    </item>',
        ])

    auto_rss.extend(['  </channel>', '</rss>'])

    with open(os.path.join(AUTOISSUE_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(auto_rss))

    print(f"    -> [autoissue SEO 완료] sitemap.xml, rss.xml ({len(rss_items)} items)", flush=True)
    return rss_items


# ==============================================================================
# 3. CHICSTORY.GITHUB.IO (포털 마스터) SEO & MASTER RSS 생성
# ==============================================================================
def generate_portal_seo(metals_items: List[Dict[str, Any]], autoissue_items: List[Dict[str, Any]]):
    """메인 포털 통합 sitemap.xml 및 전체 네트워크 통합 마스터 rss.xml 생성"""
    if not os.path.exists(PORTAL_DIR):
        return

    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    portal_url = "https://thapathlab.com"

    # 3-1. 포털 sitemap.xml 생성
    portal_sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{portal_url}/</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{portal_url}/autoissue/</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{portal_url}/metals/</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{portal_url}/engines/</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{portal_url}/guide.html</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{portal_url}/about.html</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{portal_url}/privacy.html</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>{portal_url}/contact.html</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
"""
    with open(os.path.join(PORTAL_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(portal_sitemap)

    # 3-2. 포털 마스터 통합 RSS (metals + autoissue 병합)
    # 서치 콘솔에 등록할 대표 마스터 피드
    combined_items = metals_items + autoissue_items
    combined_items.sort(key=lambda x: x.get("date", ""), reverse=True)
    master_items = combined_items[:30]  # 최신 30건 선별

    now_rfc = format_datetime(datetime.now(KST))
    portal_rss = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        '    <title>ThePathLab - 산업 자원 시세 &amp; 자동차 테크 인텔리전스 포털</title>',
        f'    <link>{portal_url}/</link>',
        '    <description>ThePathLab 통합 네트워크 공식 RSS 피드: 9대 금속원자재·스크랩 일일 시황 및 10대 완성차 결함·리콜 데일리 뉴스</description>',
        '    <language>ko-kr</language>',
        f'    <pubDate>{now_rfc}</pubDate>',
        f'    <lastBuildDate>{now_rfc}</lastBuildDate>',
        f'    <atom:link href="{portal_url}/rss.xml" rel="self" type="application/rss+xml" />',
    ]

    for itm in master_items:
        portal_rss.extend([
            '    <item>',
            f'      <title>{xml_escape(itm["title"])}</title>',
            f'      <link>{xml_escape(itm["link"])}</link>',
            f'      <guid isPermaLink="false">{xml_escape(itm["guid"])}</guid>',
            f'      <pubDate>{itm["pubDate"]}</pubDate>',
            f'      <description>{xml_escape(itm["description"])}</description>',
            f'      <category>{xml_escape(itm.get("category", "종합"))}</category>',
            '    </item>',
        ])

    portal_rss.extend(['  </channel>', '</rss>'])

    with open(os.path.join(PORTAL_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(portal_rss))

    print(f"    -> [포털 마스터 SEO 완료] sitemap.xml, rss.xml (통합 마스터 {len(master_items)} items)", flush=True)


# ==============================================================================
# 4. ENGINES SEO 도메인 및 날짜 동기화
# ==============================================================================
def update_engines_seo():
    """engines sitemap.xml 전체 URL 도메인을 thapathlab.com으로 치환하고 lastmod 갱신"""
    engines_sitemap = os.path.join(ENGINES_DIR, "sitemap.xml")
    if not os.path.exists(engines_sitemap):
        return

    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    try:
        with open(engines_sitemap, "r", encoding="utf-8") as f:
            content = f.read()

        # 1) 전체 engines URL 도메인을 https://thapathlab.com으로 치환
        content = content.replace("https://chicstory.github.io/engines/", "https://thapathlab.com/engines/")

        # 2) 첫 번째 loc (엔진 메인) 아래 lastmod를 오늘자로 갱신
        content = re.sub(
            r'(<loc>https://thapathlab\.com/engines/</loc>\s*<lastmod>)[^<]+(</lastmod>)',
            rf'\g<1>{today_str}\g<2>',
            content,
            count=1
        )

        with open(engines_sitemap, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"    -> [engines SEO 완료] sitemap.xml 도메인 치환 및 lastmod 동기화 ({today_str})", flush=True)
    except Exception as e:
        print(f"    [경고] engines sitemap.xml 갱신 실패: {e}", flush=True)


# ==============================================================================
# 5. ROBOTS.TXT 동기화 (RSS 및 Sitemap 자동 감지 명시)
# ==============================================================================
def update_all_robots_txt():
    """각 서브 저장소의 robots.txt에 sitemap 및 rss 피드 주소 등록"""
    # 5-1. chicstory.github.io
    portal_robots = """User-agent: *
Allow: /

Sitemap: https://thapathlab.com/sitemap.xml
Sitemap: https://thapathlab.com/rss.xml
Sitemap: https://thapathlab.com/metals/sitemap.xml
Sitemap: https://thapathlab.com/metals/rss.xml
Sitemap: https://thapathlab.com/autoissue/sitemap.xml
Sitemap: https://thapathlab.com/autoissue/rss.xml
Sitemap: https://thapathlab.com/engines/sitemap.xml
"""
    with open(os.path.join(PORTAL_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(portal_robots)

    # 5-2. thepathlab (metals)
    metals_robots = """User-agent: *
Allow: /

Sitemap: https://thapathlab.com/metals/sitemap.xml
Sitemap: https://thapathlab.com/metals/rss.xml
"""
    with open(os.path.join(METALS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(metals_robots)

    # 5-3. autoissue
    auto_robots = """User-agent: *
Allow: /

Sitemap: https://thapathlab.com/autoissue/sitemap.xml
Sitemap: https://thapathlab.com/autoissue/rss.xml
"""
    with open(os.path.join(AUTOISSUE_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(auto_robots)

    print("    -> [robots.txt 완료] 전체 서브 도메인 sitemap & rss 주소 등록 완료", flush=True)


# ==============================================================================
# 메인 실행 엔트리포인트
# ==============================================================================
def run_unified_seo_sync():
    print("\n=======================================================", flush=True)
    print("  🌐 [ThePathLab] 네트워크 전체 Sitemap & RSS 동기화 시작", flush=True)
    print("=======================================================", flush=True)

    metals_items = generate_metals_seo()
    autoissue_items = generate_autoissue_seo()
    generate_portal_seo(metals_items, autoissue_items)
    update_engines_seo()
    update_all_robots_txt()

    print("=======================================================", flush=True)
    print("  ✅ [동기화 완료] 서치 콘솔 및 네이버 색인용 피드 준비 완료!", flush=True)
    print("=======================================================\n", flush=True)


if __name__ == "__main__":
    run_unified_seo_sync()
