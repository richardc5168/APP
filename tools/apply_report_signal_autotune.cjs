const fs = require('fs');
const path = require('path');

function readJsonl(filePath) {
  return fs.readFileSync(filePath, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function writeJsonl(filePath, rows) {
  fs.writeFileSync(filePath, rows.map((row) => JSON.stringify(row)).join('\n') + '\n', 'utf8');
}

function topicMatch(goldenTopic, candidateTopic) {
  const a = String(goldenTopic || '').trim();
  const b = String(candidateTopic || '').trim();
  if (!a || !b) return false;
  return a === b || a.includes(b) || b.includes(a);
}

const args = process.argv;
const goldenArgIndex = args.indexOf('--golden');
const candidatesArgIndex = args.indexOf('--candidates');
const reportArgIndex = args.indexOf('--report');

const goldenPath = goldenArgIndex >= 0 ? args[goldenArgIndex + 1] : path.join(process.cwd(), 'golden', 'grade5_pack_v1.jsonl');
const candidatesPath =
  candidatesArgIndex >= 0 ? args[candidatesArgIndex + 1] : path.join(process.cwd(), 'artifacts', 'report_autotune_candidates.json');
const reportPath = reportArgIndex >= 0 ? args[reportArgIndex + 1] : path.join(process.cwd(), 'artifacts', 'report_autotune_apply.json');

if (!fs.existsSync(goldenPath)) {
  console.error('golden file not found');
  process.exit(1);
}

const rows = readJsonl(goldenPath);
const candidatesDoc = fs.existsSync(candidatesPath)
  ? JSON.parse(fs.readFileSync(candidatesPath, 'utf8'))
  : { candidates: [] };
const candidates = Array.isArray(candidatesDoc.candidates) ? candidatesDoc.candidates : [];

let changed = 0;
const touchedIds = [];

for (const row of rows) {
  const candidate = candidates.find((item) => topicMatch(row.topic, item.topic));
  if (!candidate) continue;

  const misconceptions = row.report_expectations?.misconceptions;
  const ladder = row.hint_ladder || {};
  let localChanged = false;

  if (Array.isArray(misconceptions)) {
    const topMis = (candidate.top_misconceptions || []).map((item) => String(item.name || '').trim()).filter(Boolean);
    for (const name of topMis.slice(0, 2)) {
      if (!misconceptions.includes(name)) {
        misconceptions.push(name);
        localChanged = true;
      }
    }
  }

  const nudge = (candidate.hint_nudge || []).filter(Boolean).join('；');
  if (nudge && typeof ladder.h4_check_reflect === 'string' && !ladder.h4_check_reflect.includes(nudge)) {
    ladder.h4_check_reflect = `${ladder.h4_check_reflect} ${nudge}。`;
    localChanged = true;
  }

  if (localChanged) {
    row.hint_ladder = ladder;
    changed += 1;
    touchedIds.push(row.id);
  }
}

if (changed > 0) {
  writeJsonl(goldenPath, rows);
}

fs.mkdirSync(path.dirname(reportPath), { recursive: true });
fs.writeFileSync(
  reportPath,
  JSON.stringify(
    {
      changed,
      touched_ids: touchedIds,
      golden: path.relative(process.cwd(), goldenPath),
      candidates: path.relative(process.cwd(), candidatesPath),
    },
    null,
    2
  ),
  'utf8'
);

console.log(`report autotune applied: changed=${changed}`);
