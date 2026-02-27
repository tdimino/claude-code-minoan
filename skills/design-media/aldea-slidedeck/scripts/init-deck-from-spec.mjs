#!/usr/bin/env node

/**
 * init-deck-from-spec.mjs
 *
 * Initialize an Overwatch Mode deck from a YAML spec file.
 * Copies the scaffold, generates config.ts, creates empty slide files,
 * and reports which components to import per slide type.
 *
 * Usage:
 *   node init-deck-from-spec.mjs <spec.yaml> [output-dir]
 */

import { readFileSync, writeFileSync, mkdirSync, cpSync, existsSync } from "node:fs";
import { resolve, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCAFFOLD_DIR = resolve(__dirname, "../assets/scaffold-overwatch");

// Component imports recommended per slide type
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

function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: node init-deck-from-spec.mjs <spec.yaml> [output-dir]");
    process.exit(1);
  }

  const specPath = resolve(args[0]);
  const outputDir = resolve(args[1] || `./${basename(specPath, ".yaml")}-deck`);

  if (!existsSync(specPath)) {
    console.error(`Spec file not found: ${specPath}`);
    process.exit(1);
  }

  // Parse YAML spec
  let spec;
  try {
    const raw = readFileSync(specPath, "utf-8");
    spec = parseYaml(raw);
  } catch (err) {
    console.error(`Failed to parse YAML: ${err.message}`);
    process.exit(1);
  }

  if (!spec.slides || !Array.isArray(spec.slides)) {
    console.error("Spec must contain a 'slides' array.");
    process.exit(1);
  }

  // Copy scaffold
  if (existsSync(outputDir)) {
    console.error(`Output directory already exists: ${outputDir}`);
    process.exit(1);
  }

  console.log(`Copying scaffold to ${outputDir}...`);
  cpSync(SCAFFOLD_DIR, outputDir, { recursive: true });

  // Generate config.ts
  const slides = spec.slides;
  const slideEntries = slides.map((s) => {
    const id = s.id.replace(/^\d+-/, "");
    return `  { id: "${id}", fileKey: "${s.id}", title: "${s.title || s.id}", shortTitle: "${s.shortTitle || id}" }`;
  });

  const slideModules = slides.map((s) => {
    return `  "${s.id}": () => import("./slides/${s.id}")`;
  });

  const password = spec.meta?.password || "";
  const title = spec.meta?.title || "Presentation";

  const configTs = `// Auto-generated from ${basename(specPath)}
import type { SlideEntry } from "./types";

export const config = {
  title: "${title}",
  auth: { password: "${password}" },
};

export const slides: SlideEntry[] = [
${slideEntries.join(",\n")},
];

export const slideModules: Record<string, () => Promise<{ default: React.ComponentType }>> = {
${slideModules.join(",\n")},
};
`;

  writeFileSync(resolve(outputDir, "src/config.ts"), configTs, "utf-8");
  console.log("Generated src/config.ts");

  // Create empty slide files
  const slidesDir = resolve(outputDir, "src/slides");
  mkdirSync(slidesDir, { recursive: true });

  for (const slide of slides) {
    const filePath = resolve(slidesDir, `${slide.id}.tsx`);
    const components = COMPONENT_MAP[slide.type] || [];
    const mode = slide.mode || "dark";

    const content = `import { SlideWrapper } from "../components/layout/SlideWrapper";
// TODO: Import components for "${slide.type}" template:
// Recommended: ${components.join(", ")}

export default function Slide_${slide.id.replace(/[^a-zA-Z0-9]/g, "_")}() {
  return (
    <SlideWrapper mode="${mode}">
      {/* Template: ${slide.type} */}
      {/* See overwatch-slide-templates.md for composition example */}
    </SlideWrapper>
  );
}
`;
    writeFileSync(filePath, content, "utf-8");
  }

  console.log(`Created ${slides.length} slide files in src/slides/`);

  // Apply design overrides if specified
  if (spec.design?.primaryColor) {
    const cssPath = resolve(outputDir, "src/styles.css");
    if (existsSync(cssPath)) {
      let css = readFileSync(cssPath, "utf-8");
      css = css.replace(/--color-orange:\s*[^;]+;/, `--color-orange: ${spec.design.primaryColor};`);
      writeFileSync(cssPath, css, "utf-8");
      console.log(`Applied primary color override: ${spec.design.primaryColor}`);
    }
  }

  // Summary
  console.log("\n--- Deck initialized ---");
  console.log(`Title: ${title}`);
  console.log(`Slides: ${slides.length}`);
  console.log(`Password: ${password || "(none)"}`);
  console.log("\nSlide breakdown:");
  for (const slide of slides) {
    const components = COMPONENT_MAP[slide.type] || [];
    console.log(`  ${slide.id} [${slide.type}] → ${components.join(", ") || "custom"}`);
  }
  console.log(`\nNext steps:`);
  console.log(`  cd ${outputDir}`);
  console.log(`  npm install`);
  console.log(`  npm run dev`);
  console.log(`  # Then fill in each slide using the spec + overwatch-slide-templates.md`);
}

main();
