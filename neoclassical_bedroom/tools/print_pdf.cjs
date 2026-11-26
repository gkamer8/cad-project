// Print an HTML file to a 17 x 11 in PDF with Playwright's Chromium.
//   node tools/print_pdf.cjs /abs/path/review.html /abs/path/out.pdf
const { chromium } = require('playwright');

(async () => {
  const [input, output] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + input, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: output, width: '17in', height: '11in', printBackground: true, preferCSSPageSize: true });
  await browser.close();
})();
