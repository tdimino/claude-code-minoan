#!/usr/bin/env python3
"""Generate a self-contained HTML file with a 3D vinyl record showcase.

Features: webcam reflection, procedural groove/scratch textures, scroll-driven
keyframe animation, drag-to-scratch interaction, optional vinyl audio engine.

Based on OMMA's 3D Vinyl with Camera Reflection demo, distilled into the
threejs-particle-canvas skill as Mode 5.

Usage:
    python3 vinyl_showcase_generator.py [options]
    python3 vinyl_showcase_generator.py --label-text "MINOAN MYSTERY" --label-style cool --audio crackle-only
    python3 vinyl_showcase_generator.py --groove-preset deep --scratch-intensity heavy --theme dark
"""

import argparse
import html as html_mod
import json
import sys
import textwrap
from pathlib import Path

LABEL_PALETTES = {
    "warm": {
        "a_gradient": ["#FFD166", "#FF9F43", "#EE5A24", "#D63031", "#6C0F1A", "#2C0510"],
        "b_gradient": ["#FF6B6B", "#EE5A24", "#C0392B", "#96281B", "#641E16", "#1A0505"],
        "a_splash1": "rgba(255, 56, 127, 0.25)",
        "a_splash2": "rgba(72, 126, 255, 0.2)",
        "b_splash1": "rgba(255, 200, 50, 0.22)",
        "b_splash2": "rgba(255, 80, 80, 0.18)",
    },
    "cool": {
        "a_gradient": ["#6C5CE7", "#4834D4", "#2C2C7A", "#1B1464", "#0C0832", "#050318"],
        "b_gradient": ["#0984E3", "#0652DD", "#1B1464", "#0C0832", "#050520", "#020210"],
        "a_splash1": "rgba(0, 255, 221, 0.22)",
        "a_splash2": "rgba(255, 0, 128, 0.18)",
        "b_splash1": "rgba(100, 200, 255, 0.22)",
        "b_splash2": "rgba(0, 255, 180, 0.15)",
    },
    "monochrome": {
        "a_gradient": ["#AAAAAA", "#888888", "#666666", "#444444", "#222222", "#111111"],
        "b_gradient": ["#999999", "#777777", "#555555", "#333333", "#1A1A1A", "#0A0A0A"],
        "a_splash1": "rgba(255, 255, 255, 0.15)",
        "a_splash2": "rgba(200, 200, 200, 0.1)",
        "b_splash1": "rgba(255, 255, 255, 0.12)",
        "b_splash2": "rgba(180, 180, 180, 0.08)",
    },
}

GROOVE_PRESETS = {
    "fine": {"count": 40, "depth": 0.8, "width": 1},
    "standard": {"count": 22, "depth": 1.4, "width": 2},
    "deep": {"count": 15, "depth": 2.0, "width": 3},
}

SCRATCH_PRESETS = {
    "none": {"density": 0, "depth": 0, "length": 0, "opacity": 0},
    "light": {"density": 120, "depth": 1.0, "length": 0.3, "opacity": 0.2},
    "heavy": {"density": 340, "depth": 2.0, "length": 0.5, "opacity": 0.35},
}

DEFAULT_KEYFRAMES = [
    {
        "name": "Hero",
        "posX": -0.9, "posY": -0.6, "posZ": 1.6,
        "offsetX": 1.3, "offsetY": 0.25, "offsetZ": 0,
        "rotX": 0.61, "rotY": -1.46, "rotZ": 0.43,
        "scale": 0.9, "spinSpeed": 0.007,
        "vinylRoughness": 1, "vinylMetalness": 1, "vinylClearcoat": 0.91,
        "envIntensity": 3.5,
        "reflZoom": 6, "feedRoughness": 1, "feedBlur": 0.25, "feedBrightness": 1.75,
        "hdrRotX": 1.2, "hdrRotY": 1.65, "hdrRotZ": 0.28,
    },
    {
        "name": "Detail",
        "posX": 0, "posY": 0, "posZ": 0,
        "offsetX": 0.85, "offsetY": 0.3, "offsetZ": 0,
        "rotX": -2.01, "rotY": -2.5, "rotZ": 0,
        "scale": 0.65, "spinSpeed": 0.004,
        "vinylRoughness": 1, "vinylMetalness": 0.74, "vinylClearcoat": 0.52,
        "envIntensity": 3.5,
        "reflZoom": 4.85, "feedRoughness": 0.31, "feedBlur": 0.03, "feedBrightness": 1.8,
        "hdrRotX": 2.36, "hdrRotY": 1.96, "hdrRotZ": 0.03,
    },
    {
        "name": "Close",
        "posX": -0.4, "posY": 1.2, "posZ": 0,
        "offsetX": -0.05, "offsetY": 0, "offsetZ": 0,
        "rotX": 0.5, "rotY": 0.38, "rotZ": 0.01,
        "scale": 1.25, "spinSpeed": 0.003,
        "vinylRoughness": 1, "vinylMetalness": 1, "vinylClearcoat": 1,
        "envIntensity": 5,
        "reflZoom": 4.45, "feedRoughness": 0.95, "feedBlur": 0.36, "feedBrightness": 1.75,
        "hdrRotX": 2.8, "hdrRotY": 0.27, "hdrRotZ": -0.1,
    },
]


