// ═══════════════════════════════════════════════════════════════════════
// PHOSPHOR VIGIL — Shared CRT Post-Processing Pipeline
// ═══════════════════════════════════════════════════════════════════════
//
// A 4-pass post-processing chain: velocity-driven feedback trails,
// threshold-extracted bloom, box-blurred bloom, and a CRT composite with
// scanlines, chromatic aberration, subpixel shadow mask, vignette,
// phosphor glow, grain, and warm/green tint.
//
// Shaders ported verbatim from celescript.dev/experiments/3d-butterfly
// (ButterflyScene, chunk 128.64bb229c36552b0d). Every constant preserved.
//
// Usage (ES module via import map):
//
//     import * as THREE from 'three';
//     import { PhosphorVigil } from './phosphor-vigil.js';
//
//     const fx = new PhosphorVigil(renderer, {
//         width: window.innerWidth,
//         height: window.innerHeight,
//         // optional overrides:
//         // feedbackStrength: 0.90,
//         // bloomThreshold: 0.55,
//         // bloomIntensity: 0.35,
//     });
//
//     // Per-frame, driven by the host scene:
//     fx.setVelocity(sharedVelocityVec2);  // optional
//     fx.render(scene, camera, clock.elapsedTime);
//
//     // On resize:
//     fx.setSize(window.innerWidth, window.innerHeight);
//
//     // On teardown:
//     fx.dispose();
//
// The same instance can be imported standalone into any Three.js scene —
// World War Watcher's Vector Ghost Protocol work, other skills, other
// projects. It owns no scene state beyond its render targets.
// ═══════════════════════════════════════════════════════════════════════

import * as THREE from 'three';

// ─── Default tuning knobs ──────────────────────────────────────────────
const DEFAULTS = {
    feedbackStrength: 0.90,     // Trail persistence per frame (0..1)
    bloomThreshold:   0.55,     // Brightness cutoff for bloom pass
    bloomIntensity:   0.35,     // Bloom additive mix in CRT composite
    aberrationStrength: 0.006,  // Chromatic offset magnitude
    flickerAmount:    0.02,     // Slow flicker depth
    grainAmount:      0.06,     // Film grain depth
    barrelDistortion: 0.18,     // CRT curvature amount
    phosphorTint:     [0.95, 1.0, 0.92], // Warm/green phosphor RGB multiplier
    pixelRatioCap:    2.0,      // Max device pixel ratio
};

// ─── Fullscreen triangle (shared vertex shader) ────────────────────────
// One oversized triangle instead of a quad: zero overdraw, clean UVs.
const FULLSCREEN_VERTEX = /* glsl */`
    varying vec2 vUv;
    void main() {
        vUv = uv;
        gl_Position = vec4(position, 1.0);
    }
`;

// ─── Pass 1: Feedback trail ────────────────────────────────────────────
// Per-channel UV offset based on velocity. R trails forward, B trails
// backward, G stays centered, plus perpendicular spread. Clamp to
// prevent overlapping trails from burning out white. Iridescent tint.
const FEEDBACK_FRAGMENT = /* glsl */`
    uniform sampler2D tCurrent;
    uniform sampler2D tPrevious;
    uniform float uFeedback;
    uniform vec2 uVelocity;
    uniform float uTime;
    varying vec2 vUv;

    void main() {
        vec4 current = texture2D(tCurrent, vUv);

        // Each channel reads the previous frame at a slightly different UV offset
        // Small per-frame shift that accumulates through feedback into visible trails
        vec2 vel = uVelocity;

        // R trails in velocity direction, B trails opposite, G stays center
        vec2 rOffset = vel * 0.22;
        vec2 gOffset = vec2(0.0);
        vec2 bOffset = vel * -0.22;

        // Perpendicular spread
        vec2 perp = vec2(-vel.y, vel.x) * 0.09;
        rOffset += perp;
        bOffset -= perp;

        float prevR = texture2D(tPrevious, vUv + rOffset).r;
        float prevG = texture2D(tPrevious, vUv + gOffset).g;
        float prevB = texture2D(tPrevious, vUv + bOffset).b;
        vec3 previous = vec3(prevR, prevG, prevB);

        // Blend: current on top, trails behind with feedback
        vec3 trailFaded = previous * uFeedback;
        // Cap each trail channel so overlapping R+G+B trails can't sum to white
        float trailMax = max(max(trailFaded.r, trailFaded.g), trailFaded.b);
        if (trailMax > 0.85) trailFaded *= 0.85 / trailMax;
        vec3 result = max(current.rgb, trailFaded);

        // Iridescent tint on the trails
        float trailAmount = trailMax * uFeedback;
        if (trailAmount > 0.02) {
            float iriPhase = length(vUv - 0.5) * 5.0 + uTime * 0.3;
            vec3 iri = 0.5 + 0.5 * cos(6.28318 * (iriPhase + vec3(0.0, 0.33, 0.67)));
            result += iri * 0.08 * trailAmount;
        }

        gl_FragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
    }
`;

