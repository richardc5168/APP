#!/usr/bin/env node
'use strict';
var fs = require('fs');
var path = require('path');
var files = [
  'docs/index.html','docs/about/index.html','docs/interactive-g5-empire/index.html',
  'docs/parent-report/index.html','docs/pricing/index.html',
  'dist_ai_math_web_pages/docs/index.html','dist_ai_math_web_pages/docs/about/index.html',
  'dist_ai_math_web_pages/docs/interactive-g5-empire/index.html',
  'dist_ai_math_web_pages/docs/parent-report/index.html','dist_ai_math_web_pages/docs/pricing/index.html'
];
var root = path.join(__dirname, '..');
var count = 0;
files.forEach(function(f) {
  var fp = path.join(root, f);
  if (!fs.existsSync(fp)) return;
  var src = fs.readFileSync(fp, 'utf8');
  var out = src.replace(/(?<!\d)6700/g, '6800');
  if (out !== src) {
    fs.writeFileSync(fp, out, 'utf8');
    count += (src.match(/(?<!\d)6700/g) || []).length;
    console.log('Updated', f);
  }
});
console.log('Total replacements:', count);
