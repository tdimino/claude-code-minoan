#!/usr/bin/env python3
"""Generator for scroll-cinema HTML output.

Produces single-file HTML pages with Lenis smooth scroll,
GSAP ScrollTrigger cinematic section reveals, OKLCH color transitions,
and optional Three.js painted shader backgrounds.
"""

import argparse
import re
from html import escape as html_escape
from pathlib import Path

CHAPTER_PALETTES = {
    "dawn-to-dusk": [
        {"hue": 250, "chroma": 0.15, "lightness": 0.25, "title": "Before Dawn", "body": "The world holds its breath in indigo silence."},
        {"hue": 30,  "chroma": 0.18, "lightness": 0.45, "title": "First Light", "body": "Amber spills across the horizon like molten glass."},
        {"hue": 160, "chroma": 0.12, "lightness": 0.35, "title": "Morning", "body": "Teal waters catch the rising sun."},
        {"hue": 340, "chroma": 0.20, "lightness": 0.30, "title": "Afternoon", "body": "Rose light deepens in the western sky."},
        {"hue": 60,  "chroma": 0.08, "lightness": 0.55, "title": "Golden Hour", "body": "The last light turns everything to gold."},
    ],
    "ocean-descent": [
        {"hue": 200, "chroma": 0.14, "lightness": 0.50, "title": "Surface", "body": "Sunlight scatters through the first meters."},
        {"hue": 210, "chroma": 0.16, "lightness": 0.40, "title": "Twilight Zone", "body": "The blue deepens. Light fades."},
        {"hue": 220, "chroma": 0.18, "lightness": 0.25, "title": "Midnight Zone", "body": "Complete darkness presses from every direction."},
        {"hue": 190, "chroma": 0.22, "lightness": 0.35, "title": "Bioluminescence", "body": "Life writes its own light in the abyss."},
        {"hue": 180, "chroma": 0.10, "lightness": 0.15, "title": "Hadal", "body": "The deepest pressure. The oldest silence."},
    ],
    "default": [
        {"hue": 250, "chroma": 0.15, "lightness": 0.25, "title": "Chapter One", "body": "The story begins here."},
        {"hue": 30,  "chroma": 0.18, "lightness": 0.45, "title": "Chapter Two", "body": "Something shifts."},
        {"hue": 160, "chroma": 0.12, "lightness": 0.35, "title": "Chapter Three", "body": "The turning point."},
        {"hue": 340, "chroma": 0.20, "lightness": 0.30, "title": "Chapter Four", "body": "Consequences unfold."},
        {"hue": 60,  "chroma": 0.08, "lightness": 0.55, "title": "Chapter Five", "body": "Resolution arrives."},
    ],
}

PACING_MULTIPLIERS = {
    "slow": 1.5,
    "medium": 1.0,
    "fast": 0.6,
}


def get_chapters(count, palette_name="default"):
    palette = CHAPTER_PALETTES.get(palette_name, CHAPTER_PALETTES["default"])
    if count <= len(palette):
        return palette[:count]
    chapters = []
    for i in range(count):
        idx = i % len(palette)
        ch = dict(palette[idx])
        ch["title"] = f"Chapter {i + 1}"
        chapters.append(ch)
    return chapters