def build_html(args):
    palette = LABEL_PALETTES[args.label_style]
    groove = GROOVE_PRESETS[args.groove_preset]
    scratch = SCRATCH_PRESETS[args.scratch_intensity]
    n_sections = args.sections
    keyframes = DEFAULT_KEYFRAMES[:n_sections]
    if len(keyframes) < n_sections:
        for i in range(len(keyframes), n_sections):
            kf = dict(DEFAULT_KEYFRAMES[i % len(DEFAULT_KEYFRAMES)])
            kf["name"] = f"Section {i+1}"
            keyframes.append(kf)

    bg_color = "#0a0a12" if args.theme == "dark" else "#f5f5f0"
    text_color = "rgba(255,255,255,0.85)" if args.theme == "dark" else "rgba(0,0,0,0.75)"
    dot_color = "rgba(255,255,255,0.3)" if args.theme == "dark" else "rgba(0,0,0,0.2)"
    section_bg = "rgba(0,0,0,0.3)" if args.theme == "dark" else "rgba(255,255,255,0.6)"

    label_text = args.label_text.upper()
    label_text_safe = html_mod.escape(label_text)
    subtitle = args.label_subtitle.upper() if args.label_subtitle else ""

    kf_json = json.dumps([{k: v for k, v in kf.items() if k != "name"} for kf in keyframes])
    section_names_json = json.dumps([kf["name"] for kf in keyframes])
    palette_json = json.dumps(palette)

    include_audio = args.audio != "none"
    include_music = args.audio == "full"
    audio_url_js = json.dumps(args.audio_url) if args.audio_url else "null"

    sections_html = ""
    for i, kf in enumerate(keyframes):
        safe_name = html_mod.escape(kf["name"])
        sections_html += f'''
    <div class="page-section" id="section-{i}">
      <div class="section-content">
        <h2>{safe_name}</h2>
      </div>
    </div>'''

    dots_html = ""
    for i in range(len(keyframes)):
        active = ' class="active"' if i == 0 else ""
        dots_html += f'\n      <div class="section-dot{" active" if i == 0 else ""}" data-section="section-{i}"></div>'

    return textwrap.dedent(f'''\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{label_text_safe} — Vinyl Showcase</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    background: {bg_color};
    color: {text_color};
    font-family: "Inter", "Helvetica Neue", sans-serif;
    overflow-x: hidden;
  }}
  @font-face {{
    font-family: "Inter";
    src: url("https://fonts.gstatic.com/s/inter/v18/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfAZ9hiA.woff2") format("woff2");
    font-display: swap;
  }}
  @font-face {{
    font-family: "Syne";
    src: url("https://fonts.gstatic.com/s/syne/v22/8vIS7w4qzmVxsWxjBZRjr0FKM_04uT6kR47NCV5Z.woff2") format("woff2");
    font-display: swap;
  }}
  #three-canvas {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: auto;
    cursor: grab;
  }}
  .page-section {{
    position: relative;
    min-height: 100vh;
    z-index: 1;
    pointer-events: none;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .section-content {{
    pointer-events: auto;
    background: {section_bg};
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 2rem 3rem;
    max-width: 420px;
    text-align: center;
  }}
  .section-content h2 {{
    font-family: "Syne", sans-serif;
    font-weight: 800;
    font-size: 1.8rem;
    letter-spacing: 0.05em;
  }}
  .section-dots {{
    position: fixed;
    right: 24px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 150;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .section-dot {{
    width: 10px; height: 10px;
    border-radius: 50%;
    background: {dot_color};
    cursor: pointer;
    pointer-events: auto;
    transition: transform 0.3s, background 0.3s;
  }}
  .section-dot.active {{
    background: {text_color};
    transform: scale(1.4);
  }}
  #camera-status {{
    position: fixed;
    bottom: 20px; left: 50%;
    transform: translateX(-50%);
    z-index: 100;
    font-size: 13px;
    color: {text_color};
    opacity: 1;
    transition: opacity 1s;
    pointer-events: none;
  }}
  #camera-preview {{
    position: fixed;
    bottom: 16px; right: 16px;
    width: 120px; height: 90px;
    border-radius: 8px;
    overflow: hidden;
    z-index: 90;
    opacity: 0;
    transition: opacity 0.5s;
    border: 1px solid rgba(255,255,255,0.15);
  }}
  #camera-preview.active {{ opacity: 0.6; }}
  #camera-preview:hover {{ opacity: 1; }}
  #camera-preview video {{ width: 100%; height: 100%; object-fit: cover; }}
  #webgl-fallback {{
    display: none;
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: {bg_color};
    color: {text_color};
    font-size: 1.2rem;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 2rem;
  }}
</style>
</head>
<body>
<div id="webgl-fallback">WebGL is not available in this browser.</div>
<div id="three-canvas"></div>
<div id="camera-status"></div>
<div id="camera-preview">
  <video id="camera-preview-video" autoplay muted playsinline></video>
</div>
<div class="section-dots">{dots_html}
</div>
{sections_html}

<script type="importmap">
{{
  "imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }}
}}
</script>
<script type="module">
import * as THREE from "three";

// ─── CONFIG ──────────────────────────────────────────────
const LABEL_TEXT = {json.dumps(label_text)};
const LABEL_SUBTITLE = {json.dumps(subtitle)};
const PALETTE = {palette_json};
const GROOVE = {json.dumps(groove)};
const SCRATCH = {json.dumps(scratch)};
const KEYFRAMES_DATA = {kf_json};
const SECTION_NAMES = {section_names_json};
const INCLUDE_AUDIO = {json.dumps(include_audio)};
const INCLUDE_MUSIC = {json.dumps(include_music)};
const AUDIO_URL = {audio_url_js};

// ─── SCENE ───────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = new THREE.Color({json.dumps(bg_color)});
const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.1, 1000);
camera.position.set(2.5, 1.5, 4.5);

let renderer;
try {{
  renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false }});
}} catch (e) {{
  document.getElementById("webgl-fallback").style.display = "flex";
  throw e;
}}
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.4;
document.getElementById("three-canvas").appendChild(renderer.domElement);

// ─── LIGHTS ──────────────────────────────────────────────
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);
const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
directionalLight.position.set(5, 8, 5);
scene.add(directionalLight);
const fillLight = new THREE.DirectionalLight(0x889AAB, 0.6);
fillLight.position.set(-5, 3, -5);
scene.add(fillLight);
const rimLight = new THREE.PointLight(0xAAAAFF, 0.8, 20);
rimLight.position.set(0, -3, 3);
scene.add(rimLight);
const topLight = new THREE.PointLight(0xffffff, 0.5, 15);
topLight.position.set(0, 5, 0);
scene.add(topLight);

// ─── CAMERA REFLECTION PIPELINE ──────────────────────────
const video = document.createElement("video");
video.autoplay = true;
video.muted = true;
video.playsInline = true;

const videoTexture = new THREE.VideoTexture(video);
videoTexture.minFilter = THREE.LinearFilter;
videoTexture.magFilter = THREE.LinearFilter;
videoTexture.colorSpace = THREE.SRGBColorSpace;
videoTexture.repeat.y = -1;
videoTexture.offset.y = 1;
videoTexture.wrapS = THREE.RepeatWrapping;
videoTexture.wrapT = THREE.ClampToEdgeWrapping;

const blurCanvas = document.createElement("canvas");
blurCanvas.width = 256;
blurCanvas.height = 256;
const blurCtx = blurCanvas.getContext("2d");
const blurTexture = new THREE.CanvasTexture(blurCanvas);
blurTexture.minFilter = THREE.LinearFilter;
blurTexture.magFilter = THREE.LinearFilter;
blurTexture.colorSpace = THREE.SRGBColorSpace;
blurTexture.wrapS = THREE.RepeatWrapping;
blurTexture.wrapT = THREE.ClampToEdgeWrapping;

let feedBlurAmount = 0.25;
let feedBrightnessVal = 1.75;

const cubeRenderTarget = new THREE.WebGLCubeRenderTarget(128, {{
  generateMipmaps: true,
  minFilter: THREE.LinearMipmapLinearFilter,
  type: THREE.HalfFloatType,
  format: THREE.RGBAFormat,
}});
const pmremGenerator = new THREE.PMREMGenerator(renderer);
pmremGenerator.compileCubemapShader();
let pmremDirty = true;
let lastPmremFrame = -1;

const envSphereGeo = new THREE.SphereGeometry(50, 24, 16);
const envSphereMat = new THREE.MeshBasicMaterial({{
  map: videoTexture,
  side: THREE.BackSide,
  toneMapped: false,
}});
const envSphere = new THREE.Mesh(envSphereGeo, envSphereMat);
envSphere.layers.set(1);
scene.add(envSphere);

const cubeCamera = new THREE.CubeCamera(0.1, 100, cubeRenderTarget);
cubeCamera.layers.enable(1);
scene.add(cubeCamera);
let filteredEnvMap = null;

// ─── KEYFRAMES ───────────────────────────────────────────
const KF_PROPS = [
  "posX","posY","posZ","offsetX","offsetY","offsetZ",
  "rotX","rotY","rotZ","scale","spinSpeed",
  "vinylRoughness","vinylMetalness","vinylClearcoat","envIntensity",
  "reflZoom","feedRoughness","feedBlur","feedBrightness",
  "hdrRotX","hdrRotY","hdrRotZ",
];
const keyframes = KEYFRAMES_DATA;
const settings = {{ ...keyframes[0] }};

// ─── PROCEDURAL TEXTURES ─────────────────────────────────
const MAP_SIZE = 1024;

function generateGrooveNormalMap(count, depth, width) {{
  const c = document.createElement("canvas");
  c.width = MAP_SIZE; c.height = MAP_SIZE;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "rgb(128,128,255)";
  ctx.fillRect(0, 0, MAP_SIZE, MAP_SIZE);
  const cx = MAP_SIZE / 2, cy = MAP_SIZE / 2;
  const innerR = MAP_SIZE * 0.14, outerR = MAP_SIZE * 0.49;
  const intensity = Math.floor(60 * depth);
  for (let i = 0; i < count; i++) {{
    const t = i / count;
    const r = innerR + t * (outerR - innerR);
    ctx.strokeStyle = `rgb(${{128 + intensity}},128,255)`;
    ctx.lineWidth = width;
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = `rgb(${{128 - intensity}},128,255)`;
    ctx.lineWidth = width * 0.6;
    ctx.beginPath(); ctx.arc(cx, cy, r + width * 0.5, 0, Math.PI * 2); ctx.stroke();
  }}
  return new THREE.CanvasTexture(c);
}}

function generateGrooveRoughnessMap(count) {{
  const c = document.createElement("canvas");
  c.width = MAP_SIZE; c.height = MAP_SIZE;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#333";
  ctx.fillRect(0, 0, MAP_SIZE, MAP_SIZE);
  const cx = MAP_SIZE / 2, cy = MAP_SIZE / 2;
  const innerR = MAP_SIZE * 0.14, outerR = MAP_SIZE * 0.49;
  for (let i = 0; i < count; i++) {{
    const r = innerR + (i / count) * (outerR - innerR);
    ctx.strokeStyle = "#666";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
  }}
  return new THREE.CanvasTexture(c);
}}

function generateScratchNormalMap(density, depth, length) {{
  const S = MAP_SIZE;
  const c = document.createElement("canvas");
  c.width = S; c.height = S;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "rgb(128,128,255)";
  ctx.fillRect(0, 0, S, S);
  if (density === 0) return new THREE.CanvasTexture(c);
  const cx = S / 2, cy = S / 2;
  const maxR = S * 0.49, minR = S * 0.14;
  const intensity = Math.floor(40 * depth);

  const arcCount = Math.floor(density * 2.5);
  for (let i = 0; i < arcCount; i++) {{
    const r = minR + Math.random() * (maxR - minR);
    const startAngle = Math.random() * Math.PI * 2;
    const arcLen = (Math.random() * 0.15 + 0.02) * length * 8;
    const v = 128 + (Math.random() > 0.5 ? intensity : -intensity) * (0.5 + Math.random() * 0.5);
    ctx.strokeStyle = `rgb(${{Math.round(v)}},128,255)`;
    ctx.lineWidth = Math.random() * 0.5 + 0.1;
    ctx.globalAlpha = Math.random() * 0.45 + 0.15;
    ctx.beginPath(); ctx.arc(cx, cy, r, startAngle, startAngle + arcLen); ctx.stroke();
  }}

  const hairCount = Math.floor(density * 4);
  for (let i = 0; i < hairCount; i++) {{
    const r = minR + Math.random() * (maxR - minR);
    const startAngle = Math.random() * Math.PI * 2;
    const arcLen = (Math.random() * 0.08 + 0.01) * length * 6;
    const v = 128 + (Math.random() > 0.5 ? 1 : -1) * intensity * (0.2 + Math.random() * 0.3);
    ctx.strokeStyle = `rgb(${{Math.round(v)}},128,255)`;
    ctx.lineWidth = 0.15 + Math.random() * 0.2;
    ctx.globalAlpha = Math.random() * 0.25 + 0.05;
    ctx.beginPath(); ctx.arc(cx, cy, r, startAngle, startAngle + arcLen); ctx.stroke();
  }}

  const nickCount = Math.floor(density * 0.3);
  for (let i = 0; i < nickCount; i++) {{
    const angle = Math.random() * Math.PI * 2;
    const r = minR + Math.random() * (maxR - minR);
    const sx = cx + Math.cos(angle) * r, sy = cy + Math.sin(angle) * r;
    const nickLen = (Math.random() * 0.2 + 0.05) * length * S * 0.08;
    const nickAngle = angle + (Math.random() - 0.5) * 0.6;
    const v = 128 + (Math.random() > 0.5 ? intensity * 0.6 : -intensity * 0.6);
    ctx.strokeStyle = `rgb(${{Math.round(v)}},128,255)`;
    ctx.lineWidth = Math.random() * 0.35 + 0.1;
    ctx.globalAlpha = Math.random() * 0.3 + 0.1;
    ctx.beginPath(); ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(nickAngle) * nickLen, sy + Math.sin(nickAngle) * nickLen);
    ctx.stroke();
  }}
  ctx.globalAlpha = 1;
  return new THREE.CanvasTexture(c);
}}

function generateScratchRoughnessMap(density, length) {{
  const S = MAP_SIZE;
  const c = document.createElement("canvas");
  c.width = S; c.height = S;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, S, S);
  if (density === 0) return new THREE.CanvasTexture(c);
  const cx = S / 2, cy = S / 2;
  const maxR = S * 0.49, minR = S * 0.14;

  const arcCount = Math.floor(density * 2.5);
  for (let i = 0; i < arcCount; i++) {{
    const r = minR + Math.random() * (maxR - minR);
    const sa = Math.random() * Math.PI * 2;
    const al = (Math.random() * 0.15 + 0.02) * length * 8;
    ctx.strokeStyle = `rgba(255,255,255,${{Math.random() * 0.15 + 0.02}})`;
    ctx.lineWidth = Math.random() * 0.5 + 0.1;
    ctx.beginPath(); ctx.arc(cx, cy, r, sa, sa + al); ctx.stroke();
  }}

  const hairCount = Math.floor(density * 4);
  for (let i = 0; i < hairCount; i++) {{
    const r = minR + Math.random() * (maxR - minR);
    const sa = Math.random() * Math.PI * 2;
    const al = (Math.random() * 0.08 + 0.01) * length * 6;
    ctx.strokeStyle = `rgba(255,255,255,${{Math.random() * 0.08 + 0.01}})`;
    ctx.lineWidth = 0.15 + Math.random() * 0.2;
    ctx.beginPath(); ctx.arc(cx, cy, r, sa, sa + al); ctx.stroke();
  }}

  const nickCount = Math.floor(density * 0.3);
  for (let i = 0; i < nickCount; i++) {{
    const angle = Math.random() * Math.PI * 2;
    const r = minR + Math.random() * (maxR - minR);
    const sx = cx + Math.cos(angle) * r, sy = cy + Math.sin(angle) * r;
    const nl = (Math.random() * 0.2 + 0.05) * length * S * 0.08;
    const na = angle + (Math.random() - 0.5) * 0.6;
    ctx.strokeStyle = `rgba(255,255,255,${{Math.random() * 0.1 + 0.02}})`;
    ctx.lineWidth = Math.random() * 0.35 + 0.1;
    ctx.beginPath(); ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(na) * nl, sy + Math.sin(na) * nl);
    ctx.stroke();
  }}
  return new THREE.CanvasTexture(c);
}}

// ─── VINYL GEOMETRY & MATERIALS ──────────────────────────
const vinylGroup = new THREE.Group();
scene.add(vinylGroup);

let grooveNormalTex = generateGrooveNormalMap(GROOVE.count, GROOVE.depth, GROOVE.width);
let grooveRoughTex = generateGrooveRoughnessMap(GROOVE.count);
let scratchNormalTex = generateScratchNormalMap(SCRATCH.density, SCRATCH.depth, SCRATCH.length);
let scratchRoughTex = generateScratchRoughnessMap(SCRATCH.density, SCRATCH.length);

const discGeo = new THREE.CylinderGeometry(2, 2, 0.012, 128);
const discMat = new THREE.MeshPhysicalMaterial({{
  color: 0x080808,
  metalness: 1,
  roughness: 1,
  envMapIntensity: 3.5,
  clearcoat: 0.91,
  clearcoatRoughness: 1,
  reflectivity: 1,
  ior: 1.8,
  specularIntensity: 1,
  specularColor: new THREE.Color(0xffffff),
  normalMap: grooveNormalTex,
  normalScale: new THREE.Vector2(0.8, 0.8),
  roughnessMap: grooveRoughTex,
  side: THREE.DoubleSide,
}});
const disc = new THREE.Mesh(discGeo, discMat);

const scratchDiscGeo = new THREE.CylinderGeometry(2, 2, 0.013, 64);
const scratchMat = new THREE.MeshPhysicalMaterial({{
  color: 0x080808,
  metalness: 0.9,
  roughness: 0.1,
  envMapIntensity: 3.5,
  clearcoat: 0.5,
  clearcoatRoughness: 0.05,
  normalMap: scratchNormalTex,
  normalScale: new THREE.Vector2(2, 2),
  roughnessMap: scratchRoughTex,
  transparent: true,
  opacity: SCRATCH.opacity,
  depthWrite: false,
  side: THREE.DoubleSide,
}});
const scratchDisc = new THREE.Mesh(scratchDiscGeo, scratchMat);

// ─── LABEL ART ───────────────────────────────────────────
function seededRandom(seed) {{
  let s = seed;
  return () => {{ s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }};
}}

function drawSpindleHole(ctx, cx, cy) {{
  const holeR = 55;
  const ringGrad = ctx.createRadialGradient(cx, cy, holeR - 8, cx, cy, holeR + 22);
  ringGrad.addColorStop(0, "rgba(200,200,205,0.95)");
  ringGrad.addColorStop(0.3, "rgba(230,230,235,0.9)");
  ringGrad.addColorStop(0.6, "rgba(170,170,178,0.85)");
  ringGrad.addColorStop(1, "rgba(130,130,140,0)");
  ctx.fillStyle = ringGrad;
  ctx.beginPath(); ctx.arc(cx, cy, holeR + 22, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = "#0a0a0a";
  ctx.beginPath(); ctx.arc(cx, cy, holeR - 6, 0, Math.PI * 2); ctx.fill();
}}

function drawEdgeWear(ctx, cx, cy, R, rand) {{
  ctx.globalCompositeOperation = "destination-out";
  for (let i = 0; i < 250; i++) {{
    const angle = rand() * Math.PI * 2;
    const dist = R - 40 + rand() * 50;
    const px = cx + Math.cos(angle) * dist, py = cy + Math.sin(angle) * dist;
    const size = rand() * 14 + 2;
    ctx.fillStyle = `rgba(0,0,0,${{rand() * 0.6 + 0.3}})`;
    ctx.beginPath(); ctx.ellipse(px, py, size, size * (0.3 + rand() * 0.7), angle, 0, Math.PI * 2); ctx.fill();
  }}
  ctx.globalCompositeOperation = "source-over";
}}

function drawArcText(ctx, cx, cy, text, radius, startDeg, spacing, fontSize, color, isBottom) {{
  ctx.fillStyle = color;
  ctx.font = `600 ${{fontSize}}px "Inter", sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.save();
  ctx.translate(cx, cy);
  if (isBottom) {{
    const bStart = startDeg * Math.PI / 180 + text.length * spacing / 2;
    for (let i = 0; i < text.length; i++) {{
      const a = bStart - i * spacing;
      ctx.save(); ctx.rotate(a); ctx.translate(0, radius); ctx.rotate(Math.PI);
      ctx.fillText(text[i], 0, 0); ctx.restore();
    }}
  }} else {{
    const sAngle = startDeg * Math.PI / 180 - text.length * spacing / 2;
    for (let i = 0; i < text.length; i++) {{
      const a = sAngle + i * spacing;
      ctx.save(); ctx.rotate(a); ctx.translate(0, -radius);
      ctx.fillText(text[i], 0, 0); ctx.restore();
    }}
  }}
  ctx.restore();
}}

function createLabelTexture(side, palette, labelText, subtitle) {{
  const c = document.createElement("canvas");
  c.width = 2048; c.height = 2048;
  const ctx = c.getContext("2d");
  const cx = 1024, cy = 1024;
  const grad = side === "a" ? palette.a_gradient : palette.b_gradient;
  const rand = seededRandom(side === "a" ? 42 : 137);
  const R = 1020;

  const baseGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
  const stops = [0, 0.2, 0.45, 0.7, 0.9, 1];
  grad.forEach((color, i) => baseGrad.addColorStop(stops[i], color));
  ctx.fillStyle = baseGrad;
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();

  const splash1 = side === "a" ? palette.a_splash1 : palette.b_splash1;
  const splash2 = side === "a" ? palette.a_splash2 : palette.b_splash2;
  const sg1 = ctx.createRadialGradient(cx - 350, cy - 300, 20, cx - 350, cy - 300, 500);
  sg1.addColorStop(0, splash1); sg1.addColorStop(1, splash1.replace(/[\\d.]+\\)$/, "0)"));
  ctx.fillStyle = sg1;
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();
  const sg2 = ctx.createRadialGradient(cx + 350, cy + 300, 30, cx + 350, cy + 300, 450);
  sg2.addColorStop(0, splash2); sg2.addColorStop(1, splash2.replace(/[\\d.]+\\)$/, "0)"));
  ctx.fillStyle = sg2;
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();

  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
  for (let i = 0; i < 12000; i++) {{
    const angle = rand() * Math.PI * 2;
    const r = rand() * R;
    const px = cx + Math.cos(angle) * r, py = cy + Math.sin(angle) * r;
    const alpha = rand() * 0.05 + 0.01;
    ctx.fillStyle = rand() > 0.5 ? `rgba(255,255,255,${{alpha}})` : `rgba(0,0,0,${{alpha * 0.8}})`;
    ctx.fillRect(px, py, rand() * 2 + 0.3, rand() * 0.8 + 0.2);
  }}
  ctx.restore();

  [960, 945, 930].forEach((r, i) => {{
    ctx.strokeStyle = `rgba(0,0,0,${{[0.55, 0.3, 0.12][i]}})`;
    ctx.lineWidth = [3, 1.2, 0.6][i];
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
  }});
  [140, 165].forEach((r, i) => {{
    ctx.strokeStyle = `rgba(0,0,0,${{[0.4, 0.18][i]}})`;
    ctx.lineWidth = [2, 1][i];
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
  }});

  for (let i = 0; i < 72; i++) {{
    const angle = i / 72 * Math.PI * 2;
    const isMajor = i % 6 === 0;
    ctx.strokeStyle = `rgba(0,0,0,${{isMajor ? 0.4 : 0.1}})`;
    ctx.lineWidth = isMajor ? 1.5 : 0.6;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(angle) * (isMajor ? 870 : 895), cy + Math.sin(angle) * (isMajor ? 870 : 895));
    ctx.lineTo(cx + Math.cos(angle) * 925, cy + Math.sin(angle) * 925);
    ctx.stroke();
  }}

  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
  const waveY = cy + 260;
  const waveSeed = seededRandom(side === "a" ? 77 : 201);
  for (let i = 0; i < 60; i++) {{
    const x = cx - 720 + i * 24;
    const t = i / 60;
    const envelope = Math.sin(t * Math.PI);
    const h = 30 + waveSeed() * 180 * envelope + 37 * Math.sin(t * Math.PI * 3);
    ctx.fillStyle = `rgba(0,0,0,${{0.55 + envelope * 0.3}})`;
    ctx.fillRect(x, waveY - h / 2, 16, h);
  }}
  for (let i = 0; i < 32; i++) {{
    const angle = i / 32 * Math.PI * 2;
    const isMajor = i % 4 === 0;
    ctx.strokeStyle = `rgba(0,0,0,${{isMajor ? 0.2 : 0.06}})`;
    ctx.lineWidth = isMajor ? 1.8 : 0.7;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(angle) * 200, cy + Math.sin(angle) * 200);
    ctx.lineTo(cx + Math.cos(angle) * (isMajor ? 900 : 700), cy + Math.sin(angle) * (isMajor ? 900 : 700));
    ctx.stroke();
  }}
  ctx.restore();

  ctx.fillStyle = "#000";
  ctx.font = '900 225px "Syne", "Inter", sans-serif';
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(labelText, cx, cy - 110);

  if (subtitle) {{
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.font = '500 28px "Inter", sans-serif';
    const spaced = subtitle.split("").join("  ");
    ctx.fillText(spaced, cx, cy - 5);
  }}

  ctx.fillStyle = "rgba(0,0,0,0.4)";
  ctx.font = '600 17px "Inter", sans-serif';
  ctx.fillText(`${{labelText.slice(0, 3)}} — 001  ·  ${{side === "a" ? "FIRST PRESSING" : "OBVERSE"}}`, cx, cy + 45);

  ctx.fillStyle = "rgba(0,0,0,0.8)";
  ctx.font = '800 22px "Syne", sans-serif';
  ctx.fillText(side === "a" ? "SIDE A" : "SIDE B", cx, cy + 370);

  ctx.fillStyle = "rgba(0,0,0,0.25)";
  ctx.font = '400 14px "Inter", sans-serif';
  ctx.fillText(`℗ ${{new Date().getFullYear()}} ${{labelText}} · ALL RIGHTS RESERVED`, cx, cy + 480);

  ctx.fillStyle = "rgba(0,0,0,0.35)";
  ctx.font = '700 16px "Inter", sans-serif';
  ctx.save(); ctx.translate(cx + 620, cy); ctx.rotate(Math.PI / 2);
  ctx.fillText("33⅓ RPM", 0, 0); ctx.restore();
  ctx.save(); ctx.translate(cx - 620, cy); ctx.rotate(-Math.PI / 2);
  ctx.fillText("STEREO", 0, 0); ctx.restore();

  drawArcText(ctx, cx, cy, side === "a" ? "ECHOES  IN  WAX" : "VOID  SPECTRUM", 820, -90, 0.055, 16, "rgba(0,0,0,0.3)", false);
  drawArcText(ctx, cx, cy, side === "a" ? "SIGNAL · FORM · RESONANCE" : "WAVEFORM · DECAY · STATIC", 820, 90, 0.042, 13, "rgba(0,0,0,0.2)", true);
  drawSpindleHole(ctx, cx, cy);
  drawEdgeWear(ctx, cx, cy, R, rand);

  return new THREE.CanvasTexture(c);
}}

function createLabelNormalMap() {{
  const size = 1024;
  const c = document.createElement("canvas");
  c.width = size; c.height = size;
  const ctx = c.getContext("2d");
  const cx = size / 2, cy = size / 2;
  const rand = seededRandom(99);
  ctx.fillStyle = "rgb(128,128,255)";
  ctx.fillRect(0, 0, size, size);
  const imageData = ctx.getImageData(0, 0, size, size);
  const data = imageData.data;
  for (let i = 0; i < data.length; i += 4) {{
    const px = (i / 4) % size, py = Math.floor(i / 4 / size);
    const dist = Math.sqrt((px - cx) ** 2 + (py - cy) ** 2);
    if (dist > size / 2) continue;
    data[i] = 128 + (rand() - 0.5) * 12;
    data[i + 1] = 128 + (rand() - 0.5) * 12;
  }}
  ctx.putImageData(imageData, 0, 0);
  for (let i = 0; i < 8; i++) {{
    const angle = rand() * Math.PI * 2;
    const r = rand() * (size * 0.35);
    const sx = cx + Math.cos(angle) * r, sy = cy + Math.sin(angle) * r;
    const len = 40 + rand() * 150;
    const dir = rand() * Math.PI * 2;
    const wave = (rand() - 0.5) * 30;
    ctx.strokeStyle = `rgb(${{128 + Math.round(wave)}},128,255)`;
    ctx.lineWidth = rand() * 1.5 + 0.5;
    ctx.globalAlpha = 0.3 + rand() * 0.3;
    ctx.beginPath(); ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(dir) * len, sy + Math.sin(dir) * len); ctx.stroke();
  }}
  ctx.globalAlpha = 1;
  return new THREE.CanvasTexture(c);
}}

const labelGeo = new THREE.CircleGeometry(0.5, 64);
const labelNormTex = createLabelNormalMap();
const parsedPalette = PALETTE;

const aSideTexture = createLabelTexture("a", parsedPalette, LABEL_TEXT, LABEL_SUBTITLE);
const bSideTexture = createLabelTexture("b", parsedPalette, LABEL_TEXT, LABEL_SUBTITLE);

const labelMat = new THREE.MeshPhysicalMaterial({{
  map: aSideTexture,
  normalMap: labelNormTex,
  normalScale: new THREE.Vector2(0.15, 0.15),
  metalness: 0, roughness: 0.5, envMapIntensity: 0.4,
  clearcoat: 0.1, clearcoatRoughness: 0.4,
  iridescence: 0.35, iridescenceIOR: 1.8,
  iridescenceThicknessRange: [100, 400],
  specularIntensity: 0.3, specularColor: new THREE.Color(0xFFE4DD),
  polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
}});
const label = new THREE.Mesh(labelGeo, labelMat);
label.rotation.x = -Math.PI / 2;
label.position.y = 0.0065;

const bSideLabelMat = new THREE.MeshPhysicalMaterial({{
  map: bSideTexture,
  normalMap: labelNormTex,
  normalScale: new THREE.Vector2(0.15, 0.15),
  metalness: 0, roughness: 0.55, envMapIntensity: 0.4,
  clearcoat: 0.1, clearcoatRoughness: 0.4,
  iridescence: 0.4, iridescenceIOR: 1.9,
  iridescenceThicknessRange: [100, 500],
  specularIntensity: 0.3, specularColor: new THREE.Color(0xCCCCFF),
  polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
}});
const bSideLabel = new THREE.Mesh(new THREE.CircleGeometry(0.5, 64), bSideLabelMat);
bSideLabel.rotation.x = Math.PI / 2;
bSideLabel.position.y = -0.0065;

const holeGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.02, 16);
const hole = new THREE.Mesh(holeGeo, new THREE.MeshStandardMaterial({{ color: 0 }}));

const spinPivot = new THREE.Group();
spinPivot.add(disc, scratchDisc, label, bSideLabel, hole);
vinylGroup.add(spinPivot);
vinylGroup.scale.setScalar(settings.scale);
vinylGroup.rotation.set(settings.rotX, 0, settings.rotZ);
vinylGroup.position.set(settings.posX + settings.offsetX, settings.posY + settings.offsetY, settings.posZ + settings.offsetZ);
spinPivot.rotation.y = settings.rotY;

const reflectiveMaterials = [discMat, labelMat, bSideLabelMat, scratchMat];

// ─── SCROLL KEYFRAME SYSTEM ─────────────────────────────
function getScrollProgress() {{
  const docH = document.documentElement.scrollHeight - innerHeight;
  return docH <= 0 ? 0 : (scrollY / docH) * (keyframes.length - 1);
}}

function lerp(a, b, t) {{ return a + (b - a) * t; }}

function applyScrollKeyframe(progress) {{
  const idx = Math.floor(progress);
  const t = progress - idx;
  const kfA = keyframes[Math.min(idx, keyframes.length - 1)];
  const kfB = keyframes[Math.min(idx + 1, keyframes.length - 1)];
  const ease = t * t * (3 - 2 * t);
  for (const k of KF_PROPS) settings[k] = lerp(kfA[k], kfB[k], ease);

  discMat.roughness = settings.vinylRoughness;
  discMat.metalness = settings.vinylMetalness;
  discMat.clearcoat = settings.vinylClearcoat;
  discMat.clearcoatRoughness = settings.feedRoughness;
  vinylGroup.scale.setScalar(settings.scale);
  feedBlurAmount = settings.feedBlur;
  feedBrightnessVal = settings.feedBrightness;
  reflectiveMaterials.forEach(m => m.envMapIntensity = settings.envIntensity);

  const z = settings.reflZoom;
  videoTexture.repeat.set(z, -z);
  videoTexture.offset.set(-(z - 1) / 2, 1 + (z - 1) / 2);
  blurTexture.repeat.set(z, -z);
  blurTexture.offset.set(-(z - 1) / 2, 1 + (z - 1) / 2);
  scratchMat.opacity = SCRATCH.opacity;
  scratchMat.normalScale.set(2, 2);
}}

const dots = document.querySelectorAll(".section-dot");
dots.forEach(d => d.addEventListener("click", () =>
  document.getElementById(d.dataset.section).scrollIntoView({{ behavior: "smooth" }})));

function updateActiveDot(progress) {{
  const idx = Math.round(progress);
  dots.forEach((d, i) => d.classList.toggle("active", i === idx));
}}

// ─── DRAG-TO-SCRATCH INTERACTION ─────────────────────────
let mouseX = 0, mouseY = 0, targetMouseX = 0, targetMouseY = 0;
let orbitTiltX = 0, orbitTiltZ = 0;
const ORBIT_STRENGTH = 0.15, ORBIT_LERP = 0.03;

addEventListener("mousemove", e => {{
  targetMouseX = (e.clientX / innerWidth - 0.5) * 2;
  targetMouseY = (e.clientY / innerHeight - 0.5) * 2;
}});

const raycaster = new THREE.Raycaster();
const pointerNDC = new THREE.Vector2();
let isDragging = false, dragPrevAngle = 0;
let scratchVelocity = 0, scratchOffset = 0, isScratchActive = false;
const SCRATCH_SENSITIVITY = 2, SCRATCH_FRICTION = 0.92;
let currentSpinY = 0;

let dragFrozenRotX = 0, dragFrozenRotZ = 0, dragFrozenPosX = 0;
let dragFrozenPosY = 0, dragFrozenPosZ = 0, dragFrozenScale = 1;
let dragBaseSpinY = 0, dragFrozenLookAtX = 0, dragFrozenLookAtY = 0, dragFrozenLookAtZ = 0;

function getVinylScreenCenter() {{
  const wp = new THREE.Vector3();
  vinylGroup.getWorldPosition(wp);
  const p = wp.clone().project(camera);
  const rect = renderer.domElement.getBoundingClientRect();
  return {{ x: (p.x * 0.5 + 0.5) * rect.width + rect.left, y: (-p.y * 0.5 + 0.5) * rect.height + rect.top }};
}}

function hitTestVinyl(e) {{
  const rect = renderer.domElement.getBoundingClientRect();
  pointerNDC.set((e.clientX - rect.left) / rect.width * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
  raycaster.setFromCamera(pointerNDC, camera);
  return raycaster.intersectObjects([disc, label, bSideLabel, scratchDisc], false).length > 0;
}}

function getScreenAngle(e) {{
  const c = getVinylScreenCenter();
  return Math.atan2(e.clientY - c.y, e.clientX - c.x);
}}

renderer.domElement.addEventListener("pointerdown", e => {{
  if (!hitTestVinyl(e)) return;
  isDragging = true; isScratchActive = true;
  dragPrevAngle = getScreenAngle(e);
  currentSpinY += scratchOffset; scratchOffset = 0; scratchVelocity = 0;
  dragFrozenRotX = vinylGroup.rotation.x; dragFrozenRotZ = vinylGroup.rotation.z;
  dragFrozenPosX = vinylGroup.position.x; dragFrozenPosY = vinylGroup.position.y;
  dragFrozenPosZ = vinylGroup.position.z; dragFrozenScale = settings.scale;
  dragBaseSpinY = spinPivot.rotation.y;
  dragFrozenLookAtX = settings.posX; dragFrozenLookAtY = settings.posY; dragFrozenLookAtZ = settings.posZ;
  renderer.domElement.setPointerCapture(e.pointerId);
  renderer.domElement.style.cursor = "grabbing";
  e.preventDefault();
}});

renderer.domElement.addEventListener("pointermove", e => {{
  if (!isDragging) {{ renderer.domElement.style.cursor = hitTestVinyl(e) ? "grab" : "default"; return; }}
  const angle = getScreenAngle(e);
  let delta = angle - dragPrevAngle;
  if (delta > Math.PI) delta -= Math.PI * 2;
  if (delta < -Math.PI) delta += Math.PI * 2;
  scratchVelocity = -delta * SCRATCH_SENSITIVITY;
  scratchOffset += scratchVelocity;
  dragPrevAngle = angle;
}});

renderer.domElement.addEventListener("pointerup", e => {{
  if (!isDragging) return;
  isDragging = false;
  currentSpinY = dragBaseSpinY + scratchOffset - settings.rotY;
  renderer.domElement.releasePointerCapture(e.pointerId);
  renderer.domElement.style.cursor = "grab";
}});
renderer.domElement.addEventListener("pointercancel", e => {{
  if (!isDragging) return;
  isDragging = false; isScratchActive = false; scratchVelocity = 0;
  currentSpinY = dragBaseSpinY + scratchOffset - settings.rotY;
  scratchOffset = 0;
  renderer.domElement.releasePointerCapture(e.pointerId);
  renderer.domElement.style.cursor = "grab";
}});

// ─── TOUCH HANDLERS ──────────────────────────────────────
renderer.domElement.addEventListener("touchstart", e => {{ e.preventDefault(); }}, {{ passive: false }});
renderer.domElement.addEventListener("touchmove", e => {{ e.preventDefault(); }}, {{ passive: false }});
renderer.domElement.addEventListener("touchend", e => {{ e.preventDefault(); }}, {{ passive: false }});

// ─── AUDIO ENGINE (OPTIONAL) ─────────────────────────────
{"" if not include_audio else '''
let audioCtx = null, musicGain = null, masterGain = null, musicLPF = null;
let scratchMidEQ = null, crackleGain = null, crackleSource = null;
let needleGain = null, needleSource = null;
let musicBuffer = null, activeSource = null, musicReady = false, audioInitialized = false;
let virtualPlayhead = 0, lastSourceStartTime = 0, lastSourceOffset = 0, lastSourceRate = 1;
let sourceIsPlaying = false, prevSpinY = 0, smoothedRate = 1;
let smoothedLPFFreq = 22000, smoothedLPFQ = 0.707, smoothedMidGain = 0;
let wowPhase = 0, flutterPhase = 0, currentDirection = 1, reversedBuffer = null;
let framesSinceRestart = 0;

function createNoiseBuffer(ctx, dur, type) {
  const sr = ctx.sampleRate, len = Math.floor(sr * dur);
  const buf = ctx.createBuffer(1, len, sr);
  const data = buf.getChannelData(0);
  if (type === "crackle") {
    for (let i = 0; i < len; i++) {
      const r = Math.random();
      if (r > 0.997) {
        const amp = 0.3 + Math.random() * 0.7;
        const cl = Math.floor(sr * (0.0002 + Math.random() * 0.001));
        for (let j = 0; j < cl && i + j < len; j++) data[i + j] = (Math.random() * 2 - 1) * amp * (1 - j / cl);
        i += Math.floor(sr * 0.002);
      } else if (r > 0.993) { data[i] = (Math.random() * 2 - 1) * 0.15; }
      else { data[i] = (Math.random() * 2 - 1) * 0.008; }
    }
  } else {
    let b0=0,b1=0,b2=0,b3=0,b4=0,b5=0,b6=0;
    for (let i = 0; i < len; i++) {
      const w = Math.random() * 2 - 1;
      b0=0.99886*b0+w*0.0555179; b1=0.99332*b1+w*0.0750759; b2=0.969*b2+w*0.153852;
      b3=0.8665*b3+w*0.3104856; b4=0.55*b4+w*0.5329522; b5=-0.7616*b5-w*0.016898;
      data[i] = (b0+b1+b2+b3+b4+b5+b6+w*0.5362)*0.06; b6=w*0.115926;
    }
  }
  return buf;
}

function getReversedBuffer() {
  if (reversedBuffer) return reversedBuffer;
  if (!musicBuffer) return null;
  const nCh = musicBuffer.numberOfChannels, len = musicBuffer.length;
  reversedBuffer = audioCtx.createBuffer(nCh, len, musicBuffer.sampleRate);
  for (let ch = 0; ch < nCh; ch++) {
    const src = musicBuffer.getChannelData(ch), dst = reversedBuffer.getChannelData(ch);
    for (let i = 0; i < len; i++) dst[i] = src[len - 1 - i];
  }
  return reversedBuffer;
}

function startMusicSource(offset, rate) {
  if (!audioCtx || !musicBuffer) return;
  if (activeSource) { try { activeSource.stop(); } catch(e) {} activeSource.disconnect(); activeSource = null; }
  const dur = musicBuffer.duration;
  const isRev = rate < 0, absRate = Math.max(Math.abs(rate), 0.001);
  let useBuf, safeOff;
  if (isRev) { useBuf = getReversedBuffer(); if (!useBuf) return; safeOff = ((dur - ((offset%dur+dur)%dur))%dur+dur)%dur; currentDirection = -1; }
  else { useBuf = musicBuffer; safeOff = (offset%dur+dur)%dur; currentDirection = 1; }
  const src = audioCtx.createBufferSource();
  src.buffer = useBuf; src.loop = true; src.loopStart = 0; src.loopEnd = dur;
  src.playbackRate.value = absRate; src.connect(scratchMidEQ); src.start(0, safeOff);
  activeSource = src; sourceIsPlaying = true;
  lastSourceStartTime = audioCtx.currentTime; lastSourceOffset = safeOff; lastSourceRate = absRate;
}

function getPlayhead() {
  if (!activeSource || !sourceIsPlaying || !musicBuffer) return virtualPlayhead;
  const elapsed = audioCtx.currentTime - lastSourceStartTime, dur = musicBuffer.duration;
  const rawPos = ((lastSourceOffset + elapsed * lastSourceRate) % dur + dur) % dur;
  return currentDirection === -1 ? ((dur - rawPos) % dur + dur) % dur : rawPos;
}

function initAudio() {
  if (audioCtx) return;
  try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch(e) { return; }
  masterGain = audioCtx.createGain(); masterGain.gain.value = 1; masterGain.connect(audioCtx.destination);
  scratchMidEQ = audioCtx.createBiquadFilter(); scratchMidEQ.type = "peaking";
  scratchMidEQ.frequency.value = 1800; scratchMidEQ.Q.value = 1.5; scratchMidEQ.gain.value = 0;
  musicLPF = audioCtx.createBiquadFilter(); musicLPF.type = "lowpass";
  musicLPF.frequency.value = 22000; musicLPF.Q.value = 0.707;
  musicGain = audioCtx.createGain(); musicGain.gain.value = 0.5;
  scratchMidEQ.connect(musicLPF); musicLPF.connect(musicGain); musicGain.connect(masterGain);

  const crackleBuf = createNoiseBuffer(audioCtx, 4, "crackle");
  crackleSource = audioCtx.createBufferSource(); crackleSource.buffer = crackleBuf; crackleSource.loop = true;
  const crackleFilter = audioCtx.createBiquadFilter(); crackleFilter.type = "bandpass";
  crackleFilter.frequency.value = 3000; crackleFilter.Q.value = 0.8;
  crackleGain = audioCtx.createGain(); crackleGain.gain.value = 0.02;
  crackleSource.connect(crackleFilter); crackleFilter.connect(crackleGain); crackleGain.connect(masterGain);
  crackleSource.start(0);

  const needleBuf = createNoiseBuffer(audioCtx, 3, "hiss");
  needleSource = audioCtx.createBufferSource(); needleSource.buffer = needleBuf; needleSource.loop = true;
  const needleFilter = audioCtx.createBiquadFilter(); needleFilter.type = "highpass";
  needleFilter.frequency.value = 4000; needleFilter.Q.value = 0.5;
  needleGain = audioCtx.createGain(); needleGain.gain.value = 0.025;
  needleSource.connect(needleFilter); needleFilter.connect(needleGain); needleGain.connect(masterGain);
  needleSource.start(0);
''' + ('''
  if (AUDIO_URL) {
    fetch(AUDIO_URL).then(r => r.arrayBuffer()).then(ab => audioCtx.decodeAudioData(ab)).then(decoded => {
      musicBuffer = decoded; musicReady = true; virtualPlayhead = 0; startMusicSource(0, 1);
    }).catch(e => console.warn("Music decode error:", e));
  }
''' if include_music else '') + '''
}

function ensureAudio() { if (!audioInitialized) { audioInitialized = true; initAudio(); } }
function autoPlayOnInteraction() { ensureAudio(); if (audioCtx && audioCtx.state === "suspended") audioCtx.resume(); }
addEventListener("pointerdown", autoPlayOnInteraction, { once: true });
addEventListener("keydown", autoPlayOnInteraction, { once: true });
addEventListener("scroll", autoPlayOnInteraction, { once: true, passive: true });

function updatePlatterAudio() {
  if (!audioCtx) return;
  const dt = 1/60; framesSinceRestart++;
  const fxActive = isDragging || isScratchActive;
  const currentSpinRot = spinPivot.rotation.y;
  let deltaRad = currentSpinRot - prevSpinY; prevSpinY = currentSpinRot;
  if (deltaRad > Math.PI) deltaRad -= Math.PI * 2;
  if (deltaRad < -Math.PI) deltaRad += Math.PI * 2;
  const BASE_RAD = (33.333/60) * Math.PI * 2 / 60;

  if (fxActive) {
    const perFrame = settings.spinSpeed || BASE_RAD;
    let targetRate = perFrame > 1e-5 ? deltaRad / perFrame : (Math.abs(deltaRad) > 3e-4 ? deltaRad / BASE_RAD : 0);
    targetRate = Math.max(-4, Math.min(targetRate, 4));
    const inertia = isDragging ? 0.22 : (Math.abs(targetRate) < Math.abs(smoothedRate) ? 0.035 : 0.07);
    smoothedRate += (targetRate - smoothedRate) * inertia;

    wowPhase += 0.4 * dt * Math.PI * 2; flutterPhase += 6.5 * dt * Math.PI * 2;
    const wowMod = 1 + Math.sin(wowPhase)*0.0015*Math.min(Math.abs(smoothedRate),1) + Math.sin(flutterPhase)*0.0004*Math.min(Math.abs(smoothedRate),1);
    const finalRate = smoothedRate * wowMod;

    if (activeSource && sourceIsPlaying) {
      const absNew = Math.max(Math.abs(finalRate), 0.001);
      const newDir = finalRate < -0.005 ? -1 : finalRate > 0.005 ? 1 : currentDirection;
      if (newDir !== currentDirection || (Math.abs(absNew - lastSourceRate) > 0.04 && framesSinceRestart > 3)) {
        virtualPlayhead = getPlayhead(); startMusicSource(virtualPlayhead, newDir * absNew); framesSinceRestart = 0;
      } else { activeSource.playbackRate.setTargetAtTime(absNew, audioCtx.currentTime, 0.03); lastSourceRate = absNew; }
    }

    const absRate = Math.abs(smoothedRate);
    const lpfRatio = Math.min(absRate, 1);
    smoothedLPFFreq += (180 * Math.pow(22000/180, lpfRatio) - smoothedLPFFreq) * 0.06;
    smoothedLPFQ += ((isDragging ? 2.5 : 0.707) - smoothedLPFQ) * 0.08;
    smoothedMidGain += ((isDragging && absRate > 0.05 ? 6 : 0) - smoothedMidGain) * 0.1;
    if (musicLPF) { musicLPF.frequency.setTargetAtTime(smoothedLPFFreq, audioCtx.currentTime, 0.02); musicLPF.Q.setTargetAtTime(smoothedLPFQ, audioCtx.currentTime, 0.02); }
    if (scratchMidEQ) scratchMidEQ.gain.setTargetAtTime(smoothedMidGain, audioCtx.currentTime, 0.02);
    if (musicGain) { const tv = 0.04 + 0.46 * Math.min(absRate, 1); musicGain.gain.setTargetAtTime(tv, audioCtx.currentTime, 0.05); }
    if (crackleGain) { let cv = absRate < 0.02 ? 0 : absRate < 0.5 ? 0.12*(1-absRate/0.5)+0.02*(absRate/0.5) : 0.02; if (isDragging) cv *= 2.5; crackleGain.gain.setTargetAtTime(Math.min(cv, 0.3), audioCtx.currentTime, 0.04); }
    if (crackleSource) crackleSource.playbackRate.setTargetAtTime(Math.max(0.1, absRate*1.2), audioCtx.currentTime, 0.05);
    if (needleGain) needleGain.gain.setTargetAtTime(absRate > 0.02 ? 0.025*Math.min(absRate,1) : 0, audioCtx.currentTime, 0.04);
  } else {
    smoothedRate += (1 - smoothedRate) * 0.1;
    if (activeSource && sourceIsPlaying) {
      if (currentDirection !== 1) { virtualPlayhead = getPlayhead(); startMusicSource(virtualPlayhead, 1); }
      else if (Math.abs(lastSourceRate - 1) > 0.01) { activeSource.playbackRate.setTargetAtTime(1, audioCtx.currentTime, 0.08); lastSourceRate = 1; }
    }
    smoothedLPFFreq += (22000 - smoothedLPFFreq) * 0.1; smoothedLPFQ += (0.707 - smoothedLPFQ) * 0.1; smoothedMidGain += -smoothedMidGain * 0.1;
    if (musicLPF) { musicLPF.frequency.setTargetAtTime(smoothedLPFFreq, audioCtx.currentTime, 0.05); musicLPF.Q.setTargetAtTime(smoothedLPFQ, audioCtx.currentTime, 0.05); }
    if (scratchMidEQ) scratchMidEQ.gain.setTargetAtTime(smoothedMidGain, audioCtx.currentTime, 0.05);
    if (musicGain) musicGain.gain.setTargetAtTime(0.5, audioCtx.currentTime, 0.08);
    if (crackleGain) crackleGain.gain.setTargetAtTime(0, audioCtx.currentTime, 0.1);
    if (needleGain) needleGain.gain.setTargetAtTime(0, audioCtx.currentTime, 0.1);
  }
}
'''}

// ─── WEBCAM INIT ─────────────────────────────────────────
const statusEl = document.getElementById("camera-status");
const camPreview = document.getElementById("camera-preview");
const camPreviewVideo = document.getElementById("camera-preview-video");

navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user", width: {{ ideal: 640 }}, height: {{ ideal: 480 }}, frameRate: {{ ideal: 60, min: 30 }} }} }})
  .then(stream => {{
    video.srcObject = stream; video.play();
    camPreviewVideo.srcObject = stream; camPreviewVideo.play();
    camPreview.classList.add("active");
    statusEl.textContent = "Camera connected — reflections active";
    setTimeout(() => statusEl.style.opacity = "0", 3000);
  }})
  .catch(() => {{
    statusEl.textContent = "Camera unavailable — using fallback reflections";
    setTimeout(() => statusEl.style.opacity = "0", 4000);
    const fc = document.createElement("canvas"); fc.width = 512; fc.height = 512;
    const fCtx = fc.getContext("2d");
    const fg = fCtx.createLinearGradient(0, 0, 512, 512);
    fg.addColorStop(0, "#ddeeff"); fg.addColorStop(0.3, "#bbccee");
    fg.addColorStop(0.6, "#99aadd"); fg.addColorStop(1, "#7788cc");
    fCtx.fillStyle = fg; fCtx.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 100; i++) {{
      fCtx.fillStyle = `rgba(255,255,255,${{Math.random()*0.5+0.1}})`;
      fCtx.beginPath(); fCtx.arc(Math.random()*512, Math.random()*512, Math.random()*3, 0, Math.PI*2); fCtx.fill();
    }}
    envSphereMat.map = new THREE.CanvasTexture(fc);
    envSphereMat.needsUpdate = true;
  }});

addEventListener("pagehide", () => {{
  if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
}});

// ─── LUMINANCE ANALYSIS ──────────────────────────────────
const lumCanvas = document.createElement("canvas"); lumCanvas.width = 8; lumCanvas.height = 8;
const lumCtx = lumCanvas.getContext("2d", {{ willReadFrequently: true }});
let smoothLum = 0.5, latestLum = 0.5, lumReady = false;

function analyzeLuminance() {{
  if (!video.videoWidth) return;
  lumCtx.drawImage(video, 0, 0, 8, 8);
  const data = lumCtx.getImageData(0, 0, 8, 8).data;
  let total = 0, count = 0;
  for (let i = 0; i < data.length; i += 16) {{ total += 0.2126*data[i] + 0.7152*data[i+1] + 0.0722*data[i+2]; count++; }}
  latestLum = total / (count * 255); lumReady = true;
}}
if ("requestVideoFrameCallback" in HTMLVideoElement.prototype) {{
  const onFrame = () => {{ analyzeLuminance(); video.requestVideoFrameCallback(onFrame); }};
  video.requestVideoFrameCallback(onFrame);
}} else {{ setInterval(analyzeLuminance, 500); }}

// ─── RESIZE ──────────────────────────────────────────────
addEventListener("resize", () => {{
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
}});

// ─── ANIMATE ─────────────────────────────────────────────
let time = 0, frameCount = 0;

function animate() {{
  requestAnimationFrame(animate);
  time += 0.016; frameCount++;

  mouseX += (targetMouseX - mouseX) * 0.05;
  mouseY += (targetMouseY - mouseY) * 0.05;

  const progress = getScrollProgress();
  applyScrollKeyframe(progress);
  updateActiveDot(progress);

  camera.position.set(2.5 + mouseX * 0.3, 1.5 + mouseY * -0.2, 4.5);
  camera.lookAt(isDragging ? dragFrozenLookAtX : settings.posX, isDragging ? dragFrozenLookAtY : settings.posY, isDragging ? dragFrozenLookAtZ : settings.posZ);

  if (!isDragging) {{
    orbitTiltX += (-mouseY * ORBIT_STRENGTH - orbitTiltX) * ORBIT_LERP;
    orbitTiltZ += (mouseX * ORBIT_STRENGTH - orbitTiltZ) * ORBIT_LERP;
  }}

  if (isDragging) {{
    vinylGroup.position.set(dragFrozenPosX, dragFrozenPosY, dragFrozenPosZ);
    vinylGroup.scale.setScalar(dragFrozenScale);
    vinylGroup.rotation.x = dragFrozenRotX; vinylGroup.rotation.z = dragFrozenRotZ;
  }} else {{
    const bob = Math.sin(time * 0.6) * 0.08;
    vinylGroup.position.set(settings.posX + settings.offsetX, settings.posY + settings.offsetY + bob, settings.posZ + settings.offsetZ);
    vinylGroup.rotation.x = settings.rotX + orbitTiltX;
    vinylGroup.rotation.z = settings.rotZ + orbitTiltZ;
  }}

  if (!isDragging && isScratchActive) {{
    scratchVelocity *= SCRATCH_FRICTION;
    scratchOffset += scratchVelocity;
    if (Math.abs(scratchVelocity) < 0.0003) {{ currentSpinY += scratchOffset; scratchOffset = 0; scratchVelocity = 0; isScratchActive = false; }}
  }}

  {"updatePlatterAudio();" if include_audio else ""}

  if (!isDragging) currentSpinY += settings.spinSpeed;
  spinPivot.rotation.y = isDragging ? dragBaseSpinY + scratchOffset : settings.rotY + currentSpinY + scratchOffset;

  envSphere.rotation.set(settings.hdrRotX, settings.hdrRotY, settings.hdrRotZ);

  if (frameCount % 2 === 0 && video.videoWidth) {{
    if (feedBlurAmount > 0) {{
      blurCtx.filter = `blur(${{Math.round(feedBlurAmount * 20)}}px) brightness(${{feedBrightnessVal}})`;
      blurCtx.drawImage(video, 0, 0, 256, 256);
      blurTexture.needsUpdate = true; envSphereMat.map = blurTexture;
    }} else {{ envSphereMat.map = videoTexture; envSphereMat.needsUpdate = true; }}
  }}

  const cubeInterval = isDragging || isScratchActive ? 2 : 4;
  if (frameCount % cubeInterval === 0) {{
    vinylGroup.visible = false; cubeCamera.update(renderer, scene); vinylGroup.visible = true; pmremDirty = true;
  }}

  if (pmremDirty && lastPmremFrame !== frameCount) {{
    const newEnv = pmremGenerator.fromCubemap(cubeRenderTarget.texture).texture;
    if (filteredEnvMap) filteredEnvMap.dispose();
    filteredEnvMap = newEnv; scene.environment = filteredEnvMap;
    reflectiveMaterials.forEach(m => m.envMap = filteredEnvMap);
    pmremDirty = false; lastPmremFrame = frameCount;
  }}

  if (lumReady) {{ smoothLum += (latestLum - smoothLum) * 0.15; lumReady = false; }}
  const lf = THREE.MathUtils.clamp(smoothLum, 0.05, 1);
  ambientLight.intensity = 1.2 * (0.5 + lf);
  directionalLight.intensity = 3 * (0.7 + (1 - lf) * 0.5);
  renderer.toneMappingExposure = 1.8 * (0.7 + lf * 0.6);
  rimLight.intensity = 0.8 * (0.8 + Math.sin(time * 2) * 0.2);

  if (frameCount % 3 === 0) {{
    const hp = time * 0.3;
    labelMat.iridescenceThicknessRange = [80 + Math.sin(hp) * 50, 400 + Math.cos(hp * 0.7) * 100];
    bSideLabelMat.iridescenceThicknessRange = [100 + Math.cos(hp * 0.9) * 60, 500 + Math.sin(hp * 0.5) * 120];
  }}

  renderer.render(scene, camera);
}}

animate();
</script>
</body>
</html>''')


