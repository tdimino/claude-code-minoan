"""HTML template assembly — reads static CSS/JS and builds the page shell."""

import json
import os

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def _read_static(filename):
    with open(os.path.join(_STATIC_DIR, filename)) as f:
        return f.read()


def get_html(title="mdpreview", default_author="Tom"):
    css = _read_static("styles.css")
    js = _read_static("app.js")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Victor+Mono:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<script src="https://unpkg.com/@phosphor-icons/web@2.1.1"></script>
<style>
{css}
</style>
<script>
  window.MDPREVIEW_CONFIG = {{ defaultAuthor: {json.dumps(default_author)} }};
</script>
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
  <div id="toc-resize-handle"></div>
  <button id="toc-restore" title="Show sidebar" onclick="toggleToc()"><i class="ph ph-caret-right"></i></button>

  <div id="main-area">
    <div id="tab-bar"></div>
    <div id="content"></div>
  </div>

  <div id="annotations-gutter">
    <div class="ann-gutter-header">
      <span class="ann-gutter-title">Notes</span>
      <span class="ann-gutter-count" id="ann-gutter-count">0</span>
      <button class="ann-gutter-close" id="ann-gutter-close" title="Close"><i class="ph ph-x"></i></button>
    </div>
    <div id="annotation-form" style="display:none;">
      <div class="ann-type-picker">
        <button class="ann-type-btn selected" data-type="comment"><i class="ph ph-chat-dots"></i>Comment</button>
        <button class="ann-type-btn" data-type="question"><i class="ph ph-question"></i>Question</button>
        <button class="ann-type-btn" data-type="suggestion"><i class="ph ph-lightbulb"></i>Suggestion</button>
        <button class="ann-type-btn" data-type="important"><i class="ph ph-flag"></i>Important</button>
        <button class="ann-type-btn" data-type="bookmark"><i class="ph ph-bookmark-simple"></i>Bookmark</button>
      </div>
      <div class="ann-form-label">Author</div>
      <input type="text" id="ann-author-input" value="">
      <div class="ann-form-label">Comment</div>
      <textarea id="ann-body-input" placeholder="Add a comment..." rows="3"></textarea>
      <div class="ann-form-actions">
        <button class="ann-btn-primary" id="ann-submit-btn">Comment</button>
        <button class="ann-btn-ghost" id="ann-cancel-btn">Cancel</button>
      </div>
    </div>
    <div id="annotations-list"></div>
  </div>

  <div id="annotate-carousel">
    <button class="carousel-btn" data-type="comment"><i class="ph ph-chat-dots"></i><span>Comment</span></button>
    <button class="carousel-btn" data-type="question"><i class="ph ph-question"></i><span>Question</span></button>
    <button class="carousel-btn" data-type="suggestion"><i class="ph ph-lightbulb"></i><span>Suggest</span></button>
    <button class="carousel-btn" data-type="important"><i class="ph ph-flag"></i><span>Flag</span></button>
    <button class="carousel-btn" data-type="bookmark"><i class="ph ph-bookmark-simple"></i><span>Bookmark</span></button>
  </div>
  <button id="annotations-toggle" title="Annotations"><i class="ph ph-chat-circle-dots"></i><span class="ann-count" id="ann-count-badge">0</span></button>

  <div id="status">
    <span class="filepath" id="status-filepath"></span>
    <span id="word-count"></span>
    <span class="updated"><span class="dot"></span><span id="last-updated">connecting...</span></span>
  </div>

  <script>
{js}
  </script>
</body>
</html>"""
