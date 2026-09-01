#!/usr/bin/env node

/**
 * export-deck.mjs
 *
 * Export an Overwatch Mode deck to PNG screenshots and optionally a merged PDF.
 * Requires a running dev server (or preview build).
 *
 * Usage:
 *   node export-deck.mjs [--url http://localhost:5173] [--out ./export] [--pdf] [--slides N]
 */

import { chromium } from "playwright";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { PDFDocument } from "pdf-lib";

const args = process.argv.slice(2);

function getArg(flag, fallback) {
  const idx = args.indexOf(flag);
  if (idx === -1) return fallback;
  return args[idx + 1] || fallback;
}

const baseUrl = getArg("--url", "http://localhost:5173");
const outDir = resolve(getArg("--out", "./export"));
const wantPdf = args.includes("--pdf");
const slidesOverride = getArg("--slides", null);

async function detectSlideCount(page) {
  if (slidesOverride) return parseInt(slidesOverride, 10);

  await page.goto(`${baseUrl}/deck/1?static=1`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);

  const count = await page.evaluate(() => {
    const counter = document.querySelector("[data-slide-counter]");
    if (counter) {
      const text = counter.textContent || "";
      const match = text.match(/\/(\d+)/);
      if (match) return parseInt(match[1], 10);
    }
    const el = document.querySelectorAll("[data-slide-total]");
    if (el.length > 0) {
      const val = el[0].getAttribute("data-slide-total");
      if (val) return parseInt(val, 10);
    }
    return 0;
  });

  if (count > 0) return count;

  let slideCount = 1;
  for (let n = 2; n <= 200; n++) {
    const response = await page.goto(`${baseUrl}/deck/${n}?static=1`, {
      waitUntil: "domcontentloaded",
    });
    const url = page.url();
    if (!response || response.status() >= 400 || !url.includes(`/deck/${n}`)) break;
    slideCount = n;
  }
  return slideCount;
}

async function main() {
  console.log(`Exporting deck from ${baseUrl}`);
  mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();
  await page.emulateMedia({ reducedMotion: "reduce" });

  const totalSlides = await detectSlideCount(page);
  if (totalSlides < 1) {
    console.error("Could not detect slide count. Pass --slides N explicitly.");
    await browser.close();
    process.exit(1);
  }
  console.log(`Detected ${totalSlides} slides`);

  const pngPaths = [];

  for (let n = 1; n <= totalSlides; n++) {
    const url = `${baseUrl}/deck/${n}?static=1`;
    console.log(`  Capturing slide ${n}/${totalSlides}...`);
    await page.goto(url, { waitUntil: "networkidle" });
    await page.waitForTimeout(800);

    const filename = `slide-${String(n).padStart(2, "0")}.png`;
    const filepath = resolve(outDir, filename);
    await page.screenshot({ path: filepath, fullPage: false });
    pngPaths.push(filepath);
  }

  console.log(`Saved ${pngPaths.length} PNGs to ${outDir}`);

  if (wantPdf && pngPaths.length > 0) {
    console.log("Generating PDF...");
    const pdfDoc = await PDFDocument.create();

    for (const pngPath of pngPaths) {
      const pngBytes = readFileSync(pngPath);
      const pngImage = await pdfDoc.embedPng(pngBytes);
      const { width, height } = pngImage.scale(1);
      const pdfPage = pdfDoc.addPage([width, height]);
      pdfPage.drawImage(pngImage, { x: 0, y: 0, width, height });
    }

    const pdfBytes = await pdfDoc.save();
    const pdfPath = resolve(outDir, "deck.pdf");
    writeFileSync(pdfPath, pdfBytes);
    console.log(`Saved PDF to ${pdfPath}`);
  }

  await browser.close();
  console.log("Done.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
