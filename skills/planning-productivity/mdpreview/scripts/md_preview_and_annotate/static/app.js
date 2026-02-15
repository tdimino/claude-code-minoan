/* ══════════════════════════════════════════════════════════
   mdpreview — app.js
   State, rendering, tabs, annotations, polling
   ══════════════════════════════════════════════════════════ */

/* ── State ────────────────────────────────────────────── */
const tabs = {};
let activeTabId = null;
const annotationsCache = {};
const lastAnnotationMtimes = {};
let annotateSelection = null;
const defaultAuthor = window.MDPREVIEW_CONFIG.defaultAuthor;

/* Track last-rendered markdown to avoid redundant DOM updates */
let lastRenderedMd = '';
let lastRenderedAnnotationsKey = '';

/* ── Font Size ────────────────────────────────────────── */
let currentSize = parseInt(localStorage.getItem('mdpreview-fontsize') || '15');

function applyFontSize() {
  document.documentElement.style.setProperty('--base-size', currentSize + 'px');
  const display = document.getElementById('font-size-display');
  if (display) display.textContent = currentSize;
  localStorage.setItem('mdpreview-fontsize', currentSize);
}
applyFontSize();

function adjustFont(delta) {
  currentSize = Math.max(11, Math.min(22, currentSize + delta));
  applyFontSize();
}

/* ── Theme ────────────────────────────────────────────── */
let currentTheme = localStorage.getItem('mdpreview-theme') || 'mocha';
function applyTheme() {
  document.documentElement.setAttribute('data-theme', currentTheme);
  const toggle = document.getElementById('theme-toggle');
  if (toggle) toggle.checked = (currentTheme === 'latte');
  localStorage.setItem('mdpreview-theme', currentTheme);
}
applyTheme();

function toggleTheme() {
  currentTheme = currentTheme === 'mocha' ? 'latte' : 'mocha';
  applyTheme();
}

function toggleToc() {
  document.body.classList.toggle('toc-collapsed');
}

