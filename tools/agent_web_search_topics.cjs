const fs = require('fs');
const path = require('path');

const cwd = process.cwd();
const goldenPath = path.join(cwd, 'golden', 'grade5_pack_v1.jsonl');
const memoryPath = path.join(cwd, 'golden', 'error_memory.jsonl');
const reportPath = path.join(cwd, 'artifacts', 'agent_web_search_report.json');

const SOURCE_URLS = [
  'https://www.khanacademy.org/math/cc-fifth-grade-math',
  'https://www.khanacademy.org/math/cc-sixth-grade-math',
  'https://www.mathsisfun.com/',
  'https://www.ck12.org/student/',
];

const TOPIC_KEYWORDS = [
  'fraction',
  'decimal',
  'ratio',
  'percent',
  'geometry',
  'volume',
  'area',
  'perimeter',
  'equation',
  'word problem',
  'place value',
  'coordinate',
  'mixed number',
  'common denominator',
  'unit rate',
];

function readJsonl(filePath) {
  if (!fs.existsSync(filePath)) return [];
  return fs.readFileSync(filePath, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function writeJsonl(filePath, rows) {
  const content = rows.map((row) => JSON.stringify(row)).join('\n') + '\n';
  fs.writeFileSync(filePath, content, 'utf8');
}

function sanitizeText(text = '') {
  return String(text)
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function pickKeywordsFromContent(content) {
  const lower = content.toLowerCase();
  return TOPIC_KEYWORDS.filter((k) => lower.includes(k)).slice(0, 6);
}

async function fetchTopicSignals() {
  const signals = [];
  for (const url of SOURCE_URLS) {
    try {
      const res = await fetch(url, { redirect: 'follow' });
      if (!res.ok) {
        signals.push({ url, ok: false, status: res.status, matched_topics: [] });
        continue;
      }
      const html = await res.text();
      const text = sanitizeText(html);
      const matched = pickKeywordsFromContent(text);
      signals.push({ url, ok: true, status: res.status, matched_topics: matched });
    } catch (err) {
      signals.push({ url, ok: false, status: 'fetch-error', matched_topics: [], error: String(err?.message || err) });
    }
  }
  return signals;
}

function selectedRows(rows, maxCount) {
  const ranked = rows
    .map((item, idx) => ({
      idx,
      id: item?.id,
      hintLen: JSON.stringify(item?.hint_ladder || {}).length,
    }))
    .sort((a, b) => a.hintLen - b.hintLen);
  return ranked.slice(0, Math.max(1, maxCount)).map((x) => x.idx);
}

function containsAnswerLeak(item) {
  const answer = String(item?.answer ?? '').trim();
  if (!answer) return false;
  const h3 = String(item?.hint_ladder?.h3_compute || '');
  const h2 = String(item?.hint_ladder?.h2_equation || '');
  return h2.includes(answer) || h3.includes(answer);
}

function optimizeItem(item, topics, memoryRows) {
  const out = JSON.parse(JSON.stringify(item));
  const hint = out.hint_ladder || {};
  const report = out.report_expectations || {};

  const topicPhrase = topics.length > 0 ? topics.join('、') : '分數與小數應用';
  const memoryHint = memoryRows.length > 0 ? '避免重複過去常見錯誤，先確認單位與題意。' : '先確認題意與單位是否一致。';

  if (typeof hint.h1_strategy === 'string' && !hint.h1_strategy.includes('先畫出關係')) {
    hint.h1_strategy = `${hint.h1_strategy} 先畫出關係或列出已知/未知。`;
  }
  if (typeof hint.h2_equation === 'string' && !hint.h2_equation.includes('先寫算式框架')) {
    hint.h2_equation = `${hint.h2_equation} 先寫算式框架，再代入數字。`;
  }
  if (typeof hint.h3_compute === 'string') {
    hint.h3_compute = `${hint.h3_compute} ${memoryHint}`;
  }
  if (typeof hint.h4_check_reflect === 'string' && !hint.h4_check_reflect.includes('反向驗算')) {
    hint.h4_check_reflect = `${hint.h4_check_reflect} 用反向驗算確認答案合理。`;
  }

  const misconceptions = Array.isArray(report.misconceptions) ? report.misconceptions.slice() : [];
  if (!misconceptions.includes('計算前未先判斷單位一致')) {
    misconceptions.push('計算前未先判斷單位一致');
  }
  if (!misconceptions.includes('未先建立題型步驟就直接運算')) {
    misconceptions.push('未先建立題型步驟就直接運算');
  }

  const parentTips = Array.isArray(report.parent_report_suggestions) ? report.parent_report_suggestions.slice() : [];
  const parentTip = `本題可連結 ${topicPhrase}，先口述步驟再計算，最後請孩子說明驗算方式。`;
  if (!parentTips.includes(parentTip)) {
    parentTips.push(parentTip);
  }

  out.hint_ladder = hint;
  out.report_expectations = {
    ...report,
    misconceptions,
    parent_report_suggestions: parentTips,
  };

  if (containsAnswerLeak(out)) {
    out.hint_ladder.h3_compute = item?.hint_ladder?.h3_compute || out.hint_ladder.h3_compute;
    out.hint_ladder.h2_equation = item?.hint_ladder?.h2_equation || out.hint_ladder.h2_equation;
  }

  return out;
}

async function main() {
  console.log('Starting agent web search and optimization...');
  const rows = readJsonl(goldenPath);
  const memoryRows = readJsonl(memoryPath);
  const sourceSignals = await fetchTopicSignals();
  const topicPool = [...new Set(sourceSignals.flatMap((s) => s.matched_topics || []))];
  if (rows.length === 0) {
    console.log('No golden items found.');
    return;
  }

  const numToOptimize = Math.min(2, rows.length);
  const indicesToOptimize = selectedRows(rows, numToOptimize);

  let changed = 0;
  const touched = [];

  for (const idx of indicesToOptimize) {
    const item = rows[idx];
    console.log(`Optimizing item ${item.id}...`);
    const optimizedItem = optimizeItem(item, topicPool, memoryRows);
    rows[idx] = optimizedItem;
    changed += 1;
    touched.push(item.id);
    console.log(`Successfully optimized item ${item.id}.`);
  }

  if (changed > 0) {
    writeJsonl(goldenPath, rows);
  }

  fs.mkdirSync(path.join(cwd, 'artifacts'), { recursive: true });
  fs.writeFileSync(
    reportPath,
    JSON.stringify(
      {
        changed,
        touched,
        source: 'agent-web-search-optimization',
        targetFile: 'golden/grade5_pack_v1.jsonl',
        timestamp: new Date().toISOString(),
        topic_signals: sourceSignals,
        topic_pool: topicPool,
        memory_items: memoryRows.length,
      },
      null,
      2
    ),
    'utf8'
  );

  console.log(`Agent web search optimization complete, changed=${changed}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
