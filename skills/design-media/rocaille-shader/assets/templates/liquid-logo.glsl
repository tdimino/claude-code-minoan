// Liquid Logo Shader - Shadertoy Compatible
// Mouse-reactive radial domain warp + chromatic aberration on a logo texture.
//
// Inspired by LiquidLogo by Gustav WF (https://gustavwf.supply/product/liquidlogo).
// Reimplemented from scratch — not a port of that Framer component.
//
// Drop an image into iChannel0 (Shadertoy's texture slot) and move the mouse.
// The production runtime (scripts/rocaille_generator.py --mode liquid-logo)
// generates a WebGL2 HTML file with a uTimeSinceInteract uniform driven by
// pointermove events; in Shadertoy the decay is faked with iMouse.z and an
// auto-orbiting cursor so the preview stays alive without interaction.
//
// See references/liquid-logo.md for the math.

#define DISTORTION 0.40   // Peak UV pull toward the cursor
#define RADIUS     0.25   // Gaussian falloff radius (NDC, aspect-corrected)
#define CHROMA     0.015  // RGB-channel UV split magnitude
#define IDLE_ON    1      // 1 enables Lissajous idle breathing
#define IDLE_AMP   0.012
#define IDLE_SPEED 0.6

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2  res = iResolution.xy;
    float asp = res.x / res.y;
    vec2  uv  = fragCoord / res;

    // When the mouse button is not held, orbit the cursor automatically so the
    // Shadertoy preview shows the effect without interaction. In the real WebGL2
    // runtime this is replaced by a uMouse uniform driven by pointermove.
    vec2 autoMouse = 0.5 + 0.25 * vec2(cos(iTime * 0.7), sin(iTime * 1.1));
    vec2 mUv = (iMouse.z > 0.0) ? iMouse.xy / res : autoMouse;

    // Aspect-corrected displacement from cursor to pixel.
    vec2  d  = vec2((uv.x - mUv.x) * asp, uv.y - mUv.y);
    float r2 = dot(d, d);

    // Gaussian radial falloff. In production, multiply by
    // exp(-uTimeSinceInteract * uDecay) for a soft release.
    float w = exp(-r2 / (RADIUS * RADIUS));

    // Idle Lissajous warp — constant, subtle, independent of the cursor.
    vec2 idle = vec2(0.0);
#if IDLE_ON
    vec2 iv = uv;
    iv += sin(iv.yx * 3.0 + iTime * IDLE_SPEED) * IDLE_AMP;
    iv += sin(iv.yx * 1.7 - iTime * IDLE_SPEED * 0.8) * IDLE_AMP * 0.6;
    idle = iv - uv;
#endif

    // Pull the sample UV toward the cursor. `d` points cursor -> pixel, so
    // sampling at (uv - d*strength) reads content from closer to the cursor and
    // stretches it outward — the bulge we read as "liquid."
    vec2 pullUv   = vec2(d.x / asp, d.y) * (DISTORTION * w);
    vec2 sampleUv = uv - pullUv + idle;

    // Chromatic aberration: split R/B along the cursor-to-pixel direction.
    vec2 chromaDir = (r2 > 1e-6) ? normalize(d) : vec2(0.0);
    vec2 chromaOff = vec2(chromaDir.x / asp, chromaDir.y) * (CHROMA * w);

    float r = texture(iChannel0, sampleUv - chromaOff).r;
    vec4  g = texture(iChannel0, sampleUv);
    float b = texture(iChannel0, sampleUv + chromaOff).b;

    fragColor = vec4(r, g.g, b, g.a);
}