def main():
    parser = argparse.ArgumentParser(description="Generate a 3D vinyl showcase HTML file")
    parser.add_argument("--label-text", default="VINYL", help="Main label text (default: VINYL)")
    parser.add_argument("--label-subtitle", default="", help="Subtitle text below main label")
    parser.add_argument("--label-style", choices=["warm", "cool", "monochrome"], default="warm",
                        help="Label color palette (default: warm)")
    parser.add_argument("--groove-preset", choices=["fine", "standard", "deep"], default="standard",
                        help="Groove density/depth (default: standard)")
    parser.add_argument("--scratch-intensity", choices=["none", "light", "heavy"], default="heavy",
                        help="Scratch density (default: heavy)")
    parser.add_argument("--sections", type=int, default=3, choices=range(1, 6),
                        help="Number of scroll sections/keyframes (default: 3)")
    parser.add_argument("--audio", choices=["none", "crackle-only", "full"], default="crackle-only",
                        help="Audio engine: none, crackle-only, or full with music (default: crackle-only)")
    parser.add_argument("--audio-url", default=None, help="MP3 URL for --audio full mode")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark",
                        help="Page theme (default: dark)")
    parser.add_argument("-o", "--output", default="vinyl-showcase.html",
                        help="Output file path (default: vinyl-showcase.html)")
    args = parser.parse_args()

    if args.audio == "full" and not args.audio_url:
        print("Warning: --audio full requires --audio-url <mp3-url>. Falling back to crackle-only.", file=sys.stderr)
        args.audio = "crackle-only"

    html = build_html(args)
    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    print(f"Generated: {out} ({len(html):,} bytes)")
    print(f"  Label: {args.label_text} ({args.label_style})")
    print(f"  Grooves: {args.groove_preset} | Scratches: {args.scratch_intensity}")
    print(f"  Sections: {args.sections} | Audio: {args.audio} | Theme: {args.theme}")


if __name__ == "__main__":
    main()
