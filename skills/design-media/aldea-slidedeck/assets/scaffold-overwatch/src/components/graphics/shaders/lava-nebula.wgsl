struct Uniforms {
  resolution: vec2f,
  time: f32,
  _pad: f32,
  mouse: vec2f,
}

@group(0) @binding(0) var<uniform> u: Uniforms;

@vertex
fn vs(@builtin(vertex_index) i: u32) -> @builtin(position) vec4f {
  let pos = array<vec2f, 4>(
    vec2f(-1, -1), vec2f(1, -1), vec2f(-1, 1), vec2f(1, 1)
  );
  return vec4f(pos[i], 0, 1);
}

@fragment
fn fs(@builtin(position) fragCoord: vec4f) -> @location(0) vec4f {
  let R = u.resolution;
  let t = u.time;
  var uv = (fragCoord.xy * 2.0 - R) / R.y;

  // Mouse influence — subtle camera offset
  uv += vec2f(u.mouse.x - 0.5, u.mouse.y - 0.5) * 0.15;

  let d = length(uv);
  let a = atan2(uv.y, uv.x);
  var col = vec3f(0.0);

  // Raymarching accumulation
  for (var i = 0; i < 80; i++) {
    let fi = f32(i);
    var p = vec3f(uv * (1.0 + fi * 0.02), fi * 0.1 + t * 0.3);
    p += sin(a * d + vec3f(t)).zxy / d;
    col += sin(p) * 0.02;
  }

  // Tone mapping with color base
  let base = vec3f(0.0, 1.0, 8.0);
  col = tanh(col * col * base);

  return vec4f(col, 1.0);
}