def generate_shader_glsl(preset):
    if preset == "painted-dots":
        return """
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uScroll;
uniform float uTime;
uniform float uVelocity;
uniform float uChapter;
uniform float uChapterHue;
uniform float uChapterLightness;

vec3 hsl2rgb(float h, float s, float l) {
  vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
  return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}

void main() {
  vec2 screenUv = gl_FragCoord.xy / uResolution;
  float aspect = uResolution.x / uResolution.y;
  vec2 uv = vec2(screenUv.x * aspect, screenUv.y);
  float gridSize = mix(14.0, 28.0, uScroll) * (1.0 + uChapter * 0.05);
  vec2 gridUv = fract(uv * gridSize);
  vec2 gridId = floor(uv * gridSize);
  float dist = length(gridUv - 0.5);
  vec2 mouseUv = vec2(uMouse.x * aspect, uMouse.y);
  float mouseDist = length(uv - mouseUv);
  float mouseInfluence = smoothstep(0.35, 0.0, mouseDist);
  float pulse = sin(uTime * 0.5 + gridId.x * 0.3 + gridId.y * 0.5) * 0.04;
  float baseRadius = 0.14 + pulse + mouseInfluence * 0.16;
  float radius = baseRadius * (1.0 + uVelocity * 0.5);
  float dot = smoothstep(radius + 0.025, radius - 0.025, dist);
  float h = uChapterHue;
  float s = 0.4 + mouseInfluence * 0.3;
  float l = uChapterLightness + 0.15 + mouseInfluence * 0.1;
  vec3 dotColor = hsl2rgb(h, s, l);
  vec3 bgColor = hsl2rgb(h, 0.1, uChapterLightness * 0.3);
  gl_FragColor = vec4(mix(bgColor, dotColor, dot), 1.0);
}"""
    elif preset == "watercolor":
        return """
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uScroll;
uniform float uTime;
uniform float uVelocity;
uniform float uChapter;
uniform float uMobile;
uniform float uChapterHue;
uniform float uChapterLightness;

vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }
float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz; x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
  m = m*m; m = m*m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
  vec3 g; g.x = a0.x*x0.x + h.x*x0.y; g.yz = a0.yz*x12.xz + h.yz*x12.yw;
  return 130.0 * dot(m, g);
}

vec3 hsl2rgb(float h, float s, float l) {
  vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
  return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}

void main() {
  vec2 screenUv = gl_FragCoord.xy / uResolution;
  float aspect = uResolution.x / uResolution.y;
  vec2 uv = vec2(screenUv.x * aspect, screenUv.y);
  vec2 mouseUv = vec2(uMouse.x * aspect, uMouse.y);
  float mouseDist = length(uv - mouseUv);
  vec2 mouseDisplace = (uv - mouseUv) * smoothstep(0.4, 0.0, mouseDist) * 0.15;
  vec2 noiseUv = uv + mouseDisplace + vec2(uScroll * 2.0, uScroll * 0.5);
  float freqScale = 1.0 + uChapter * 0.15;
  float n1 = snoise(noiseUv * 2.0 * freqScale + uTime * 0.05) * 0.6;
  float n2 = snoise(noiseUv * 4.0 * freqScale - uTime * 0.03) * 0.3;
  float noise;
  if (uMobile > 0.5) {
    noise = (n1 + n2) * (1.0 + uVelocity * 0.3);
  } else {
    float n3 = snoise(noiseUv * 8.0 * freqScale + uTime * 0.02) * 0.1;
    noise = (n1 + n2 + n3) * (1.0 + uVelocity * 0.3);
  }
  float quantized = floor(noise * 4.0 + 0.5) / 4.0;
  float h = uChapterHue + quantized * 0.08;
  float s = 0.35 + quantized * 0.15;
  float l = uChapterLightness + 0.1 + quantized * 0.12;
  vec3 color = hsl2rgb(h, s, l);
  if (uMobile < 0.5) {
    float edge = length(vec2(dFdx(noise), dFdy(noise))) * 80.0;
    float edgeLine = smoothstep(0.15, 0.35, edge);
    color = mix(color, color * 0.6, edgeLine * 0.4);
  }
  gl_FragColor = vec4(color, 1.0);
}"""
    else:  # domain-warp
        return """
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uScroll;
uniform float uTime;
uniform float uVelocity;
uniform float uChapter;
uniform float uChapterHue;
uniform float uChapterLightness;

vec3 hsl2rgb(float h, float s, float l) {
  vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
  return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}

void main() {
  vec2 screenUv = gl_FragCoord.xy / uResolution;
  float aspect = uResolution.x / uResolution.y;
  vec2 uv = vec2(screenUv.x * aspect, screenUv.y);
  vec2 mouseUv = vec2(uMouse.x * aspect, uMouse.y);
  vec2 mouseOffset = (uv - mouseUv) * smoothstep(0.5, 0.0, length(uv - mouseUv)) * 0.1;
  vec2 v = uv * 2.0 - 1.0 + mouseOffset;
  float t = uTime * 0.3 + uChapter * 0.5;
  int warpCount = int(mix(2.0, 6.0, uScroll));
  float amplitude = 2.0;
  for (int i = 0; i < 6; i++) {
    if (i >= warpCount) break;
    v += sin(v.yx * (1.0 + float(i) * 0.3) + t) / amplitude * (1.0 + uVelocity * 0.4);
    amplitude += 0.5;
  }
  float h = uChapterHue + v.x * 0.05 + v.y * 0.03;
  float s = 0.4 + sin(v.x * 3.0) * 0.15;
  float l = uChapterLightness + 0.15 + sin(v.y * 2.0 + v.x) * 0.1;
  vec3 color = hsl2rgb(h, s, clamp(l, 0.05, 0.85));
  gl_FragColor = vec4(color, 1.0);
}"""


def _sanitize_font(font):
    return re.sub(r'[^A-Za-z0-9 _-]', '', font)


def _sanitize_css_value(value):
    return re.sub(r'[^A-Za-z0-9().,%# -]', '', value)


SHADER_DESCRIPTIONS = {
    "painted-dots": {
        "title": "Painted Dots",
        "body": "Dot-grid with mouse-reactive ripple and scroll-driven density shift. The lightest preset.",
    },
    "watercolor": {
        "title": "Watercolor",
        "body": "NPR watercolor effect with layered simplex noise, quantized color bands, and ink-like edge detection.",
    },
    "domain-warp": {
        "title": "Domain Warp",
        "body": "Progressive sinusoidal domain warping. Complexity builds as the reader scrolls deeper.",
    },
}