// ─── Pass 2: Bloom threshold ───────────────────────────────────────────
// Smoothstep the bright pixels out of the trail-composited frame.
const THRESHOLD_FRAGMENT = /* glsl */`
    uniform sampler2D tInput;
    uniform float uThreshold;
    varying vec2 vUv;

    void main() {
        vec3 color = texture2D(tInput, vUv).rgb;
        float brightness = max(max(color.r, color.g), color.b);
        float soft = smoothstep(uThreshold - 0.1, uThreshold + 0.2, brightness);
        gl_FragColor = vec4(color * soft, 1.0);
    }
`;

// ─── Pass 3: Bloom blur ────────────────────────────────────────────────
// Single-iteration 4-tap box blur on the thresholded bloom texture.
const BLUR_FRAGMENT = /* glsl */`
    uniform sampler2D tInput;
    uniform vec2 uTexelSize;
    uniform float uOffset;
    varying vec2 vUv;

    void main() {
        vec3 color = vec3(0.0);
        float off = uOffset + 0.5;
        color += texture2D(tInput, vUv + vec2(-off, -off) * uTexelSize).rgb;
        color += texture2D(tInput, vUv + vec2( off, -off) * uTexelSize).rgb;
        color += texture2D(tInput, vUv + vec2(-off,  off) * uTexelSize).rgb;
        color += texture2D(tInput, vUv + vec2( off,  off) * uTexelSize).rgb;
        gl_FragColor = vec4(color * 0.25, 1.0);
    }
`;

// ─── Pass 4: CRT composite ─────────────────────────────────────────────
// Barrel distortion, chromatic aberration, bloom add, dual-frequency
// scanlines, RGB subpixel shadow mask, vignette, dual-frequency flicker,
// phosphor glow, hash-noise grain, warm/green phosphor tint.
const COMPOSITE_FRAGMENT = /* glsl */`
    uniform sampler2D tInput;
    uniform sampler2D tBloom;
    uniform vec2 uResolution;
    uniform float uTime;
    uniform float uBloomIntensity;
    uniform float uAberrationStrength;
    uniform float uFlickerAmount;
    uniform float uGrainAmount;
    uniform float uBarrelDistortion;
    uniform vec3 uPhosphorTint;
    varying vec2 vUv;

    // Hash-based noise
    float hash(vec2 p) {
        vec3 p3 = fract(vec3(p.xyx) * 0.1031);
        p3 += dot(p3, p3.yzx + 33.33);
        return fract((p3.x + p3.y) * p3.z);
    }

    vec2 barrelDistortion(vec2 uv) {
        vec2 cc = uv - 0.5;
        float dist = dot(cc, cc);
        return uv + cc * dist * uBarrelDistortion;
    }

    void main() {
        vec2 uv = barrelDistortion(vUv);

        // Out of bounds → black
        if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
            gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
            return;
        }

        // Chromatic aberration — split R/G/B sampling from center
        vec2 dir = uv - 0.5;
        float aberr = length(dir) * uAberrationStrength;
        float r = texture2D(tInput, uv + dir * aberr).r;
        float g = texture2D(tInput, uv).g;
        float b = texture2D(tInput, uv - dir * aberr).b;
        vec3 color = vec3(r, g, b);

        // Add bloom
        vec3 bloom = texture2D(tBloom, uv).rgb;
        color += bloom * uBloomIntensity;

        // Scanlines — dual frequency for more authentic CRT look
        float scanFine = sin(uv.y * uResolution.y * 1.5) * 0.5 + 0.5;
        scanFine = pow(scanFine, 1.2);
        float scanCoarse = sin(uv.y * uResolution.y * 0.25) * 0.5 + 0.5;
        float scanline = scanFine * (0.85 + 0.15 * scanCoarse);
        color *= 0.6 + 0.4 * scanline;

        // RGB subpixel columns
        float pixelX = gl_FragCoord.x;
        float subpixel = mod(pixelX, 3.0);
        vec3 mask = vec3(
            smoothstep(0.0, 1.0, 1.0 - abs(subpixel - 0.5) / 1.5),
            smoothstep(0.0, 1.0, 1.0 - abs(subpixel - 1.5) / 1.5),
            smoothstep(0.0, 1.0, 1.0 - abs(subpixel - 2.5) / 1.5)
        );
        color *= 0.75 + 0.25 * mask;

        // Vignette — darker edges
        vec2 vig = uv * (1.0 - uv);
        float vigAmount = pow(vig.x * vig.y * 15.0, 0.25);
        color *= vigAmount;

        // Flicker — two frequencies for organic feel
        float flicker = 1.0 - sin(uTime * 8.0) * uFlickerAmount - sin(uTime * 60.0) * (uFlickerAmount * 0.25);
        color *= flicker;

        // Phosphor glow — bloom on bright areas
        float brightness = max(max(color.r, color.g), color.b);
        color += color * brightness * 0.18;

        // Film grain noise
        float noise = hash(uv * uResolution + uTime * 100.0) * uGrainAmount - (uGrainAmount * 0.5);
        color += noise;

        // Slight green/warm phosphor tint
        color *= uPhosphorTint;

        gl_FragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
    }
`;

