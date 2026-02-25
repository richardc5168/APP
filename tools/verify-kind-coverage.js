#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';

const ROOT = process.cwd();
const FALLBACK_WHITELIST = new Set([
  'generic_fraction_word',
]);

function parseBankKinds(bankText) {
  const match = bankText.match(/window\.FRACTION_WORD_G5_BANK\s*=\s*(\[[\s\S]*\])\s*;\s*$/);
  if (!match) throw new Error('Cannot parse bank.js payload');
  const arr = JSON.parse(match[1]);
  const items = arr.map((q) => ({ id: String(q?.id || ''), kind: String(q?.kind || '') }));
  return items;
}

function parseKindOptions(htmlText) {
  const selectMatch = htmlText.match(/<select\s+id="kind"[\s\S]*?<\/select>/i);
  if (!selectMatch) throw new Error('Cannot find <select id="kind"> in HTML');
  const options = [];
  const re = /<option\s+value="([^"]+)"/g;
  let m;
  while ((m = re.exec(selectMatch[0])) !== null) {
    options.push(String(m[1] || '').trim());
  }
  return new Set(options.filter(Boolean));
}

async function main() {
  const docsBankPath = path.join(ROOT, 'docs', 'interactive-g5-national-bank', 'bank.js');
  const distBankPath = path.join(ROOT, 'dist_ai_math_web_pages', 'docs', 'interactive-g5-national-bank', 'bank.js');
  const docsHtmlPath = path.join(ROOT, 'docs', 'interactive-g5-national-bank', 'index.html');
  const distHtmlPath = path.join(ROOT, 'dist_ai_math_web_pages', 'docs', 'interactive-g5-national-bank', 'index.html');

  const [docsBank, distBank, docsHtml, distHtml] = await Promise.all([
    fs.readFile(docsBankPath, 'utf8'),
    fs.readFile(distBankPath, 'utf8'),
    fs.readFile(docsHtmlPath, 'utf8'),
    fs.readFile(distHtmlPath, 'utf8'),
  ]);

  const docsKinds = parseBankKinds(docsBank);
  const distKinds = parseBankKinds(distBank);
  const docsOptions = parseKindOptions(docsHtml);
  const distOptions = parseKindOptions(distHtml);

  const uiKinds = new Set([...docsOptions].filter((x) => x !== 'all'));
  const distUiKinds = new Set([...distOptions].filter((x) => x !== 'all'));

  const bankKinds = new Set(docsKinds.map((x) => x.kind));
  const distBankKinds = new Set(distKinds.map((x) => x.kind));

  const issues = [];

  for (const kind of bankKinds) {
    if (!uiKinds.has(kind) && !FALLBACK_WHITELIST.has(kind)) {
      const ids = docsKinds.filter((x) => x.kind === kind).map((x) => x.id).slice(0, 20);
      issues.push({ kind, ids });
    }
  }

  if (bankKinds.size !== distBankKinds.size || [...bankKinds].some((k) => !distBankKinds.has(k))) {
    issues.push({ kind: '__DOCS_DIST_KIND_SET_MISMATCH__', ids: [] });
  }

  if (uiKinds.size !== distUiKinds.size || [...uiKinds].some((k) => !distUiKinds.has(k))) {
    issues.push({ kind: '__DOCS_DIST_UI_KIND_SET_MISMATCH__', ids: [] });
  }

  if (issues.length) {
    console.error('FAIL: kind coverage check failed');
    for (const item of issues) {
      if (item.ids.length) {
        console.error(`- missing kind: ${item.kind} | question_ids: ${item.ids.join(', ')}`);
      } else {
        console.error(`- ${item.kind}`);
      }
    }
    process.exit(1);
  }

  console.log(`PASS: kind coverage OK (bank kinds=${bankKinds.size}, ui kinds=${uiKinds.size})`);
}

main().catch((err) => {
  console.error('FAIL: verify-kind-coverage crashed');
  console.error(String(err?.stack || err));
  process.exit(1);
});
