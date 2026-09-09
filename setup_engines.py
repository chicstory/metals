# -*- coding: utf-8 -*-
"""
Setup and Build Script for 'engines' Repository
Migrates blogtool files to engines/, injects Google Translate widget,
adds Anonymous Live Comment Box (with honeypot + math captcha),
and configures global navigation links.
"""
import os
import shutil
import glob
import re


# 3-1. GA4 Measurement Snippet
GA4_SNIPPET = """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-K3PFHN6VW7"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-K3PFHN6VW7');
    </script>
"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOGTOOL_DIR = os.path.join(BASE_DIR, "blogtool")
ENGINES_DIR = os.path.join(BASE_DIR, "engines")

# 1. Directories to copy
brand_dirs = ["현대", "기아", "제네시스", "BMW", "벤츠", "아우디", "폭스바겐", "쌍용", "KGM"]
for b in brand_dirs:
    src = os.path.join(BLOGTOOL_DIR, b)
    dst = os.path.join(ENGINES_DIR, b)
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"Copied brand directory: {b}")

# 2. Manufacturer tables to copy
table_files = [
    "audi_engine_table.html",
    "bmw_engine_table.html",
    "hyundai_kia_engine_table.html",
    "kgm_ssangyong_engine_table.html",
    "mercedes_benz_engine_table.html",
    "volkswagen_engine_table.html"
]
for tf in table_files:
    src = os.path.join(BLOGTOOL_DIR, tf)
    dst = os.path.join(ENGINES_DIR, tf)
    if os.path.exists(src):
        with open(src, 'r', encoding='utf-8') as rfp:
            t_content = rfp.read()
        if 'G-K3PFHN6VW7' not in t_content and '<head>' in t_content:
            t_content = t_content.replace('<head>', '<head>\n' + GA4_SNIPPET, 1)
        with open(dst, 'w', encoding='utf-8') as wfp:
            wfp.write(t_content)
        print(f"Copied and injected table file: {tf}")

# 3. Google Translate Widget snippet (for head and navigation)
TRANSLATE_HEAD_SNIPPET = """
    <!-- Google Translate Script -->
    <div id="google_translate_element" style="display:none;"></div>
    <script type="text/javascript">
        function googleTranslateElementInit() {
            new google.translate.TranslateElement({
                pageLanguage: 'ko',
                includedLanguages: 'ko,en,ru,es,ja,zh-CN,de,fr',
                autoDisplay: false
            }, 'google_translate_element');
        }
        function changeLanguage(lang) {
            var select = document.querySelector('.goog-te-combo');
            if (select) {
                select.value = lang;
                select.dispatchEvent(new Event('change'));
            } else {
                // Fallback for cookie-based Google Translate
                document.cookie = 'googtrans=/ko/' + lang + '; path=/;';
                location.reload();
            }
        }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
"""

TRANSLATE_BTN_HTML = """
<div class="lang-switcher" style="display:inline-flex; align-items:center; gap:4px; background:rgba(18,26,43,0.8); border:1px solid rgba(0,242,254,0.2); padding:3px 6px; border-radius:8px;">
    <span style="font-size:0.75rem; color:#64748b; margin-right:4px;"><i class="bi-globe"></i></span>
    <button type="button" onclick="changeLanguage('ko')" style="background:transparent; border:none; color:#f1f5f9; cursor:pointer; font-size:0.75rem; padding:2px 4px; border-radius:4px; font-weight:600;">🇰🇷 KO</button>
    <span style="color:#334155; font-size:0.7rem;">|</span>
    <button type="button" onclick="changeLanguage('en')" style="background:transparent; border:none; color:#94a3b8; cursor:pointer; font-size:0.75rem; padding:2px 4px; border-radius:4px; font-weight:600;">🇺🇸 EN</button>
    <span style="color:#334155; font-size:0.7rem;">|</span>
    <button type="button" onclick="changeLanguage('ru')" style="background:transparent; border:none; color:#94a3b8; cursor:pointer; font-size:0.75rem; padding:2px 4px; border-radius:4px; font-weight:600;">🇷🇺 RU</button>
    <span style="color:#334155; font-size:0.7rem;">|</span>
    <button type="button" onclick="changeLanguage('es')" style="background:transparent; border:none; color:#94a3b8; cursor:pointer; font-size:0.75rem; padding:2px 4px; border-radius:4px; font-weight:600;">🇪🇸 ES</button>
