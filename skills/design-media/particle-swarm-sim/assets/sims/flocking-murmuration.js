const flockRadius = addControl('radius', 'Flock Radius', 5, 30, 15);
const speed = addControl('speed', 'Speed', 0.5, 5.0, 2.0);
const coherence = addControl('coherence', 'Coherence', 0.1, 1.0, 0.6);
const turbulence = addControl('turbulence', 'Turbulence', 0, 2.0, 0.3);

if (i === 0) {
  setInfo('Murmuration', 'Collective flight through implicit rules');
}

const t = i / count;
const groupSize = 200;
const groupIndex = Math.floor(i / groupSize);
const localIndex = i % groupSize;
const localT = localIndex / groupSize;

const groupPhase = groupIndex * 2.399 + time * speed * 0.3;
const groupCenterX = Math.sin(groupPhase) * flockRadius * 0.5;
const groupCenterY = Math.cos(groupPhase * 0.7 + 1.3) * flockRadius * 0.3;
const groupCenterZ = Math.sin(groupPhase * 0.5 + 2.7) * flockRadius * 0.4;

const baseAngle = localT * Math.PI * 2 + time * speed;
const layerAngle = baseAngle * (1 + localT * 0.3);
const layerRadius = (1 - coherence) * 8 + 2;

const noiseX = Math.sin(i * 127.1 + time * 1.7) * turbulence;
const noiseY = Math.sin(i * 311.7 + time * 2.3) * turbulence;
const noiseZ = Math.sin(i * 74.3 + time * 1.1) * turbulence;

const flowX = Math.sin(time * speed * 0.4 + t * 6.28) * 3;
const flowY = Math.cos(time * speed * 0.3 + t * 6.28 + 1.0) * 2;
const flowZ = Math.sin(time * speed * 0.5 + t * 6.28 + 2.0) * 3;

const px = groupCenterX + Math.cos(layerAngle) * layerRadius + noiseX + flowX;
const py = groupCenterY + Math.sin(layerAngle * 1.3) * layerRadius * 0.6 + noiseY + flowY;
const pz = groupCenterZ + Math.sin(layerAngle) * layerRadius + noiseZ + flowZ;

target.set(px, py, pz);

const velocity = Math.abs(Math.cos(baseAngle * 2)) * 0.5 + 0.3;
const hue = 0.55 + groupIndex * 0.02 + velocity * 0.1;
const lum = 0.3 + velocity * 0.4;

color.setHSL(hue % 1, 0.6, lum);