/* ── Utility ──────────────────────────────────────────── */
function slugify(text) {
  return text.toLowerCase().replace(/[^\w]+/g, '-').replace(/^-|-$/g, '');
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

/* ── Annotations Toggle & Gutter Overlay ──────────────── */
function updateAnnotationsBadge(count) {
  const toggle = document.getElementById('annotations-toggle');
  const badge = document.getElementById('ann-count-badge');
  const gutterCount = document.getElementById('ann-gutter-count');
  if (!toggle || !badge) return;

  if (count > 0) {
    toggle.classList.add('has-annotations');
    badge.textContent = count;
  } else {
    toggle.classList.remove('has-annotations');
    badge.textContent = '0';
  }

  if (gutterCount) gutterCount.textContent = count;

  /* On wide screens where gutter is natively visible, hide toggle */
  const gutter = document.getElementById('annotations-gutter');
  const isNativelyVisible = gutter && window.innerWidth > 1400;
  if (isNativelyVisible) {
    toggle.classList.add('gutter-native');
  } else {
    toggle.classList.remove('gutter-native');
  }
}

function openGutterOverlay() {
  const gutter = document.getElementById('annotations-gutter');
  gutter.classList.add('overlay-open');
}

function closeGutterOverlay() {
  const gutter = document.getElementById('annotations-gutter');
  gutter.classList.remove('overlay-open');
}

document.getElementById('annotations-toggle').onclick = () => {
  const gutter = document.getElementById('annotations-gutter');
  if (gutter.classList.contains('overlay-open')) {
    closeGutterOverlay();
  } else {
    openGutterOverlay();
  }
};

document.getElementById('ann-gutter-close').onclick = () => {
  closeGutterOverlay();
};

/* ── TOC ──────────────────────────────────────────────── */
function buildToc(html) {
  const tmp = document.createElement('div');
  tmp.innerHTML = html;
  const headings = tmp.querySelectorAll('h1, h2, h3, h4');
  const toc = document.getElementById('toc-list');
  toc.innerHTML = '';
  headings.forEach((h, i) => {
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
  });
}

/* Scroll spy — throttled with rAF */
let scrollSpyPending = false;
function updateActiveHeading() {
  if (scrollSpyPending) return;
  scrollSpyPending = true;
  requestAnimationFrame(() => {
    scrollSpyPending = false;
    const headings = document.querySelectorAll('#content h1, #content h2, #content h3, #content h4');
    const links = document.querySelectorAll('#toc a');
    let current = '';

    headings.forEach(h => {
      const rect = h.getBoundingClientRect();
      if (rect.top <= 80) current = h.id;
    });

    links.forEach(a => {
      a.classList.toggle('active', a.dataset.target === current);
    });

    const activeLink = document.querySelector('#toc a.active');
    if (activeLink) {
      const sc = document.getElementById('toc-scroll');
      const lr = activeLink.getBoundingClientRect();
      const sr = sc.getBoundingClientRect();
      if (lr.top < sr.top + 20 || lr.bottom > sr.bottom - 40) {
        activeLink.scrollIntoView({ block: 'center', behavior: 'smooth' });
      }
    }
  });
}
window.addEventListener('scroll', updateActiveHeading, { passive: true });

/* ── Render ───────────────────────────────────────────── */
function render(md) {
  /* Skip if content hasn't changed */
  if (md === lastRenderedMd) return;
  lastRenderedMd = md;

  const html = marked.parse(md, { gfm: true, breaks: false });
  buildToc(html);

  const content = document.getElementById('content');
  content.innerHTML = html;

  /* Assign IDs to headings */
  content.querySelectorAll('h1, h2, h3, h4').forEach((h, i) => {
    h.id = slugify(h.textContent) + '-' + i;
  });

  /* Syntax highlighting */
  if (typeof hljs !== 'undefined') {
    content.querySelectorAll('pre code').forEach(el => {
      hljs.highlightElement(el);
    });
  }

  document.getElementById('last-updated').textContent =
    new Date().toLocaleTimeString();

  updateActiveHeading();
  updateWordCount(md);

  /* Re-apply annotation highlights after content change */
  applyAnnotationHighlights();
}

/* ── Word Count ───────────────────────────────────────── */
function updateWordCount(md) {
  const text = md.replace(/[#*_`~\[\]()>|\\-]/g, ' ').trim();
  const words = text.split(/\s+/).filter(w => w.length > 0).length;
  const mins = Math.max(1, Math.ceil(words / 250));
  const el = document.getElementById('word-count');
  if (el) el.textContent = words.toLocaleString() + ' words \u00b7 ' + mins + ' min read';
}

/* ── Tab Bar ──────────────────────────────────────────── */
function renderTabBar() {
  const bar = document.getElementById('tab-bar');
  bar.innerHTML = '';

  const ids = Object.keys(tabs);
  ids.forEach(id => {
    const tab = tabs[id];
    const div = document.createElement('div');
    div.className = 'tab' + (id === activeTabId ? ' active' : '');
    div.dataset.tab = id;
    div.title = tab.filepath;

    const nameSpan = document.createElement('span');
    nameSpan.textContent = tab.filename;
    div.appendChild(nameSpan);

    if (ids.length > 1) {
      const close = document.createElement('span');
      close.className = 'tab-close';
      close.innerHTML = '&times;';
      close.onclick = (e) => { e.stopPropagation(); closeTab(id); };
      div.appendChild(close);
    }

    div.onclick = () => switchTab(id);
    bar.appendChild(div);
  });

  /* + button */
  const addBtn = document.createElement('button');
  addBtn.id = 'tab-add';
  addBtn.title = 'Open file';
  addBtn.innerHTML = '<i class="ph ph-plus"></i>';
  addBtn.onclick = showAddFileInput;
  bar.appendChild(addBtn);
}

function switchTab(id) {
  if (id === activeTabId || !tabs[id]) return;

  /* Cancel pending annotation */
  document.getElementById('annotation-form').style.display = 'none';
  document.getElementById('annotate-btn').style.display = 'none';
  annotateSelection = null;

  /* Save scroll position */
  if (activeTabId && tabs[activeTabId]) {
    tabs[activeTabId].scrollY = window.scrollY;
  }

  activeTabId = id;
  lastRenderedMd = '';  /* Force re-render for new tab */
  lastRenderedAnnotationsKey = '';
  localStorage.setItem('mdpreview-active-tab', id);

  renderTabBar();

  if (tabs[id].content) {
    render(tabs[id].content);
  } else {
    /* Content not yet loaded — fetch immediately */
    fetchTabContent(id);
  }

  /* Restore scroll position */
  requestAnimationFrame(() => {
    window.scrollTo(0, tabs[id].scrollY || 0);
  });

  /* Update status bar */
  document.getElementById('status-filepath').textContent = tabs[id].filepath;
}

/* Fetch content for a single tab and render if active */
async function fetchTabContent(id) {
  try {
    const res = await fetch('/api/content?tab=' + id);
    const data = await res.json();
    if (data.error || !tabs[id]) return;
    tabs[id].content = data.content;
    tabs[id].mtime = data.mtime;
    if (id === activeTabId) render(data.content);
  } catch (e) { /* ignore */ }
}

async function closeTab(id) {
  if (Object.keys(tabs).length <= 1) return;

  try {
    await fetch('/api/close', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id: id})
    });
  } catch(e) {}

  delete tabs[id];
  delete annotationsCache[id];
  delete lastAnnotationMtimes[id];

  if (id === activeTabId) {
    activeTabId = Object.keys(tabs)[0] || null;
    lastRenderedMd = '';
    if (activeTabId && tabs[activeTabId].content) {
      render(tabs[activeTabId].content);
      document.getElementById('status-filepath').textContent = tabs[activeTabId].filepath;
    }
  }
  renderTabBar();
}

