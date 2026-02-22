const fs = require('fs');
const path = require('path');

function readJsonl(filePath) {
  return fs.readFileSync(filePath, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function normalizeSignals(rows) {
  const topicMap = new Map();
  for (const row of rows) {
    const topic = String(row.topic || row.topic_name || '').trim();
    if (!topic) continue;

    const misconceptionsRaw = row.top_misconceptions || row.misconceptions || [];
    const misconceptions = Array.isArray(misconceptionsRaw)
      ? misconceptionsRaw.map((value) => (typeof value === 'string' ? value : String(value?.label || value?.name || ''))).filter(Boolean)
      : [];

    const recommendationsRaw = row.recommended_next_practice || row.recommendations || [];
    const recommendations = Array.isArray(recommendationsRaw)
      ? recommendationsRaw.map((value) => (typeof value === 'string' ? value : String(value?.label || value?.name || ''))).filter(Boolean)
      : [];

    const hintUsage = row.hint_usage_rate || {};
    const h3 = Number(hintUsage.h3 || hintUsage.level3 || 0);
    const h4 = Number(hintUsage.h4 || hintUsage.level4 || 0);

    const current = topicMap.get(topic) || {
      topic,
      misconceptionCounts: new Map(),
      recommendationCounts: new Map(),
      hint_h3_low_count: 0,
      hint_h4_low_count: 0,
      samples: 0,
    };

    misconceptions.forEach((item) => {
      current.misconceptionCounts.set(item, (current.misconceptionCounts.get(item) || 0) + 1);
    });
    recommendations.forEach((item) => {
      current.recommendationCounts.set(item, (current.recommendationCounts.get(item) || 0) + 1);
    });

    if (h3 > 0 && h3 < 0.25) current.hint_h3_low_count += 1;
    if (h4 > 0 && h4 < 0.15) current.hint_h4_low_count += 1;
    current.samples += 1;
    topicMap.set(topic, current);
  }

  const candidates = [];
  for (const item of topicMap.values()) {
    const topMisconceptions = [...item.misconceptionCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([name, count]) => ({ name, count }));

    const topRecommendations = [...item.recommendationCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([name, count]) => ({ name, count }));

    const nudge = [];
    if (item.hint_h3_low_count > 0) nudge.push('加強第三層計算步驟的可跟隨性');
    if (item.hint_h4_low_count > 0) nudge.push('補強第四層合理性檢查與反思語句');

    candidates.push({
      topic: item.topic,
      samples: item.samples,
      top_misconceptions: topMisconceptions,
      top_recommendations: topRecommendations,
      hint_nudge: nudge,
    });
  }

  return candidates;
}

const args = process.argv;
const inArgIndex = args.indexOf('--in');
const outArgIndex = args.indexOf('--out');

const inputPath = inArgIndex >= 0 ? args[inArgIndex + 1] : path.join(process.cwd(), 'feedback', 'parent_report_signals.jsonl');
const outPath = outArgIndex >= 0 ? args[outArgIndex + 1] : path.join(process.cwd(), 'artifacts', 'report_autotune_candidates.json');

let rows = [];
if (fs.existsSync(inputPath)) {
  rows = readJsonl(inputPath);
}

const candidates = normalizeSignals(rows);
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(
  outPath,
  JSON.stringify(
    {
      source: path.relative(process.cwd(), inputPath),
      candidate_count: candidates.length,
      candidates,
    },
    null,
    2
  ),
  'utf8'
);

console.log(`derived candidates: ${candidates.length}`);
