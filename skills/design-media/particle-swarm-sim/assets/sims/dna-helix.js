const radius = addControl('radius', 'Helix Radius', 2, 10, 5);
const pitch = addControl('pitch', 'Pitch', 0.5, 4.0, 1.5);
const rungDensity = addControl('rungs', 'Rung Density', 0.1, 1.0, 0.4);
const rotSpeed = addControl('rotation', 'Rotation Speed', 0.1, 3.0, 0.5);

if (i === 0) {
  setInfo('Double Helix', 'Base pairs bridge two phosphate backbones');
}

const strand = i % 3;
const idx = Math.floor(i / 3);
const groupCount = Math.floor(count / 3);
const t = Math.min(idx / (groupCount + 0.0001), 1.0);
const height = (t - 0.5) * 40;
const turns = 8 / pitch;
const angle = t * Math.PI * 2 * turns + time * rotSpeed;

const strandAAngle = angle;
const strandBAngle = angle + Math.PI;

if (strand === 0) {
  target.set(
    radius * Math.cos(strandAAngle),
    height,
    radius * Math.sin(strandAAngle)
  );
  color.setHSL(0.58, 0.8, 0.55);
} else if (strand === 1) {
  target.set(
    radius * Math.cos(strandBAngle),
    height,
    radius * Math.sin(strandBAngle)
  );
  color.setHSL(0.08, 0.8, 0.55);
} else {
  const rungPhase = Math.sin(t * Math.PI * 2 * 20);
  const isRung = Math.abs(rungPhase) < rungDensity;
  const rungLerp = (Math.sin(i * 43.7) * 0.5 + 0.5);

  const ax = radius * Math.cos(strandAAngle);
  const az = radius * Math.sin(strandAAngle);
  const bx = radius * Math.cos(strandBAngle);
  const bz = radius * Math.sin(strandBAngle);

  const px = ax + (bx - ax) * rungLerp;
  const pz = az + (bz - az) * rungLerp;
  const py = height + (isRung ? 0 : (Math.sin(i * 17.3) - 0.5) * 2);

  target.set(px * (isRung ? 1 : 0.1), py, pz * (isRung ? 1 : 0.1));

  const basePair = Math.floor(i * 0.01) % 4;
  const hue = basePair === 0 ? 0.0 : basePair === 1 ? 0.33 : basePair === 2 ? 0.15 : 0.75;
  color.setHSL(hue, isRung ? 0.9 : 0.2, isRung ? 0.6 : 0.15);
}