function showAddFileInput() {
  const bar = document.getElementById('tab-bar');
  const addBtn = document.getElementById('tab-add');
  addBtn.style.display = 'none';

  const input = document.createElement('input');
  input.className = 'tab-add-input';
  input.type = 'text';
  input.placeholder = 'path/to/file.md';

  input.onkeydown = async (e) => {
    if (e.key === 'Enter') {
      const path = input.value.trim();
      if (path) {
        try {
          const res = await fetch('/api/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filepath: path})
          });
          const data = await res.json();
          if (data.id && !tabs[data.id]) {
            tabs[data.id] = {
              filepath: data.filepath || path,
              filename: data.filename,
              content: '', mtime: 0, scrollY: 0
            };
            /* Fetch content immediately */
            fetchTabContent(data.id);
          }
          renderTabBar();
        } catch(err) {
          console.error('Failed to add file:', err);
        }
      }
      input.remove();
      addBtn.style.display = '';
    } else if (e.key === 'Escape') {
      input.remove();
      addBtn.style.display = '';
    }
  };

  input.onblur = () => {
    setTimeout(() => {
      if (bar.contains(input)) {
        input.remove();
        addBtn.style.display = '';
      }
    }, 150);
  };

  bar.insertBefore(input, addBtn);
  input.focus();
}

/* ── Annotations ──────────────────────────────────────── */

/* Separate highlight application from bubble rendering */
function applyAnnotationHighlights() {
  /* Remove existing highlights */
  document.querySelectorAll('mark.annotation-highlight').forEach(m => {
    const parent = m.parentNode;
    parent.replaceChild(document.createTextNode(m.textContent), m);
    parent.normalize();
  });

  const anns = annotationsCache[activeTabId] || [];
  anns.forEach(ann => {
    if (!ann.anchor || !ann.anchor.text || ann.resolved) return;
    const content = document.getElementById('content');
    const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT);
    let node;
    while (node = walker.nextNode()) {
      const idx = node.textContent.indexOf(ann.anchor.text);
      if (idx >= 0) {
        try {
          const range = document.createRange();
          range.setStart(node, idx);
          range.setEnd(node, idx + ann.anchor.text.length);
          const mark = document.createElement('mark');
          mark.className = 'annotation-highlight';
          mark.dataset.annotationId = ann.id;
          range.surroundContents(mark);
        } catch(e) {}
        break;
      }
    }
  });

  /* Click highlights → scroll to bubble */
  document.querySelectorAll('mark.annotation-highlight').forEach(mark => {
    mark.onclick = () => {
      const id = mark.dataset.annotationId;
      const bubble = document.querySelector('.ann-bubble[data-annotation-id="' + id + '"]');
      if (bubble) {
        bubble.scrollIntoView({ behavior: 'smooth', block: 'center' });
        bubble.classList.add('focused');
        setTimeout(() => bubble.classList.remove('focused'), 1500);
      }
    };
  });
}

