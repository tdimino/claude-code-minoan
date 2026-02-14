#!/usr/bin/env python3
"""Live Markdown preview server — Catppuccin Mocha theme with TOC.

Usage: python3 mdpreview.py <file.md> [--port 3031]
"""

import http.server
import json
import os
import sys

PORT = 3031

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Victor+Mono:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<script src="https://unpkg.com/@phosphor-icons/web@2.1.1"></script>
<style>
  /* ── Catppuccin Mocha (dark — default) ── */
  :root, [data-theme="mocha"] {{
    --ctp-rosewater: #f5e0dc;
    --ctp-flamingo: #f2cdcd;
    --ctp-pink: #f5c2e7;
    --ctp-mauve: #cba6f7;
    --ctp-red: #f38ba8;
    --ctp-maroon: #eba0ac;
    --ctp-peach: #fab387;
    --ctp-yellow: #f9e2af;
    --ctp-green: #a6e3a1;
    --ctp-teal: #94e2d5;
    --ctp-sky: #89dcfe;
    --ctp-sapphire: #74c7ec;
    --ctp-blue: #89b4fa;
    --ctp-lavender: #b4befe;
    --ctp-text: #cdd6f4;
    --ctp-subtext1: #bac2de;
    --ctp-subtext0: #a6adc8;
    --ctp-overlay2: #9399b2;
    --ctp-overlay1: #7f849c;
    --ctp-overlay0: #6c7086;
    --ctp-surface2: #585b70;
    --ctp-surface1: #45475a;
    --ctp-surface0: #313244;
    --ctp-base: #1e1e2e;
    --ctp-mantle: #181825;
    --ctp-crust: #11111b;

    --bold-color: #e6edf3;
    --italic-color: #a5d6ff;
    --blockquote-color: #d4a5ff;
    --blockquote-bg: rgba(24, 24, 37, 0.6);
    --toc-active-bg: rgba(137, 180, 250, 0.08);
    --row-even-bg: rgba(49, 50, 68, 0.25);
    --row-hover-bg: rgba(137, 180, 250, 0.04);

    --base-size: 15px;
    --heading-scale: 1;
    color-scheme: dark;
  }}

  /* ── Catppuccin Latte (light) ── */
  [data-theme="latte"] {{
    --ctp-rosewater: #dc8a78;
    --ctp-flamingo: #dd7878;
    --ctp-pink: #ea76cb;
    --ctp-mauve: #8839ef;
    --ctp-red: #d20f39;
    --ctp-maroon: #e64553;
    --ctp-peach: #fe640b;
    --ctp-yellow: #df8e1d;
    --ctp-green: #40a02b;
    --ctp-teal: #179299;
    --ctp-sky: #04a5e5;
    --ctp-sapphire: #209fb5;
    --ctp-blue: #1e66f5;
    --ctp-lavender: #7287fd;
    --ctp-text: #4c4f69;
    --ctp-subtext1: #5c5f77;
    --ctp-subtext0: #6c6f85;
    --ctp-overlay2: #7c7f93;
    --ctp-overlay1: #8c8fa1;
    --ctp-overlay0: #9ca0b0;
    --ctp-surface2: #acb0be;
    --ctp-surface1: #bcc0cc;
    --ctp-surface0: #ccd0da;
    --ctp-base: #eff1f5;
    --ctp-mantle: #e6e9ef;
    --ctp-crust: #dce0e8;

    --bold-color: #2c2d3a;
    --italic-color: #1e66f5;
    --blockquote-color: #8839ef;
    --blockquote-bg: rgba(230, 233, 239, 0.8);
    --toc-active-bg: rgba(30, 102, 245, 0.08);
    --row-even-bg: rgba(204, 208, 218, 0.3);
    --row-hover-bg: rgba(30, 102, 245, 0.04);

    color-scheme: light;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}

  body {{
    background: var(--ctp-base);
    color: var(--ctp-text);
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: var(--base-size);
    line-height: 1.65;
    display: flex;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }}

  /* ── TOC Sidebar ── */
  #toc {{
    position: fixed;
    top: 0; left: 0;
    width: 260px;
    height: 100vh;
    background: var(--ctp-mantle);
    border-right: 1px solid var(--ctp-surface0);
    padding: 0;
    z-index: 10;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}

  /* ── Chrome bar — collapse + controls in one tight row ── */
  #toc-chrome {{
    display: flex;
    align-items: center;
    padding: 12px 12px 0;
    flex-shrink: 0;
    gap: 1px;
  }}
  #toc-toggle {{
    background: none;
    border: none;
    color: var(--ctp-overlay0);
    cursor: pointer;
    font-size: 12px;
    width: 22px; height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
    flex-shrink: 0;
  }}
  #toc-toggle:hover {{
    color: var(--ctp-text);
    background: var(--ctp-surface0);
  }}
  .chrome-spacer {{ flex: 1; }}
  .ctrl-btn {{
    background: none;
    border: none;
    color: var(--ctp-overlay0);
    cursor: pointer;
    font-size: 11px;
    width: 22px; height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
    flex-shrink: 0;
  }}
  .ctrl-btn:hover {{
    color: var(--ctp-text);
    background: var(--ctp-surface0);
  }}
  #font-size-display {{
    color: var(--ctp-overlay0);
    font-family: 'Victor Mono', monospace;
    font-size: 9px;
    min-width: 16px;
    text-align: center;
    flex-shrink: 0;
    user-select: none;
  }}

  /* Theme toggle — tiny pill */
  .theme-switch {{
    position: relative;
    width: 28px; height: 14px;
    flex-shrink: 0;
    margin: 0 2px;
  }}
  .theme-switch input {{ display: none; }}
  .theme-switch .slider {{
    position: absolute;
    inset: 0;
    background: var(--ctp-surface1);
    border-radius: 7px;
    cursor: pointer;
    transition: background 0.3s ease;
  }}
  .theme-switch .slider::before {{
    content: '';
    position: absolute;
    top: 2px; left: 2px;
    width: 10px; height: 10px;
    background: var(--ctp-overlay2);
    border-radius: 50%;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }}
  .theme-switch input:checked + .slider {{
    background: var(--ctp-blue);
  }}
  .theme-switch input:checked + .slider::before {{
    transform: translateX(14px);
    background: white;
  }}
  .theme-icon {{
    font-size: 10px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    transition: opacity 0.2s;
  }}
  .theme-icon.icon-moon {{ color: var(--ctp-mauve); opacity: 0.45; }}
  .theme-icon.icon-sun {{ color: var(--ctp-yellow); opacity: 0.2; }}
  [data-theme="latte"] .theme-icon.icon-moon {{ opacity: 0.2; }}
  [data-theme="latte"] .theme-icon.icon-sun {{ opacity: 0.45; }}

  /* ── "INDEX" label ── */
  #toc-label {{
    color: var(--ctp-overlay0);
    font-family: 'Victor Mono', monospace;
    font-size: 8px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    padding: 10px 14px 6px;
    flex-shrink: 0;
  }}

  /* Smooth theme transition */
  body, #toc, #status, #toc-restore,
  h1, h2, h3, h4, h5, h6,
  blockquote, code, pre, th, td, tr {{
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
  }}

  /* ── TOC scroll area ── */
  #toc-scroll {{
    overflow-y: auto;
    flex: 1;
    padding: 0 6px 40px;
    mask-image: linear-gradient(to bottom, black calc(100% - 28px), transparent 100%);
    -webkit-mask-image: linear-gradient(to bottom, black calc(100% - 28px), transparent 100%);
  }}
  #toc-scroll::-webkit-scrollbar {{ width: 0; }}

  /* ── TOC entries ── */
  #toc ul {{ list-style: none; }}
  #toc li {{
    margin: 0;
    animation: tocSlideIn 0.25s ease both;
  }}
  @keyframes tocSlideIn {{
    from {{ opacity: 0; transform: translateX(-6px); }}
    to {{ opacity: 1; transform: translateX(0); }}
  }}

  #toc a {{
    color: var(--ctp-overlay2);
    text-decoration: none;
    display: block;
    padding: 3px 8px 3px 12px;
    border-left: 2px solid transparent;
    transition: color 0.15s, border-color 0.2s, box-shadow 0.2s;
    line-height: 1.45;
    word-break: break-word;
    font-family: 'DM Sans', sans-serif;
  }}
  #toc a:hover {{
    color: var(--ctp-text);
    border-left-color: var(--ctp-surface1);
  }}
  #toc a.active {{
    color: var(--ctp-blue);
    border-left-color: var(--ctp-blue);
    box-shadow: -4px 0 8px -3px rgba(137, 180, 250, 0.15);
  }}
  [data-theme="latte"] #toc a.active {{
    box-shadow: -4px 0 8px -3px rgba(30, 102, 245, 0.12);
  }}

  /* h1 — document title, rendered like a book title */
  #toc .toc-h1 {{
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-weight: 600;
    font-style: italic;
    color: var(--ctp-lavender);
    font-size: 13px;
    padding: 6px 8px 8px 12px;
    margin-bottom: 2px;
    letter-spacing: -0.01em;
    line-height: 1.35;
    border-left-color: transparent !important;
  }}

  /* h2 — primary sections, the structural rhythm */
  #toc .toc-h2 {{
    font-weight: 600;
    font-size: 11px;
    color: var(--ctp-subtext0);
    padding: 4px 8px 4px 12px;
    margin-top: 14px;
    letter-spacing: 0.01em;
  }}
  /* Tighter top margin for first h2 after h1 */
  #toc li:first-child > .toc-h2 {{
    margin-top: 2px;
  }}

  /* h3 — subsections, clustered tight under h2 */
  #toc .toc-h3 {{
    font-weight: 400;
    font-size: 10.5px;
    color: var(--ctp-overlay2);
    padding-left: 24px;
    padding-top: 2px;
    padding-bottom: 2px;
  }}

  /* h4 — deep detail, ghostly until hovered or active */
  #toc .toc-h4 {{
    font-weight: 400;
    font-size: 10px;
    color: var(--ctp-overlay1);
    padding-left: 34px;
    padding-top: 1px;
    padding-bottom: 1px;
    opacity: 0.65;
    transition: opacity 0.15s, color 0.15s, border-color 0.2s;
  }}
  #toc .toc-h4:hover {{ opacity: 1; }}
  #toc .toc-h4.active {{ opacity: 1; }}

  /* Active overrides per level */
  #toc .toc-h1.active {{ color: var(--ctp-blue); }}
  #toc .toc-h2.active {{ color: var(--ctp-blue); }}
  #toc .toc-h3.active {{ color: var(--ctp-blue); font-weight: 500; }}

  /* ── Main Content ── */
  #content {{
    margin-left: 260px;
    max-width: 900px;
    padding: 48px 56px 80px;
    min-height: 100vh;
    transition: margin-left 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }}

  /* collapsed TOC */
  body.toc-collapsed #toc {{ transform: translateX(-260px); }}
  body.toc-collapsed #content {{ margin-left: 0; }}
  body.toc-collapsed #toc-restore {{
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  #toc-restore {{
    display: none;
    position: fixed;
    top: 12px; left: 12px;
    width: 32px; height: 32px;
    background: var(--ctp-mantle);
    border: 1px solid var(--ctp-surface0);
    color: var(--ctp-overlay1);
    cursor: pointer;
    font-size: 16px;
    border-radius: 6px;
    z-index: 20;
    transition: all 0.15s;
  }}
  #toc-restore:hover {{ background: var(--ctp-surface0); color: var(--ctp-text); }}

  /* ── Typography ── */
  h1, h2, h3, h4, h5, h6 {{
    color: var(--ctp-text);
    margin: 1.6em 0 0.6em;
    font-family: 'Cormorant Garamond', 'Georgia', serif;
    line-height: 1.25;
    letter-spacing: -0.01em;
  }}
  h1 {{
    font-size: calc(2em * var(--heading-scale));
    color: var(--ctp-blue);
    border-bottom: 1px solid var(--ctp-surface0);
    padding-bottom: 0.35em;
    font-weight: 700;
    letter-spacing: -0.02em;
  }}
  h2 {{
    font-size: calc(1.5em * var(--heading-scale));
    color: var(--ctp-blue);
    border-bottom: 1px solid var(--ctp-surface0);
    padding-bottom: 0.25em;
    font-weight: 600;
  }}
  h3 {{
    font-size: calc(1.2em * var(--heading-scale));
    color: var(--ctp-green);
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
  }}
  h4 {{
    font-size: calc(1.05em * var(--heading-scale));
    color: var(--ctp-yellow);
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
  }}
  h5 {{
    font-size: calc(0.95em * var(--heading-scale));
    color: var(--ctp-peach);
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
  }}

  p {{ margin: 0.75em 0; }}
  strong {{ color: var(--bold-color); font-weight: 600; }}
  em {{ color: var(--italic-color); font-style: italic; }}

  blockquote {{
    color: var(--blockquote-color);
    font-style: italic;
    border-left: 3px solid var(--ctp-mauve);
    padding: 0.6em 1.2em;
    margin: 1.2em 0;
    background: var(--blockquote-bg);
    border-radius: 0 6px 6px 0;
  }}

  a {{ color: var(--ctp-blue); text-decoration: none; }}
  a:hover {{ color: var(--ctp-lavender); text-decoration: underline; }}

  hr {{
    border: none;
    border-top: 1px solid var(--ctp-surface0);
    margin: 2.5em 0;
  }}

  /* ── Lists ── */
  ul, ol {{ margin: 0.6em 0; padding-left: 2em; }}
  li {{ margin: 0.3em 0; }}
  li::marker {{ color: var(--ctp-overlay1); }}

  /* ── Code ── */
  code {{
    background: var(--ctp-surface0);
    color: var(--ctp-red);
    padding: 0.15em 0.45em;
    border-radius: 4px;
    font-family: 'Victor Mono', 'Fira Code', monospace;
    font-size: 0.88em;
  }}
  pre {{
    background: var(--ctp-mantle);
    border: 1px solid var(--ctp-surface0);
    border-radius: 8px;
    padding: 1.1em 1.3em;
    overflow-x: auto;
    margin: 1.2em 0;
  }}
  pre code {{
    background: none;
    color: var(--ctp-text);
    padding: 0;
    font-size: 12px;
  }}

  /* ── Tables ── */
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1.2em 0;
    font-size: 13px;
  }}
  thead {{ position: sticky; top: 0; }}
  th {{
    background: var(--ctp-mantle);
    color: var(--ctp-blue);
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
    border: 1px solid var(--ctp-surface0);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  td {{
    padding: 8px 14px;
    border: 1px solid var(--ctp-surface0);
  }}
  tr:nth-child(even) {{ background: var(--row-even-bg); }}
  tr:hover {{ background: var(--row-hover-bg); }}

  /* ── Images ── */
  img {{ max-width: 100%; border-radius: 8px; margin: 1em 0; }}

  /* ── Status Bar ── */
  #status {{
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: var(--ctp-crust);
    border-top: 1px solid var(--ctp-surface0);
    color: var(--ctp-overlay0);
    font-family: 'Victor Mono', monospace;
    font-size: 11px;
    padding: 4px 16px;
    display: flex;
    justify-content: space-between;
    z-index: 30;
  }}
  #status .filepath {{ color: var(--ctp-overlay1); }}
  #status .updated {{ color: var(--ctp-green); }}
  #status .dot {{
    display: inline-block;
    width: 6px; height: 6px;
    background: var(--ctp-green);
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.3; }}
  }}

  /* ── Print ── */
  @media print {{
    #toc, #status, #toc-restore {{ display: none !important; }}
    #content {{ margin-left: 0; max-width: 100%; padding: 0; }}
    body {{ background: white; color: black; }}
    h1, h2 {{ color: #1a1a2e; border-bottom-color: #ddd; }}
    h3 {{ color: #2d6a4f; }}
    a {{ color: #1a73e8; }}
    table, th, td {{ border-color: #ccc; }}
    th {{ background: #f5f5f5; color: #333; }}
  }}
</style>
</head>
<body>
  <nav id="toc">
    <div id="toc-chrome">
      <button id="toc-toggle" title="Collapse" onclick="toggleToc()"><i class="ph ph-caret-left"></i></button>
      <span class="chrome-spacer"></span>
      <button class="ctrl-btn" onclick="adjustFont(-1)" title="Smaller"><i class="ph ph-minus"></i></button>
      <span id="font-size-display">15</span>
      <button class="ctrl-btn" onclick="adjustFont(1)" title="Larger"><i class="ph ph-plus"></i></button>
      <span style="width:8px"></span>
      <i class="ph-fill ph-moon theme-icon icon-moon"></i>
      <div class="theme-switch">
        <input type="checkbox" id="theme-toggle" onchange="toggleTheme()">
        <label class="slider" for="theme-toggle"></label>
      </div>
      <i class="ph-fill ph-sun theme-icon icon-sun"></i>
    </div>
    <div id="toc-label">Index</div>
    <div id="toc-scroll">
      <ul id="toc-list"></ul>
    </div>
  </nav>
  <button id="toc-restore" title="Show sidebar" onclick="toggleToc()"><i class="ph ph-caret-right"></i></button>
  <div id="content"></div>
  <div id="status">
    <span class="filepath">{filepath}</span>
    <span class="updated"><span class="dot"></span><span id="last-updated">connecting...</span></span>
  </div>

  <script>
    let lastMtime = 0;

    let currentSize = parseInt(localStorage.getItem('mdpreview-fontsize') || '15');

    function applyFontSize() {{
      document.documentElement.style.setProperty('--base-size', currentSize + 'px');
      const display = document.getElementById('font-size-display');
      if (display) display.textContent = currentSize;
      localStorage.setItem('mdpreview-fontsize', currentSize);
    }}
    applyFontSize();

    function adjustFont(delta) {{
      currentSize = Math.max(11, Math.min(22, currentSize + delta));
      applyFontSize();
    }}

    // Theme toggle
    let currentTheme = localStorage.getItem('mdpreview-theme') || 'mocha';
    function applyTheme() {{
      document.documentElement.setAttribute('data-theme', currentTheme);
      const toggle = document.getElementById('theme-toggle');
      if (toggle) toggle.checked = (currentTheme === 'latte');
      localStorage.setItem('mdpreview-theme', currentTheme);
    }}
    applyTheme();

    function toggleTheme() {{
      currentTheme = currentTheme === 'mocha' ? 'latte' : 'mocha';
      applyTheme();
    }}

    function toggleToc() {{
      document.body.classList.toggle('toc-collapsed');
    }}

    function slugify(text) {{
      return text.toLowerCase().replace(/[^\w]+/g, '-').replace(/^-|-$/g, '');
    }}

    function buildToc(html) {{
      const tmp = document.createElement('div');
      tmp.innerHTML = html;
      const headings = tmp.querySelectorAll('h1, h2, h3, h4');
      const toc = document.getElementById('toc-list');
      toc.innerHTML = '';
      headings.forEach((h, i) => {{
        const level = h.tagName.toLowerCase();
        const text = h.textContent;
        const id = slugify(text) + '-' + i;
        const li = document.createElement('li');
        li.style.animationDelay = (i * 0.02) + 's';
        const a = document.createElement('a');
        a.href = '#' + id;
        a.textContent = text;
        a.className = 'toc-' + level;
        a.dataset.target = id;
        li.appendChild(a);
        toc.appendChild(li);
      }});
    }}

    // Scroll spy — highlight active TOC entry + auto-scroll sidebar
    function updateActiveHeading() {{
      const headings = document.querySelectorAll('#content h1, #content h2, #content h3, #content h4');
      const links = document.querySelectorAll('#toc a');
      let current = '';

      headings.forEach(h => {{
        const rect = h.getBoundingClientRect();
        if (rect.top <= 80) current = h.id;
      }});

      links.forEach(a => {{
        a.classList.toggle('active', a.dataset.target === current);
      }});

      // Keep active entry visible in sidebar scroll
      const activeLink = document.querySelector('#toc a.active');
      if (activeLink) {{
        const sc = document.getElementById('toc-scroll');
        const lr = activeLink.getBoundingClientRect();
        const sr = sc.getBoundingClientRect();
        if (lr.top < sr.top + 20 || lr.bottom > sr.bottom - 40) {{
          activeLink.scrollIntoView({{ block: 'center', behavior: 'smooth' }});
        }}
      }}
    }}
    window.addEventListener('scroll', updateActiveHeading, {{ passive: true }});

    function render(md) {{
      const html = marked.parse(md, {{ gfm: true, breaks: false }});
      buildToc(html);

      const content = document.getElementById('content');
      content.innerHTML = html;

      // Assign IDs to headings
      const rendered = content.querySelectorAll('h1, h2, h3, h4');
      rendered.forEach((h, i) => {{
        h.id = slugify(h.textContent) + '-' + i;
      }});

      document.getElementById('last-updated').textContent =
        new Date().toLocaleTimeString();

      updateActiveHeading();
    }}

    async function poll() {{
      try {{
        const res = await fetch('/api/content');
        const data = await res.json();
        if (data.mtime !== lastMtime) {{
          lastMtime = data.mtime;
          render(data.content);
        }}
      }} catch(e) {{}}
      setTimeout(poll, 500);
    }}

    poll();
  </script>
</body>
</html>"""


class PreviewHandler(http.server.BaseHTTPRequestHandler):
    filepath = ""
    _cache = {"content": "", "mtime": 0}

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/content":
            try:
                mtime = os.path.getmtime(self.filepath)
                if mtime != self._cache["mtime"]:
                    with open(self.filepath, "r") as f:
                        self._cache["content"] = f.read()
                    self._cache["mtime"] = mtime
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps({
                "content": self._cache["content"],
                "mtime": self._cache["mtime"],
            }).encode())
        else:
            title = os.path.basename(self.filepath)
            html = HTML_TEMPLATE.format(title=title, filepath=self.filepath)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mdpreview.py <file.md> [--port PORT]")
        sys.exit(1)

    filepath = os.path.abspath(sys.argv[1])
    port = PORT

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    PreviewHandler.filepath = filepath

    server = http.server.HTTPServer(("127.0.0.1", port), PreviewHandler)
    print(f"\033[38;2;137;180;250m📄 {os.path.basename(filepath)}\033[0m")
    print(f"\033[38;2;166;227;161m🌐 http://127.0.0.1:{port}\033[0m")
    print(f"\033[38;2;88;91;112m⚡ Live reload · Catppuccin Mocha · TOC\033[0m")
    print(f"\nCtrl+C to stop")

    # Launch in Chrome --app mode for a standalone window (no address bar/tabs)
    import shutil
    url = f"http://127.0.0.1:{port}"
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    chrome = next((p for p in chrome_paths if os.path.exists(p)), None)
    if chrome:
        import subprocess
        subprocess.Popen([chrome, f"--app={url}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        os.system(f"open {url}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\033[38;2;88;91;112mStopped.\033[0m")
        server.server_close()


if __name__ == "__main__":
    main()