// ─── PhosphorVigil pipeline ────────────────────────────────────────────
export class PhosphorVigil {
    constructor(renderer, options = {}) {
        this.renderer = renderer;
        this.opts = { ...DEFAULTS, ...options };

        const width  = options.width  || renderer.domElement.width  || window.innerWidth;
        const height = options.height || renderer.domElement.height || window.innerHeight;

        // Orthographic FX camera + fullscreen triangle scene
        this.fxCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
        this.fxScene = new THREE.Scene();
        const triGeo = new THREE.BufferGeometry();
        triGeo.setAttribute('position', new THREE.BufferAttribute(
            new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3
        ));
        triGeo.setAttribute('uv', new THREE.BufferAttribute(
            new Float32Array([0, 0, 2, 0, 0, 2]), 2
        ));
        this.fsTriangle = triGeo;

        // Shared velocity channel (Vector2). Host code writes to this.
        this._velocity = new THREE.Vector2(0, 0);

        // Materials for each pass
        this._buildMaterials();

        // Single fullscreen triangle mesh — _drawFS() swaps its material
        // between passes instead of creating four independent meshes.
        this._fsMesh = new THREE.Mesh(this.fsTriangle, this.matFeedback);
        this._fsMesh.frustumCulled = false;
        this.fxScene.add(this._fsMesh);

        // Render targets: scene, feedback ping-pong, bloom threshold, bloom blur
        const rtParams = {
            minFilter: THREE.LinearFilter,
            magFilter: THREE.LinearFilter,
            format: THREE.RGBAFormat,
            type: THREE.UnsignedByteType,
            depthBuffer: true,
            stencilBuffer: false,
        };
        this.rtScene      = new THREE.WebGLRenderTarget(width, height, rtParams);
        this.rtFeedbackA  = new THREE.WebGLRenderTarget(width, height, { ...rtParams, depthBuffer: false });
        this.rtFeedbackB  = new THREE.WebGLRenderTarget(width, height, { ...rtParams, depthBuffer: false });
        this.rtBloom      = new THREE.WebGLRenderTarget(width, height, { ...rtParams, depthBuffer: false });
        this.rtBloomBlur  = new THREE.WebGLRenderTarget(width, height, { ...rtParams, depthBuffer: false });

        // Ping-pong cursor — alternates between the two feedback RTs
        this._feedbackSrc = this.rtFeedbackA;
        this._feedbackDst = this.rtFeedbackB;

        this.width = width;
        this.height = height;
    }

    _buildMaterials() {
        this.matFeedback = new THREE.ShaderMaterial({
            vertexShader: FULLSCREEN_VERTEX,
            fragmentShader: FEEDBACK_FRAGMENT,
            uniforms: {
                tCurrent:  { value: null },
                tPrevious: { value: null },
                uFeedback: { value: this.opts.feedbackStrength },
                uVelocity: { value: this._velocity || new THREE.Vector2(0, 0) },
                uTime:     { value: 0 },
            },
            depthTest: false,
            depthWrite: false,
        });

        this.matThreshold = new THREE.ShaderMaterial({
            vertexShader: FULLSCREEN_VERTEX,
            fragmentShader: THRESHOLD_FRAGMENT,
            uniforms: {
                tInput:     { value: null },
                uThreshold: { value: this.opts.bloomThreshold },
            },
            depthTest: false,
            depthWrite: false,
        });

        this.matBlur = new THREE.ShaderMaterial({
            vertexShader: FULLSCREEN_VERTEX,
            fragmentShader: BLUR_FRAGMENT,
            uniforms: {
                tInput:     { value: null },
                uTexelSize: { value: new THREE.Vector2(1 / 1024, 1 / 1024) },
                uOffset:    { value: 1.0 },
            },
            depthTest: false,
            depthWrite: false,
        });

        this.matComposite = new THREE.ShaderMaterial({
            vertexShader: FULLSCREEN_VERTEX,
            fragmentShader: COMPOSITE_FRAGMENT,
            uniforms: {
                tInput:              { value: null },
                tBloom:              { value: null },
                uResolution:         { value: new THREE.Vector2(1, 1) },
                uTime:               { value: 0 },
                uBloomIntensity:     { value: this.opts.bloomIntensity },
                uAberrationStrength: { value: this.opts.aberrationStrength },
                uFlickerAmount:      { value: this.opts.flickerAmount },
                uGrainAmount:        { value: this.opts.grainAmount },
                uBarrelDistortion:   { value: this.opts.barrelDistortion },
                uPhosphorTint:       { value: new THREE.Vector3(...this.opts.phosphorTint) },
            },
            depthTest: false,
            depthWrite: false,
        });
    }

