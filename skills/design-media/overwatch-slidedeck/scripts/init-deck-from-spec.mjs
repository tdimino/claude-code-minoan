#!/usr/bin/env node

/**
 * init-deck-from-spec.mjs
 *
 * Initialize an Overwatch Mode deck from a YAML spec file.
 * Copies the scaffold, generates config.ts matching the scaffold's exact API
 * contract, creates empty slide files, applies design overrides, and reports
 * next steps.
 *
 * Usage:
 *   node scripts/init-deck-from-spec.mjs <spec.yaml> [output-dir]
 *
 * Requires: npm install in scripts/ (provides the yaml package).
 */

import { readFileSync, writeFileSync, mkdirSync, cpSync, existsSync } from "node:fs";
import { resolve, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCAFFOLD_DIR = resolve(__dirname, "../assets/scaffold");

// ── Known archetypes ────────────────────────────────────────────────────────

const KNOWN_TYPES = new Set([
  "shader-cover",
  "social-proof-grid",
  "split-text-list",
  "interactive-feature-grid",
  "data-visualization-cards",
  "product-demo",
  "two-column-gtm",
  "full-bleed-quote",
  "cli-product-demo",
  "horizontal-timeline",
  "three-audience-gtm",
  "simple-card-grid",
  "section-divider",
  "interactive-vertical-explorer",
]);

const VALID_TRANSITIONS = new Set(["none", "fade", "slide", "scale"]);

const COMPONENT_MAP = {
  "shader-cover": ["WebGPUCanvas", "CenterLayout", "StaggeredAnimation", "AnimatedItem"],
  "social-proof-grid": ["SplitLayout", "GridLayout", "SocialProofCard", "HoverLift", "MonoLabel"],
  "split-text-list": ["SplitLayout", "Eyebrow", "SubHeadline", "BodyText", "MonoLabel"],
  "interactive-feature-grid": ["SplitLayout", "GridLayout", "HoverLift", "MonoLabel", "BodyText", "AnimatePresence"],
  "data-visualization-cards": ["GridLayout", "HoverLift", "MonoLabel", "InfiniteScrollTicker", "ProgressBar"],
  "product-demo": ["SplitLayout", "PulseIndicator", "MonoLabel", "HoverLift", "BodyText"],
  "two-column-gtm": ["SplitLayout", "SubHeadline", "NetworkGraph", "Tooltip"],
  "full-bleed-quote": ["CenterLayout", "StaggeredAnimation", "AnimatedItem"],
  "cli-product-demo": ["SplitLayout", "GridLayout", "TerminalTyper", "HoverLift", "MonoLabel", "BodyText"],
  "horizontal-timeline": ["TimelineConnector", "StaggeredAnimation", "AnimatedItem", "Eyebrow"],
  "three-audience-gtm": ["GridLayout", "HoverLift", "StaggeredAnimation", "AnimatedItem", "ProgressBar", "PulseIndicator"],
  "simple-card-grid": ["GridLayout", "StaggeredAnimation", "AnimatedItem", "HoverLift", "BodyText"],
  "section-divider": ["CenterLayout", "AnimatedItem"],
  "interactive-vertical-explorer": ["SplitLayout", "HoverLift", "SVGRadarChart", "ProgressBar", "MonoLabel", "BodyText"],
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function escapeTs(str) {
  if (typeof str !== "string") return String(str);
  return str
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r");
}

function darkenHex(hex, factor = 0.78) {
  const m = hex.match(/^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  if (!m) return hex;
  const r = Math.round(parseInt(m[1], 16) * factor);
  const g = Math.round(parseInt(m[2], 16) * factor);
  const b = Math.round(parseInt(m[3], 16) * factor);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

// ── Validation ──────────────────────────────────────────────────────────────

function validate(spec) {
  const errors = [];

  if (!spec.meta?.title) {
    errors.push("Missing required field: meta.title");
  }

  if (!spec.slides || !Array.isArray(spec.slides)) {
    errors.push("Missing or invalid 'slides' array");
    return errors;
  }

  if (spec.slides.length === 0) {
    errors.push("'slides' array is empty");
  }

  const seenIds = new Set();
  for (let i = 0; i < spec.slides.length; i++) {
    const s = spec.slides[i];
    const prefix = `slides[${i}]`;

    if (!s.id) {
      errors.push(`${prefix}: missing required field 'id'`);
    } else {
      if (seenIds.has(s.id)) {
        errors.push(`${prefix}: duplicate id "${s.id}"`);
      }
      seenIds.add(s.id);

      if (s.id.includes("/") || s.id.includes("\\")) {
        errors.push(`${prefix}: id "${s.id}" contains path separators`);
      }
      if (s.id.includes("..")) {
        errors.push(`${prefix}: id "${s.id}" contains '..'`);
      }
      if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(s.id)) {
        errors.push(`${prefix}: id "${s.id}" must start with alphanumeric and contain only [a-zA-Z0-9_-]`);
      }
    }

    if (!s.type) {
      errors.push(`${prefix}: missing required field 'type'`);
    } else if (!KNOWN_TYPES.has(s.type)) {
      errors.push(`${prefix}: unknown type "${s.type}" (known: ${[...KNOWN_TYPES].join(", ")})`);
    }

    if (s.transition !== undefined && !VALID_TRANSITIONS.has(s.transition)) {
      errors.push(`${prefix}: invalid transition "${s.transition}" (valid: ${[...VALID_TRANSITIONS].join(", ")})`);
    }
    if (s.transitionDuration !== undefined && (typeof s.transitionDuration !== "number" || s.transitionDuration < 0)) {
      errors.push(`${prefix}: transitionDuration must be a non-negative number`);
    }
  }

  const deckTransition = spec.design?.transition ?? spec.transition;
  if (deckTransition !== undefined && !VALID_TRANSITIONS.has(deckTransition)) {
    errors.push(`Deck-level transition "${deckTransition}" is invalid (valid: ${[...VALID_TRANSITIONS].join(", ")})`);
  }

  const deckDuration = spec.design?.transitionDuration ?? spec.transitionDuration;
  if (deckDuration !== undefined && (typeof deckDuration !== "number" || deckDuration < 0)) {
    errors.push("Deck-level transitionDuration must be a non-negative number");
  }

  return errors;
}

// ── config.ts generation ────────────────────────────────────────────────────

function generateConfigTs(spec, specFilename) {
  const slides = spec.slides;
  const title = escapeTs(spec.meta.title);
  const password = escapeTs(spec.meta?.password || "");
  const deckTransition = spec.design?.transition ?? spec.transition ?? "fade";
  const deckTransitionDuration = spec.design?.transitionDuration ?? spec.transitionDuration ?? 400;

  const slideEntryLines = slides.map((s) => {
    const displayId = s.id.replace(/^\d+-/, "");
    const parts = [
      `    id: "${escapeTs(displayId)}"`,
      `    fileKey: "${escapeTs(s.id)}"`,
      `    title: "${escapeTs(s.title || s.headline || s.text || s.quote || s.id)}"`,
      `    shortTitle: "${escapeTs(s.shortTitle || displayId)}"`,
    ];
    if (s.notes) {
      parts.push(`    notes: "${escapeTs(s.notes)}"`);
    }
    if (s.transition) {
      parts.push(`    transition: "${escapeTs(s.transition)}"`);
    }
    if (s.transitionDuration !== undefined) {
      parts.push(`    transitionDuration: ${s.transitionDuration}`);
    }
    return `  {\n${parts.join(",\n")},\n  }`;
  });

  const moduleLines = slides.map((s) => {
    return `  "${escapeTs(s.id)}": () => import("./slides/${escapeTs(s.id)}")`;
  });

  return `// Generated from ${escapeTs(specFilename)}
import { lazy, type ComponentType } from "react";

export type TransitionType = "none" | "fade" | "slide" | "scale";

/**
 * Deck configuration — title, auth, design, navigation, and transition defaults.
 */
export const config = {
  title: "${title}",

  auth: {
    password: "${password}",
  },

  design: {
    width: 1920,
    height: 1080,
    minViewportWidth: 375,
  },

  navigation: {
    autoCollapseDelay: 3000,
  },

  transition: "${deckTransition}" as TransitionType,
  transitionDuration: ${deckTransitionDuration},
} as const;

// ---------------------------------------------------------------------------
// Slide registry
// ---------------------------------------------------------------------------

export interface SlideEntry {
  id: string;
  fileKey: string;
  title: string;
  shortTitle: string;
  notes?: string;
  transition?: TransitionType;
  transitionDuration?: number;
}

export const slides: SlideEntry[] = [
${slideEntryLines.join(",\n")},
];

export const totalSlides = slides.length;

// ---------------------------------------------------------------------------
// Lazy component loader
// ---------------------------------------------------------------------------

const slideModules: Record<string, () => Promise<{ default: ComponentType }>> = {
${moduleLines.join(",\n")},
};

const lazySlides: Record<string, ComponentType> = Object.fromEntries(
  Object.entries(slideModules).map(([key, loader]) => [key, lazy(loader)])
);

const NullComponent = () => null;

export function getSlideComponent(slideNumber: number): ComponentType {
  const index = slideNumber - 1;
  if (index < 0 || index >= slides.length) return NullComponent;
  return lazySlides[slides[index].fileKey] ?? NullComponent;
}

export function preloadSlide(slideNumber: number): void {
  const index = slideNumber - 1;
  if (index < 0 || index >= slides.length) return;
  const fileKey = slides[index].fileKey;
  slideModules[fileKey]?.();
}

export const slideList = slides.map((s, i) => ({
  number: i + 1,
  title: s.title,
  shortTitle: s.shortTitle,
}));
`;
}

// ── Design overrides ────────────────────────────────────────────────────────

function applyDesignOverrides(outputDir, spec) {
  const design = spec.design || {};
  const cssPath = resolve(outputDir, "src/styles/globals.css");
  const htmlPath = resolve(outputDir, "index.html");

  if (!existsSync(cssPath)) return;

  let css = readFileSync(cssPath, "utf-8");
  let html = existsSync(htmlPath) ? readFileSync(htmlPath, "utf-8") : null;
  let cssChanged = false;
  let htmlChanged = false;

  // Primary color → --color-orange and --color-orange-muted
  if (design.primaryColor) {
    const pc = design.primaryColor;
    const muted = darkenHex(pc);
    css = css.replace(/--color-orange:\s*[^;]+;/, `--color-orange: ${pc};`);
    css = css.replace(/--color-orange-muted:\s*[^;]+;/, `--color-orange-muted: ${muted};`);
    cssChanged = true;
    console.error(`Applied primaryColor: ${pc} (muted: ${muted})`);
  }

  // Font overrides → CSS custom properties
  if (design.fontHeading) {
    css = css.replace(
      /--font-heading:\s*[^;]+;/,
      `--font-heading: "${design.fontHeading}", "Editorial New", Georgia, serif;`,
    );
    cssChanged = true;
    console.error(`Applied fontHeading: ${design.fontHeading}`);
  }

  if (design.fontBody) {
    css = css.replace(
      /--font-body:\s*[^;]+;/,
      `--font-body: "${design.fontBody}", system-ui, -apple-system, sans-serif;`,
    );
    cssChanged = true;
    console.error(`Applied fontBody: ${design.fontBody}`);
  }

  if (cssChanged) {
    writeFileSync(cssPath, css, "utf-8");
  }

  // Google Fonts link — rebuild if heading or body font changed
  if (html && (design.fontHeading || design.fontBody)) {
    const newLink = buildGoogleFontsLink(design.fontHeading, design.fontBody);
    html = html.replace(
      /href="https:\/\/fonts\.googleapis\.com\/css2\?[^"]*"/,
      `href="${newLink}"`,
    );
    htmlChanged = true;
  }

  // Update <title> to match deck title
  if (html && spec.meta?.title) {
    html = html.replace(/<title>[^<]*<\/title>/, `<title>${escapeHtml(spec.meta.title)}</title>`);
    htmlChanged = true;
  }

  if (htmlChanged) {
    writeFileSync(htmlPath, html, "utf-8");
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function buildGoogleFontsLink(headingFont, bodyFont) {
  const families = [];

  // Heading font (variable weight + italic)
  const hf = (headingFont || "Playfair Display").replace(/ /g, "+");
  families.push(`family=${hf}:ital,wght@0,400..900;1,400..900`);

  // Mono font (always included)
  families.push("family=IBM+Plex+Mono:wght@300;400;500;600");

  // Body font — only add if it's not a system font
  const SYSTEM_BODY = new Set(["inter", "system-ui", "-apple-system", "sans-serif"]);
  if (bodyFont && !SYSTEM_BODY.has(bodyFont.toLowerCase())) {
    const bf = bodyFont.replace(/ /g, "+");
    families.push(`family=${bf}:wght@300;400;500;600;700`);
  }

  return `https://fonts.googleapis.com/css2?${families.join("&")}&display=swap`;
}

// ── Slide file scaffolding ──────────────────────────────────────────────────

function createSlideFiles(outputDir, slides) {
  const slidesDir = resolve(outputDir, "src/slides");
  mkdirSync(slidesDir, { recursive: true });

  for (const slide of slides) {
    const filePath = resolve(slidesDir, `${slide.id}.tsx`);
    const components = COMPONENT_MAP[slide.type] || [];
    const mode = slide.mode || "dark";
    const funcName = `Slide_${slide.id.replace(/[^a-zA-Z0-9]/g, "_")}`;

    const content = `import { SlideWrapper } from "../components/layout/SlideWrapper";
// TODO: Import components for "${slide.type}" template:
// Recommended: ${components.join(", ")}

export default function ${funcName}() {
  return (
    <SlideWrapper mode="${mode}">
      <div className="flex items-center justify-center h-full w-full">
        <p className="text-sm opacity-40">Slide: ${slide.id} (${slide.type})</p>
      </div>
    </SlideWrapper>
  );
}
`;
    writeFileSync(filePath, content, "utf-8");
  }
}

// ── Main ────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: node scripts/init-deck-from-spec.mjs <spec.yaml> [output-dir]");
    process.exit(1);
  }

  const specPath = resolve(args[0]);
  const outputDir = resolve(args[1] || `./${basename(specPath, ".yaml")}-deck`);

  if (!existsSync(specPath)) {
    console.error(`Spec file not found: ${specPath}`);
    process.exit(1);
  }

  // Parse YAML
  let spec;
  try {
    const raw = readFileSync(specPath, "utf-8");
    spec = parseYaml(raw);
  } catch (err) {
    console.error(`Failed to parse YAML: ${err.message}`);
    process.exit(1);
  }

  // Validate — collect all errors before any filesystem writes
  const errors = validate(spec);
  if (errors.length > 0) {
    console.error("Validation failed:");
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }

  // Copy scaffold
  if (existsSync(outputDir)) {
    console.error(`Output directory already exists: ${outputDir}`);
    process.exit(1);
  }

  console.error(`Copying scaffold to ${outputDir}...`);
  cpSync(SCAFFOLD_DIR, outputDir, { recursive: true });

  // Generate config.ts
  const configTs = generateConfigTs(spec, basename(specPath));
  writeFileSync(resolve(outputDir, "src/config.ts"), configTs, "utf-8");
  console.error("Generated src/config.ts");

  // Create slide files
  createSlideFiles(outputDir, spec.slides);
  console.error(`Created ${spec.slides.length} slide files in src/slides/`);

  // Apply design overrides
  applyDesignOverrides(outputDir, spec);

  // Summary
  console.error("\n--- Deck initialized ---");
  console.error(`Title: ${spec.meta.title}`);
  console.error(`Slides: ${spec.slides.length}`);
  console.error(`Password: ${spec.meta?.password || "(none)"}`);
  const deckTransition = spec.design?.transition ?? spec.transition ?? "fade";
  console.error(`Transition: ${deckTransition}`);
  console.error("\nSlide breakdown:");
  for (const slide of spec.slides) {
    const components = COMPONENT_MAP[slide.type] || [];
    const extras = [];
    if (slide.notes) extras.push("notes");
    if (slide.transition) extras.push(`transition:${slide.transition}`);
    const suffix = extras.length ? ` (${extras.join(", ")})` : "";
    console.error(`  ${slide.id} [${slide.type}] → ${components.join(", ") || "custom"}${suffix}`);
  }
  console.error(`\nNext steps:`);
  console.error(`  cd ${outputDir}`);
  console.error(`  npm install`);
  console.error(`  npm run dev`);
}

main();
