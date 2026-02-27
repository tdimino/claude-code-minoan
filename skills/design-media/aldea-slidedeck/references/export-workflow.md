# Export Workflow

Complete guide for exporting Aldea slide decks to PDF and static HTML.

---

## Quick Reference

```bash
# Static HTML (shareable folder)
npm run export          # Output: out/

# PDF (multi-page document)
npm run dev &           # Start dev server first
npm run pdf             # Output: output/[name]-YYYY-MM-DD.pdf

# Distribution package
zip -rq deck.zip out/   # Creates deck.zip
```

---

## Static HTML Export

Build a static version that can be hosted anywhere or opened directly in browser.

### Command

```bash
npm run export
```

### Output

```
out/
├── index.html          # Main page
├── _next/              # Next.js assets
│   ├── static/         # CSS, JS bundles
│   └── ...
└── images/             # Copied from public/images
```

### Configuration (next.config.js)

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',           // Enable static export
  images: {
    unoptimized: true,        // Disable Next.js Image optimization
  },
};

module.exports = nextConfig;
```

### Hosting Options

**Local viewing:**
```bash
# Open directly in browser
open out/index.html

# Or serve with a local server
npx serve out
```

**Vercel (recommended):**
```bash
npm i -g vercel
vercel                        # Follow prompts
# Result: https://your-deck.vercel.app
```

**Netlify:**
```bash
# Drag-and-drop out/ folder to netlify.com
# Or use Netlify CLI:
npm i -g netlify-cli
netlify deploy --dir=out
```

**GitHub Pages:**
```bash
# Push out/ folder to gh-pages branch
# Or configure GitHub Actions
```

---

## PDF Export

Generate a multi-page PDF using Puppeteer.

### Prerequisites

1. **Dev server running** — PDF script connects to localhost
2. **Puppeteer installed** — `npm install puppeteer`

### Commands

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Generate PDF
npm run pdf
```

### Output

```
output/
└── aldea-journey-2026-01-06.pdf    # Date-stamped PDF
```

### Script (scripts/export-pdf.js)

```js
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function exportToPDF() {
  console.log('🚀 Starting PDF export...');

  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu'
    ]
  });

  const page = await browser.newPage();

  // Set viewport to match slide dimensions (16:9)
  await page.setViewport({
    width: 1280,
    height: 720,
    deviceScaleFactor: 2
  });

  const url = process.env.URL || 'http://localhost:3200';
  console.log(`📡 Connecting to ${url}...`);

  try {
    await page.goto(url, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });
  } catch (error) {
    console.error('❌ Failed to connect. Make sure the dev server is running:');
    console.error('   npm run dev');
    process.exit(1);
  }

  // Wait for fonts to load
  await page.evaluateHandle('document.fonts.ready');
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Inject print CSS to make each .slide a separate page
  await page.addStyleTag({
    content: `
      @media print {
        @page {
          size: 1280px 720px;
          margin: 0;
        }
        body {
          margin: 0;
          padding: 0;
        }
        .slide {
          width: 1280px !important;
          height: 720px !important;
          page-break-after: always;
          page-break-inside: avoid;
          break-after: page;
          break-inside: avoid;
        }
        .slide:last-child {
          page-break-after: auto;
        }
      }
    `
  });

  const slideCount = await page.evaluate(() => {
    return document.querySelectorAll('.slide').length;
  });
  console.log(`📊 Found ${slideCount} slides`);

  const outputDir = path.join(__dirname, '..', 'output');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().split('T')[0];
  const outputPath = path.join(outputDir, `aldea-journey-${timestamp}.pdf`);

  console.log('📄 Generating PDF...');

  await page.pdf({
    path: outputPath,
    width: '1280px',
    height: '720px',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 }
  });

  console.log(`\n✅ PDF exported to: ${outputPath}`);

  await browser.close();
}

exportToPDF().catch(console.error);
```

### Customization

**Change output filename:**
```js
const outputPath = path.join(outputDir, `my-deck-${timestamp}.pdf`);
```

**Change port:**
```bash
URL=http://localhost:3000 npm run pdf
```

**Increase wait time (for slow-loading content):**
```js
await new Promise(resolve => setTimeout(resolve, 5000)); // 5 seconds
```

---

## Print CSS Requirements

Your slides must have the `.slide` class and proper print styles.

### Slide Class

```tsx
// In SlideLayout.tsx
<div className="slide relative ...">
  {children}
</div>
```

### Print Styles (globals.css)

```css
@media print {
  @page {
    size: 1280px 720px;
    margin: 0;
  }

  body {
    margin: 0;
    padding: 0;
  }

  .slide {
    width: 1280px !important;
    height: 720px !important;
    page-break-after: always;
    page-break-inside: avoid;
    break-after: page;
    break-inside: avoid;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .slide:last-child {
    page-break-after: auto;
  }
}
```

### Color Preservation

The `-webkit-print-color-adjust: exact` and `print-color-adjust: exact` properties ensure backgrounds and colors are preserved in print/PDF output.

---

## Distribution Package

Create a zip file for easy sharing.

### Command

```bash
# Create zip from static export
zip -rq deck.zip out/

# Or include PDF
zip -rq deck-bundle.zip out/ output/*.pdf
```

### Full Export Script

```bash
#!/bin/bash
# export-all.sh

echo "Building static export..."
npm run export

echo "Starting dev server..."
npm run dev &
DEV_PID=$!
sleep 5

echo "Generating PDF..."
npm run pdf

echo "Stopping dev server..."
kill $DEV_PID

echo "Creating zip..."
rm -f deck.zip
zip -rq deck.zip out/

echo "Done!"
ls -la deck.zip
```

---

## Troubleshooting

### PDF is empty

**Cause:** Dev server not running or wrong port.

**Fix:**
```bash
# Make sure dev server is running
npm run dev
# Check it's accessible
curl http://localhost:3200
```

### All slides show the same content

**Cause:** Print CSS not properly set up.

**Fix:** Ensure `.slide` class is on each slide and print CSS includes `page-break-after: always`.

### Colors look wrong in PDF

**Cause:** Print color adjustment not set.

**Fix:** Add to your CSS:
```css
.slide {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
```

### Fonts not loading

**Cause:** Fonts not fully loaded before PDF generation.

**Fix:** Increase wait time in export-pdf.js:
```js
await page.evaluateHandle('document.fonts.ready');
await new Promise(resolve => setTimeout(resolve, 3000)); // Increase to 3s
```

### Static export fails

**Cause:** Dynamic routes or server-side features used.

**Fix:** Ensure all pages are static. Check next.config.js has:
```js
output: 'export',
images: { unoptimized: true }
```

### Slides overflow page boundaries

**Cause:** Content taller than 720px.

**Fix:**
1. Use `flex-1` for content areas to auto-fit
2. Reduce content or font sizes
3. Use `overflow-hidden` on slide containers

---

## Package.json Scripts

```json
{
  "scripts": {
    "dev": "next dev -p 3200",
    "build": "next build",
    "export": "next build",
    "pdf": "node scripts/export-pdf.js"
  }
}
```

---

## Checklist Before Export

- [ ] All slides render correctly at 1280×720
- [ ] Slide numbers are sequential
- [ ] Total slide count in SlideLayout is accurate
- [ ] Images are in public/images/
- [ ] Fonts are loaded (Google Fonts in _document.tsx)
- [ ] Print styles are in globals.css
- [ ] Dev server starts without errors