function renderAnnotations() {
  const list = document.getElementById('annotations-list');
  if (!list) return;

  const anns = annotationsCache[activeTabId] || [];

  /* Build a cache key to avoid redundant re-renders */
  const cacheKey = activeTabId + ':' + JSON.stringify(anns.map(a => a.id + a.resolved));
  if (cacheKey === lastRenderedAnnotationsKey) return;
  lastRenderedAnnotationsKey = cacheKey;

  list.innerHTML = '';

  updateAnnotationsBadge(anns.length);

  if (anns.length === 0) {
    list.innerHTML = '<div class="ann-hint">Select text to annotate</div>';
    applyAnnotationHighlights();
    return;
  }

  anns.forEach(ann => {
    const found = !!document.querySelector('mark[data-annotation-id="' + ann.id + '"]');

    /* Create bubble card */
    const bubble = document.createElement('div');
    bubble.className = 'ann-bubble'
      + (ann.resolved ? ' resolved' : '')
      + (!found && !ann.resolved && ann.anchor && ann.anchor.text ? ' orphaned' : '');
    bubble.dataset.annotationId = ann.id;

    const authorType = (ann.author && ann.author.type === 'ai') ? 'ai' : 'human';
    const authorIcon = authorType === 'ai'
      ? '<i class="ph ph-robot" style="font-size:10px"></i> ' : '';
    const timeStr = ann.created
      ? new Date(ann.created).toLocaleDateString('en-US', {
          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
        })
      : '';

    const bodyText = ann.resolved
      ? '<s>' + escapeHtml(ann.body) + '</s>'
      : escapeHtml(ann.body);
    const anchorSnippet = (ann.anchor && ann.anchor.text)
      ? '<div class="ann-anchor-text">&ldquo;'
        + escapeHtml(ann.anchor.text.substring(0, 60))
        + (ann.anchor.text.length > 60 ? '&hellip;' : '')
        + '&rdquo;</div>'
      : '';

    bubble.innerHTML =
      '<div class="ann-author ' + authorType + '">'
        + authorIcon + escapeHtml(ann.author ? ann.author.name : 'Unknown')
        + '<span class="ann-time">' + timeStr + '</span>'
        + '<span class="ann-actions">'
          + '<button class="ann-resolve-btn" data-ann-id="' + ann.id + '" title="'
          + (ann.resolved ? 'Unresolve' : 'Resolve') + '">'
          + '<i class="ph ' + (ann.resolved ? 'ph-arrow-counter-clockwise' : 'ph-check') + '"></i>'
          + '</button>'
          + '<button class="ann-delete-btn" data-ann-id="' + ann.id + '" title="Delete">'
          + '<i class="ph ph-trash"></i>'
          + '</button>'
        + '</span>'
      + '</div>'
      + '<div class="ann-body">' + bodyText + '</div>'
      + anchorSnippet;

    /* Click bubble → scroll to highlight */
    bubble.onclick = (e) => {
      if (e.target.closest('.ann-resolve-btn')) return;
      const mark = document.querySelector('mark[data-annotation-id="' + ann.id + '"]');
      if (mark) {
        mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
        mark.classList.add('pulse');
        setTimeout(() => mark.classList.remove('pulse'), 600);
      }
    };

    list.appendChild(bubble);
  });

  /* Resolve button handlers */
  list.querySelectorAll('.ann-resolve-btn').forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      resolveAnnotation(btn.dataset.annId);
    };
  });

  /* Delete button handlers */
  list.querySelectorAll('.ann-delete-btn').forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      deleteAnnotation(btn.dataset.annId);
    };
  });

  /* Apply highlights after bubbles are rendered */
  applyAnnotationHighlights();
}

async function resolveAnnotation(annId) {
  try {
    await fetch('/api/resolve', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tab: activeTabId, id: annId})
    });
    lastAnnotationMtimes[activeTabId] = -1;
    lastRenderedAnnotationsKey = '';
  } catch(e) {}
}