</div>
"""

# 4. Anonymous Comment Box snippet with Honeypot + Math Captcha
COMMENT_BOX_HTML = """
    <!-- ==================== ANONYMOUS OWNER & MECHANIC MEMO BOX ==================== -->
    <div class="section-card memo-section" id="ownerMemoSection">
        <div class="memo-header">
            <div class="memo-header-left">
                <i class="bi-chat-dots-fill"></i>
                <h3 class="memo-title">차주 & 정비사 한줄 실전 메모장</h3>
                <span class="memo-badge">익명 실시간</span>
            </div>
            <span class="memo-guide-text">오일 점도 추천, 고질병 해결법, 실전 정비 팁을 자유롭게 남겨주세요</span>
        </div>

        <!-- Input Form -->
        <form id="commentForm" onsubmit="handleCommentSubmit(event)" class="memo-form">
            <!-- Honeypot (Spam trap) -->
            <input type="text" id="hp_url_check" name="website_url" style="display:none !important;" tabindex="-1" autocomplete="off">
            
            <div class="memo-form-grid">
                <input type="text" id="commentAuthor" placeholder="닉네임 (예: 차주 / 정비사)" maxlength="15" required class="memo-input memo-input-author">
                <input type="text" id="commentText" placeholder="엔진 경험담, 정비 팁, 권장 소모품 (최대 120자)" maxlength="120" required class="memo-input memo-input-text">
                <div class="memo-quiz-wrap">
                    <span id="mathQuizLabel" class="memo-quiz-label">3 + 4 =</span>
                    <input type="number" id="mathAnswer" placeholder="정답" required class="memo-input memo-input-quiz">
                    <button type="submit" id="btnSubmitMemo" class="memo-submit-btn">등록</button>
                </div>
            </div>
        </form>

        <!-- Comments List -->
        <div id="commentsList" class="memo-comments-list">
            <!-- Dynamic Items will be rendered here -->
        </div>
    </div>

<style>
/* Memo Section Responsive Styling */
.memo-section {
    margin-bottom: 2.2rem;
}
.memo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--border-subtle);
}
.memo-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.memo-header-left i {
    color: var(--accent-cyan);
    font-size: 1.3rem;
}
.memo-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}
.memo-badge {
    background: rgba(0, 242, 254, 0.15);
    color: var(--accent-cyan);
    font-size: 0.74rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 12px;
    border: 1px solid rgba(0, 242, 254, 0.3);
}
.memo-guide-text {
    font-size: 0.82rem;
    color: var(--text-dim);
}
.memo-form {
    margin-bottom: 1.2rem;
}
.memo-form-grid {
    display: grid;
    grid-template-columns: 150px 1fr auto;
    gap: 10px;
    align-items: center;
}
.memo-input {
    background: rgba(11, 15, 25, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #f1f5f9;
    padding: 0.65rem 0.85rem;
    border-radius: 8px;
    font-size: 0.88rem;
    outline: none;
    transition: border-color 0.2s;
    font-family: inherit;
    box-sizing: border-box;
}
.memo-input:focus {
    border-color: var(--accent-cyan);
    box-shadow: 0 0 8px rgba(0, 242, 254, 0.2);
}
.memo-quiz-wrap {
    display: flex;
    gap: 6px;
    align-items: center;
}
.memo-quiz-label {
    font-size: 0.84rem;
    color: var(--accent-cyan);
    font-weight: 700;
    white-space: nowrap;
    font-family: 'JetBrains Mono', monospace;
}
.memo-input-quiz {
    width: 60px;
    text-align: center;
    padding: 0.65rem 0.4rem;
}
.memo-submit-btn {
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
    color: #0b0f19;
    font-weight: 700;
    border: none;
    padding: 0.65rem 1.1rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.88rem;
    white-space: nowrap;
    transition: all 0.2s ease;
}
.memo-submit-btn:hover {
    transform: scale(1.03);
    box-shadow: 0 4px 14px rgba(0, 242, 254, 0.4);
}
.memo-comments-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 380px;
    overflow-y: auto;
    padding-right: 4px;
}
.memo-comments-list::-webkit-scrollbar { width: 5px; }
.memo-comments-list::-webkit-scrollbar-track { background: rgba(11, 15, 25, 0.5); }
.memo-comments-list::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 3px; }