def generate_catalog_html(color_scheme, font, accent, title="Shader Catalog"):
    safe_title = html_escape(title)
    safe_font = _sanitize_font(font)
    safe_accent = _sanitize_css_value(accent) if accent else None

    text_color = "#E8ECF4" if color_scheme == "dark" else "#1a1a2e"
    text_heading = "#FFFFFF" if color_scheme == "dark" else "#0a0a1a"
    text_muted = "rgba(232,236,244,0.6)" if color_scheme == "dark" else "rgba(26,26,46,0.6)"
    bg_lightness = 0.15 if color_scheme == "dark" else 0.92

    presets = ["painted-dots", "watercolor", "domain-warp"]
    cards_html = ""
    for preset in presets:
        desc = SHADER_DESCRIPTIONS[preset]
        cards_html += f"""
      <div class="catalog-card" data-shader="{preset}">
        <div class="shader-viewport" aria-hidden="true"></div>
        <h3>{html_escape(desc['title'])}</h3>
        <p>{html_escape(desc['body'])}</p>
      </div>"""

    shader_sources = {}
    for preset in presets:
        shader_sources[preset] = generate_shader_glsl(preset)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family={safe_font.replace(' ', '+')}:wght@400;700&display=swap" rel="stylesheet" crossorigin="anonymous">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lenis@1.2.3/dist/lenis.css" integrity="sha384-UuB6deGAnAeGSShmQfNVypuoM4D1q+qgqcc3FRyZPVLuPc4psm5o1VShNhqmootN" crossorigin="anonymous">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --sc-bg: oklch({bg_lightness} 0.02 250);
      --sc-text: {text_color};
      --sc-text-muted: {text_muted};
      --sc-text-heading: {text_heading};
      --sc-accent: {safe_accent if safe_accent else 'oklch(0.75 0.18 160)'};
      --sc-font-display: '{safe_font}', system-ui, sans-serif;
      --sc-font-body: '{safe_font}', system-ui, sans-serif;
    }}
    html, body {{
      font-family: var(--sc-font-body);
      color: var(--sc-text);
      background-color: var(--sc-bg);
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }}
    html.lenis, html.lenis body {{ height: auto; }}
    .lenis.lenis-smooth {{ scroll-behavior: auto !important; }}
    .catalog-header {{
      text-align: center;
      padding: clamp(3rem, 8vw, 6rem) 2rem clamp(2rem, 4vw, 4rem);
    }}
    .catalog-header h1 {{
      font-family: var(--sc-font-display);
      font-size: clamp(2rem, 4vw, 3.5rem);
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--sc-text-heading);
      margin-bottom: 0.75rem;
    }}
    .catalog-header p {{
      color: var(--sc-text-muted);
      font-size: clamp(1rem, 1.2vw, 1.25rem);
      max-width: 36rem;
      margin: 0 auto;
    }}
    .catalog-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 400px), 1fr));
      gap: 2rem;
      padding: 0 clamp(1rem, 3vw, 4rem) clamp(3rem, 6vw, 6rem);
      max-width: 1400px;
      margin: 0 auto;
    }}
    .catalog-card {{
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      background: oklch({bg_lightness + 0.05} 0.03 250);
    }}
    .shader-viewport {{
      width: 100%;
      aspect-ratio: 16 / 10;
      position: relative;
    }}
    .catalog-card h3 {{
      font-family: var(--sc-font-display);
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--sc-text-heading);
      padding: 1.25rem 1.5rem 0.25rem;
    }}
    .catalog-card p {{
      font-size: 0.95rem;
      line-height: 1.6;
      color: var(--sc-text-muted);
      padding: 0 1.5rem 1.5rem;
    }}
    #catalog-canvas {{
      position: fixed;
      top: 0; left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 1;
    }}
    .catalog-card h3, .catalog-card p {{ position: relative; z-index: 2; }}
    @media (max-width: 768px) {{
      .catalog-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .catalog-card {{ opacity: 1 !important; transform: none !important; }}
    }}
  </style>
  <script type="importmap">
  {{
    "imports": {{ "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js" }},
    "integrity": {{ "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js": "sha384-GY5FqjttLCFRt/McQbyaVdCk2O1IQtOeX8Py6NfD89BIAsIyJFRl4UgSXrk2vXAk" }}
  }}
  </script>
