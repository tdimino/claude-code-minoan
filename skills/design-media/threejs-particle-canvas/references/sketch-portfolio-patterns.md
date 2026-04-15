# Sketch Portfolio Patterns

Production Three.js recipes from a 10-sketch WebGL portfolio:
shader injection, scene lifecycle, PBR transmission, InstancedMesh,
and recursive geometry animation. Source: curllmooha.vercel.app
(Vite + Three.js + GSAP, by Vipin Pathak).

## 1. onBeforeCompile Shader Injection

```javascript
material.onBeforeCompile = (shader) => {
  shader.uniforms.uTime = { value: 0 };
  shader.vertexShader = shader.vertexShader
    .replace('#include <begin_vertex>', customVertexCode);
};
```

- Lighter than full custom ShaderMaterial
- Preserves PBR lighting pipeline
- Gotcha: string replacement fragile across Three.js versions
- **WebGL-only** — WebGPU renderer uses NodeMaterial instead

## 2. InstancedMesh with Per-Instance Attributes

```javascript
const attr = new THREE.InstancedBufferAttribute(data, 1);
mesh.geometry.setAttribute('aProximity', attr);
// Per-frame: update data[i], set attr.needsUpdate = true
```

## 3. Lazy Scene Loading with Cleanup

```javascript
export function startScene(container) {
  // ... setup renderer, scene, camera, geometry, material
  return function cleanup() {
    geometry.dispose();
    material.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
  };
}
```

- Prevents WebGL context leaks across transitions
- `forceContextLoss()` releases GPU memory immediately

## 4. PBR Transmission Materials (Glass/Liquid)

```javascript
const glass = new THREE.MeshPhysicalMaterial({
  transmission: 1.0,
  thickness: 0.5,
  ior: 1.5,
  dispersion: 0.3,
  clearcoat: 1.0,
  attenuationColor: new THREE.Color(0x88ccff),
});
```

## 5. Gallery UI

- 3-column masonry (`nth-child(3n+2)` offset)
- Grayscale → color hover, custom cursor with GSAP lerp
- `(hover: hover)` media query hides cursor on touch