    // Update the velocity vector the feedback pass reads.
    // Callers pass a THREE.Vector2 they own, or a bare {x, y}.
    // The uniform value is the same Vector2 instance as this._velocity
    // (bound in _buildMaterials), so the in-place .set() updates both.
    setVelocity(vec) {
        if (vec && typeof vec.x === 'number' && typeof vec.y === 'number') {
            this._velocity.set(vec.x, vec.y);
        }
    }

    setSize(width, height) {
        this.width = width;
        this.height = height;
        this.rtScene.setSize(width, height);
        this.rtFeedbackA.setSize(width, height);
        this.rtFeedbackB.setSize(width, height);
        this.rtBloom.setSize(width, height);
        this.rtBloomBlur.setSize(width, height);
    }

    // Main render entry. Replaces renderer.render(scene, camera) in the host.
    render(scene, camera, elapsedTime) {
        const renderer = this.renderer;

        // Resolution for composite and blur
        const dpr = Math.min(window.devicePixelRatio || 1, this.opts.pixelRatioCap);
        const resX = this.width * dpr;
        const resY = this.height * dpr;

        // ─── Pass 0: render scene to rtScene ───────────────────────────
        renderer.setRenderTarget(this.rtScene);
        renderer.clear();
        renderer.render(scene, camera);

        // ─── Pass 1: feedback trail (ping-pong) ────────────────────────
        this.matFeedback.uniforms.tCurrent.value  = this.rtScene.texture;
        this.matFeedback.uniforms.tPrevious.value = this._feedbackSrc.texture;
        this.matFeedback.uniforms.uTime.value     = elapsedTime;
        this._drawFS(this.matFeedback, this._feedbackDst);

        // Swap so next frame reads from the most recent destination
        const prevDst = this._feedbackDst;
        this._feedbackDst = this._feedbackSrc;
        this._feedbackSrc = prevDst;

        // The feedback output lives in _feedbackSrc after the swap
        const feedbackOut = this._feedbackSrc;

        // ─── Pass 2: bloom threshold ───────────────────────────────────
        this.matThreshold.uniforms.tInput.value = feedbackOut.texture;
        this._drawFS(this.matThreshold, this.rtBloom);

        // ─── Pass 3: bloom blur ────────────────────────────────────────
        this.matBlur.uniforms.tInput.value = this.rtBloom.texture;
        this.matBlur.uniforms.uTexelSize.value.set(1 / resX, 1 / resY);
        this._drawFS(this.matBlur, this.rtBloomBlur);

        // ─── Pass 4: CRT composite → screen ────────────────────────────
        this.matComposite.uniforms.tInput.value = feedbackOut.texture;
        this.matComposite.uniforms.tBloom.value = this.rtBloomBlur.texture;
        this.matComposite.uniforms.uResolution.value.set(resX, resY);
        this.matComposite.uniforms.uTime.value  = elapsedTime;

        renderer.setRenderTarget(null);
        renderer.clear();
        this._drawFS(this.matComposite, null);
    }

    // Draw the pre-built fullscreen triangle with the given material
    // into target (or screen). The mesh is built once in the constructor;
    // passes just swap its material reference each call.
    _drawFS(material, target) {
        this._fsMesh.material = material;
        this.renderer.setRenderTarget(target);
        this.renderer.render(this.fxScene, this.fxCamera);
    }

    dispose() {
        [this.rtScene, this.rtFeedbackA, this.rtFeedbackB, this.rtBloom, this.rtBloomBlur].forEach(rt => rt.dispose());
        [this.matFeedback, this.matThreshold, this.matBlur, this.matComposite].forEach(m => m.dispose());
        this.fsTriangle.dispose();
    }
}