</head>
<body>
  <canvas id="catalog-canvas" aria-hidden="true"></canvas>
  <main>
    <section class="catalog-header" aria-label="Shader catalog">
      <h1>{safe_title}</h1>
      <p>Three shader presets for atmospheric backgrounds. Move your cursor and scroll to interact.</p>
    </section>
    <section class="catalog-grid" aria-label="Shader presets">
      {cards_html}
    </section>
  </main>

  <script defer src="https://cdn.jsdelivr.net/npm/lenis@1.2.3/dist/lenis.min.js" integrity="sha384-Ij66tWIEasctUl2SOYsvptZxi68o/ru5F3Y1fE6RZFoHP3KsEr7aEUbRm5H4k1Oz" crossorigin="anonymous"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/gsap.min.js" integrity="sha384-pEQB1h4Zmn9xhS6jotzltHSIQq6N0Oh3BXkCNOH5LKI81R2NRbb9efarAJYw9gTY" crossorigin="anonymous"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/ScrollTrigger.min.js" integrity="sha384-TgZ1GoXcDnrw/czNfaiSZSFV1zgIRv8aQOevBA8ppS4SkNONmzYfjARpXsDfdnUE" crossorigin="anonymous"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/CustomEase.min.js" integrity="sha384-fQWfiXBcbv8HgKB74Cic5DBJ0P/ZjQkjCcgk00t6l8Yv3rk/DG+9LPi/bbea+HwI" crossorigin="anonymous"></script>

  <script type="module">
    import * as THREE from 'three';

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    gsap.registerPlugin(ScrollTrigger, CustomEase);
    CustomEase.create('cinematicSmooth', '0.25,0.1,0.25,1');

    const canvas = document.getElementById('catalog-canvas');
    const renderer = new THREE.WebGLRenderer({{ canvas, alpha: true, antialias: false }});
    const isMobile = window.innerWidth <= 768;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.5 : 2.0));
    renderer.setSize(window.innerWidth, window.innerHeight);

    const vertexShader = `void main() {{ gl_Position = vec4(position.xy, 0.0, 1.0); }}`;

    const shaderSources = {{
      'painted-dots': `{shader_sources["painted-dots"]}`,
      'watercolor': `{shader_sources["watercolor"]}`,
      'domain-warp': `{shader_sources["domain-warp"]}`
    }};

    const cards = document.querySelectorAll('.catalog-card');
    const scenes = [];

    cards.forEach((card) => {{
      const preset = card.dataset.shader;
      const viewport = card.querySelector('.shader-viewport');
      const scene = new THREE.Scene();
      const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
      const uniforms = {{
        uTime: {{ value: 0 }},
        uMouse: {{ value: new THREE.Vector2(0.5, 0.5) }},
        uScroll: {{ value: 0 }},
        uResolution: {{ value: new THREE.Vector2(400, 250) }},
        uVelocity: {{ value: 0 }},
        uChapter: {{ value: 0 }},
        uMobile: {{ value: isMobile ? 1.0 : 0.0 }},
        uChapterHue: {{ value: 0.694 }},
        uChapterLightness: {{ value: 0.25 }}
      }};
      const material = new THREE.ShaderMaterial({{
        uniforms, vertexShader,
        fragmentShader: shaderSources[preset],
        depthTest: false, depthWrite: false
      }});
      scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));
      scenes.push({{ scene, camera, uniforms, material, element: viewport }});
    }});

    const lenis = new Lenis({{ autoRaf: false }});

    let scrollProgress = 0;
    let scrollVelocity = 0;
    lenis.on('scroll', ({{ scroll, limit, velocity }}) => {{
      scrollProgress = limit > 0 ? scroll / limit : 0;
      scrollVelocity = velocity;
    }});
    lenis.on('scroll', ScrollTrigger.update);

    let mouseTarget = {{ x: 0.5, y: 0.5 }};
    document.addEventListener('mousemove', (e) => {{
      mouseTarget.x = e.clientX / window.innerWidth;
      mouseTarget.y = 1.0 - (e.clientY / window.innerHeight);
    }});
    document.addEventListener('touchmove', (e) => {{
      const t = e.touches[0];
      mouseTarget.x = t.clientX / window.innerWidth;
      mouseTarget.y = 1.0 - (t.clientY / window.innerHeight);
    }}, {{ passive: true }});

    const tickCallback = (time) => {{
      lenis.raf(time * 1000);

      renderer.setScissorTest(true);
      const canvasRect = canvas.getBoundingClientRect();

      scenes.forEach(({{ scene, camera, uniforms, element }}) => {{
        const rect = element.getBoundingClientRect();
        if (rect.bottom < 0 || rect.top > canvasRect.height) return;

        const x = rect.left - canvasRect.left;
        const y = canvasRect.height - rect.bottom + canvasRect.top;
        const w = rect.width;
        const h = rect.height;

        renderer.setViewport(x, y, w, h);
        renderer.setScissor(x, y, w, h);

        uniforms.uScroll.value += (scrollProgress - uniforms.uScroll.value) * 0.05;
        uniforms.uMouse.value.x += (mouseTarget.x - uniforms.uMouse.value.x) * 0.08;
        uniforms.uMouse.value.y += (mouseTarget.y - uniforms.uMouse.value.y) * 0.08;
        const clampedVel = Math.max(-3, Math.min(3, scrollVelocity));
        uniforms.uVelocity.value += (Math.abs(clampedVel) / 3 - uniforms.uVelocity.value) * 0.10;
        uniforms.uTime.value = time;
        uniforms.uResolution.value.set(w, h);

        renderer.render(scene, camera);
      }});

      renderer.setScissorTest(false);
    }};

    if (!reducedMotion) {{
      gsap.ticker.add(tickCallback);
      gsap.ticker.lagSmoothing(0);

      cards.forEach((card, i) => {{
        gsap.from(card, {{
          y: 60, opacity: 0,
          duration: 0.8,
          delay: i * 0.15,
          ease: 'cinematicSmooth',
          scrollTrigger: {{ trigger: card, start: 'top 85%', toggleActions: 'play none none reverse' }}
        }});
      }});
    }} else {{
      renderer.setScissorTest(true);
      const canvasRect = canvas.getBoundingClientRect();
      scenes.forEach(({{ scene, camera, uniforms, element }}) => {{
        const rect = element.getBoundingClientRect();
        const x = rect.left - canvasRect.left;
        const y = canvasRect.height - rect.bottom + canvasRect.top;
        const w = rect.width;
        const h = rect.height;
        renderer.setViewport(x, y, w, h);
        renderer.setScissor(x, y, w, h);
        uniforms.uResolution.value.set(w, h);
        renderer.render(scene, camera);
      }});
      renderer.setScissorTest(false);
    }}

    let resizeTimeout;
    window.addEventListener('resize', () => {{
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {{
        const mobile = window.innerWidth <= 768;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1.5 : 2.0));
        renderer.setSize(window.innerWidth, window.innerHeight);
        scenes.forEach((s) => {{ s.uniforms.uMobile.value = mobile ? 1.0 : 0.0; }});
      }}, 80);
    }});

    function cleanup() {{
      gsap.ticker.remove(tickCallback);
      lenis.destroy();
      ScrollTrigger.killAll();
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    }}
    window.__scCleanup = cleanup;
  </script>
