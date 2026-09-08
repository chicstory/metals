import os
import datetime
import urllib.parse

ENGINES_DIR = r"c:\Users\chics\OneDrive\문서\gemini\engines"
BASE_URL = "https://chicstory.github.io/engines/"
TODAY = datetime.date.today().isoformat()

urls = [
    (BASE_URL, "1.0", "daily"),
    (BASE_URL + "hyundai_kia_engine_table.html", "0.9", "weekly"),
    (BASE_URL + "bmw_engine_table.html", "0.9", "weekly"),
    (BASE_URL + "mercedes_benz_engine_table.html", "0.9", "weekly"),
    (BASE_URL + "audi_engine_table.html", "0.9", "weekly"),
    (BASE_URL + "volkswagen_engine_table.html", "0.9", "weekly"),
    (BASE_URL + "kgm_ssangyong_engine_table.html", "0.9", "weekly"),
]

for root, dirs, files in os.walk(ENGINES_DIR):
    for file in files:
        if file.endswith(".html") and file != "index.html" and not file.endswith("_table.html"):
            rel_path = os.path.relpath(os.path.join(root, file), ENGINES_DIR).replace("\\", "/")
            encoded_rel = urllib.parse.quote(rel_path)
            urls.append((BASE_URL + encoded_rel, "0.8", "monthly"))

xml = ['<?xml version="1.0" encoding="UTF-8"?>']
xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
for loc, prio, freq in urls:
    xml.append("  <url>")
    xml.append(f"    <loc>{loc}</loc>")
    xml.append(f"    <lastmod>{TODAY}</lastmod>")
    xml.append(f"    <changefreq>{freq}</changefreq>")
    xml.append(f"    <priority>{prio}</priority>")
    xml.append("  </url>")
xml.append("</urlset>")

sitemap_path = os.path.join(ENGINES_DIR, "sitemap.xml")
with open(sitemap_path, "w", encoding="utf-8") as f:
    f.write("\n".join(xml))

print(f"Generated sitemap.xml with {len(urls)} URLs at {sitemap_path}")