.memo-comment-row {
    background: rgba(11, 15, 25, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 0.75rem 1rem;
    border-radius: 10px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    transition: border-color 0.15s;
}
.memo-comment-row:hover {
    border-color: rgba(0, 242, 254, 0.2);
}
.memo-comment-left {
    display: flex;
    align-items: baseline;
    gap: 10px;
    flex: 1;
    min-width: 0;
    flex-wrap: wrap;
}
.memo-comment-author {
    color: var(--accent-cyan);
    font-size: 0.84rem;
    font-weight: 700;
    white-space: nowrap;
}
.memo-comment-text {
    color: #e2e8f0;
    font-size: 0.86rem;
    word-break: break-word;
    flex: 1;
    min-width: 180px;
}
.memo-comment-time {
    font-size: 0.74rem;
    color: #64748b;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
    flex-shrink: 0;
}

@media (max-width: 768px) {
    .memo-section {
        padding: 1.4rem 1.1rem;
    }
    .memo-form-grid {
        grid-template-columns: 1fr;
        gap: 8px;
    }
    .memo-input-author {
        width: 100%;
    }
    .memo-input-text {
        width: 100%;
    }
    .memo-quiz-wrap {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
    }
    .memo-input-quiz {
        flex: 1;
        width: auto;
    }
    .memo-submit-btn {
        flex: 1.5;
    }
    .memo-comment-row {
        flex-direction: column;
        gap: 6px;
        align-items: flex-start;
    }
    .memo-comment-time {
        align-self: flex-end;
        font-size: 0.7rem;
    }
}
</style>
"""

COMMENT_SCRIPT_HTML = """<script>
    // Math Captcha Logic
    let numA = Math.floor(Math.random() * 8) + 2;
    let numB = Math.floor(Math.random() * 8) + 1;
    let correctSum = numA + numB;
    const quizEl = document.getElementById('mathQuizLabel');
    if (quizEl) quizEl.innerText = numA + ' + ' + numB + ' =';

    const pageKey = 'engine_memo_' + (location.pathname.split('/').pop().replace('.html','').toUpperCase() || 'GENERAL');

    function getComments() {
        try {
            const data = localStorage.getItem(pageKey);
            return data ? JSON.parse(data) : [];
        } catch(e) { return []; }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function renderComments() {
        const listEl = document.getElementById('commentsList');
        if (!listEl) return;
        const comments = getComments();
        if (comments.length === 0) {
            listEl.innerHTML = '<div style="text-align:center; padding:1.2rem; color:#64748b; font-size:0.85rem;"><i class="bi-pencil-square" style="margin-right:4px;"></i>아직 등록된 실전 메모가 없습니다. 첫 꿀팁의 주인공이 되어보세요!</div>';
            return;
        }
        listEl.innerHTML = comments.slice().reverse().map(c => `
            <div class="memo-comment-row">
                <div class="memo-comment-left">
                    <strong class="memo-comment-author">${escapeHtml(c.author)}</strong>
                    <span class="memo-comment-text">${escapeHtml(c.text)}</span>
                </div>
                <span class="memo-comment-time">${escapeHtml(c.time)}</span>
            </div>
        `).join('');
    }

    function handleCommentSubmit(e) {
        e.preventDefault();
        // 1. Honeypot check
        if (document.getElementById('hp_url_check').value !== '') {
            return false;
        }
        // 2. Math Captcha check
        const userAns = parseInt(document.getElementById('mathAnswer').value);
        if (userAns !== correctSum) {
            alert('스팸 방지 산수 문제의 정답이 올바르지 않습니다.');
            return false;
        }
        // 3. Cooldown check
        const lastPost = localStorage.getItem('last_memo_post_time');
        const now = Date.now();
        if (lastPost && now - parseInt(lastPost) < 10000) {
            alert('도배 방지를 위해 10초 후에 다시 작성하실 수 있습니다.');
            return false;
        }

        const author = document.getElementById('commentAuthor').value.trim();
        const text = document.getElementById('commentText').value.trim();
        if (!author || !text) return;

        const d = new Date();
        const timeStr = (d.getMonth()+1) + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0');

        const comments = getComments();
        comments.push({ author, text, time: timeStr });
        localStorage.setItem(pageKey, JSON.stringify(comments));
        localStorage.setItem('last_memo_post_time', now.toString());

        document.getElementById('commentText').value = '';
        document.getElementById('mathAnswer').value = '';
        renderComments();

        // Regenerate quiz
        numA = Math.floor(Math.random() * 8) + 2;
        numB = Math.floor(Math.random() * 8) + 1;
        correctSum = numA + numB;
        if (quizEl) quizEl.innerText = numA + ' + ' + numB + ' =';
    }

    // Initial render
    document.addEventListener('DOMContentLoaded', renderComments);
</script>
"""

# 5. Process all engine html files in engines/ (Add translate and comment box)
print("Processing engine detail HTML files...")
modified_count = 0
for root, dirs, files in os.walk(ENGINES_DIR):
    for f in files:
        if f.endswith('.html') and f not in table_files and f != 'index.html':
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                
                # Check if already modified
                if 'memo-section' in content:
                    continue
                
                # Inject Translate in Head if not present
                if 'google_translate_element' not in content:
                    content = content.replace('</head>', TRANSLATE_HEAD_SNIPPET + '\n</head>')
                
                # In top-nav, inject Global Portal link and Translate Button
                if '<div class="top-nav">' in content:
                    nav_addon = f"""
                    <div style="display:flex; align-items:center; gap:8px;">
                        <a href="https://chicstory.github.io/" class="btn-back" style="background:rgba(255,255,255,0.06); border-color:rgba(255,255,255,0.15); color:#94a3b8;">
                            <i class="bi-house-door"></i> ThePathLab
                        </a>
                        <a href="../../index.html" class="btn-back">
                            <i class="bi-grid-fill"></i> 엔진 백과 목차
                        </a>
                        {TRANSLATE_BTN_HTML}
                    </div>
                    """
                    # Replace the existing btn-back or top-nav inner
                    content = re.sub(r'<div class="top-nav">.*?</div>', f'<div class="top-nav">{nav_addon}</div>', content, count=1, flags=re.DOTALL)
                
                # Inject Comment Box right before footer (inside container)
                if '<!-- Footer -->' in content:
                    content = content.replace('<!-- Footer -->', COMMENT_BOX_HTML + '\n    <!-- Footer -->', 1)
                elif '<footer>' in content:
                    content = content.replace('<footer>', COMMENT_BOX_HTML + '\n    <footer>', 1)
                
                if '</body>' in content and 'handleCommentSubmit' not in content:
                    content = content.replace('</body>', COMMENT_SCRIPT_HTML + '\n</body>', 1)

                if 'G-K3PFHN6VW7' not in content and '<head>' in content:
                    content = content.replace('<head>', '<head>\n' + GA4_SNIPPET, 1)

                if 'G-K3PFHN6VW7' not in content and '<head>' in content:
                    content = content.replace('<head>', '<head>\n' + GA4_SNIPPET, 1)
                with open(filepath, 'w', encoding='utf-8') as fp:
                    fp.write(content)
                modified_count += 1
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

print(f"Engine detail pages updated: {modified_count}")

# 6. Build index.html for engines/
src_index = os.path.join(BLOGTOOL_DIR, "engine_posts_index.html")
dst_index = os.path.join(ENGINES_DIR, "index.html")
if os.path.exists(src_index):
    with open(src_index, 'r', encoding='utf-8') as fp:
        idx_content = fp.read()
    
    # Inject Translate head snippet
    if 'G-K3PFHN6VW7' not in idx_content and '<head>' in idx_content:
        idx_content = idx_content.replace('<head>', '<head>\n' + GA4_SNIPPET, 1)
    if 'google_translate_element' not in idx_content:
        idx_content = idx_content.replace('</head>', TRANSLATE_HEAD_SNIPPET + '\n</head>')
    
    # Add Top Portal Navigation bar above header-section
    PORTAL_TOP_BAR = f"""
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:2rem; padding:0.8rem 1.2rem; background:rgba(18,26,43,0.85); border:1px solid rgba(0,242,254,0.2); border-radius:14px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <a href="https://chicstory.github.io/" style="display:inline-flex; align-items:center; gap:6px; color:#00f2fe; text-decoration:none; font-weight:700; font-size:0.95rem;">
                <i class="bi-arrow-left-circle-fill"></i> ThePathLab 포털 홈
            </a>
            <span style="color:#334155;">|</span>
            <a href="https://chicstory.github.io/metals/" style="display:inline-flex; align-items:center; gap:6px; color:#94a3b8; text-decoration:none; font-size:0.9rem; font-weight:600;">
                <i class="bi-graph-up-arrow" style="color:#ffb800;"></i> 7대 금속 원자재 시세
            </a>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            {TRANSLATE_BTN_HTML}
        </div>
    </div>

    <!-- Manufacturer Comprehensive Tables Quick Nav -->
    <div style="margin-bottom:2rem; background:rgba(18,26,43,0.6); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:1rem 1.2rem;">
        <div style="font-size:0.85rem; color:#94a3b8; font-weight:700; margin-bottom:0.6rem; display:flex; align-items:center; gap:6px;">
            <i class="bi-table" style="color:#00f2fe;"></i> 제조사별 전수 스펙 종합 비교표 바로가기:
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:8px;">
            <a href="hyundai_kia_engine_table.html" style="color:#e2e8f0; text-decoration:none; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:5px 12px; border-radius:8px; font-size:0.82rem; font-weight:600; transition:0.2s;">현대·기아 (87종)</a>
            <a href="bmw_engine_table.html" style="color:#e2e8f0; text-decoration:none; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:5px 12px; border-radius:8px; font-size:0.82rem; font-weight:600; transition:0.2s;">BMW (45종)</a>
            <a href="mercedes_benz_engine_table.html" style="color:#e2e8f0; text-decoration:none; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:5px 12px; border-radius:8px; font-size:0.82rem; font-weight:600; transition:0.2s;">메르세데스-벤츠 (40종)</a>
            <a href="audi_engine_table.html" style="color:#e2e8f0; text-decoration:none; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:5px 12px; border-radius:8px; font-size:0.82rem; font-weight:600; transition:0.2s;">아우디 (32종)</a>
            <a href="volkswagen_engine_table.html" style="color:#e2e8f0; text-decoration:none; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:5px 12px; border-radius:8px; font-size:0.82rem; font-weight:600; transition:0.2s;">폭스바겐 (20종)</a>
            <a href="kgm_ssangyong_engine_table.html" style="color:#e2e8f0; text-decoration:none; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:5px 12px; border-radius:8px; font-size:0.82rem; font-weight:600; transition:0.2s;">KGM·쌍용 (20종)</a>
        </div>
    </div>
    """
    
    idx_content = idx_content.replace('<div class="header-section">', PORTAL_TOP_BAR + '\n<div class="header-section">')
    
    with open(dst_index, 'w', encoding='utf-8') as fp:
        fp.write(idx_content)
    print("Created engines/index.html with portal navigation and translate controls.")

print("All engines setup completed!")