async function deleteAnnotation(annId) {
  try {
    await fetch('/api/delete-annotation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tab: activeTabId, id: annId})
    });
    lastAnnotationMtimes[activeTabId] = -1;
    lastRenderedAnnotationsKey = '';
  } catch(e) {}
}

/* ── Text Selection → Annotate ────────────────────────── */
document.addEventListener('mouseup', (e) => {
  const btn = document.getElementById('annotate-btn');
  const sel = window.getSelection();

  if (!sel || sel.isCollapsed || !sel.toString().trim()) {
    setTimeout(() => { if (btn) btn.style.display = 'none'; }, 200);
    return;
  }

  const content = document.getElementById('content');
  if (!content.contains(sel.anchorNode)) {
    if (btn) btn.style.display = 'none';
    return;
  }

  const text = sel.toString().trim();
  const range = sel.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  /* Find nearest heading above selection */
  let heading = '';
  let el = sel.anchorNode.nodeType === Node.TEXT_NODE ? sel.anchorNode.parentElement : sel.anchorNode;
  while (el && el !== content) {
    let prev = el.previousElementSibling;
    while (prev) {
      if (/^H[1-4]$/i.test(prev.tagName)) {
        heading = prev.id || '';
        break;
      }
      prev = prev.previousElementSibling;
    }
    if (heading) break;
    el = el.parentElement;
  }

  annotateSelection = { text: text, heading: heading };

  btn.style.display = 'flex';
  btn.style.left = (rect.left + rect.width / 2 - 16 + window.scrollX) + 'px';
  btn.style.top = (rect.top + window.scrollY - 40) + 'px';
});

document.getElementById('annotate-btn').onclick = () => {
  if (!annotateSelection) return;
  /* On narrow screens, force-open gutter so the form is visible */
  if (window.innerWidth <= 1400) {
    openGutterOverlay();
  }
  showAnnotationForm();
  document.getElementById('annotate-btn').style.display = 'none';
};

function showAnnotationForm() {
  const form = document.getElementById('annotation-form');
  form.style.display = 'block';
  document.getElementById('ann-author-input').value = defaultAuthor;
  document.getElementById('ann-body-input').value = '';
  document.getElementById('ann-body-input').focus();
}

document.getElementById('ann-submit-btn').onclick = async () => {
  const author = document.getElementById('ann-author-input').value.trim();
  const body = document.getElementById('ann-body-input').value.trim();

  if (!body || !annotateSelection) return;

  const authorType = ['claude', 'ai', 'assistant'].includes(author.toLowerCase()) ? 'ai' : 'human';

  try {
    await fetch('/api/annotate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        tab: activeTabId,
        anchor: { text: annotateSelection.text, heading: annotateSelection.heading, offset: 0 },
        author: { name: author, type: authorType },
        body: body
      })
    });
  } catch(e) {
    console.error('Failed to annotate:', e);
  }

  document.getElementById('annotation-form').style.display = 'none';
  annotateSelection = null;
  window.getSelection().removeAllRanges();
  lastAnnotationMtimes[activeTabId] = -1;
  lastRenderedAnnotationsKey = '';
};

document.getElementById('ann-cancel-btn').onclick = () => {
  document.getElementById('annotation-form').style.display = 'none';
  annotateSelection = null;
};

/* Keyboard shortcuts in annotation form */
document.getElementById('ann-body-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
    document.getElementById('ann-submit-btn').click();
  } else if (e.key === 'Escape') {
    document.getElementById('ann-cancel-btn').click();
  }
});

/* ── Cross-file Link Interception ─────────────────────── */
document.addEventListener('click', (e) => {
  const a = e.target.closest('#content a');
  if (!a) return;
  const href = a.getAttribute('href');
  if (!href) return;

  if (href.endsWith('.md') && !href.startsWith('http')) {
    e.preventDefault();
    openFileAsTab(href);
  }
});

async function openFileAsTab(path) {
  try {
    const res = await fetch('/api/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({filepath: path})
    });
    const data = await res.json();
    if (data.error) { console.error(data.error); return; }
    if (data.id && !tabs[data.id]) {
      tabs[data.id] = {
        filepath: data.filepath || path,
        filename: data.filename,
        content: '', mtime: 0, scrollY: 0
      };
    }
    if (data.id) {
      renderTabBar();
      switchTab(data.id);
    }
  } catch(e) {
    console.error('Failed to open file:', e);
  }
}

