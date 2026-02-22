const fs = require('fs');
const path = require('path');

function readJsonl(filePath) {
  return fs.readFileSync(filePath, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function writeJsonl(filePath, rows) {
  const content = rows.map((row) => JSON.stringify(row)).join('\n') + '\n';
  fs.writeFileSync(filePath, content, 'utf8');
}

function scoreBreakdown(item) {
  const breakdown = item.breakdown || {};
  return {
    strategy: Number(breakdown.strategy || 0),
    equation: Number(breakdown.equation || 0),
    compute: Number(breakdown.compute || 0),
    misconception: Number(breakdown.misconception || 0),
    check: Number(breakdown.check || 0),
  };
}

const cwd = process.cwd();
const goldenPath = path.join(cwd, 'golden', 'grade5_pack_v1.jsonl');
const judgePath = path.join(cwd, 'artifacts', 'hint_judge.json');
const reportPath = path.join(cwd, 'artifacts', 'autotune_report.json');

if (!fs.existsSync(goldenPath) || !fs.existsSync(judgePath)) {
  console.error('missing golden set or hint_judge artifact');
  process.exit(1);
}

const rows = readJsonl(goldenPath);
const judge = JSON.parse(fs.readFileSync(judgePath, 'utf8'));
const byId = new Map((judge.items || []).map((item) => [item.id, item]));

let changed = 0;
const touched = [];

for (const row of rows) {
  const judged = byId.get(row.id);
  if (!judged) continue;
  const b = scoreBreakdown(judged);

  const ladder = row.hint_ladder || {};
  let localChange = false;

  if (b.equation < 2 && typeof ladder.h2_equation === 'string' && !ladder.h2_equation.includes('列式：')) {
    ladder.h2_equation = `列式：${ladder.h2_equation}`;
    localChange = true;
  }

  if (b.check < 2 && typeof ladder.h4_check_reflect === 'string' && !ladder.h4_check_reflect.includes('估算')) {
    ladder.h4_check_reflect = `${ladder.h4_check_reflect} 再用估算檢查量級是否合理。`;
    localChange = true;
  }

  if (b.misconception < 2) {
    const misconceptions = row.report_expectations?.misconceptions;
    if (Array.isArray(misconceptions) && misconceptions.length > 0) {
      const extra = '把提示內容誤當最終答案';
      if (!misconceptions.includes(extra)) {
        misconceptions.push(extra);
        localChange = true;
      }
    }
  }

  if (localChange) {
    row.hint_ladder = ladder;
    changed += 1;
    touched.push(row.id);
  }
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
      source: 'rule-based-autotune',
      targetFile: 'golden/grade5_pack_v1.jsonl',
    },
    null,
    2
  ),
  'utf8'
);

console.log(`autotune complete, changed=${changed}`);
