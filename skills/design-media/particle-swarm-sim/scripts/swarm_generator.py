#!/usr/bin/env python3
"""Generate particle swarm simulators.

Modes:
    sandbox - Generate a complete sandbox runtime HTML
    sim     - Output a behavior function body (from preset or boilerplate)

Usage:
    python3 swarm_generator.py --mode sandbox --output sandbox.html
    python3 swarm_generator.py --mode sandbox --particles 30000 --gesture --output sandbox.html
    python3 swarm_generator.py --mode sandbox --minimal --output embed.html
    python3 swarm_generator.py --mode sim --preset galaxy-spiral --output galaxy.js
    python3 swarm_generator.py --mode sim --list
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / 'assets' / 'templates'
SIMS_DIR = SKILL_DIR / 'assets' / 'sims'

AVAILABLE_PRESETS = [
    ('galaxy-spiral', 'Logarithmic spiral arms with density wave theory'),
    ('dna-helix', 'Double helix with base pair connections'),
    ('flocking-murmuration', 'Boids-like flocking via phase-shifted oscillators'),
]

DEFAULT_BOILERPLATE = """const speed = addControl('speed', 'Speed', 0.1, 5.0, 1.0);
const scale = addControl('scale', 'Scale', 5, 40, 15);

if (i === 0) setInfo('Untitled Sim', 'Describe your simulation here');

const phi = (i / count) * Math.PI * 2 * 10;
const theta = Math.acos(1 - 2 * (i / count));
const r = scale + Math.sin(time * speed + i * 0.01) * 3;

target.set(
  r * Math.sin(theta) * Math.cos(phi),
  r * Math.sin(theta) * Math.sin(phi),
  r * Math.cos(theta)
);
color.setHSL(i / count, 0.8, 0.5 + 0.2 * Math.sin(time + i * 0.1));"""


def generate_sandbox(args):
    template_name = 'sandbox-minimal.html' if args.minimal else 'sandbox-runtime.html'
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        print(f'Error: Template not found: {template_path}', file=sys.stderr)
        sys.exit(1)

    html = template_path.read_text()

    if args.particles != 20000:
        html = html.replace('particleCount: 20000', f'particleCount: {args.particles}')

    if args.size != 0.06:
        html = html.replace('particleSize: 0.06', f'particleSize: {args.size}')

    if args.bg != '#050508':
        hex_int = args.bg.lstrip('#')
        html = html.replace('backgroundColor: 0x050508', f'backgroundColor: 0x{hex_int}')

    if not args.gesture and 'gestureEnabled' in html:
        html = html.replace('gestureEnabled: true', 'gestureEnabled: false')

    return html


def generate_sim(args):
    if args.preset:
        preset_path = SIMS_DIR / f'{args.preset}.js'
        if not preset_path.exists():
            print(f'Error: Preset not found: {args.preset}', file=sys.stderr)
            print(f'Available: {", ".join(p[0] for p in AVAILABLE_PRESETS)}', file=sys.stderr)
            sys.exit(1)
        return preset_path.read_text()
    else:
        return DEFAULT_BOILERPLATE


def list_presets():
    print('Available presets:')
    print()
    for name, desc in AVAILABLE_PRESETS:
        path = SIMS_DIR / f'{name}.js'
        exists = '✓' if path.exists() else '✗'
        print(f'  {exists} {name:25s} {desc}')

    extra_files = sorted(SIMS_DIR.glob('*.js'))
    known_names = {p[0] for p in AVAILABLE_PRESETS}
    extras = [f for f in extra_files if f.stem not in known_names]
    if extras:
        print()
        print('Additional sims:')
        for f in extras:
            print(f'  ✓ {f.stem}')


def main():
    parser = argparse.ArgumentParser(description='Generate particle swarm simulators')
    parser.add_argument('--mode', required=True, choices=['sandbox', 'sim'])
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--particles', type=int, default=20000, help='Particle count (sandbox mode)')
    parser.add_argument('--size', type=float, default=0.06, help='Particle size (sandbox mode)')
    parser.add_argument('--bg', default='#050508', help='Background color hex (sandbox mode)')
    parser.add_argument('--gesture', action='store_true', help='Enable gesture OS (sandbox mode)')
    parser.add_argument('--minimal', action='store_true', help='Use minimal template (sandbox mode)')
    parser.add_argument('--preset', help='Sim preset name (sim mode)')
    parser.add_argument('--list', action='store_true', help='List available presets (sim mode)')

    args = parser.parse_args()

    if args.list:
        list_presets()
        return

    if args.mode == 'sandbox':
        output = generate_sandbox(args)
    else:
        output = generate_sim(args)

    if args.output:
        Path(args.output).write_text(output)
        print(f'Written: {args.output}', file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
