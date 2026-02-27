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
        .slide-wrapper {
          min-height: unset !important;
          height: auto !important;
          padding: 0 !important;
          margin: 0 !important;
          display: block !important;
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
  const outputPath = path.join(outputDir, `aldea-deck-${timestamp}.pdf`);

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
