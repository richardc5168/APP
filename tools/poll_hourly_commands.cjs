const fs = require('fs');
const path = require('path');
const { runCommand } = require('./_runner.cjs');

const COMMAND_FILE_DEFAULT = path.join(process.cwd(), 'ops', 'hourly_commands.json');
const STATE_PATH = path.join(process.cwd(), 'artifacts', 'hourly_command_state.json');
const RUN_LOG_PATH = path.join(process.cwd(), 'artifacts', 'hourly_command_runs.jsonl');

const ALLOWED_NPM_SCRIPTS = new Set([
  'verify:all',
  'topic:align',
  'summary:iteration',
  'triage:agent',
  'memory:update',
  'judge:hints',
  'scorecard',
  'trend:improvement',
  'gate:scorecard'
]);

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  if (idx < 0 || idx + 1 >= process.argv.length) return fallback;
  return process.argv[idx + 1];
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureArtifacts() {
  const p = path.join(process.cwd(), 'artifacts');
  fs.mkdirSync(p, { recursive: true });
}

function readState() {
  if (!fs.existsSync(STATE_PATH)) return { executed_ids: [] };
  try {
    return JSON.parse(fs.readFileSync(STATE_PATH, 'utf8'));
  } catch {
    return { executed_ids: [] };
  }
}

function writeState(state) {
  ensureArtifacts();
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + '\n', 'utf8');
}

function appendRunLog(entry) {
  ensureArtifacts();
  fs.appendFileSync(RUN_LOG_PATH, `${JSON.stringify(entry)}\n`, 'utf8');
}

function normalizeCommands(payload) {
  if (!payload || !Array.isArray(payload.commands)) return [];
  return payload.commands.filter((c) => c && typeof c.id === 'string');
}

function readCommandFile(commandFilePath) {
  if (!fs.existsSync(commandFilePath)) {
    throw new Error(`command file not found: ${commandFilePath}`);
  }
  return JSON.parse(fs.readFileSync(commandFilePath, 'utf8'));
}

function executeCommand(cmd) {
  if (cmd.action !== 'npm_script') {
    return { pass: false, status: 1, reason: `unsupported action: ${cmd.action}` };
  }

  const script = String(cmd.value || '').trim();
  if (!ALLOWED_NPM_SCRIPTS.has(script)) {
    return { pass: false, status: 1, reason: `script not in allow-list: ${script}` };
  }

  const result = runCommand('npm', ['run', script]);
  return {
    pass: result.pass,
    status: result.status,
    stdout: result.stdout,
    stderr: result.stderr,
    reason: result.pass ? '' : 'npm script failed'
  };
}

async function runOnce(commandFilePath) {
  const now = new Date().toISOString();
  const state = readState();
  const executed = new Set(state.executed_ids || []);

  const pullRes = runCommand('git', ['pull', '--ff-only', 'origin', 'main']);
  const pullOk = pullRes.pass;

  const payload = readCommandFile(commandFilePath);
  const commands = normalizeCommands(payload);
  const pending = commands.filter((c) => c.enabled && !executed.has(c.id));

  for (const cmd of pending) {
    const startedAt = new Date().toISOString();
    const result = executeCommand(cmd);
    const endedAt = new Date().toISOString();

    appendRunLog({
      id: cmd.id,
      action: cmd.action,
      value: cmd.value,
      started_at: startedAt,
      ended_at: endedAt,
      pass: result.pass,
      status: result.status,
      reason: result.reason || '',
      note: cmd.note || ''
    });

    if (result.pass) {
      executed.add(cmd.id);
    }
  }

  const nextState = {
    last_checked_at: now,
    command_file: commandFilePath,
    git_pull_ok: pullOk,
    executed_ids: Array.from(executed)
  };
  writeState(nextState);

  console.log(JSON.stringify({
    checked_at: now,
    command_file: commandFilePath,
    git_pull_ok: pullOk,
    total_commands: commands.length,
    pending_executed: pending.length,
    executed_ids_count: nextState.executed_ids.length
  }, null, 2));
}

async function main() {
  const commandFilePath = argValue('--command-file', COMMAND_FILE_DEFAULT);
  const intervalMin = Number(argValue('--interval-min', '60'));
  const once = hasFlag('--once') || !hasFlag('--watch');

  if (once) {
    await runOnce(commandFilePath);
    return;
  }

  while (true) {
    try {
      await runOnce(commandFilePath);
    } catch (err) {
      appendRunLog({
        id: 'poll-error',
        started_at: new Date().toISOString(),
        ended_at: new Date().toISOString(),
        pass: false,
        status: 1,
        reason: String(err?.message || err)
      });
      console.error(err);
    }

    const ms = Math.max(1, intervalMin) * 60 * 1000;
    console.log(`sleep ${intervalMin} minutes before next command poll...`);
    await sleep(ms);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
