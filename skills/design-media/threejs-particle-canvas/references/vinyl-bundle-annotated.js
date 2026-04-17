// virtual:index.js
import * as THREE from "three";
var scene = new THREE.Scene();
scene.background = new THREE.Color(16777215);
var camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.1, 1e3);
camera.position.set(2.5, 1.5, 4.5);
var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.4;
var container = document.getElementById("three-canvas");
container.appendChild(renderer.domElement);
var ambientLight = new THREE.AmbientLight(16777215, 0.6);
ambientLight.name = "ambientLight";
scene.add(ambientLight);
var directionalLight = new THREE.DirectionalLight(16777215, 2);
directionalLight.position.set(5, 8, 5);
directionalLight.name = "mainDirectionalLight";
scene.add(directionalLight);
var fillLight = new THREE.DirectionalLight(8952251, 0.6);
fillLight.position.set(-5, 3, -5);
fillLight.name = "fillLight";
scene.add(fillLight);
var rimLight = new THREE.PointLight(11189247, 0.8, 20);
rimLight.position.set(0, -3, 3);
rimLight.name = "rimLight";
scene.add(rimLight);
var topLight = new THREE.PointLight(16777215, 0.5, 15);
topLight.position.set(0, 5, 0);
topLight.name = "topLight";
scene.add(topLight);
var video = document.createElement("video");
video.autoplay = true;
video.muted = true;
video.playsInline = true;
var videoTexture = new THREE.VideoTexture(video);
videoTexture.minFilter = THREE.LinearFilter;
videoTexture.magFilter = THREE.LinearFilter;
videoTexture.colorSpace = THREE.SRGBColorSpace;
videoTexture.repeat.y = -1;
videoTexture.offset.y = 1;
videoTexture.wrapS = THREE.RepeatWrapping;
videoTexture.wrapT = THREE.RepeatWrapping;
var blurCanvas = document.createElement("canvas");
blurCanvas.width = 256;
blurCanvas.height = 256;
var blurCtx = blurCanvas.getContext("2d");
var blurTexture = new THREE.CanvasTexture(blurCanvas);
blurTexture.minFilter = THREE.LinearFilter;
blurTexture.magFilter = THREE.LinearFilter;
blurTexture.colorSpace = THREE.SRGBColorSpace;
blurTexture.wrapS = THREE.RepeatWrapping;
blurTexture.wrapT = THREE.RepeatWrapping;
var feedBlurAmount = 0.09;
var feedBrightnessVal = 1.6;
var cubeRenderTarget = new THREE.WebGLCubeRenderTarget(128, {
  generateMipmaps: true,
  minFilter: THREE.LinearMipmapLinearFilter,
  type: THREE.HalfFloatType,
  format: THREE.RGBAFormat
});
var pmremGenerator = new THREE.PMREMGenerator(renderer);
pmremGenerator.compileCubemapShader();
var pmremDirty = true;
var lastPmremFrame = -1;
var envSphereGeo = new THREE.SphereGeometry(50, 24, 16);
var envSphereMat = new THREE.MeshBasicMaterial({
  map: videoTexture,
  side: THREE.BackSide,
  toneMapped: false
});
var envSphere = new THREE.Mesh(envSphereGeo, envSphereMat);
envSphere.name = "envSphere";
envSphere.layers.set(1);
scene.add(envSphere);
var cubeCamera = new THREE.CubeCamera(0.1, 100, cubeRenderTarget);
cubeCamera.layers.enable(1);
cubeCamera.name = "cubeCamera";
scene.add(cubeCamera);
var filteredEnvMap = null;
var frameCount = 0;
var KF_PROPS = [
  "posX",
  "posY",
  "posZ",
  "offsetX",
  "offsetY",
  "offsetZ",
  "rotX",
  "rotY",
  "rotZ",
  "scale",
  "spinSpeed",
  "vinylRoughness",
  "vinylMetalness",
  "vinylClearcoat",
  "envIntensity",
  "reflZoom",
  "feedRoughness",
  "feedBlur",
  "feedBrightness",
  "hdrRotX",
  "hdrRotY",
  "hdrRotZ",
  "grooveCount",
  "grooveDepth",
  "grooveWidth",
  "scratchDensity",
  "scratchDepth",
  "scratchLength",
  "scratchOpacity",
  "scratchNormalScale",
  "scratchArcMul",
  "scratchHairMul",
  "scratchCurveMul",
  "scratchNickMul",
  "scratchSweepMul",
  "scratchSCurveMul",
  "scratchClusterMul",
  "scratchArcAlpha",
  "scratchHairAlpha",
  "scratchCurveAlpha",
  "scratchNickAlpha",
  "scratchSweepAlpha"
];
var defaultSettings = {
  // Hero — position
  posX: -0.9,
  posY: -0.6,
  posZ: 1.6,
  // Hero — offset
  offsetX: 1.3,
  offsetY: 0.25,
  offsetZ: 0,
  // Hero — rotation
  rotX: 0.61,
  rotY: -1.46,
  rotZ: 0.43,
  // Hero — scale & spin
  scale: 0.9,
  spinSpeed: 7e-3,
  // Hero — surface
  vinylRoughness: 1,
  vinylMetalness: 1,
  vinylClearcoat: 0.91,
  envIntensity: 3.5,
  // Hero — camera feed
  reflZoom: 6,
  feedRoughness: 1,
  feedBlur: 0.25,
  feedBrightness: 1.75,
  // Hero — HDR orientation
  hdrRotX: 1.2,
  hdrRotY: 1.65,
  hdrRotZ: 0.28,
  // Hero — grooves
  grooveCount: 22,
  grooveDepth: 1.4,
  grooveWidth: 2,
  // Hero — scratches
  scratchDensity: 340,
  scratchDepth: 2,
  scratchLength: 0.5,
  scratchOpacity: 0.35,
  scratchNormalScale: 2,
  scratchArcMul: 5,
  scratchHairMul: 6.6,
  scratchCurveMul: 1.55,
  scratchNickMul: 0.9,
  scratchSweepMul: 0.24,
  scratchSCurveMul: 0.15,
  scratchClusterMul: 0.04,
  scratchArcAlpha: 0.67,
  scratchHairAlpha: 0.25,
  scratchCurveAlpha: 0.35,
  scratchNickAlpha: 0.55,
  scratchSweepAlpha: 0.19
};
var keyframes = [
  { ...defaultSettings },
  // Hero — already matches JSON exactly above
  {
    // Artists
    ...defaultSettings,
    // position
    posX: 0,
    posY: 0,
    posZ: 0,
    // offset
    offsetX: 0.85,
    offsetY: 0.3,
    offsetZ: 0,
    // rotation
    rotX: -2.01,
    rotY: -2.5,
    rotZ: 0,
    // scale & spin
    scale: 0.65,
    spinSpeed: 4e-3,
    // surface
    vinylRoughness: 1,
    vinylMetalness: 0.74,
    vinylClearcoat: 0.52,
    envIntensity: 3.5,
    // camera feed
    reflZoom: 4.85,
    feedRoughness: 0.31,
    feedBlur: 0.03,
    feedBrightness: 1.8,
    // HDR orientation
    hdrRotX: 2.36,
    hdrRotY: 1.96,
    hdrRotZ: 0.03,
    // grooves
    grooveCount: 35,
    grooveDepth: 1,
    grooveWidth: 2,
    // scratches
    scratchDensity: 340,
    scratchDepth: 2,
    scratchLength: 0.5,
    scratchOpacity: 0.35,
    scratchNormalScale: 2,
    scratchArcMul: 2.5,
    scratchHairMul: 4,
    scratchCurveMul: 0.6,
    scratchNickMul: 0.3,
    scratchSweepMul: 0.08,
    scratchSCurveMul: 0.15,
    scratchClusterMul: 0.04,
    scratchArcAlpha: 0.45,
    scratchHairAlpha: 0.25,
    scratchCurveAlpha: 0.35,
    scratchNickAlpha: 0.3,
    scratchSweepAlpha: 0.15
  },
  {
    // Contact
    ...defaultSettings,
    // position
    posX: -0.4,
    posY: 1.2,
    posZ: 0,
    // offset
    offsetX: -0.05,
    offsetY: 0,
    offsetZ: 0,
    // rotation
    rotX: 0.5,
    rotY: 0.38,
    rotZ: 0.01,
    // scale & spin
    scale: 1.25,
    spinSpeed: 3e-3,
    // surface
    vinylRoughness: 1,
    vinylMetalness: 1,
    vinylClearcoat: 1,
    envIntensity: 5,
    // camera feed
    reflZoom: 4.45,
    feedRoughness: 0.95,
    feedBlur: 0.36,
    feedBrightness: 1.75,
    // HDR orientation
    hdrRotX: 2.8,
    hdrRotY: 0.27,
    hdrRotZ: -0.1,
    // grooves
    grooveCount: 35,
    grooveDepth: 1,
    grooveWidth: 2,
    // scratches
    scratchDensity: 340,
    scratchDepth: 2,
    scratchLength: 0.5,
    scratchOpacity: 0.35,
    scratchNormalScale: 2,
    scratchArcMul: 2.5,
    scratchHairMul: 4,
    scratchCurveMul: 0.6,
    scratchNickMul: 0.3,
    scratchSweepMul: 0.08,
    scratchSCurveMul: 0.15,
    scratchClusterMul: 0.04,
    scratchArcAlpha: 0.45,
    scratchHairAlpha: 0.25,
    scratchCurveAlpha: 0.35,
    scratchNickAlpha: 0.3,
    scratchSweepAlpha: 0.15
  }
];
var settings = { ...defaultSettings };
var activeKfTab = 0;
var KF_EDITABLE_PROPS = [
  "posX",
  "posY",
  "posZ",
  "offsetX",
  "offsetY",
  "offsetZ",
  "rotX",
  "rotY",
  "rotZ",
  "scale",
  "spinSpeed",
  "vinylRoughness",
  "vinylMetalness",
  "vinylClearcoat",
  "envIntensity",
  "reflZoom",
  "feedRoughness",
  "feedBlur",
  "feedBrightness",
  "hdrRotX",
  "hdrRotY",
  "hdrRotZ"
];
var vinylGroup = new THREE.Group();
vinylGroup.name = "vinylGroup";
scene.add(vinylGroup);
var GROOVE_MAP_SIZE = 1024;
function generateGrooveNormalMap(count, depth, width) {
  const c = document.createElement("canvas");
  c.width = GROOVE_MAP_SIZE;
  c.height = GROOVE_MAP_SIZE;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "rgb(128,128,255)";
  ctx.fillRect(0, 0, GROOVE_MAP_SIZE, GROOVE_MAP_SIZE);
  const cx = GROOVE_MAP_SIZE / 2, cy = GROOVE_MAP_SIZE / 2;
  const innerR = GROOVE_MAP_SIZE * 0.14, outerR = GROOVE_MAP_SIZE * 0.49;
  for (let i = 0; i < count; i++) {
    const t = i / count;
    const r = innerR + t * (outerR - innerR);
    const intensity = Math.floor(60 * depth);
    ctx.strokeStyle = `rgb(${128 + intensity},128,255)`;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = `rgb(${128 - intensity},128,255)`;
    ctx.lineWidth = width * 0.6;
    ctx.beginPath();
    ctx.arc(cx, cy, r + width * 0.5, 0, Math.PI * 2);
    ctx.stroke();
  }
  return new THREE.CanvasTexture(c);
}
function generateGrooveRoughnessMap(count) {
  const c = document.createElement("canvas");
  c.width = GROOVE_MAP_SIZE;
  c.height = GROOVE_MAP_SIZE;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#333";
  ctx.fillRect(0, 0, GROOVE_MAP_SIZE, GROOVE_MAP_SIZE);
  const cx = GROOVE_MAP_SIZE / 2, cy = GROOVE_MAP_SIZE / 2;
  const innerR = GROOVE_MAP_SIZE * 0.14, outerR = GROOVE_MAP_SIZE * 0.49;
  for (let i = 0; i < count; i++) {
    const t = i / count;
    const r = innerR + t * (outerR - innerR);
    ctx.strokeStyle = "#666";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
  }
  return new THREE.CanvasTexture(c);
}
function generateScratchNormalMap(density, depth, length, params) {
  const p = params || {};
  const arcMul = p.arcMul ?? 2.5;
  const hairMul = p.hairMul ?? 4;
  const nickMul = p.nickMul ?? 0.3;
  const arcAlpha = p.arcAlpha ?? 0.45;
  const hairAlpha = p.hairAlpha ?? 0.25;
  const nickAlpha = p.nickAlpha ?? 0.3;
  const S = GROOVE_MAP_SIZE;
  const c = document.createElement("canvas");
  c.width = S;
  c.height = S;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "rgb(128,128,255)";
  ctx.fillRect(0, 0, S, S);
  const cx2 = S / 2, cy2 = S / 2;
  const maxR = S * 0.49, minR = S * 0.14;
  const intensity = Math.floor(40 * depth);
  const arcCount = Math.floor(density * arcMul);
  for (let i = 0; i < arcCount; i++) {
    const r = minR + Math.random() * (maxR - minR);
    const startAngle = Math.random() * Math.PI * 2;
    const arcLen = (Math.random() * 0.15 + 0.02) * length * 8;
    const v = 128 + (Math.random() > 0.5 ? intensity : -intensity) * (0.5 + Math.random() * 0.5);
    ctx.strokeStyle = `rgb(${Math.round(v)},128,255)`;
    ctx.lineWidth = Math.random() * 0.5 + 0.1;
    ctx.globalAlpha = Math.random() * arcAlpha + arcAlpha * 0.33;
    ctx.beginPath();
    ctx.arc(cx2, cy2, r, startAngle, startAngle + arcLen);
    ctx.stroke();
  }
  const hairlineCount = Math.floor(density * hairMul);
  for (let i = 0; i < hairlineCount; i++) {
    const r = minR + Math.random() * (maxR - minR);
    const startAngle = Math.random() * Math.PI * 2;
    const arcLen = (Math.random() * 0.08 + 0.01) * length * 6;
    const v = 128 + (Math.random() > 0.5 ? 1 : -1) * intensity * (0.2 + Math.random() * 0.3);
    ctx.strokeStyle = `rgb(${Math.round(v)},128,255)`;
    ctx.lineWidth = 0.15 + Math.random() * 0.2;
    ctx.globalAlpha = Math.random() * hairAlpha + hairAlpha * 0.2;
    ctx.beginPath();
    ctx.arc(cx2, cy2, r, startAngle, startAngle + arcLen);
    ctx.stroke();
  }
  const nickCount = Math.floor(density * nickMul);
  for (let i = 0; i < nickCount; i++) {
    const angle = Math.random() * Math.PI * 2;
    const r = minR + Math.random() * (maxR - minR);
    const sx = cx2 + Math.cos(angle) * r, sy = cy2 + Math.sin(angle) * r;
    const nickLen = (Math.random() * 0.2 + 0.05) * length * S * 0.08;
    const nickAngle = angle + (Math.random() - 0.5) * 0.6;
    const v = 128 + (Math.random() > 0.5 ? intensity * 0.6 : -intensity * 0.6);
    ctx.strokeStyle = `rgb(${Math.round(v)},128,255)`;
    ctx.lineWidth = Math.random() * 0.35 + 0.1;
    ctx.globalAlpha = Math.random() * nickAlpha + nickAlpha * 0.33;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(nickAngle) * nickLen, sy + Math.sin(nickAngle) * nickLen);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
  return new THREE.CanvasTexture(c);
}
function generateScratchRoughnessMap(density, length, params) {
  const p = params || {};
  const arcMul = p.arcMul ?? 2.5;
  const hairMul = p.hairMul ?? 4;
  const nickMul = p.nickMul ?? 0.3;
  const S = GROOVE_MAP_SIZE;
  const c = document.createElement("canvas");
  c.width = S;
  c.height = S;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, S, S);
  const cx2 = S / 2, cy2 = S / 2;
  const maxR = S * 0.49, minR = S * 0.14;
  const arcCount = Math.floor(density * arcMul);
  for (let i = 0; i < arcCount; i++) {
    const r = minR + Math.random() * (maxR - minR);
    const startAngle = Math.random() * Math.PI * 2;
    const arcLen = (Math.random() * 0.15 + 0.02) * length * 8;
    ctx.strokeStyle = `rgba(255,255,255,${Math.random() * 0.15 + 0.02})`;
    ctx.lineWidth = Math.random() * 0.5 + 0.1;
    ctx.beginPath();
    ctx.arc(cx2, cy2, r, startAngle, startAngle + arcLen);
    ctx.stroke();
  }
  const hairlineCount = Math.floor(density * hairMul);
  for (let i = 0; i < hairlineCount; i++) {
    const r = minR + Math.random() * (maxR - minR);
    const startAngle = Math.random() * Math.PI * 2;
    const arcLen = (Math.random() * 0.08 + 0.01) * length * 6;
    ctx.strokeStyle = `rgba(255,255,255,${Math.random() * 0.08 + 0.01})`;
    ctx.lineWidth = 0.15 + Math.random() * 0.2;
    ctx.beginPath();
    ctx.arc(cx2, cy2, r, startAngle, startAngle + arcLen);
    ctx.stroke();
  }
  const nickCount = Math.floor(density * nickMul);
  for (let i = 0; i < nickCount; i++) {
    const angle = Math.random() * Math.PI * 2;
    const r = minR + Math.random() * (maxR - minR);
    const sx = cx2 + Math.cos(angle) * r, sy = cy2 + Math.sin(angle) * r;
    const nickLen = (Math.random() * 0.2 + 0.05) * length * S * 0.08;
    const nickAngle = angle + (Math.random() - 0.5) * 0.6;
    ctx.strokeStyle = `rgba(255,255,255,${Math.random() * 0.1 + 0.02})`;
    ctx.lineWidth = Math.random() * 0.35 + 0.1;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(nickAngle) * nickLen, sy + Math.sin(nickAngle) * nickLen);
    ctx.stroke();
  }
  return new THREE.CanvasTexture(c);
}
function getScratchParams() {
  return {
    arcMul: settings.scratchArcMul,
    hairMul: settings.scratchHairMul,
    curveMul: settings.scratchCurveMul,
    nickMul: settings.scratchNickMul,
    sweepMul: settings.scratchSweepMul,
    sCurveMul: settings.scratchSCurveMul,
    clusterMul: settings.scratchClusterMul,
    arcAlpha: settings.scratchArcAlpha,
    hairAlpha: settings.scratchHairAlpha,
    curveAlpha: settings.scratchCurveAlpha,
    nickAlpha: settings.scratchNickAlpha,
    sweepAlpha: settings.scratchSweepAlpha
  };
}
var grooveNormalTex = generateGrooveNormalMap(settings.grooveCount, settings.grooveDepth, settings.grooveWidth);
var grooveRoughTex = generateGrooveRoughnessMap(settings.grooveCount);
var scratchNormalTex = generateScratchNormalMap(settings.scratchDensity, settings.scratchDepth, settings.scratchLength, getScratchParams());
var scratchRoughTex = generateScratchRoughnessMap(settings.scratchDensity, settings.scratchLength, getScratchParams());
var discGeo = new THREE.CylinderGeometry(2, 2, 0.012, 128);
var discMat = new THREE.MeshPhysicalMaterial({
  color: 526344,
  metalness: settings.vinylMetalness,
  roughness: settings.vinylRoughness,
  envMapIntensity: settings.envIntensity,
  clearcoat: settings.vinylClearcoat,
  clearcoatRoughness: settings.feedRoughness,
  reflectivity: 1,
  ior: 1.8,
  specularIntensity: 1,
  specularColor: new THREE.Color(16777215),
  normalMap: grooveNormalTex,
  normalScale: new THREE.Vector2(0.8, 0.8),
  roughnessMap: grooveRoughTex,
  side: THREE.DoubleSide
});
var scratchDiscGeo = new THREE.CylinderGeometry(2, 2, 0.013, 64);
var scratchMat = new THREE.MeshPhysicalMaterial({
  color: 526344,
  metalness: 0.9,
  roughness: 0.1,
  envMapIntensity: settings.envIntensity,
  clearcoat: 0.5,
  clearcoatRoughness: 0.05,
  normalMap: scratchNormalTex,
  normalScale: new THREE.Vector2(settings.scratchNormalScale, settings.scratchNormalScale),
  roughnessMap: scratchRoughTex,
  transparent: true,
  opacity: settings.scratchOpacity,
  depthWrite: false,
  side: THREE.DoubleSide
});
var disc = new THREE.Mesh(discGeo, discMat);
disc.name = "vinylDisc";
vinylGroup.add(disc);
var scratchDisc = new THREE.Mesh(scratchDiscGeo, scratchMat);
scratchDisc.name = "scratchLayer";
vinylGroup.add(scratchDisc);
var labelGeo = new THREE.CircleGeometry(0.5, 64);
function seededRandom(seed) {
  let s = seed;
  return function() {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}
function drawSpindleHole(ctx, cx, cy) {
  const holeR = 55;
  const ringGrad = ctx.createRadialGradient(cx, cy, holeR - 8, cx, cy, holeR + 22);
  ringGrad.addColorStop(0, "rgba(200, 200, 205, 0.95)");
  ringGrad.addColorStop(0.3, "rgba(230, 230, 235, 0.9)");
  ringGrad.addColorStop(0.6, "rgba(170, 170, 178, 0.85)");
  ringGrad.addColorStop(1, "rgba(130, 130, 140, 0)");
  ctx.fillStyle = ringGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, holeR + 22, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#0a0a0a";
  ctx.beginPath();
  ctx.arc(cx, cy, holeR - 6, 0, Math.PI * 2);
  ctx.fill();
}
function drawEdgeWear(ctx, cx, cy, R, rand) {
  ctx.globalCompositeOperation = "destination-out";
  for (let i = 0; i < 250; i++) {
    const angle = rand() * Math.PI * 2;
    const dist = R - 40 + rand() * 50;
    const px = cx + Math.cos(angle) * dist, py = cy + Math.sin(angle) * dist;
    const size = rand() * 14 + 2;
    ctx.fillStyle = `rgba(0,0,0,${rand() * 0.6 + 0.3})`;
    ctx.beginPath();
    ctx.ellipse(px, py, size, size * (0.3 + rand() * 0.7), angle, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalCompositeOperation = "source-over";
}
function drawArcText(ctx, cx, cy, text, radius, startAngleDeg, charSpacing, fontSize, color, isBottom) {
  ctx.fillStyle = color;
  ctx.font = `600 ${fontSize}px "Inter", sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.save();
  ctx.translate(cx, cy);
  if (isBottom) {
    const bStartAngle = startAngleDeg * Math.PI / 180 + text.length * charSpacing / 2;
    for (let i = 0; i < text.length; i++) {
      const charAngle = bStartAngle - i * charSpacing;
      ctx.save();
      ctx.rotate(charAngle);
      ctx.translate(0, radius);
      ctx.rotate(Math.PI);
      ctx.fillText(text[i], 0, 0);
      ctx.restore();
    }
  } else {
    const sAngle = startAngleDeg * Math.PI / 180 - text.length * charSpacing / 2;
    for (let i = 0; i < text.length; i++) {
      const charAngle = sAngle + i * charSpacing;
      ctx.save();
      ctx.rotate(charAngle);
      ctx.translate(0, -radius);
      ctx.fillText(text[i], 0, 0);
      ctx.restore();
    }
  }
  ctx.restore();
}
function createStickerTexture() {
  const c = document.createElement("canvas");
  c.width = 2048;
  c.height = 2048;
  const ctx = c.getContext("2d");
  const cx = 1024, cy = 1024;
  const rand = seededRandom(42);
  const R = 1020;
  const baseGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
  baseGrad.addColorStop(0, "#FFD166");
  baseGrad.addColorStop(0.2, "#FF9F43");
  baseGrad.addColorStop(0.45, "#EE5A24");
  baseGrad.addColorStop(0.7, "#D63031");
  baseGrad.addColorStop(0.9, "#6C0F1A");
  baseGrad.addColorStop(1, "#2C0510");
  ctx.fillStyle = baseGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  const pinkSplash = ctx.createRadialGradient(cx - 350, cy - 300, 20, cx - 350, cy - 300, 500);
  pinkSplash.addColorStop(0, "rgba(255, 56, 127, 0.25)");
  pinkSplash.addColorStop(0.5, "rgba(255, 56, 127, 0.08)");
  pinkSplash.addColorStop(1, "rgba(255, 56, 127, 0)");
  ctx.fillStyle = pinkSplash;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  const blueSplash = ctx.createRadialGradient(cx + 350, cy + 300, 30, cx + 350, cy + 300, 450);
  blueSplash.addColorStop(0, "rgba(72, 126, 255, 0.2)");
  blueSplash.addColorStop(0.5, "rgba(72, 126, 255, 0.06)");
  blueSplash.addColorStop(1, "rgba(72, 126, 255, 0)");
  ctx.fillStyle = blueSplash;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  const centerGlow = ctx.createRadialGradient(cx, cy - 60, 10, cx, cy - 60, 350);
  centerGlow.addColorStop(0, "rgba(255, 255, 220, 0.3)");
  centerGlow.addColorStop(0.5, "rgba(255, 220, 150, 0.1)");
  centerGlow.addColorStop(1, "rgba(255, 200, 100, 0)");
  ctx.fillStyle = centerGlow;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.clip();
  for (let i = 0; i < 12e3; i++) {
    const angle = rand() * Math.PI * 2;
    const r = rand() * R;
    const px = cx + Math.cos(angle) * r;
    const py = cy + Math.sin(angle) * r;
    const bright = rand() > 0.5;
    const alpha = rand() * 0.05 + 0.01;
    ctx.fillStyle = bright ? `rgba(255,255,255,${alpha})` : `rgba(0,0,0,${alpha * 0.8})`;
    ctx.fillRect(px, py, rand() * 2 + 0.3, rand() * 0.8 + 0.2);
  }
  ctx.restore();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.55)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(cx, cy, 960, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.3)";
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.arc(cx, cy, 945, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.12)";
  ctx.lineWidth = 0.6;
  ctx.beginPath();
  ctx.arc(cx, cy, 930, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.4)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, 140, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.18)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(cx, cy, 165, 0, Math.PI * 2);
  ctx.stroke();
  for (let i = 0; i < 72; i++) {
    const angle = i / 72 * Math.PI * 2;
    const isMajor = i % 6 === 0;
    const innerR = isMajor ? 870 : 895;
    ctx.strokeStyle = `rgba(0, 0, 0, ${isMajor ? 0.4 : 0.1})`;
    ctx.lineWidth = isMajor ? 1.5 : 0.6;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(angle) * innerR, cy + Math.sin(angle) * innerR);
    ctx.lineTo(cx + Math.cos(angle) * 925, cy + Math.sin(angle) * 925);
    ctx.stroke();
  }
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.clip();
  const waveY = cy + 260;
  const barCount = 60;
  const barSpacing = 24;
  const totalW = barCount * barSpacing;
  const startX = cx - totalW / 2;
  const waveSeed = seededRandom(77);
  for (let i = 0; i < barCount; i++) {
    const x = startX + i * barSpacing;
    const t = i / barCount;
    const envelope = Math.sin(t * Math.PI);
    const h = 30 + waveSeed() * 180 * envelope + 37 * Math.sin(t * Math.PI * 3);
    const barW = 16;
    const barAlpha = 0.55 + envelope * 0.3;
    ctx.fillStyle = `rgba(0, 0, 0, ${barAlpha})`;
    ctx.fillRect(x, waveY - h / 2, barW, h);
  }
  ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
  ctx.beginPath();
  ctx.moveTo(cx - 440, cy - 480);
  ctx.lineTo(cx - 440, cy - 310);
  ctx.lineTo(cx - 300, cy - 395);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "rgba(0, 0, 0, 0.45)";
  ctx.strokeStyle = "rgba(0, 0, 0, 0.7)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(cx + 380, cy - 500);
  ctx.lineTo(cx + 480, cy - 390);
  ctx.lineTo(cx + 380, cy - 280);
  ctx.lineTo(cx + 280, cy - 390);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.4)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.ellipse(cx, cy + 80, 280, 85, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
  ctx.beginPath();
  ctx.arc(cx, cy + 80, 38, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.55)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy + 80, 38, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = "rgba(0, 0, 0, 0.15)";
  ctx.beginPath();
  ctx.arc(cx - 10, cy + 72, 12, 0, Math.PI * 2);
  ctx.fill();
  for (let i = 0; i < 32; i++) {
    const angle = i / 32 * Math.PI * 2;
    const isMajor = i % 4 === 0;
    ctx.strokeStyle = `rgba(0, 0, 0, ${isMajor ? 0.2 : 0.06})`;
    ctx.lineWidth = isMajor ? 1.8 : 0.7;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(angle) * 200, cy + Math.sin(angle) * 200);
    ctx.lineTo(cx + Math.cos(angle) * (isMajor ? 900 : 700), cy + Math.sin(angle) * (isMajor ? 900 : 700));
    ctx.stroke();
  }
  const dotPatternSeed = seededRandom(33);
  for (let i = 0; i < 36; i++) {
    const angle = i / 36 * Math.PI * 2;
    const r = 550;
    const px = cx + Math.cos(angle) * r;
    const py = cy + Math.sin(angle) * r;
    const size = 5 + dotPatternSeed() * 8;
    ctx.fillStyle = `rgba(0, 0, 0, ${0.2 + dotPatternSeed() * 0.35})`;
    ctx.beginPath();
    ctx.arc(px, py, size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.strokeStyle = "rgba(0, 0, 0, 0.25)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(cx - 550, cy + 130);
  ctx.lineTo(cx + 550, cy + 130);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.12)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx - 480, cy + 320);
  ctx.lineTo(cx + 480, cy + 320);
  ctx.stroke();
  const crossPositions = [
    [cx - 520, cy - 250],
    [cx + 500, cy - 270],
    [cx - 500, cy + 400],
    [cx + 520, cy + 420],
    [cx, cy - 500],
    [cx, cy + 500]
  ];
  crossPositions.forEach(([x, y]) => {
    ctx.strokeStyle = "rgba(0, 0, 0, 0.3)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x - 20, y);
    ctx.lineTo(x + 20, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y - 20);
    ctx.lineTo(x, y + 20);
    ctx.stroke();
  });
  ctx.strokeStyle = "rgba(0, 0, 0, 0.2)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx + 420, cy + 160, 100, -Math.PI * 0.3, Math.PI * 0.5);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx + 420, cy + 160, 130, -Math.PI * 0.2, Math.PI * 0.4);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx - 420, cy + 160, 100, Math.PI * 0.5, Math.PI * 1.3);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx - 420, cy + 160, 130, Math.PI * 0.6, Math.PI * 1.2);
  ctx.stroke();
  ctx.restore();
  ctx.fillStyle = "#000000";
  ctx.font = '900 225px "Syne", "Inter", sans-serif';
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("\xD8NYX", cx, cy - 110);
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.font = '500 28px "Inter", sans-serif';
  ctx.fillText("F  R  E  Q  U  E  N  C  Y", cx, cy - 5);
  ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
  ctx.font = '600 17px "Inter", sans-serif';
  ctx.fillText("\xD8X \u2014 001  \xB7  FIRST PRESSING", cx, cy + 45);
  ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
  ctx.font = '800 22px "Syne", sans-serif';
  ctx.fillText("SIDE A", cx, cy + 370);
  ctx.fillStyle = "rgba(0, 0, 0, 0.25)";
  ctx.font = '400 14px "Inter", sans-serif';
  ctx.fillText("\u2117 2024 \xD8NYX FREQUENCY \xB7 ALL RIGHTS RESERVED", cx, cy + 480);
  ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
  ctx.font = '700 16px "Inter", sans-serif';
  ctx.save();
  ctx.translate(cx + 620, cy);
  ctx.rotate(Math.PI / 2);
  ctx.fillText("33\u2153 RPM", 0, 0);
  ctx.restore();
  ctx.save();
  ctx.translate(cx - 620, cy);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("STEREO", 0, 0);
  ctx.restore();
  drawArcText(ctx, cx, cy, "ECHOES  IN  WAX", 820, -90, 0.055, 16, "rgba(0,0,0,0.3)", false);
  drawArcText(ctx, cx, cy, "SIGNAL \xB7 FORM \xB7 RESONANCE", 820, 90, 0.042, 13, "rgba(0,0,0,0.2)", true);
  drawSpindleHole(ctx, cx, cy);
  drawEdgeWear(ctx, cx, cy, R, rand);
  return new THREE.CanvasTexture(c);
}
function createBSideStickerTexture() {
  const c = document.createElement("canvas");
  c.width = 2048;
  c.height = 2048;
  const ctx = c.getContext("2d");
  const cx = 1024, cy = 1024;
  const rand = seededRandom(137);
  const R = 1020;
  const baseGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
  baseGrad.addColorStop(0, "#6C5CE7");
  baseGrad.addColorStop(0.2, "#4834D4");
  baseGrad.addColorStop(0.45, "#2C2C7A");
  baseGrad.addColorStop(0.7, "#1B1464");
  baseGrad.addColorStop(0.9, "#0C0832");
  baseGrad.addColorStop(1, "#050318");
  ctx.fillStyle = baseGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  const cyanSplash = ctx.createRadialGradient(cx + 300, cy - 350, 20, cx + 300, cy - 350, 500);
  cyanSplash.addColorStop(0, "rgba(0, 255, 221, 0.22)");
  cyanSplash.addColorStop(0.5, "rgba(0, 255, 221, 0.06)");
  cyanSplash.addColorStop(1, "rgba(0, 255, 221, 0)");
  ctx.fillStyle = cyanSplash;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  const magSplash = ctx.createRadialGradient(cx - 300, cy + 350, 30, cx - 300, cy + 350, 450);
  magSplash.addColorStop(0, "rgba(255, 0, 128, 0.18)");
  magSplash.addColorStop(0.5, "rgba(255, 0, 128, 0.05)");
  magSplash.addColorStop(1, "rgba(255, 0, 128, 0)");
  ctx.fillStyle = magSplash;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  const centerGlow = ctx.createRadialGradient(cx, cy - 40, 10, cx, cy - 40, 300);
  centerGlow.addColorStop(0, "rgba(165, 140, 255, 0.25)");
  centerGlow.addColorStop(1, "rgba(100, 80, 200, 0)");
  ctx.fillStyle = centerGlow;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.clip();
  for (let i = 0; i < 12e3; i++) {
    const angle = rand() * Math.PI * 2;
    const r = rand() * R;
    const px = cx + Math.cos(angle) * r;
    const py = cy + Math.sin(angle) * r;
    const bright = rand() > 0.5;
    const alpha = rand() * 0.04 + 8e-3;
    ctx.fillStyle = bright ? `rgba(200,200,255,${alpha})` : `rgba(0,0,30,${alpha})`;
    ctx.fillRect(px, py, rand() * 2 + 0.3, rand() * 0.8 + 0.2);
  }
  ctx.restore();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.45)";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.arc(cx, cy, 960, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.2)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(cx, cy, 945, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.1)";
  ctx.lineWidth = 0.6;
  ctx.beginPath();
  ctx.arc(cx, cy, 930, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.35)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, 140, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.15)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(cx, cy, 165, 0, Math.PI * 2);
  ctx.stroke();
  for (let i = 0; i < 72; i++) {
    const angle = i / 72 * Math.PI * 2;
    const isMajor = i % 6 === 0;
    const innerR = isMajor ? 870 : 895;
    ctx.strokeStyle = `rgba(0, 0, 0, ${isMajor ? 0.35 : 0.08})`;
    ctx.lineWidth = isMajor ? 1.5 : 0.5;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(angle) * innerR, cy + Math.sin(angle) * innerR);
    ctx.lineTo(cx + Math.cos(angle) * 925, cy + Math.sin(angle) * 925);
    ctx.stroke();
  }
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.clip();
  const waveY = cy + 260;
  const barCount = 60;
  const barSpacing = 24;
  const totalW = barCount * barSpacing;
  const startX = cx - totalW / 2;
  const waveSeed = seededRandom(201);
  for (let i = 0; i < barCount; i++) {
    const x = startX + i * barSpacing;
    const t = i / barCount;
    const envelope = Math.sin(t * Math.PI);
    const h = 30 + waveSeed() * 150 * envelope + 30 * Math.sin(t * Math.PI * 4);
    const barW = 15;
    ctx.fillStyle = `rgba(0, 0, 0, ${0.45 + envelope * 0.3})`;
    ctx.fillRect(x, waveY - h / 2, barW, h);
  }
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(cx - 440, cy - 480, 40, 150);
  ctx.fillRect(cx - 380, cy - 480, 40, 150);
  ctx.strokeStyle = "rgba(0, 0, 0, 0.5)";
  ctx.lineWidth = 3.5;
  ctx.fillStyle = "rgba(0, 0, 0, 0.08)";
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const angle = i / 6 * Math.PI * 2 - Math.PI / 6;
    const hx = cx + 380 + Math.cos(angle) * 90;
    const hy = cy - 400 + Math.sin(angle) * 90;
    i === 0 ? ctx.moveTo(hx, hy) : ctx.lineTo(hx, hy);
  }
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.2)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i <= 360; i++) {
    const angle = i / 360 * Math.PI * 2;
    const waveR = 560 + Math.sin(i * 0.12) * 35 + Math.sin(i * 0.05) * 20;
    const px = cx + Math.cos(angle) * waveR;
    const py = cy + Math.sin(angle) * waveR;
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
  }
  ctx.stroke();
  for (let i = 0; i < 20; i++) {
    const angle = i / 20 * Math.PI * 2;
    const isMajor = i % 5 === 0;
    ctx.strokeStyle = `rgba(0, 0, 0, ${isMajor ? 0.18 : 0.06})`;
    ctx.lineWidth = isMajor ? 1.5 : 0.7;
    ctx.setLineDash(isMajor ? [10, 14] : [4, 10]);
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(angle) * 200, cy + Math.sin(angle) * 200);
    ctx.lineTo(cx + Math.cos(angle) * 850, cy + Math.sin(angle) * 850);
    ctx.stroke();
  }
  ctx.setLineDash([]);
  for (let i = 0; i < 28; i++) {
    const angle = i / 28 * Math.PI * 2;
    const pr = 430;
    const px = cx + Math.cos(angle) * pr;
    const py = cy + Math.sin(angle) * pr;
    ctx.fillStyle = `rgba(0, 0, 0, ${0.2 + (i % 4 === 0 ? 0.3 : 0)})`;
    ctx.beginPath();
    ctx.arc(px, py, i % 4 === 0 ? 8 : 4, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.strokeStyle = "rgba(0, 0, 0, 0.2)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(cx - 550, cy + 130);
  ctx.lineTo(cx + 550, cy + 130);
  ctx.stroke();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.1)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx - 480, cy + 320);
  ctx.lineTo(cx + 480, cy + 320);
  ctx.stroke();
  const crossPos = [
    [cx - 520, cy - 250],
    [cx + 500, cy - 270],
    [cx - 500, cy + 400],
    [cx + 520, cy + 420],
    [cx - 200, cy - 480],
    [cx + 200, cy + 480]
  ];
  crossPos.forEach(([x, y]) => {
    ctx.strokeStyle = "rgba(0, 0, 0, 0.25)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x - 18, y);
    ctx.lineTo(x + 18, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y - 18);
    ctx.lineTo(x, y + 18);
    ctx.stroke();
  });
  ctx.restore();
  ctx.fillStyle = "#000000";
  ctx.font = '900 225px "Syne", "Inter", sans-serif';
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("\xD8NYX", cx, cy - 110);
  ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
  ctx.font = '500 28px "Inter", sans-serif';
  ctx.fillText("S  U  B  V  E  R  S  E", cx, cy - 5);
  ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
  ctx.font = '600 17px "Inter", sans-serif';
  ctx.fillText("\xD8X \u2014 001  \xB7  OBVERSE", cx, cy + 45);
  ctx.fillStyle = "rgba(0, 0, 0, 0.75)";
  ctx.font = '800 22px "Syne", sans-serif';
  ctx.fillText("SIDE B", cx, cy + 370);
  ctx.fillStyle = "rgba(0, 0, 0, 0.2)";
  ctx.font = '400 14px "Inter", sans-serif';
  ctx.fillText("\u2117 2024 \xD8NYX FREQUENCY \xB7 ALL RIGHTS RESERVED", cx, cy + 480);
  ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
  ctx.font = '700 16px "Inter", sans-serif';
  ctx.save();
  ctx.translate(cx + 620, cy);
  ctx.rotate(Math.PI / 2);
  ctx.fillText("33\u2153 RPM", 0, 0);
  ctx.restore();
  ctx.save();
  ctx.translate(cx - 620, cy);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("STEREO", 0, 0);
  ctx.restore();
  drawArcText(ctx, cx, cy, "VOID  SPECTRUM", 820, -90, 0.055, 16, "rgba(0,0,0,0.25)", false);
  drawArcText(ctx, cx, cy, "WAVEFORM \xB7 DECAY \xB7 STATIC", 820, 90, 0.042, 13, "rgba(0,0,0,0.18)", true);
  drawSpindleHole(ctx, cx, cy);
  drawEdgeWear(ctx, cx, cy, R, rand);
  return new THREE.CanvasTexture(c);
}
var labelTexture = createStickerTexture();
var bSideLabelTexture = createBSideStickerTexture();
function createStickerNormalMap() {
  const size = 1024;
  const c = document.createElement("canvas");
  c.width = size;
  c.height = size;
  const ctx = c.getContext("2d");
  const cx = size / 2, cy = size / 2;
  const rand = seededRandom(99);
  ctx.fillStyle = "rgb(128,128,255)";
  ctx.fillRect(0, 0, size, size);
  const imageData = ctx.getImageData(0, 0, size, size);
  const data = imageData.data;
  for (let i = 0; i < data.length; i += 4) {
    const px = i / 4 % size;
    const py = Math.floor(i / 4 / size);
    const dx = px - cx, dy = py - cy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > size / 2) continue;
    data[i] = 128 + (rand() - 0.5) * 12;
    data[i + 1] = 128 + (rand() - 0.5) * 12;
  }
  ctx.putImageData(imageData, 0, 0);
  for (let i = 0; i < 8; i++) {
    const angle = rand() * Math.PI * 2;
    const r = rand() * (size * 0.35);
    const sx = cx + Math.cos(angle) * r, sy = cy + Math.sin(angle) * r;
    const len = 40 + rand() * 150;
    const dir = rand() * Math.PI * 2;
    const wave = (rand() - 0.5) * 30;
    ctx.strokeStyle = `rgb(${128 + Math.round(wave)},128,255)`;
    ctx.lineWidth = rand() * 1.5 + 0.5;
    ctx.globalAlpha = 0.3 + rand() * 0.3;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(dir) * len, sy + Math.sin(dir) * len);
    ctx.stroke();
  }
  for (let i = 0; i < 120; i++) {
    const angle = rand() * Math.PI * 2;
    const dist = size / 2 - 20 - rand() * 40;
    const px = cx + Math.cos(angle) * dist, py = cy + Math.sin(angle) * dist;
    const wave = (rand() - 0.5) * 40;
    ctx.fillStyle = `rgb(${128 + Math.round(wave)},${128 + Math.round((rand() - 0.5) * 20)},255)`;
    ctx.globalAlpha = 0.3 + rand() * 0.4;
    ctx.beginPath();
    ctx.arc(px, py, rand() * 6 + 2, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  return new THREE.CanvasTexture(c);
}
var labelNormTex = createStickerNormalMap();
var labelMat = new THREE.MeshPhysicalMaterial({
  map: labelTexture,
  normalMap: labelNormTex,
  normalScale: new THREE.Vector2(0.15, 0.15),
  metalness: 0,
  roughness: 0.5,
  envMapIntensity: 0.4,
  clearcoat: 0.1,
  clearcoatRoughness: 0.4,
  iridescence: 0.35,
  iridescenceIOR: 1.8,
  iridescenceThicknessRange: [100, 400],
  specularIntensity: 0.3,
  specularColor: new THREE.Color(16772829),
  polygonOffset: true,
  polygonOffsetFactor: -1,
  polygonOffsetUnits: -1
});
var label = new THREE.Mesh(labelGeo, labelMat);
label.rotation.x = -Math.PI / 2;
label.position.y = 65e-4;
label.name = "vinylLabel";
vinylGroup.add(label);
var bSideLabelGeo = new THREE.CircleGeometry(0.5, 64);
var bSideLabelMat = new THREE.MeshPhysicalMaterial({
  map: bSideLabelTexture,
  normalMap: labelNormTex,
  normalScale: new THREE.Vector2(0.15, 0.15),
  metalness: 0,
  roughness: 0.55,
  envMapIntensity: 0.4,
  clearcoat: 0.1,
  clearcoatRoughness: 0.4,
  iridescence: 0.4,
  iridescenceIOR: 1.9,
  iridescenceThicknessRange: [100, 500],
  specularIntensity: 0.3,
  specularColor: new THREE.Color(13426175),
  polygonOffset: true,
  polygonOffsetFactor: -1,
  polygonOffsetUnits: -1
});
var bSideLabel = new THREE.Mesh(bSideLabelGeo, bSideLabelMat);
bSideLabel.rotation.x = Math.PI / 2;
bSideLabel.position.y = -65e-4;
bSideLabel.name = "vinylLabelBSide";
vinylGroup.add(bSideLabel);
var holeGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.02, 16);
var holeMat = new THREE.MeshStandardMaterial({ color: 0 });
var hole = new THREE.Mesh(holeGeo, holeMat);
hole.name = "spindleHole";
vinylGroup.add(hole);
vinylGroup.scale.setScalar(settings.scale);
vinylGroup.rotation.set(settings.rotX, 0, settings.rotZ);
vinylGroup.position.set(
  settings.posX + settings.offsetX,
  settings.posY + settings.offsetY,
  settings.posZ + settings.offsetZ
);
var spinPivot = new THREE.Group();
spinPivot.name = "spinPivot";
vinylGroup.remove(disc);
vinylGroup.remove(scratchDisc);
vinylGroup.remove(label);
vinylGroup.remove(bSideLabel);
vinylGroup.remove(hole);
spinPivot.add(disc);
spinPivot.add(scratchDisc);
spinPivot.add(label);
spinPivot.add(bSideLabel);
spinPivot.add(hole);
vinylGroup.add(spinPivot);
spinPivot.rotation.y = settings.rotY;
videoTexture.repeat.x = settings.reflZoom;
videoTexture.repeat.y = -settings.reflZoom;
videoTexture.offset.x = -(settings.reflZoom - 1) / 2;
videoTexture.offset.y = 1 + (settings.reflZoom - 1) / 2;
blurTexture.repeat.x = settings.reflZoom;
blurTexture.repeat.y = -settings.reflZoom;
blurTexture.offset.x = -(settings.reflZoom - 1) / 2;
blurTexture.offset.y = 1 + (settings.reflZoom - 1) / 2;
var reflectiveMaterials = [discMat, labelMat, bSideLabelMat, scratchMat];
var mouseX = 0;
var mouseY = 0;
var targetMouseX = 0;
var targetMouseY = 0;
var orbitTiltX = 0;
var orbitTiltZ = 0;
var ORBIT_STRENGTH = 0.15;
var ORBIT_LERP = 0.03;
window.addEventListener("mousemove", (e) => {
  targetMouseX = (e.clientX / window.innerWidth - 0.5) * 2;
  targetMouseY = (e.clientY / window.innerHeight - 0.5) * 2;
});
var raycaster = new THREE.Raycaster();
var pointerNDC = new THREE.Vector2();
var isDragging = false;
var dragPrevAngle = 0;
var scratchVelocity = 0;
var scratchOffset = 0;
var isScratchActive = false;
var SCRATCH_SENSITIVITY = 2;
var SCRATCH_FRICTION = 0.92;
function getVinylScreenCenter() {
  const worldPos = new THREE.Vector3();
  vinylGroup.getWorldPosition(worldPos);
  const projected = worldPos.clone().project(camera);
  const rect = renderer.domElement.getBoundingClientRect();
  return {
    x: (projected.x * 0.5 + 0.5) * rect.width + rect.left,
    y: (-projected.y * 0.5 + 0.5) * rect.height + rect.top
  };
}
function hitTestVinyl(e) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointerNDC.x = (e.clientX - rect.left) / rect.width * 2 - 1;
  pointerNDC.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointerNDC, camera);
  const hits = raycaster.intersectObjects([disc, label, bSideLabel, scratchDisc], false);
  return hits.length > 0;
}
function getScreenAngle(e) {
  const center = getVinylScreenCenter();
  return Math.atan2(e.clientY - center.y, e.clientX - center.x);
}
renderer.domElement.style.pointerEvents = "auto";
renderer.domElement.style.cursor = "grab";
var dragFrozenRotX = 0;
var dragFrozenRotZ = 0;
var dragFrozenRotY = 0;
var dragFrozenPosX = 0;
var dragFrozenPosY = 0;
var dragFrozenPosZ = 0;
var dragFrozenScale = 1;
var dragBaseSpinY = 0;
var dragFrozenLookAtX = 0;
var dragFrozenLookAtY = 0;
var dragFrozenLookAtZ = 0;
renderer.domElement.addEventListener("pointerdown", (e) => {
  if (!hitTestVinyl(e)) return;
  isDragging = true;
  isScratchActive = true;
  dragPrevAngle = getScreenAngle(e);
  currentSpinY += scratchOffset;
  scratchOffset = 0;
  scratchVelocity = 0;
  dragFrozenRotX = vinylGroup.rotation.x;
  dragFrozenRotZ = vinylGroup.rotation.z;
  dragFrozenRotY = settings.rotY;
  dragFrozenPosX = vinylGroup.position.x;
  dragFrozenPosY = vinylGroup.position.y;
  dragFrozenPosZ = vinylGroup.position.z;
  dragFrozenScale = settings.scale;
  dragBaseSpinY = spinPivot.rotation.y;
  dragFrozenLookAtX = settings.posX;
  dragFrozenLookAtY = settings.posY;
  dragFrozenLookAtZ = settings.posZ;
  renderer.domElement.setPointerCapture(e.pointerId);
  renderer.domElement.style.cursor = "grabbing";
  e.preventDefault();
});
renderer.domElement.addEventListener("pointermove", (e) => {
  if (!isDragging) {
    renderer.domElement.style.cursor = hitTestVinyl(e) ? "grab" : "default";
    return;
  }
  const currentAngle = getScreenAngle(e);
  let delta = currentAngle - dragPrevAngle;
  if (delta > Math.PI) delta -= Math.PI * 2;
  if (delta < -Math.PI) delta += Math.PI * 2;
  const mapped = -delta * SCRATCH_SENSITIVITY;
  scratchVelocity = mapped;
  scratchOffset += mapped;
  dragPrevAngle = currentAngle;
});
renderer.domElement.addEventListener("pointerup", (e) => {
  if (!isDragging) return;
  isDragging = false;
  currentSpinY = dragBaseSpinY + scratchOffset - settings.rotY - scratchOffset;
  renderer.domElement.releasePointerCapture(e.pointerId);
  renderer.domElement.style.cursor = "grab";
});
renderer.domElement.addEventListener("pointercancel", () => {
  isDragging = false;
  renderer.domElement.style.cursor = "default";
});
var MUSIC_URL = "https://rrzvgzjttmyseqsmmyvn.supabase.co/storage/v1/object/sign/attachments/5a11113d-9132-449e-b7e4-84acda40e43b/generated-audio/e4598hkslv4-1776361634520-vkke.mp3?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV8xMjY1MWQ4My04ODE0LTQ3NzMtOGRlNS00MzliNDBkODY2NmYiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJhdHRhY2htZW50cy81YTExMTEzZC05MTMyLTQ0OWUtYjdlNC04NGFjZGE0MGU0M2IvZ2VuZXJhdGVkLWF1ZGlvL2U0NTk4aGtzbHY0LTE3NzYzNjE2MzQ1MjAtdmtrZS5tcDMiLCJpYXQiOjE3NzYzNjE2MzUsImV4cCI6MjA5MTcyMTYzNX0.a-CNyjuFxqWOEE5Nap8RANW6xbYoQF2VH8RA3ie6ri0";
var RPM_33 = 33 + 1 / 3;
var BASE_RAD_PER_SEC = RPM_33 / 60 * Math.PI * 2;
var ASSUMED_FPS = 60;
var BASE_RAD_PER_FRAME = BASE_RAD_PER_SEC / ASSUMED_FPS;
var INERTIA_BRAKE = 0.035;
var INERTIA_MOTOR = 0.07;
var INERTIA_SCRATCH = 0.22;
var RATE_MAX = 4;
var RATE_IDLE = 1;
var LPF_FREQ_MAX = 22e3;
var LPF_FREQ_MIN = 180;
var LPF_Q_NORMAL = 0.707;
var LPF_Q_SCRATCH = 2.5;
var LPF_LERP = 0.06;
var SCRATCH_MID_FREQ = 1800;
var SCRATCH_MID_GAIN = 6;
var VOL_BASE = 0.5;
var VOL_MIN = 0.04;
var WOW_RATE = 0.4;
var WOW_DEPTH = 15e-4;
var FLUTTER_RATE = 6.5;
var FLUTTER_DEPTH = 4e-4;
var CRACKLE_VOL_SLOW = 0.12;
var CRACKLE_VOL_FAST = 0.02;
var CRACKLE_VOL_STOP = 0;
var NEEDLE_VOL_MAX = 0.025;
var audioCtx = null;
var musicGain = null;
var masterGain = null;
var musicLPF = null;
var scratchMidEQ = null;
var crackleGain = null;
var crackleSource = null;
var crackleFilter = null;
var needleGain = null;
var needleSource = null;
var needleFilter = null;
var musicBuffer = null;
var activeSource = null;
var musicReady = false;
var audioInitialized = false;
var virtualPlayhead = 0;
var lastSourceStartTime = 0;
var lastSourceOffset = 0;
var lastSourceRate = 1;
var sourceIsPlaying = false;
var prevSpinY = 0;
var smoothedRate = RATE_IDLE;
var smoothedLPFFreq = LPF_FREQ_MAX;
var smoothedLPFQ = LPF_Q_NORMAL;
var smoothedMidGain = 0;
var wowPhase = 0;
var flutterPhase = 0;
function createNoiseBuffer(ctx, duration, type) {
  const sr = ctx.sampleRate;
  const len = Math.floor(sr * duration);
  const buf = ctx.createBuffer(1, len, sr);
  const data = buf.getChannelData(0);
  if (type === "crackle") {
    for (let i = 0; i < len; i++) {
      const r = Math.random();
      if (r > 0.997) {
        const amp = 0.3 + Math.random() * 0.7;
        const clickLen = Math.floor(sr * (2e-4 + Math.random() * 1e-3));
        for (let j = 0; j < clickLen && i + j < len; j++) {
          data[i + j] = (Math.random() * 2 - 1) * amp * (1 - j / clickLen);
        }
        i += Math.floor(sr * 2e-3);
      } else if (r > 0.993) {
        data[i] = (Math.random() * 2 - 1) * 0.15;
      } else {
        data[i] = (Math.random() * 2 - 1) * 8e-3;
      }
    }
  } else {
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (let i = 0; i < len; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.969 * b2 + white * 0.153852;
      b3 = 0.8665 * b3 + white * 0.3104856;
      b4 = 0.55 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.016898;
      data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.06;
      b6 = white * 0.115926;
    }
  }
  return buf;
}
var reversedBuffer = null;
function getReversedBuffer() {
  if (reversedBuffer) return reversedBuffer;
  if (!musicBuffer) return null;
  const nCh = musicBuffer.numberOfChannels;
  const len = musicBuffer.length;
  const sr = musicBuffer.sampleRate;
  reversedBuffer = audioCtx.createBuffer(nCh, len, sr);
  for (let ch = 0; ch < nCh; ch++) {
    const src = musicBuffer.getChannelData(ch);
    const dst = reversedBuffer.getChannelData(ch);
    for (let i = 0; i < len; i++) {
      dst[i] = src[len - 1 - i];
    }
  }
  return reversedBuffer;
}
var currentDirection = 1;
function startMusicSource(offset, rate) {
  if (!audioCtx || !musicBuffer) return;
  if (activeSource) {
    try {
      activeSource.stop();
    } catch (e) {
    }
    activeSource.disconnect();
    activeSource = null;
  }
  const dur = musicBuffer.duration;
  const isReverse = rate < 0;
  const absRate = Math.max(Math.abs(rate), 1e-3);
  let useBuffer, safeOffset;
  if (isReverse) {
    useBuffer = getReversedBuffer();
    if (!useBuffer) return;
    const fwdOffset = (offset % dur + dur) % dur;
    safeOffset = ((dur - fwdOffset) % dur + dur) % dur;
    currentDirection = -1;
  } else {
    useBuffer = musicBuffer;
    safeOffset = (offset % dur + dur) % dur;
    currentDirection = 1;
  }
  const src = audioCtx.createBufferSource();
  src.buffer = useBuffer;
  src.loop = true;
  src.loopStart = 0;
  src.loopEnd = dur;
  src.playbackRate.value = absRate;
  src.connect(scratchMidEQ);
  src.start(0, safeOffset);
  activeSource = src;
  sourceIsPlaying = true;
  lastSourceStartTime = audioCtx.currentTime;
  lastSourceOffset = safeOffset;
  lastSourceRate = absRate;
}
function getPlayhead() {
  if (!activeSource || !sourceIsPlaying || !musicBuffer) return virtualPlayhead;
  const elapsed = audioCtx.currentTime - lastSourceStartTime;
  const dur = musicBuffer.duration;
  const rawPos = ((lastSourceOffset + elapsed * lastSourceRate) % dur + dur) % dur;
  if (currentDirection === -1) {
    return ((dur - rawPos) % dur + dur) % dur;
  }
  return rawPos;
}
function initAudio() {
  if (audioCtx) return;
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  } catch (err) {
    console.warn("AudioContext unavailable:", err);
    return;
  }
  masterGain = audioCtx.createGain();
  masterGain.gain.value = 1;
  masterGain.connect(audioCtx.destination);
  scratchMidEQ = audioCtx.createBiquadFilter();
  scratchMidEQ.type = "peaking";
  scratchMidEQ.frequency.value = SCRATCH_MID_FREQ;
  scratchMidEQ.Q.value = 1.5;
  scratchMidEQ.gain.value = 0;
  musicLPF = audioCtx.createBiquadFilter();
  musicLPF.type = "lowpass";
  musicLPF.frequency.value = LPF_FREQ_MAX;
  musicLPF.Q.value = LPF_Q_NORMAL;
  musicGain = audioCtx.createGain();
  musicGain.gain.value = VOL_BASE;
  scratchMidEQ.connect(musicLPF);
  musicLPF.connect(musicGain);
  musicGain.connect(masterGain);
  const crackleBuf = createNoiseBuffer(audioCtx, 4, "crackle");
  crackleSource = audioCtx.createBufferSource();
  crackleSource.buffer = crackleBuf;
  crackleSource.loop = true;
  crackleFilter = audioCtx.createBiquadFilter();
  crackleFilter.type = "bandpass";
  crackleFilter.frequency.value = 3e3;
  crackleFilter.Q.value = 0.8;
  crackleGain = audioCtx.createGain();
  crackleGain.gain.value = CRACKLE_VOL_FAST;
  crackleSource.connect(crackleFilter);
  crackleFilter.connect(crackleGain);
  crackleGain.connect(masterGain);
  crackleSource.start(0);
  const needleBuf = createNoiseBuffer(audioCtx, 3, "hiss");
  needleSource = audioCtx.createBufferSource();
  needleSource.buffer = needleBuf;
  needleSource.loop = true;
  needleFilter = audioCtx.createBiquadFilter();
  needleFilter.type = "highpass";
  needleFilter.frequency.value = 4e3;
  needleFilter.Q.value = 0.5;
  needleGain = audioCtx.createGain();
  needleGain.gain.value = NEEDLE_VOL_MAX;
  needleSource.connect(needleFilter);
  needleFilter.connect(needleGain);
  needleGain.connect(masterGain);
  needleSource.start(0);
  fetch(MUSIC_URL).then((r) => r.arrayBuffer()).then((ab) => audioCtx.decodeAudioData(ab)).then((decoded) => {
    musicBuffer = decoded;
    musicReady = true;
    virtualPlayhead = 0;
    startMusicSource(0, 1);
  }).catch((err) => console.warn("Music decode error:", err));
}
function ensureAudio() {
  if (audioInitialized) return;
  audioInitialized = true;
  initAudio();
}
function autoPlayOnInteraction() {
  ensureAudio();
  if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
}
window.addEventListener("pointerdown", autoPlayOnInteraction, { once: true });
window.addEventListener("keydown", autoPlayOnInteraction, { once: true });
window.addEventListener("scroll", autoPlayOnInteraction, { once: true, passive: true });
var RATE_CHANGE_THRESHOLD = 0.04;
var RATE_CHANGE_INTERVAL = 3;
var framesSinceRestart = 0;
function updatePlatterAudio() {
  if (!musicReady || !audioCtx) return;
  const dt = 1 / 60;
  framesSinceRestart++;
  const fxActive = isDragging || isScratchActive;
  const currentSpinRot = spinPivot.rotation.y;
  let deltaRad = currentSpinRot - prevSpinY;
  prevSpinY = currentSpinRot;
  if (deltaRad > Math.PI) deltaRad -= Math.PI * 2;
  if (deltaRad < -Math.PI) deltaRad += Math.PI * 2;
  if (fxActive) {
    const perFrameBase = settings.spinSpeed || BASE_RAD_PER_FRAME;
    let targetRate;
    if (perFrameBase > 1e-5) {
      targetRate = deltaRad / perFrameBase;
    } else {
      targetRate = Math.abs(deltaRad) > 3e-4 ? deltaRad / BASE_RAD_PER_FRAME : 0;
    }
    targetRate = Math.max(-RATE_MAX, Math.min(targetRate, RATE_MAX));
    let inertia;
    if (isDragging) {
      inertia = INERTIA_SCRATCH;
    } else if (Math.abs(targetRate) < Math.abs(smoothedRate)) {
      inertia = INERTIA_BRAKE;
    } else {
      inertia = INERTIA_MOTOR;
    }
    smoothedRate += (targetRate - smoothedRate) * inertia;
    wowPhase += WOW_RATE * dt * Math.PI * 2;
    flutterPhase += FLUTTER_RATE * dt * Math.PI * 2;
    const wowMod = 1 + Math.sin(wowPhase) * WOW_DEPTH * Math.min(Math.abs(smoothedRate), 1) + Math.sin(flutterPhase) * FLUTTER_DEPTH * Math.min(Math.abs(smoothedRate), 1);
    const finalRate = smoothedRate * wowMod;
    if (activeSource && sourceIsPlaying) {
      const absNewRate = Math.max(Math.abs(finalRate), 1e-3);
      const newDirection = finalRate < -5e-3 ? -1 : finalRate > 5e-3 ? 1 : currentDirection;
      const dirFlipped = newDirection !== currentDirection;
      const bigShift = Math.abs(absNewRate - lastSourceRate) > RATE_CHANGE_THRESHOLD;
      if (dirFlipped || bigShift && framesSinceRestart > RATE_CHANGE_INTERVAL) {
        virtualPlayhead = getPlayhead();
        startMusicSource(virtualPlayhead, newDirection * absNewRate);
        framesSinceRestart = 0;
      } else {
        activeSource.playbackRate.setTargetAtTime(absNewRate, audioCtx.currentTime, 0.03);
        lastSourceRate = absNewRate;
      }
    }
    const absRate = Math.abs(smoothedRate);
    const lpfRatio = Math.min(absRate / RATE_IDLE, 1);
    const targetFreq = LPF_FREQ_MIN * Math.pow(LPF_FREQ_MAX / LPF_FREQ_MIN, lpfRatio);
    const prevLPFFreq = smoothedLPFFreq;
    smoothedLPFFreq += (targetFreq - smoothedLPFFreq) * LPF_LERP;
    const targetQ = isDragging ? LPF_Q_SCRATCH : LPF_Q_NORMAL;
    const prevLPFQ = smoothedLPFQ;
    smoothedLPFQ += (targetQ - smoothedLPFQ) * 0.08;
    if (musicLPF && (Math.abs(smoothedLPFFreq - prevLPFFreq) > 20 || Math.abs(smoothedLPFQ - prevLPFQ) > 0.02)) {
      musicLPF.frequency.setTargetAtTime(smoothedLPFFreq, audioCtx.currentTime, 0.02);
      musicLPF.Q.setTargetAtTime(smoothedLPFQ, audioCtx.currentTime, 0.02);
    }
    const targetMidGain = isDragging && absRate > 0.05 ? SCRATCH_MID_GAIN : 0;
    const prevMidGain = smoothedMidGain;
    smoothedMidGain += (targetMidGain - smoothedMidGain) * 0.1;
    if (scratchMidEQ && Math.abs(smoothedMidGain - prevMidGain) > 0.05) {
      scratchMidEQ.gain.setTargetAtTime(smoothedMidGain, audioCtx.currentTime, 0.02);
    }
    if (musicGain) {
      const volRatio = Math.min(absRate / RATE_IDLE, 1);
      const targetVol = VOL_MIN + (VOL_BASE - VOL_MIN) * volRatio;
      if (Math.abs(musicGain.gain.value - targetVol) > 0.01) {
        musicGain.gain.setTargetAtTime(targetVol, audioCtx.currentTime, 0.05);
      }
    }
    if (crackleGain) {
      let crackleVol;
      if (absRate < 0.02) {
        crackleVol = CRACKLE_VOL_STOP;
      } else if (absRate < 0.5) {
        const t = absRate / 0.5;
        crackleVol = CRACKLE_VOL_SLOW * (1 - t) + CRACKLE_VOL_FAST * t;
      } else {
        crackleVol = CRACKLE_VOL_FAST;
      }
      if (isDragging) crackleVol *= 2.5;
      const clampedCrackle = Math.min(crackleVol, 0.3);
      if (Math.abs(crackleGain.gain.value - clampedCrackle) > 5e-3) {
        crackleGain.gain.setTargetAtTime(clampedCrackle, audioCtx.currentTime, 0.04);
      }
    }
    if (crackleSource) {
      const crackleRate = Math.max(0.1, absRate * 1.2);
      if (Math.abs(crackleSource.playbackRate.value - crackleRate) > 0.02) {
        crackleSource.playbackRate.setTargetAtTime(crackleRate, audioCtx.currentTime, 0.05);
      }
    }
    if (needleGain) {
      const needleVol = absRate > 0.02 ? NEEDLE_VOL_MAX * Math.min(absRate, 1) : 0;
      if (Math.abs(needleGain.gain.value - needleVol) > 2e-3) {
        needleGain.gain.setTargetAtTime(needleVol, audioCtx.currentTime, 0.04);
      }
    }
  } else {
    smoothedRate += (RATE_IDLE - smoothedRate) * 0.1;
    if (activeSource && sourceIsPlaying) {
      if (currentDirection !== 1) {
        virtualPlayhead = getPlayhead();
        startMusicSource(virtualPlayhead, 1);
        framesSinceRestart = 0;
      } else if (Math.abs(lastSourceRate - 1) > 0.01) {
        activeSource.playbackRate.setTargetAtTime(1, audioCtx.currentTime, 0.08);
        lastSourceRate = 1;
      }
    }
    const cleanNeedsUpdate = Math.abs(smoothedLPFFreq - LPF_FREQ_MAX) > 50 || Math.abs(smoothedLPFQ - LPF_Q_NORMAL) > 0.02 || Math.abs(smoothedMidGain) > 0.1;
    if (cleanNeedsUpdate) {
      smoothedLPFFreq += (LPF_FREQ_MAX - smoothedLPFFreq) * 0.1;
      smoothedLPFQ += (LPF_Q_NORMAL - smoothedLPFQ) * 0.1;
      smoothedMidGain += (0 - smoothedMidGain) * 0.1;
      if (musicLPF) {
        musicLPF.frequency.setTargetAtTime(smoothedLPFFreq, audioCtx.currentTime, 0.05);
        musicLPF.Q.setTargetAtTime(smoothedLPFQ, audioCtx.currentTime, 0.05);
      }
      if (scratchMidEQ) {
        scratchMidEQ.gain.setTargetAtTime(smoothedMidGain, audioCtx.currentTime, 0.05);
      }
    }
    if (musicGain && Math.abs(musicGain.gain.value - VOL_BASE) > 0.01) {
      musicGain.gain.setTargetAtTime(VOL_BASE, audioCtx.currentTime, 0.08);
    }
    if (crackleGain && crackleGain.gain.value > 1e-3) crackleGain.gain.setTargetAtTime(0, audioCtx.currentTime, 0.1);
    if (needleGain && needleGain.gain.value > 1e-3) needleGain.gain.setTargetAtTime(0, audioCtx.currentTime, 0.1);
  }
}
var statusEl = document.getElementById("camera-status");
var camPreview = document.getElementById("camera-preview");
var camPreviewVideo = document.getElementById("camera-preview-video");
navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 60, min: 30 } } }).then((stream) => {
  video.srcObject = stream;
  video.play();
  camPreviewVideo.srcObject = stream;
  camPreviewVideo.play();
  camPreview.classList.add("active");
  statusEl.textContent = "\u{1F3B5} Camera connected \u2014 reflections active";
  setTimeout(() => {
    statusEl.style.opacity = "0";
  }, 3e3);
}).catch((err) => {
  console.warn("Camera not available:", err);
  statusEl.textContent = "\u26A0 Camera unavailable \u2014 using fallback reflections";
  setTimeout(() => {
    statusEl.style.opacity = "0";
  }, 4e3);
  const fallbackCanvas = document.createElement("canvas");
  fallbackCanvas.width = 512;
  fallbackCanvas.height = 512;
  const fCtx = fallbackCanvas.getContext("2d");
  const fGrad = fCtx.createLinearGradient(0, 0, 512, 512);
  fGrad.addColorStop(0, "#ddeeff");
  fGrad.addColorStop(0.3, "#bbccee");
  fGrad.addColorStop(0.6, "#99aadd");
  fGrad.addColorStop(1, "#7788cc");
  fCtx.fillStyle = fGrad;
  fCtx.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 100; i++) {
    fCtx.fillStyle = `rgba(255,255,255,${Math.random() * 0.5 + 0.1})`;
    fCtx.beginPath();
    fCtx.arc(Math.random() * 512, Math.random() * 512, Math.random() * 3, 0, Math.PI * 2);
    fCtx.fill();
  }
  envSphereMat.map = new THREE.CanvasTexture(fallbackCanvas);
  envSphereMat.needsUpdate = true;
});
var luminanceCanvas = document.createElement("canvas");
luminanceCanvas.width = 8;
luminanceCanvas.height = 8;
var luminanceCtx = luminanceCanvas.getContext("2d", { willReadFrequently: true });
var smoothLuminance = 0.5;
var latestLuminance = 0.5;
var luminanceReady = false;
function analyzeCameraLuminanceAsync() {
  if (!video.videoWidth) return;
  luminanceCtx.drawImage(video, 0, 0, 8, 8);
  const data = luminanceCtx.getImageData(0, 0, 8, 8).data;
  let totalLum = 0, count = 0;
  for (let i = 0; i < data.length; i += 16) {
    totalLum += 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
    count++;
  }
  latestLuminance = totalLum / (count * 255);
  luminanceReady = true;
}
if ("requestVideoFrameCallback" in HTMLVideoElement.prototype) {
  let onVideoFrame = function() {
    analyzeCameraLuminanceAsync();
    video.requestVideoFrameCallback(onVideoFrame);
  };
  video.requestVideoFrameCallback(onVideoFrame);
} else {
  setInterval(analyzeCameraLuminanceAsync, 500);
}
var sectionEls = [
  document.getElementById("section-hero"),
  document.getElementById("section-artists"),
  document.getElementById("section-contact")
];
var dots = document.querySelectorAll(".section-dot");
dots.forEach((dot) => {
  dot.addEventListener("click", () => {
    const targetId = dot.dataset.section;
    document.getElementById(targetId).scrollIntoView({ behavior: "smooth" });
  });
});
function getScrollProgress() {
  const scrollY = window.scrollY;
  const docH = document.documentElement.scrollHeight - window.innerHeight;
  if (docH <= 0) return 0;
  const raw = scrollY / docH;
  return raw * (keyframes.length - 1);
}
var lastGrooveCount = settings.grooveCount;
var lastGrooveDepth = settings.grooveDepth;
var lastGrooveWidth = settings.grooveWidth;
var lastScratchDensity = settings.scratchDensity;
var lastScratchDepth = settings.scratchDepth;
var lastScratchLength = settings.scratchLength;
var lastScratchArcMul = Math.round(settings.scratchArcMul * 10);
var lastScratchHairMul = Math.round(settings.scratchHairMul * 10);
function lerp(a, b, t) {
  return a + (b - a) * t;
}
function applyScrollKeyframe(progress) {
  const idx = Math.floor(progress);
  const t = progress - idx;
  const kfA = keyframes[Math.min(idx, keyframes.length - 1)];
  const kfB = keyframes[Math.min(idx + 1, keyframes.length - 1)];
  const ease = t * t * (3 - 2 * t);
  for (let i = 0; i < KF_PROPS.length; i++) {
    const k = KF_PROPS[i];
    settings[k] = lerp(kfA[k], kfB[k], ease);
  }
  discMat.roughness = settings.vinylRoughness;
  discMat.metalness = settings.vinylMetalness;
  discMat.clearcoat = settings.vinylClearcoat;
  discMat.clearcoatRoughness = settings.feedRoughness;
  vinylGroup.scale.setScalar(settings.scale);
  feedBlurAmount = settings.feedBlur;
  feedBrightnessVal = settings.feedBrightness;
  for (let mi = 0; mi < reflectiveMaterials.length; mi++) reflectiveMaterials[mi].envMapIntensity = settings.envIntensity;
  const z = settings.reflZoom;
  videoTexture.repeat.x = z;
  videoTexture.repeat.y = -z;
  videoTexture.offset.x = -(z - 1) / 2;
  videoTexture.offset.y = 1 + (z - 1) / 2;
  blurTexture.repeat.x = z;
  blurTexture.repeat.y = -z;
  blurTexture.offset.x = -(z - 1) / 2;
  blurTexture.offset.y = 1 + (z - 1) / 2;
  scratchMat.opacity = settings.scratchOpacity;
  scratchMat.normalScale.set(settings.scratchNormalScale, settings.scratchNormalScale);
}
var isScrolling = false;
var scrollSettleTimer = null;
window.addEventListener("scroll", () => {
  isScrolling = true;
  clearTimeout(scrollSettleTimer);
  scrollSettleTimer = setTimeout(() => {
    isScrolling = false;
  }, 200);
}, { passive: true });
function updateActiveDot(progress) {
  const activeIdx = Math.round(progress);
  dots.forEach((d, i) => {
    d.classList.toggle("active", i === activeIdx);
  });
}
var panel = document.getElementById("settings-panel");
var settingsOpen = false;
var manualOverride = false;
window.addEventListener("keydown", (e) => {
  if (e.key === "s" || e.key === "S") {
    if (document.activeElement && document.activeElement.tagName === "INPUT") return;
    settingsOpen = !settingsOpen;
    panel.classList.toggle("visible", settingsOpen);
    if (settingsOpen) {
      manualOverride = true;
      syncSlidersFromSettings();
    } else {
      manualOverride = false;
    }
  }
});
function syncKfSlidersFromKeyframe(kfIdx) {
  const kf = keyframes[kfIdx];
  KF_EDITABLE_PROPS.forEach((k) => {
    const slider = document.getElementById("kf-" + k);
    const valEl = document.getElementById("kf-" + k + "-val");
    if (!slider || !valEl) return;
    slider.value = kf[k];
    const step = parseFloat(slider.step) || 1;
    const decimals = step < 1 ? step < 0.1 ? step < 0.01 ? 3 : 2 : 1 : 0;
    valEl.textContent = parseFloat(kf[k]).toFixed(decimals);
  });
}
function syncGlobalSlidersFromSettings() {
  const globalKeys = KF_PROPS.filter((k) => !KF_EDITABLE_PROPS.includes(k));
  globalKeys.forEach((k) => {
    const slider = document.getElementById(k);
    const valEl = document.getElementById(k + "-val");
    if (!slider || !valEl) return;
    slider.value = settings[k];
    const step = parseFloat(slider.step) || 1;
    const decimals = step < 1 ? step < 0.1 ? step < 0.01 ? 3 : 2 : 1 : 0;
    valEl.textContent = parseFloat(settings[k]).toFixed(decimals);
  });
}
function syncSlidersFromSettings() {
  syncKfSlidersFromKeyframe(activeKfTab);
  syncGlobalSlidersFromSettings();
}
function wireSlider(id, callback) {
  const slider = document.getElementById(id);
  const valEl = document.getElementById(id + "-val");
  if (!slider || !valEl) return;
  slider.addEventListener("input", () => {
    const v = parseFloat(slider.value);
    const step = parseFloat(slider.step) || 1;
    const decimals = step < 1 ? step < 0.1 ? step < 0.01 ? 3 : 2 : 1 : 0;
    valEl.textContent = v.toFixed(decimals);
    callback(v);
  });
}
function wireKfSlider(prop) {
  const id = "kf-" + prop;
  wireSlider(id, (v) => {
    keyframes[activeKfTab][prop] = v;
    settings[prop] = v;
    if (prop === "scale") vinylGroup.scale.setScalar(v);
    else if (prop === "vinylRoughness") discMat.roughness = v;
    else if (prop === "vinylMetalness") discMat.metalness = v;
    else if (prop === "vinylClearcoat") discMat.clearcoat = v;
    else if (prop === "envIntensity") {
      for (let i = 0; i < reflectiveMaterials.length; i++) reflectiveMaterials[i].envMapIntensity = v;
    } else if (prop === "reflZoom") {
      videoTexture.repeat.x = v;
      videoTexture.repeat.y = -v;
      videoTexture.offset.x = -(v - 1) / 2;
      videoTexture.offset.y = 1 + (v - 1) / 2;
      blurTexture.repeat.x = v;
      blurTexture.repeat.y = -v;
      blurTexture.offset.x = -(v - 1) / 2;
      blurTexture.offset.y = 1 + (v - 1) / 2;
    } else if (prop === "feedRoughness") {
      discMat.clearcoatRoughness = v;
    } else if (prop === "feedBlur") feedBlurAmount = v;
    else if (prop === "feedBrightness") feedBrightnessVal = v;
  });
}
KF_EDITABLE_PROPS.forEach((prop) => wireKfSlider(prop));
function rebuildGrooveMaps() {
  const oldGN = grooveNormalTex, oldGR = grooveRoughTex;
  grooveNormalTex = generateGrooveNormalMap(settings.grooveCount, settings.grooveDepth, settings.grooveWidth);
  grooveRoughTex = generateGrooveRoughnessMap(settings.grooveCount);
  discMat.normalMap = grooveNormalTex;
  discMat.roughnessMap = grooveRoughTex;
  grooveNormalTex.needsUpdate = true;
  grooveRoughTex.needsUpdate = true;
  oldGN.dispose();
  oldGR.dispose();
}
wireSlider("grooveCount", (v) => {
  settings.grooveCount = Math.round(v);
  keyframes[activeKfTab].grooveCount = Math.round(v);
  rebuildGrooveMaps();
});
wireSlider("grooveDepth", (v) => {
  settings.grooveDepth = v;
  keyframes[activeKfTab].grooveDepth = v;
  rebuildGrooveMaps();
});
wireSlider("grooveWidth", (v) => {
  settings.grooveWidth = v;
  keyframes[activeKfTab].grooveWidth = v;
  rebuildGrooveMaps();
});
function rebuildScratchMaps() {
  const sp = getScratchParams();
  const oldSN = scratchNormalTex, oldSR = scratchRoughTex;
  scratchNormalTex = generateScratchNormalMap(settings.scratchDensity, settings.scratchDepth, settings.scratchLength, sp);
  scratchRoughTex = generateScratchRoughnessMap(settings.scratchDensity, settings.scratchLength, sp);
  scratchMat.normalMap = scratchNormalTex;
  scratchMat.normalScale.set(settings.scratchNormalScale, settings.scratchNormalScale);
  scratchMat.roughnessMap = scratchRoughTex;
  scratchMat.opacity = settings.scratchOpacity;
  scratchNormalTex.needsUpdate = true;
  scratchRoughTex.needsUpdate = true;
  oldSN.dispose();
  oldSR.dispose();
}
wireSlider("scratchDensity", (v) => {
  settings.scratchDensity = Math.round(v);
  keyframes[activeKfTab].scratchDensity = Math.round(v);
  rebuildScratchMaps();
});
wireSlider("scratchDepth", (v) => {
  settings.scratchDepth = v;
  keyframes[activeKfTab].scratchDepth = v;
  rebuildScratchMaps();
});
wireSlider("scratchLength", (v) => {
  settings.scratchLength = v;
  keyframes[activeKfTab].scratchLength = v;
  rebuildScratchMaps();
});
wireSlider("scratchOpacity", (v) => {
  settings.scratchOpacity = v;
  keyframes[activeKfTab].scratchOpacity = v;
  scratchMat.opacity = v;
});
wireSlider("scratchNormalScale", (v) => {
  settings.scratchNormalScale = v;
  keyframes[activeKfTab].scratchNormalScale = v;
  scratchMat.normalScale.set(v, v);
});
wireSlider("scratchArcMul", (v) => {
  settings.scratchArcMul = v;
  keyframes[activeKfTab].scratchArcMul = v;
  rebuildScratchMaps();
});
wireSlider("scratchHairMul", (v) => {
  settings.scratchHairMul = v;
  keyframes[activeKfTab].scratchHairMul = v;
  rebuildScratchMaps();
});
wireSlider("scratchCurveMul", (v) => {
  settings.scratchCurveMul = v;
  keyframes[activeKfTab].scratchCurveMul = v;
  rebuildScratchMaps();
});
wireSlider("scratchNickMul", (v) => {
  settings.scratchNickMul = v;
  keyframes[activeKfTab].scratchNickMul = v;
  rebuildScratchMaps();
});
wireSlider("scratchSweepMul", (v) => {
  settings.scratchSweepMul = v;
  keyframes[activeKfTab].scratchSweepMul = v;
  rebuildScratchMaps();
});
wireSlider("scratchSCurveMul", (v) => {
  settings.scratchSCurveMul = v;
  keyframes[activeKfTab].scratchSCurveMul = v;
  rebuildScratchMaps();
});
wireSlider("scratchClusterMul", (v) => {
  settings.scratchClusterMul = v;
  keyframes[activeKfTab].scratchClusterMul = v;
  rebuildScratchMaps();
});
wireSlider("scratchArcAlpha", (v) => {
  settings.scratchArcAlpha = v;
  keyframes[activeKfTab].scratchArcAlpha = v;
  rebuildScratchMaps();
});
wireSlider("scratchHairAlpha", (v) => {
  settings.scratchHairAlpha = v;
  keyframes[activeKfTab].scratchHairAlpha = v;
  rebuildScratchMaps();
});
wireSlider("scratchCurveAlpha", (v) => {
  settings.scratchCurveAlpha = v;
  keyframes[activeKfTab].scratchCurveAlpha = v;
  rebuildScratchMaps();
});
wireSlider("scratchNickAlpha", (v) => {
  settings.scratchNickAlpha = v;
  keyframes[activeKfTab].scratchNickAlpha = v;
  rebuildScratchMaps();
});
wireSlider("scratchSweepAlpha", (v) => {
  settings.scratchSweepAlpha = v;
  keyframes[activeKfTab].scratchSweepAlpha = v;
  rebuildScratchMaps();
});
var kfTabs = document.querySelectorAll(".kf-tab");
var kfSectionNames = ["Hero", "Artists", "Contact"];
function applyKfToPreview(kfIdx) {
  const kf = keyframes[kfIdx];
  KF_EDITABLE_PROPS.forEach((k) => {
    settings[k] = kf[k];
  });
  KF_PROPS.forEach((k) => {
    if (!KF_EDITABLE_PROPS.includes(k)) {
      settings[k] = kf[k];
    }
  });
  discMat.roughness = settings.vinylRoughness;
  discMat.metalness = settings.vinylMetalness;
  discMat.clearcoat = settings.vinylClearcoat;
  discMat.clearcoatRoughness = settings.feedRoughness;
  vinylGroup.scale.setScalar(settings.scale);
  feedBlurAmount = settings.feedBlur;
  feedBrightnessVal = settings.feedBrightness;
  reflectiveMaterials.forEach((m) => {
    m.envMapIntensity = settings.envIntensity;
  });
  const z = settings.reflZoom;
  videoTexture.repeat.x = z;
  videoTexture.repeat.y = -z;
  videoTexture.offset.x = -(z - 1) / 2;
  videoTexture.offset.y = 1 + (z - 1) / 2;
  blurTexture.repeat.x = z;
  blurTexture.repeat.y = -z;
  blurTexture.offset.x = -(z - 1) / 2;
  blurTexture.offset.y = 1 + (z - 1) / 2;
  rebuildGrooveMaps();
  rebuildScratchMaps();
}
kfTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    activeKfTab = parseInt(tab.dataset.kf);
    kfTabs.forEach((t, i) => t.classList.toggle("active", i === activeKfTab));
    syncKfSlidersFromKeyframe(activeKfTab);
    applyKfToPreview(activeKfTab);
    syncGlobalSlidersFromSettings();
    const sectionIds = ["section-hero", "section-artists", "section-contact"];
    const targetSection = document.getElementById(sectionIds[activeKfTab]);
    if (targetSection) targetSection.scrollIntoView({ behavior: "smooth" });
    showToast("Editing keyframe: " + kfSectionNames[activeKfTab]);
  });
});
var lastScrollY = 0;
var navHidden = false;
var navEl = document.querySelector(".nav");
var scrollHintEl = document.getElementById("scroll-hint");
var footerEl = document.querySelector(".site-footer");
window.addEventListener("scroll", () => {
  const currentScrollY = window.scrollY;
  const delta = currentScrollY - lastScrollY;
  if (delta > 5 && currentScrollY > 80) {
    if (!navHidden) {
      navEl.classList.add("nav-hidden");
      navHidden = true;
    }
  } else if (delta < -5) {
    if (navHidden) {
      navEl.classList.remove("nav-hidden");
      navHidden = false;
    }
  }
  if (scrollHintEl) {
    if (currentScrollY > 100) {
      scrollHintEl.classList.add("hidden");
    } else {
      scrollHintEl.classList.remove("hidden");
    }
  }
  lastScrollY = currentScrollY;
}, { passive: true });
var time = 0;
var currentSpinY = 0;
function animate() {
  time += 0.016;
  frameCount++;
  mouseX += (targetMouseX - mouseX) * 0.05;
  mouseY += (targetMouseY - mouseY) * 0.05;
  if (!manualOverride) {
    const progress = getScrollProgress();
    applyScrollKeyframe(progress);
    updateActiveDot(progress);
  }
  camera.position.x = 2.5 + mouseX * 0.3;
  camera.position.y = 1.5 + mouseY * -0.2;
  camera.position.z = 4.5;
  if (isDragging) {
    camera.lookAt(dragFrozenLookAtX, dragFrozenLookAtY, dragFrozenLookAtZ);
  } else {
    camera.lookAt(settings.posX, settings.posY, settings.posZ);
  }
  if (!isDragging) {
    const targetOrbitTiltX = -mouseY * ORBIT_STRENGTH;
    const targetOrbitTiltZ = mouseX * ORBIT_STRENGTH;
    orbitTiltX += (targetOrbitTiltX - orbitTiltX) * ORBIT_LERP;
    orbitTiltZ += (targetOrbitTiltZ - orbitTiltZ) * ORBIT_LERP;
  }
  let finalX, finalY, finalZ;
  if (isDragging) {
    finalX = dragFrozenPosX;
    finalY = dragFrozenPosY;
    finalZ = dragFrozenPosZ;
    vinylGroup.scale.setScalar(dragFrozenScale);
  } else {
    finalX = settings.posX + settings.offsetX;
    const bob = Math.sin(time * 0.6) * 0.08;
    finalY = settings.posY + settings.offsetY + bob;
    finalZ = settings.posZ + settings.offsetZ;
  }
  vinylGroup.position.set(finalX, finalY, finalZ);
  if (!isDragging && isScratchActive) {
    scratchVelocity *= SCRATCH_FRICTION;
    scratchOffset += scratchVelocity;
    if (Math.abs(scratchVelocity) < 3e-4) {
      currentSpinY += scratchOffset;
      scratchOffset = 0;
      scratchVelocity = 0;
      isScratchActive = false;
    }
  }
  updatePlatterAudio();
  if (!isDragging) {
    currentSpinY += settings.spinSpeed;
  }
  if (isDragging) {
    vinylGroup.rotation.x = dragFrozenRotX;
    vinylGroup.rotation.z = dragFrozenRotZ;
  } else {
    vinylGroup.rotation.x = settings.rotX + orbitTiltX;
    vinylGroup.rotation.z = settings.rotZ + orbitTiltZ;
  }
  if (isDragging) {
    spinPivot.rotation.y = dragBaseSpinY + scratchOffset;
  } else {
    spinPivot.rotation.y = settings.rotY + currentSpinY + scratchOffset;
  }
  envSphere.rotation.x = settings.hdrRotX;
  envSphere.rotation.y = settings.hdrRotY;
  envSphere.rotation.z = settings.hdrRotZ;
  if (frameCount % 2 === 0 && video.videoWidth) {
    if (feedBlurAmount > 0) {
      blurCtx.filter = `blur(${Math.round(feedBlurAmount * 20)}px) brightness(${feedBrightnessVal})`;
      blurCtx.drawImage(video, 0, 0, 256, 256);
      blurTexture.needsUpdate = true;
      envSphereMat.map = blurTexture;
    } else if (feedBrightnessVal !== 1) {
      blurCtx.filter = `brightness(${feedBrightnessVal})`;
      blurCtx.drawImage(video, 0, 0, 256, 256);
      blurTexture.needsUpdate = true;
      envSphereMat.map = blurTexture;
    } else {
      envSphereMat.map = videoTexture;
    }
  }
  const cubeInterval = isDragging || isScratchActive ? 2 : 4;
  if (frameCount % cubeInterval === 0) {
    vinylGroup.visible = false;
    cubeCamera.update(renderer, scene);
    vinylGroup.visible = true;
    pmremDirty = true;
  }
  if (pmremDirty && lastPmremFrame !== frameCount) {
    const newEnvMap = pmremGenerator.fromCubemap(cubeRenderTarget.texture).texture;
    if (filteredEnvMap) filteredEnvMap.dispose();
    filteredEnvMap = newEnvMap;
    scene.environment = filteredEnvMap;
    for (let i = 0; i < reflectiveMaterials.length; i++) {
      reflectiveMaterials[i].envMap = filteredEnvMap;
    }
    pmremDirty = false;
    lastPmremFrame = frameCount;
  }
  if (luminanceReady) {
    smoothLuminance += (latestLuminance - smoothLuminance) * 0.15;
    luminanceReady = false;
  }
  const lf = THREE.MathUtils.clamp(smoothLuminance, 0.05, 1);
  ambientLight.intensity = 1.2 * (0.5 + lf);
  directionalLight.intensity = 3 * (0.7 + (1 - lf) * 0.5);
  renderer.toneMappingExposure = 1.8 * (0.7 + lf * 0.6);
  rimLight.intensity = 0.8 * (0.8 + Math.sin(time * 2) * 0.2);
  if (frameCount % 3 === 0) {
    const holoPhase = time * 0.3;
    labelMat.iridescenceThicknessRange = [
      80 + Math.sin(holoPhase) * 50,
      400 + Math.cos(holoPhase * 0.7) * 100
    ];
    bSideLabelMat.iridescenceThicknessRange = [
      100 + Math.cos(holoPhase * 0.9) * 60,
      500 + Math.sin(holoPhase * 0.5) * 120
    ];
  }
  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);
var copyBtn = document.getElementById("copyJsonBtn");
if (copyBtn) {
  copyBtn.addEventListener("click", () => {
    const sectionNames = ["hero", "artists", "contact"];
    const kfExport = {};
    keyframes.forEach((kf, i) => {
      const entry = {};
      entry.position = { x: kf.posX, y: kf.posY, z: kf.posZ };
      entry.offset = { x: kf.offsetX, y: kf.offsetY, z: kf.offsetZ };
      entry.rotation = { x: kf.rotX, y: kf.rotY, z: kf.rotZ };
      entry.scale = kf.scale;
      entry.spinSpeed = kf.spinSpeed;
      entry.surface = {
        roughness: kf.vinylRoughness,
        metalness: kf.vinylMetalness,
        clearcoat: kf.vinylClearcoat,
        envIntensity: kf.envIntensity
      };
      entry.cameraFeed = {
        reflZoom: kf.reflZoom,
        roughness: kf.feedRoughness,
        blur: kf.feedBlur,
        brightness: kf.feedBrightness
      };
      entry.hdrOrientation = { x: kf.hdrRotX, y: kf.hdrRotY, z: kf.hdrRotZ };
      entry.grooves = { count: kf.grooveCount, depth: kf.grooveDepth, width: kf.grooveWidth };
      entry.scratches = {
        density: kf.scratchDensity,
        depth: kf.scratchDepth,
        length: kf.scratchLength,
        opacity: kf.scratchOpacity,
        normalScale: kf.scratchNormalScale,
        arcMul: kf.scratchArcMul,
        hairMul: kf.scratchHairMul,
        curveMul: kf.scratchCurveMul,
        nickMul: kf.scratchNickMul,
        sweepMul: kf.scratchSweepMul,
        sCurveMul: kf.scratchSCurveMul,
        clusterMul: kf.scratchClusterMul,
        arcAlpha: kf.scratchArcAlpha,
        hairAlpha: kf.scratchHairAlpha,
        curveAlpha: kf.scratchCurveAlpha,
        nickAlpha: kf.scratchNickAlpha,
        sweepAlpha: kf.scratchSweepAlpha
      };
      kfExport[sectionNames[i]] = entry;
    });
    const exportData = {
      _context: {
        description: "VYNL Records \u2014 vinyl keyframe animation data",
        sections: ["hero", "artists", "contact"],
        interpolation: "smoothstep (hermite)",
        trigger: "scroll position between sections"
      },
      keyframes: kfExport
    };
    const json = JSON.stringify(exportData, null, 2);
    navigator.clipboard.writeText(json).then(() => {
      copyBtn.textContent = "\u2713 COPIED";
      copyBtn.classList.add("copied");
      showToast("Settings + keyframes copied to clipboard");
      setTimeout(() => {
        copyBtn.textContent = "COPY AS JSON";
        copyBtn.classList.remove("copied");
      }, 2e3);
    }).catch(() => {
      const ta = document.createElement("textarea");
      ta.value = json;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      ;
      (document.getElementById("root") ?? document.body).appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      copyBtn.textContent = "\u2713 COPIED";
      copyBtn.classList.add("copied");
      showToast("Settings + keyframes copied to clipboard");
      setTimeout(() => {
        copyBtn.textContent = "COPY AS JSON";
        copyBtn.classList.remove("copied");
      }, 2e3);
    });
  });
}
function showToast(msg) {
  let toast = document.querySelector(".toast-msg");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast-msg";
    ;
    (document.getElementById("root") ?? document.body).appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
