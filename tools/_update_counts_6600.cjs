#!/usr/bin/env node
/**
 * Update "6400" references to "6600" across dashboard/marketing HTML files.
 * Skips 86400000 (milliseconds in a day).
 */
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const files = [
  'docs/index.html',
  'docs/about/index.html',
  'docs/interactive-g5-empire/index.html',
  'docs/parent-report/index.html',
  'docs/pricing/index.html',
  'dist_ai_math_web_pages/docs/index.html',
  'dist_ai_math_web_pages/docs/about/index.html',
  'dist_ai_math_web_pages/docs/interactive-g5-empire/index.html',
  'dist_ai_math_web_pages/docs/parent-report/index.html',
  'dist_ai_math_web_pages/docs/pricing/index.html',
];

let totalChanges = 0;

for (const f of files) {
  const p = path.join(ROOT, f);
  if (!fs.existsSync(p)) { console.log('SKIP', f); continue; }
  let s = fs.readFileSync(p, 'utf8');
  const before = s;

  // Replace "6400+" but NOT "86400000" etc.
  // Pattern: 6400 preceded by NOT a digit
  s = s.replace(/(?<!\d)6400\+/g, '6600+');
  s = s.replace(/data-target="6400"/g, 'data-target="6600"');
  s = s.replace(/data-count="6200"/g, 'data-count="6600"');
  // Handle cases like "(6400+" or "6400+ 題"
  s = s.replace(/(?<!\d)6400(?=\s*題)/g, '6600');
  s = s.replace(/(?<!\d)6400(?=\s*道)/g, '6600');

  if (s !== before) {
    fs.writeFileSync(p, s, 'utf8');
    totalChanges++;
    console.log('  Updated:', f);
  } else {
    console.log('  No change:', f);
  }
}

console.log('\nFiles updated:', totalChanges);
