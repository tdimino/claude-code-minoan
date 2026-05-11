const arms = addControl('arms', 'Spiral Arms', 2, 8, 4);
const spin = addControl('spin', 'Spin Rate', 0.1, 3.0, 0.5);
const thickness = addControl('thickness', 'Disk Thickness', 0.5, 5.0, 1.5);
const spread = addControl('spread', 'Arm Spread', 0.5, 3.0, 1.5);

if (i === 0) {
  setInfo('Galaxy Spiral', 'Logarithmic arms with density wave');
  annotate('core', 0, 0, 0, 'Galactic Core');
}

const armCount = Math.floor(arms);
const armIndex = i % armCount;
const t = i / count;

const angle = armIndex * (Math.PI * 2 / armCount) + t * 12 + time * spin;
const r = Math.pow(t, 0.5) * 20;
const spiralAngle = angle + Math.log(r + 0.001) * spread;

const jitterX = Math.sin(i * 127.1 + time * 0.2) * thickness * t * 0.3;
const jitterY = Math.sin(i * 7.31 + time * 0.3) * thickness * t;
const jitterZ = Math.sin(i * 311.7 + time * 0.15) * thickness * t * 0.3;

target.set(
  r * Math.cos(spiralAngle) + jitterX,
  jitterY,
  r * Math.sin(spiralAngle) + jitterZ
);

const hue = 0.55 + armIndex * 0.06 + t * 0.15;
const sat = 0.6 + 0.4 * (1 - t);
const lum = 0.25 + 0.45 * (1 - t) + 0.1 * Math.sin(time * 2 + i * 0.05);

color.setHSL(hue % 1, sat, lum);