</body>
</html>"""


def generate_html(mode, shader, chapters, pacing, color_scheme, font, accent, title="Scroll Cinema", entrance="fade-up"):
    if mode == "catalog":
        return generate_catalog_html(color_scheme, font, accent, title)

    m = PACING_MULTIPLIERS.get(pacing, 1.0)
    chapter_height = int(200 * m)
    entrance_duration = round(1.2 * m, 2)
    stagger_delay = round(0.08 * m, 3)
    include_threejs = mode in ("painted-backdrop", "full-cinema")
    include_chapters = mode in ("chapter-reveal", "full-cinema")

    safe_title = html_escape(title)
    safe_font = _sanitize_font(font)
    safe_accent = _sanitize_css_value(accent) if accent else None

    chapters = [
        {k: float(v) if k in ("hue", "chroma", "lightness") else v for k, v in ch.items()}
        for ch in chapters
    ]
    first_ch = chapters[0] if chapters else {"hue": 250, "chroma": 0.15, "lightness": 0.25}

    text_color = "#E8ECF4" if color_scheme == "dark" else "#1a1a2e"
    text_heading = "#FFFFFF" if color_scheme == "dark" else "#0a0a1a"
    text_muted = "rgba(232,236,244,0.6)" if color_scheme == "dark" else "rgba(26,26,46,0.6)"

    sections_html = ""
    if include_chapters:
        for i, ch in enumerate(chapters):
            t = html_escape(ch['title'])
            b = html_escape(ch['body'])
            sections_html += f"""
    <section class="chapter" data-chapter="{i}" data-hue="{ch['hue']}" data-chroma="{ch['chroma']}" data-lightness="{ch['lightness']}" aria-label="{t}">
      <div class="chapter-content">
        <h2 class="chapter-title">{t}</h2>
        <p class="chapter-body">{b}</p>
      </div>
    </section>"""
    elif mode == "painted-backdrop":
        for i, ch in enumerate(chapters):
            sections_html += f"""
    <section class="chapter" data-chapter="{i}" data-hue="{ch['hue']}" data-chroma="{ch['chroma']}" data-lightness="{ch['lightness']}" aria-label="Scene {i + 1}" style="min-height: {chapter_height}vh;"></section>"""

    shader_glsl = generate_shader_glsl(shader) if include_threejs else ""

    canvas_html = '<canvas id="shader-canvas" aria-hidden="true"></canvas>' if include_threejs else ''

    import_map = ""
    if include_threejs:
        import_map = """
  <script type="importmap">
  {
    "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js" },
    "integrity": { "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js": "sha384-GY5FqjttLCFRt/McQbyaVdCk2O1IQtOeX8Py6NfD89BIAsIyJFRl4UgSXrk2vXAk" }
  }
  </script>"""

    # Three.js setup block (inside the module)
    threejs_setup = ""
    if include_threejs:
        threejs_setup = f"""
    import * as THREE from 'three';

    const canvas = document.getElementById('shader-canvas');
    const renderer = new THREE.WebGLRenderer({{ canvas, alpha: true, antialias: false }});
    const isMobile = window.innerWidth <= 768;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.5 : 2.0));
    renderer.setSize(window.innerWidth, window.innerHeight);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const uniforms = {{
      uTime: {{ value: 0 }},
      uMouse: {{ value: new THREE.Vector2(0.5, 0.5) }},
      uScroll: {{ value: 0 }},
      uResolution: {{ value: new THREE.Vector2(window.innerWidth, window.innerHeight) }},
      uVelocity: {{ value: 0 }},
      uChapter: {{ value: 0 }},
      uMobile: {{ value: isMobile ? 1.0 : 0.0 }},
      uChapterHue: {{ value: {first_ch['hue'] / 360.0:.3f} }},
      uChapterLightness: {{ value: {first_ch['lightness']} }}
    }};

    const vertexShader = `void main() {{ gl_Position = vec4(position.xy, 0.0, 1.0); }}`;
    const fragmentShader = `{shader_glsl}`;

    const material = new THREE.ShaderMaterial({{
      uniforms, vertexShader, fragmentShader,
      depthTest: false, depthWrite: false
    }});
    scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));

    let mouseTarget = {{ x: 0.5, y: 0.5 }};
    document.addEventListener('mousemove', (e) => {{
      mouseTarget.x = e.clientX / window.innerWidth;
      mouseTarget.y = 1.0 - (e.clientY / window.innerHeight);
    }});
    document.addEventListener('touchmove', (e) => {{
      const t = e.touches[0];
      mouseTarget.x = t.clientX / window.innerWidth;
      mouseTarget.y = 1.0 - (t.clientY / window.innerHeight);
    }}, {{ passive: true }});

    let resizeTimeout;
    window.addEventListener('resize', () => {{
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {{
        const w = window.innerWidth, h = window.innerHeight;
        const mobile = w <= 768;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1.5 : 2.0));
        renderer.setSize(w, h);
        uniforms.uResolution.value.set(w, h);
        uniforms.uMobile.value = mobile ? 1.0 : 0.0;
      }}, 80);
    }});"""

    # Shader state bridge for chapter colors → uniforms
    shader_state_init = ""
    if include_threejs:
        shader_state_init = f"\n    const shaderState = {{ hue: {first_ch['hue']}, lightness: {first_ch['lightness']} }};"

    # Ticker uniform updates
    ticker_shader = ""
    if include_threejs:
        ticker_shader = """
      uniforms.uScroll.value += (scrollProgress - uniforms.uScroll.value) * 0.05;
      uniforms.uMouse.value.x += (mouseTarget.x - uniforms.uMouse.value.x) * 0.08;
      uniforms.uMouse.value.y += (mouseTarget.y - uniforms.uMouse.value.y) * 0.08;
      const clampedVel = Math.max(-3, Math.min(3, scrollVelocity));
      uniforms.uVelocity.value += (Math.abs(clampedVel) / 3 - uniforms.uVelocity.value) * 0.10;
      uniforms.uChapter.value += (currentChapter - uniforms.uChapter.value) * 0.03;
      uniforms.uTime.value = time;
      uniforms.uChapterHue.value += (shaderState.hue / 360.0 - uniforms.uChapterHue.value) * 0.03;
      uniforms.uChapterLightness.value += (shaderState.lightness - uniforms.uChapterLightness.value) * 0.03;
      renderer.render(scene, camera);"""

    # Reduced motion block — only emit else branch when Three.js needs a static render
    reduced_motion_block = """\
    if (!reducedMotion) {
      gsap.ticker.add(tickCallback);
      gsap.ticker.lagSmoothing(0);
    }"""
    if include_threejs:
        reduced_motion_block = """\
    if (!reducedMotion) {
      gsap.ticker.add(tickCallback);
      gsap.ticker.lagSmoothing(0);
    } else {
      renderer.render(scene, camera);
    }"""

    # Cleanup
    cleanup_renderer = ""
    if include_threejs:
        cleanup_renderer = "\n      renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove();"

    # Shader state tween in chapter transitions
    shader_state_tween = ""
    if include_threejs:
        shader_state_tween = 'gsap.to(shaderState, { hue: parseFloat(hue), lightness: parseFloat(lightness), ease: "cinematicLinear", scrollTrigger: { trigger: section, start: "top center", end: "top top", scrub: 1 } });'

    # Text contrast transitions
    text_contrast_js = ""
    if include_chapters:
        text_contrast_js = """
        const isDark = parseFloat(lightness) < 0.5;
        gsap.to(':root', {
          '--sc-text': isDark ? '#E8ECF4' : '#1a1a2e',
          '--sc-text-heading': isDark ? '#FFFFFF' : '#0a0a1a',
          scrollTrigger: { trigger: section, start: 'top center', end: 'top top', scrub: 1 }
        });"""

    # Entrance animations
    entrance_js = ""
    if include_chapters:
        body_duration = round(entrance_duration * 0.8, 2)
        word_duration = round(entrance_duration * 0.67, 2)

        if entrance == "split-text":
            entrance_js = f"""
    if (!reducedMotion) {{
      const isMobileView = window.innerWidth <= 768;
      sections.forEach((section) => {{
        const title = section.querySelector('.chapter-title');
        const body = section.querySelector('.chapter-body');
        if (title) {{
          if (isMobileView) {{
            gsap.from(title, {{
              y: 80, opacity: 0,
              duration: {entrance_duration},
              ease: 'cinematicSilk',
              scrollTrigger: {{ trigger: section, start: 'top 80%', toggleActions: 'play none none reverse' }}
            }});
          }} else {{
            const text = title.textContent;
            title.textContent = '';
            text.split(/\\s+/).filter(w => w).forEach(word => {{
              const span = document.createElement('span');
              span.textContent = word + ' ';
              span.style.display = 'inline-block';
              title.appendChild(span);
            }});
            gsap.from(title.children, {{
              y: 40, opacity: 0,
              duration: {word_duration},
              stagger: {stagger_delay},
              ease: 'cinematicFlow',
              scrollTrigger: {{ trigger: section, start: 'top 75%', toggleActions: 'play none none reverse' }}
            }});
          }}
        }}
        if (body) {{
          gsap.from(body, {{
            y: 40, opacity: 0,
            duration: {body_duration},
            delay: 0.3,
            ease: 'cinematicSmooth',
            scrollTrigger: {{ trigger: section, start: 'top 80%', toggleActions: 'play none none reverse' }}
          }});
        }}
      }});
    }}"""
        elif entrance == "clip-path-wipe":
            entrance_js = f"""
    if (!reducedMotion) {{
      const isMobileView = window.innerWidth <= 768;
      sections.forEach((section) => {{
        const content = section.querySelector('.chapter-content');
        if (content) {{
          if (isMobileView) {{
            gsap.from(content, {{
              opacity: 0,
              duration: {entrance_duration},
              ease: 'cinematicSmooth',
              scrollTrigger: {{ trigger: section, start: 'top 80%', toggleActions: 'play none none reverse' }}
            }});
          }} else {{
            gsap.from(content, {{
              clipPath: 'inset(100% 0 0 0)',
              duration: {entrance_duration},
              ease: 'cinematicFlow',
              scrollTrigger: {{ trigger: section, start: 'top 80%', toggleActions: 'play none none reverse' }}
            }});
          }}
        }}
      }});
    }}"""
        elif entrance == "scale-reveal":
            entrance_js = f"""
    if (!reducedMotion) {{
      sections.forEach((section) => {{
        const content = section.querySelector('.chapter-content');
        if (content) {{
          gsap.from(content, {{
            scale: 0.85, opacity: 0,
            duration: {entrance_duration},
            ease: 'cinematicSmooth',
            scrollTrigger: {{ trigger: section, start: 'top 70%', toggleActions: 'play none none reverse' }}
          }});
        }}
      }});
    }}"""
        else:  # fade-up (default)
            entrance_js = f"""
    if (!reducedMotion) {{
      sections.forEach((section) => {{
        const title = section.querySelector('.chapter-title');
        const body = section.querySelector('.chapter-body');
        if (title) {{
          gsap.from(title, {{
            y: 80, opacity: 0,
            duration: {entrance_duration},
            ease: 'cinematicSilk',
            scrollTrigger: {{ trigger: section, start: 'top 80%', toggleActions: 'play none none reverse' }}
          }});
        }}
        if (body) {{
          gsap.from(body, {{
            y: 40, opacity: 0,
            duration: {body_duration},
            delay: 0.3,
            ease: 'cinematicSmooth',
            scrollTrigger: {{ trigger: section, start: 'top 80%', toggleActions: 'play none none reverse' }}
          }});
        }}
      }});
    }}"""

    # Chapter tracking for uChapter uniform
    chapter_tracking = ""
    if include_threejs:
        chapter_tracking = """
    sections.forEach((section, i) => {
      ScrollTrigger.create({
        trigger: section,
        start: 'top center',
        end: 'bottom center',
        onUpdate: (self) => { currentChapter = i + self.progress; }
      });
    });"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family={safe_font.replace(' ', '+')}:wght@400;700&display=swap" rel="stylesheet" crossorigin="anonymous">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lenis@1.2.3/dist/lenis.css" integrity="sha384-UuB6deGAnAeGSShmQfNVypuoM4D1q+qgqcc3FRyZPVLuPc4psm5o1VShNhqmootN" crossorigin="anonymous">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --sc-hue: {first_ch['hue']}deg;
      --sc-chroma: {first_ch['chroma']};
      --sc-lightness: {first_ch['lightness']};
      --sc-bg: oklch(var(--sc-lightness) var(--sc-chroma) var(--sc-hue));
      --sc-text: {text_color};
      --sc-text-muted: {text_muted};
      --sc-text-heading: {text_heading};
      --sc-accent: {safe_accent if safe_accent else 'oklch(0.75 0.18 160)'};
      --sc-font-display: '{safe_font}', system-ui, sans-serif;
      --sc-font-body: '{safe_font}', system-ui, sans-serif;
      --sc-heading-size: clamp(2.5rem, 5vw, 4.5rem);
      --sc-heading-weight: 700;
      --sc-heading-tracking: -0.02em;
      --sc-heading-leading: 1.1;
      --sc-body-size: clamp(1rem, 1.2vw, 1.25rem);
      --sc-body-leading: 1.7;
      --sc-body-max-width: 42rem;
      --sc-chapter-height: {chapter_height}vh;
      --sc-chapter-padding: clamp(2rem, 5vw, 6rem);
      --sc-entrance-duration: {entrance_duration}s;
      --sc-stagger-delay: {stagger_delay}s;
    }}

    html, body {{
      font-family: var(--sc-font-body);
      font-size: var(--sc-body-size);
      line-height: var(--sc-body-leading);
      color: var(--sc-text);
      background-color: var(--sc-bg);
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}

    html.lenis, html.lenis body {{ height: auto; }}
    .lenis.lenis-smooth {{ scroll-behavior: auto !important; }}

    {'#shader-canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; pointer-events: none; }' if include_threejs else ''}

    .chapter {{
      position: relative;
      min-height: var(--sc-chapter-height);
    }}

    .chapter-content {{
      position: sticky;
      top: 0;
      height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--sc-chapter-padding);
      text-align: center;
    }}

    .chapter-title {{
      font-family: var(--sc-font-display);
      font-size: var(--sc-heading-size);
      font-weight: var(--sc-heading-weight);
      letter-spacing: var(--sc-heading-tracking);
      line-height: var(--sc-heading-leading);
      color: var(--sc-text-heading);
      margin-bottom: 1.5rem;
    }}

    .chapter-body {{
      font-size: var(--sc-body-size);
      line-height: var(--sc-body-leading);
      max-width: var(--sc-body-max-width);
      color: var(--sc-text-muted);
    }}

    @media (max-width: 768px) {{
      :root {{
        --sc-chapter-height: {int(chapter_height * 0.75)}vh;
        --sc-heading-size: clamp(1.8rem, 4vw, 2.5rem);
      }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      :root {{
        --sc-entrance-duration: 0s;
        --sc-stagger-delay: 0s;
      }}
      .chapter-content {{
        opacity: 1 !important;
        transform: none !important;
        clip-path: none !important;
      }}
    }}
  </style>{import_map}
</head>
<body>
  {canvas_html}
  <main>
    {sections_html}
  </main>

  <script defer src="https://cdn.jsdelivr.net/npm/lenis@1.2.3/dist/lenis.min.js" integrity="sha384-Ij66tWIEasctUl2SOYsvptZxi68o/ru5F3Y1fE6RZFoHP3KsEr7aEUbRm5H4k1Oz" crossorigin="anonymous"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/gsap.min.js" integrity="sha384-pEQB1h4Zmn9xhS6jotzltHSIQq6N0Oh3BXkCNOH5LKI81R2NRbb9efarAJYw9gTY" crossorigin="anonymous"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/ScrollTrigger.min.js" integrity="sha384-TgZ1GoXcDnrw/czNfaiSZSFV1zgIRv8aQOevBA8ppS4SkNONmzYfjARpXsDfdnUE" crossorigin="anonymous"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/CustomEase.min.js" integrity="sha384-fQWfiXBcbv8HgKB74Cic5DBJ0P/ZjQkjCcgk00t6l8Yv3rk/DG+9LPi/bbea+HwI" crossorigin="anonymous"></script>

  <script type="module">
    gsap.registerPlugin(ScrollTrigger, CustomEase);

    CustomEase.create('cinematicSilk',   '0.45,0.05,0.55,0.95');
    CustomEase.create('cinematicSmooth', '0.25,0.1,0.25,1');
    CustomEase.create('cinematicFlow',   '0.33,0,0.2,1');
    CustomEase.create('cinematicLinear', '0.4,0,0.6,1');

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    {threejs_setup}

    if (typeof CSS !== 'undefined' && CSS.registerProperty) {{
      try {{
        CSS.registerProperty({{ name: '--sc-hue', syntax: '<angle>', inherits: true, initialValue: '{first_ch["hue"]}deg' }});
        CSS.registerProperty({{ name: '--sc-chroma', syntax: '<number>', inherits: true, initialValue: '{first_ch["chroma"]}' }});
        CSS.registerProperty({{ name: '--sc-lightness', syntax: '<number>', inherits: true, initialValue: '{first_ch["lightness"]}' }});
      }} catch(e) {{}}
    }}

    const lenis = new Lenis({{ autoRaf: false }});

    let scrollProgress = 0;
    let scrollVelocity = 0;
    let currentChapter = 0;
    lenis.on('scroll', ({{ scroll, limit, velocity }}) => {{
      scrollProgress = limit > 0 ? scroll / limit : 0;
      scrollVelocity = velocity;
    }});
    lenis.on('scroll', ScrollTrigger.update);
    {shader_state_init}

    const tickCallback = (time) => {{
      lenis.raf(time * 1000);
      {ticker_shader}
    }};

    {reduced_motion_block}

    function cleanup() {{
      gsap.ticker.remove(tickCallback);
      lenis.destroy();
      ScrollTrigger.killAll();{cleanup_renderer}
    }}
    window.__scCleanup = cleanup;

    const sections = document.querySelectorAll('.chapter');
    const supportsOKLCH = CSS.supports && CSS.supports('color', 'oklch(0.5 0.1 250)');

    {chapter_tracking}

    sections.forEach((section, i) => {{
      if (i === 0) return;
      const hue = section.dataset.hue;
      const chroma = section.dataset.chroma;
      const lightness = section.dataset.lightness;

      if (supportsOKLCH && typeof CSS !== 'undefined' && CSS.registerProperty) {{
        gsap.to(':root', {{
          '--sc-hue': hue + 'deg',
          '--sc-chroma': parseFloat(chroma),
          '--sc-lightness': parseFloat(lightness),
          ease: 'cinematicLinear',
          scrollTrigger: {{ trigger: section, start: 'top center', end: 'top top', scrub: 1 }}
        }});
        {shader_state_tween}
      }} else {{
        const h = hue;
        const s = Math.round(parseFloat(chroma) * 500);
        const l = Math.round(parseFloat(lightness) * 100);
        gsap.to('body', {{
          backgroundColor: 'hsl(' + h + ', ' + s + '%, ' + l + '%)',
          ease: 'cinematicLinear',
          scrollTrigger: {{ trigger: section, start: 'top center', end: 'top top', scrub: 1 }}
        }});
      }}
      {text_contrast_js}
    }});

    {entrance_js}
  </script>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate scroll-cinema HTML")
    parser.add_argument("--mode", choices=["chapter-reveal", "painted-backdrop", "full-cinema", "catalog"],
                        default="full-cinema")
    parser.add_argument("--shader", choices=["painted-dots", "watercolor", "domain-warp"],
                        default="painted-dots")
    parser.add_argument("--chapters", type=int, default=5)
    parser.add_argument("--palette", default="default",
                        help="Named palette: dawn-to-dusk, ocean-descent, or default")
    parser.add_argument("--entrance", choices=["fade-up", "split-text", "scale-reveal", "clip-path-wipe"],
                        default="fade-up")
    parser.add_argument("--pacing", choices=["slow", "medium", "fast"], default="medium")
    parser.add_argument("--color-scheme", choices=["dark", "light"], default="dark")
    parser.add_argument("--font", default="Geist")
    parser.add_argument("--accent", default=None)
    parser.add_argument("--title", default="Scroll Cinema")
    parser.add_argument("--output", "-o", default="output.html")
    args = parser.parse_args()

    chapters = get_chapters(args.chapters, args.palette)

    html = generate_html(args.mode, args.shader, chapters, args.pacing,
                         args.color_scheme, args.font, args.accent, args.title,
                         args.entrance)

    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Generated: {args.output} ({len(html):,} bytes)")
    print(f"  Mode: {args.mode}")
    print(f"  Shader: {args.shader}")
    print(f"  Chapters: {args.chapters}")
    print(f"  Pacing: {args.pacing} ({PACING_MULTIPLIERS[args.pacing]}x)")
    if args.mode in ("chapter-reveal", "full-cinema"):
        print(f"  Entrance: {args.entrance}")


if __name__ == "__main__":
    main()