/* ── Polling ──────────────────────────────────────────── */
const POLL_ACTIVE_MS = 500;
const POLL_TABS_MS = 2000;
let lastTabsCheck = 0;

async function poll() {
  const now = Date.now();

  /* Always poll active tab content (fast) */
  if (activeTabId && tabs[activeTabId]) {
    try {
      const res = await fetch('/api/content?tab=' + activeTabId);
      const data = await res.json();
      if (!data.error && data.mtime !== tabs[activeTabId].mtime) {
        tabs[activeTabId].content = data.content;
        tabs[activeTabId].mtime = data.mtime;
        render(data.content);
      }
    } catch (e) { /* ignore */ }
  }

  /* Check for new/removed tabs and poll inactive tab mtimes less frequently */
  if (now - lastTabsCheck >= POLL_TABS_MS) {
    lastTabsCheck = now;

    /* Poll inactive tabs */
    const inactiveIds = Object.keys(tabs).filter(id => id !== activeTabId);
    if (inactiveIds.length > 0) {
      await Promise.all(
        inactiveIds.map(id =>
          fetch('/api/content?tab=' + id)
            .then(r => r.json())
            .then(data => {
              if (!data.error && data.mtime !== tabs[id].mtime) {
                tabs[id].content = data.content;
                tabs[id].mtime = data.mtime;
              }
            })
            .catch(() => {})
        )
      );
    }

    /* Check for tabs added/removed externally */
    try {
      const res = await fetch('/api/tabs');
      const tabList = await res.json();
      let changed = false;
      tabList.forEach(t => {
        if (!tabs[t.id]) {
          tabs[t.id] = { filepath: t.filepath, filename: t.filename, content: '', mtime: 0, scrollY: 0 };
          changed = true;
          /* Immediately fetch content for new tab */
          fetchTabContent(t.id);
        }
      });
      const serverIds = new Set(tabList.map(t => t.id));
      for (const id of Object.keys(tabs)) {
        if (!serverIds.has(id)) {
          delete tabs[id];
          changed = true;
          if (id === activeTabId) {
            activeTabId = Object.keys(tabs)[0] || null;
            lastRenderedMd = '';
            if (activeTabId) {
              render(tabs[activeTabId].content);
              document.getElementById('status-filepath').textContent = tabs[activeTabId].filepath;
            }
          }
        }
      }
      if (changed) renderTabBar();
    } catch(e) {}
  }

  /* Poll annotations for active tab */
  if (activeTabId) {
    try {
      const res = await fetch('/api/annotations?tab=' + activeTabId);
      const data = await res.json();
      if (data.mtime !== (lastAnnotationMtimes[activeTabId] || 0)) {
        lastAnnotationMtimes[activeTabId] = data.mtime;
        annotationsCache[activeTabId] = data.annotations;
        renderAnnotations();
      }
    } catch(e) {}
  }

  setTimeout(poll, POLL_ACTIVE_MS);
}

/* ── Init ─────────────────────────────────────────────── */
async function init() {
  const res = await fetch('/api/tabs');
  const tabList = await res.json();

  tabList.forEach(t => {
    tabs[t.id] = { filepath: t.filepath, filename: t.filename, content: '', mtime: 0, scrollY: 0 };
  });

  /* Restore active tab from localStorage, or use first */
  const stored = localStorage.getItem('mdpreview-active-tab');
  if (stored && tabs[stored]) {
    activeTabId = stored;
  } else if (tabList.length > 0) {
    activeTabId = tabList[0].id;
  }

  renderTabBar();

  /* Fetch all content in parallel */
  await Promise.all(
    Object.keys(tabs).map(id =>
      fetch('/api/content?tab=' + id)
        .then(r => r.json())
        .then(data => {
          tabs[id].content = data.content;
          tabs[id].mtime = data.mtime;
        })
        .catch(() => {})
    )
  );

  if (activeTabId && tabs[activeTabId]) {
    render(tabs[activeTabId].content);
    document.getElementById('status-filepath').textContent = tabs[activeTabId].filepath;
  }

  poll();
}

init();
