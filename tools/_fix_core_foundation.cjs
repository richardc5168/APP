#!/usr/bin/env node
/**
 * Add L4 hints and improve common_mistakes for interactive-g56-core-foundation.
 * - All 102 questions currently have 3-level hints → add L4 from commonMistake field.
 * - All 102 have placeholder common_mistakes → derive from commonMistake field.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const BANK_PATH = path.join(__dirname, '..', 'docs', 'interactive-g56-core-foundation', 'g56_core_foundation.json');
const DIST_PATH = path.join(__dirname, '..', 'dist_ai_math_web_pages', 'docs', 'interactive-g56-core-foundation', 'g56_core_foundation.json');

const data = JSON.parse(fs.readFileSync(BANK_PATH, 'utf8'));

let l4Added = 0;
let cmFixed = 0;

for (const q of data) {
  // --- Add L4 hint ---
  if (q.hints && q.hints.length === 3 && q.commonMistake) {
    // Build L4 from commonMistake
    const cm = q.commonMistake.trim();
    const l4 = '\u{1F4CC} 常見錯誤：' + cm + ' 做完後回頭檢查一次！';
    q.hints.push(l4);
    l4Added++;
  }

  // --- Fix common_mistakes ---
  const isPlaceholder = Array.isArray(q.common_mistakes) &&
    q.common_mistakes.length === 2 &&
    q.common_mistakes[0] === '計算粗心。' &&
    q.common_mistakes[1] === '單位或標記寫錯。';

  if (isPlaceholder && q.commonMistake) {
    // Split commonMistake by semicolons/periods to get distinct mistakes
    const parts = q.commonMistake
      .split(/[；;]/)
      .map(s => s.replace(/^或/, '').trim())
      .filter(s => s.length > 4);
    if (parts.length >= 2) {
      q.common_mistakes = parts.map(p => p.endsWith('。') ? p : p + '。');
    } else if (parts.length === 1) {
      q.common_mistakes = [
        parts[0].endsWith('。') ? parts[0] : parts[0] + '。',
        '計算過程粗心導致數字錯誤。'
      ];
    }
    cmFixed++;
  }
}

// Write back
const out = JSON.stringify(data, null, 2) + '\n';
fs.writeFileSync(BANK_PATH, out, 'utf8');
if (fs.existsSync(path.dirname(DIST_PATH))) {
  fs.writeFileSync(DIST_PATH, out, 'utf8');
  console.log('  Synced to dist');
}

console.log('L4 hints added:', l4Added);
console.log('CM entries fixed:', cmFixed);
console.log('Total questions:', data.length);
