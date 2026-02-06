#!/usr/bin/env node
/**
 * CLI wrapper for beautiful-mermaid
 * Renders Mermaid diagrams as ASCII/Unicode art or SVG
 */

import { renderMermaid, renderMermaidAscii, THEMES } from 'beautiful-mermaid';
import { writeFileSync, readFileSync, existsSync } from 'fs';

const args = process.argv.slice(2);

// Mermaid diagram keywords for inline detection
const MERMAID_KEYWORDS = [
  'graph', 'flowchart', 'sequenceDiagram', 'stateDiagram',
  'classDiagram', 'erDiagram', 'journey', 'gantt', 'pie',
  'gitGraph', 'timeline', 'quadrantChart', 'requirementDiagram',
  'C4Context', 'C4Container', 'C4Component', 'C4Dynamic', 'C4Deployment',
  'mindmap', 'sankey', 'xychart', 'block'
];

// Parse arguments
let input = null;
let output = null;
let theme = 'zinc-dark';
let format = 'ascii';  // ascii | svg
let useAscii = false;  // true = pure ASCII, false = Unicode box-drawing

for (let i = 0; i < args.length; i++) {
  if (args[i] === '-i' || args[i] === '--input') input = args[++i];
  else if (args[i] === '-o' || args[i] === '--output') output = args[++i];
  else if (args[i] === '-t' || args[i] === '--theme') theme = args[++i];
  else if (args[i] === '-f' || args[i] === '--format') format = args[++i];
  else if (args[i] === '--ascii') useAscii = true;
  else if (args[i] === '--themes') { listThemes(); process.exit(0); }
  else if (args[i] === '-h' || args[i] === '--help') { showHelp(); process.exit(0); }
  else if (!input) input = args[i];  // First positional arg is input
}

function listThemes() {
  console.log('Available themes:');
  for (const [name, colors] of Object.entries(THEMES)) {
    const type = isLightTheme(colors.bg) ? 'light' : 'dark';
    console.log(`  ${name.padEnd(20)} (${type})`);
  }
}

function isLightTheme(bg) {
  // Simple heuristic: light themes have high luminance backgrounds
  const hex = bg.replace('#', '');
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5;
}

function isMermaidDiagram(text) {
  // Check if text looks like inline Mermaid diagram
  if (text.includes('\n')) return true;
  return MERMAID_KEYWORDS.some(keyword => text.startsWith(keyword));
}

function showHelp() {
  console.log(`Usage: mermaid.mjs [options] [input]

Render Mermaid diagrams as ASCII art or SVG.

Arguments:
  input               Mermaid file, inline diagram text, or - for stdin

Options:
  -i, --input FILE    Input file (alternative to positional arg)
  -o, --output FILE   Output file (default: stdout)
  -t, --theme NAME    Theme name for SVG (default: zinc-dark)
  -f, --format TYPE   Output format: ascii | svg (default: ascii)
  --ascii             Use pure ASCII instead of Unicode box-drawing
  --themes            List available themes
  -h, --help          Show this help

Supported diagram types:
  - Flowcharts (graph TD/LR/BT/RL)
  - State diagrams (stateDiagram-v2)
  - Sequence diagrams (sequenceDiagram)
  - Class diagrams (classDiagram)
  - ER diagrams (erDiagram)
  - And more: gantt, pie, gitGraph, journey, timeline, etc.

Examples:
  # ASCII output to terminal (requires newlines)
  mermaid.mjs $'graph TD\\n    A --> B --> C'

  # From stdin (recommended for inline diagrams)
  printf "graph TD\\n    A --> B" | mermaid.mjs -

  # Pure ASCII output (maximum compatibility)
  mermaid.mjs --ascii diagram.mmd

  # SVG with theme
  mermaid.mjs -f svg -t tokyo-night diagram.mmd -o diagram.svg

  # From file
  mermaid.mjs diagram.mmd

  # List themes
  mermaid.mjs --themes
`);
}

// Main execution
async function main() {
  // Read diagram from file, stdin, or inline
  let diagram;

  if (input === '-') {
    // Explicit stdin request
    try {
      diagram = readFileSync(0, 'utf8');
    } catch (e) {
      console.error('Error: Could not read from stdin.');
      process.exit(1);
    }
  } else if (!input) {
    // No input provided - show help
    console.error('Error: No input provided. Use --help for usage.');
    process.exit(1);
  } else if (existsSync(input)) {
    // Read from file
    diagram = readFileSync(input, 'utf8');
  } else if (isMermaidDiagram(input)) {
    // Treat as inline diagram
    diagram = input;
  } else {
    console.error(`Error: File not found: ${input}`);
    console.error('If this is an inline diagram, ensure it starts with a valid Mermaid keyword');
    console.error('(graph, flowchart, sequenceDiagram, etc.) or contains newlines.');
    process.exit(1);
  }

  // Validate theme
  if (format === 'svg' && !THEMES[theme]) {
    console.error(`Error: Unknown theme '${theme}'. Use --themes to list available themes.`);
    process.exit(1);
  }

  try {
    let result;

    if (format === 'svg') {
      result = await renderMermaid(diagram, THEMES[theme]);
    } else {
      result = renderMermaidAscii(diagram, { useAscii });
    }

    if (output) {
      writeFileSync(output, result);
      console.error(`Written to: ${output}`);
    } else {
      console.log(result);
    }
  } catch (e) {
    // Categorize errors for better feedback
    const msg = e.message || String(e);
    if (msg.includes('Parse error') || msg.includes('syntax') || msg.includes('Invalid')) {
      console.error(`Diagram syntax error: ${msg}`);
      console.error('Check your Mermaid syntax. Diagrams require newlines between elements.');
      console.error('Use: printf "graph TD\\n    A --> B" | mermaid.mjs -');
    } else if (msg.includes('unsupported') || msg.includes('not supported')) {
      console.error(`Unsupported feature: ${msg}`);
      console.error('This diagram type may not be fully supported in ASCII mode.');
    } else {
      console.error(`Error rendering diagram: ${msg}`);
    }
    process.exit(1);
  }
}

main();
