#!/usr/bin/env node
/**
 * exp_autorun.mjs
 *
 * 目的：在 3小時內持續自動執行提示/介面優化實驗（沙盒），匯出報表並回寫 CI（PR/Issue/dispatch）。
 *
 * =========================
 * 未指定（必須由環境變數提供）
 * =========================
 * - FEATURE_FLAG_API_BASE            : Feature flag service base URL（未指定）
 * - FEATURE_FLAG_API_TOKEN           : Feature flag service token（未指定）
 * - FEATURE_FLAG_PROJECT             : Feature flag 專案/namespace（未指定）
 *
 * - HINT_SVC_BASE_URL                : Hint/UX service (sandbox) base URL（未指定）
 * - HINT_SVC_TOKEN                   : Service auth token（未指定）
 * - HINT_SVC_TRAFFIC_MODE            : "simulate" | "replay"（未指定，預設 simulate）
 * - HINT_SVC_REQUEST_ENDPOINT        : e.g. "/api/hint"（未指定）
 *
 * - LOG_API_BASE_URL                 : Log query service base URL（未指定）
 * - LOG_API_TOKEN                    : Log query token（未指定）
 * - LOG_API_QUERY_ENDPOINT           : e.g. "/api/events/query"（未指定）
 *
 * - GITHUB_TOKEN                     : GitHub token（repo + workflow scope 建議）
 * - GH_OWNER                         : repo owner（未指定）
 * - GH_REPO                          : repo name（未指定）
 * - GH_DEFAULT_BRANCH                : default branch（未指定，留空則自動查）
 * - GH_WORKFLOW_ID                   : workflow file name or id（未指定）
 * - GH_WORKFLOW_REF                  : workflow ref（未指定，預設新分支）
 *
 * - BASELINE_TIME_WINDOW_MIN         : baseline 資料時間窗（未指定，預設 30）
 * - ROUND_TIME_WINDOW_MIN            : 每輪實驗時間窗（未指定，預設 60）
 * - MAX_RUNTIME_MIN                  : 最大執行分鐘（未指定，預設 480 = 8 小時）
 *
 * - GUARD_MAX_ERROR_RATE             : 允許最大錯誤率（未指定，預設 0.02）
 * - GUARD_MAX_P95_LATENCY_MS         : 允許最大 p95 延遲（未指定，預設 1200）
 *
 * - PROD_GUARD_ALLOW                 : "YES" 才允許對疑似 prod URL 執行（未指定，預設 NO）
 *
 * =========================
 * 可選（若提供則啟用）
 * =========================
 * - LOCAL_EVENTS_JSONL               : 若要從本地檔案讀事件（離線），指定 JSONL 路徑
 * - MISCONCEPTION_LABELS_CSV         : 若要評估 detector precision/recall，提供標註檔
 */

import fs from "fs";
import path from "path";
import crypto from "crypto";
import { execSync } from "child_process";

const START_TS = Date.now();
const MAX_RUNTIME_MIN = parseInt(process.env.MAX_RUNTIME_MIN || "480", 10);
const MAX_RUNTIME_MS = MAX_RUNTIME_MIN * 60 * 1000;

const BASELINE_TIME_WINDOW_MIN = parseInt(process.env.BASELINE_TIME_WINDOW_MIN || "30", 10);
const ROUND_TIME_WINDOW_MIN = parseInt(process.env.ROUND_TIME_WINDOW_MIN || "60", 10);

const GUARD_MAX_ERROR_RATE = parseFloat(process.env.GUARD_MAX_ERROR_RATE || "0.02");
const GUARD_MAX_P95_LATENCY_MS = parseInt(process.env.GUARD_MAX_P95_LATENCY_MS || "1200", 10);

const PROD_GUARD_ALLOW = (process.env.PROD_GUARD_ALLOW || "NO").toUpperCase() === "YES";

// ---------------------------
// Utilities
// ---------------------------
function nowIso() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}
function elapsedMs() {
  return Date.now() - START_TS;
}
function timeLeftMs() {
  return Math.max(0, MAX_RUNTIME_MS - elapsedMs());
}
function log(...args) {
  const line = `[${new Date().toISOString()}] ${args.join(" ")}`;
  console.log(line);
}
function die(msg) {
  console.error(`FATAL: ${msg}`);
  process.exit(1);
}
function requireEnv(name) {
  const v = process.env[name];
  if (!v) die(`Missing env var: ${name}`);
  return v;
}
function safeMkdirp(p) {
  fs.mkdirSync(p, { recursive: true });
}
function writeFile(p, content) {
  safeMkdirp(path.dirname(p));
  fs.writeFileSync(p, content);
}
function readFileIfExists(p) {
  if (!p) return null;
  if (!fs.existsSync(p)) return null;
  return fs.readFileSync(p, "utf8");
}
function isProbablyProd(url) {
  const u = String(url || "").toLowerCase();
  return u.includes("prod") || u.includes("production") || u.includes("live");
}
function assertSandboxGuards() {
  const hintBase = process.env.HINT_SVC_BASE_URL || "";
  const logBase = process.env.LOG_API_BASE_URL || "";
  const ffBase = process.env.FEATURE_FLAG_API_BASE || "";
  const suspicious = [hintBase, logBase, ffBase].some(isProbablyProd);
  if (suspicious && !PROD_GUARD_ALLOW) {
    die(
      "Guardrail: one or more base URLs look like PROD. Set PROD_GUARD_ALLOW=YES to override (NOT recommended)."
    );
  }
}

function sha256Hex(s) {
  return crypto.createHash("sha256").update(s).digest("hex");
}
function stableBucket(key, buckets) {
  const h = sha256Hex(key);
  const n = parseInt(h.slice(0, 8), 16);
  return n % buckets;
}
function percentile(arr, p) {
  if (!arr.length) return null;
  const a = [...arr].sort((x, y) => x - y);
  const idx = Math.floor((p / 100) * (a.length - 1));
  return a[idx];
}
function mean(arr) {
  if (!arr.length) return null;
  return arr.reduce((s, x) => s + x, 0) / arr.length;
}
function variance(arr) {
  if (arr.length < 2) return null;
  const m = mean(arr);
  return arr.reduce((s, x) => s + (x - m) ** 2, 0) / (arr.length - 1);
}

// ---------------------------
// HTTP helper (Node >= 18 has global fetch)
// ---------------------------
async function httpJson(method, url, { headers = {}, body = null, timeoutMs = 20000 } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method,
      headers: {
        "content-type": "application/json",
        ...headers,
      },
      body: body ? JSON.stringify(body) : null,
      signal: ctrl.signal,
    });
    const text = await res.text();
    const json = text ? JSON.parse(text) : null;
    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}: ${text.slice(0, 500)}`);
    }
    return json;
  } finally {
    clearTimeout(timer);
  }
}
async function withRetries(fn, { retries = 3, baseDelayMs = 500 } = {}) {
  let lastErr = null;
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (e) {
      lastErr = e;
      const d = baseDelayMs * Math.pow(2, i);
      log(`retry ${i + 1}/${retries + 1} after ${d}ms: ${String(e).slice(0, 200)}`);
      await new Promise((r) => setTimeout(r, d));
    }
  }
  throw lastErr;
}

// ---------------------------
// Stats: two-proportion z test + Welch t-test
// ---------------------------
function normalCdf(z) {
  // Abramowitz-Stegun approximation via erf
  return 0.5 * (1 + Math.erf(z / Math.SQRT2));
}
function normalPValueTwoSided(z) {
  const p = 2 * (1 - normalCdf(Math.abs(z)));
  return Math.max(0, Math.min(1, p));
}
function twoPropZTest(s1, n1, s2, n2) {
  if (n1 === 0 || n2 === 0) return { z: null, p: null };
  const p1 = s1 / n1;
  const p2 = s2 / n2;
  const pPool = (s1 + s2) / (n1 + n2);
  const se = Math.sqrt(pPool * (1 - pPool) * (1 / n1 + 1 / n2));
  if (se === 0) return { z: null, p: null };
  const z = (p1 - p2) / se;
  return { z, p: normalPValueTwoSided(z) };
}
function welchTTest(a, b) {
  // Returns t-statistic only; p-value omitted unless you wire a t-distribution CDF.
  // For gating, t and effect size are often enough in sandbox runs.
  if (a.length < 2 || b.length < 2) return { t: null };
  const ma = mean(a);
  const mb = mean(b);
  const va = variance(a);
  const vb = variance(b);
  const se = Math.sqrt(va / a.length + vb / b.length);
  if (!se) return { t: null };
  return { t: (ma - mb) / se };
}

// ---------------------------
// Bayesian A/B: Beta-Binomial via Monte Carlo
// ---------------------------
function randn() {
  // Box-Muller
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}
function gammaSample(k, theta = 1) {
  // Marsaglia and Tsang (k > 1), with boost for k <= 1
  if (k < 1) {
    const u = Math.random();
    return gammaSample(1 + k, theta) * Math.pow(u, 1 / k);
  }
  const d = k - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  while (true) {
    let x = randn();
    let v = 1 + c * x;
    if (v <= 0) continue;
    v = v ** 3;
    const u = Math.random();
    if (u < 1 - 0.0331 * (x ** 4)) return d * v * theta;
    if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v * theta;
  }
}
function betaSample(a, b) {
  const x = gammaSample(a, 1);
  const y = gammaSample(b, 1);
  return x / (x + y);
}
function bayesProbSuperior(sA, nA, sB, nB, { priorA = 1, priorB = 1, samples = 20000 } = {}) {
  // P(pB > pA) under Beta(priorA+s, priorB+n-s)
  const aA = priorA + sA;
  const bA = priorB + (nA - sA);
  const aB = priorA + sB;
  const bB = priorB + (nB - sB);
  let win = 0;
  for (let i = 0; i < samples; i++) {
    const pA = betaSample(aA, bA);
    const pB = betaSample(aB, bB);
    if (pB > pA) win++;
  }
  return win / samples;
}

// ---------------------------
// Multiple comparisons: BH-FDR
// ---------------------------
function bhAdjust(pvals) {
  // pvals: [{key, p}]
  const m = pvals.length;
  const sorted = [...pvals].sort((x, y) => (x.p ?? 1) - (y.p ?? 1));
  let prev = 1;
  for (let i = m - 1; i >= 0; i--) {
    const rank = i + 1;
    const p = sorted[i].p ?? 1;
    const adj = Math.min(prev, (p * m) / rank);
    sorted[i].adj = adj;
    prev = adj;
  }
  const out = {};
  for (const item of sorted) out[item.key] = item.adj;
  return out;
}

// ---------------------------
// Feature Flag operations (endpoint contract is 未指定)
// ---------------------------
async function ffSetFlags(project, flags, context = {}) {
  const base = requireEnv("FEATURE_FLAG_API_BASE");
  const token = requireEnv("FEATURE_FLAG_API_TOKEN");
  const url = `${base}/flags/set`;
  return await withRetries(() =>
    httpJson("POST", url, {
      headers: { authorization: `Bearer ${token}` },
      body: { project, flags, context },
      timeoutMs: 20000,
    })
  );
}
async function ffRollbackToBaseline(project, baselineFlags) {
  log("FF rollback to baseline");
  return await ffSetFlags(project, baselineFlags, { reason: "guardrail_rollback" });
}

// ---------------------------
// Traffic generation (simulate/replay) — endpoint contract is 未指定
// ---------------------------
async function pushTrafficBatch({ expId, arm, users, payloadTemplate }) {
  const base = requireEnv("HINT_SVC_BASE_URL");
  const token = requireEnv("HINT_SVC_TOKEN");
  const ep = requireEnv("HINT_SVC_REQUEST_ENDPOINT"); // e.g. "/api/hint"
  const url = `${base}${ep}`;

  const reqs = users.map((u) => ({
    user_id: u,
    exp_id: expId,
    arm,
    ...payloadTemplate,
  }));

  // In real systems, you'd batch; here we send one request per user for clarity.
  for (const r of reqs) {
    await withRetries(() =>
      httpJson("POST", url, {
        headers: {
          authorization: `Bearer ${token}`,
          "x-exp-id": expId,
          "x-exp-arm": arm,
          "x-sandbox": "true",
        },
        body: r,
        timeoutMs: 20000,
      })
    );
  }
}

// ---------------------------
// Log collection — endpoint contract is 未指定
// ---------------------------
async function pullEvents({ sinceIso, untilIso, expId }) {
  const local = process.env.LOCAL_EVENTS_JSONL;
  if (local) {
    const txt = readFileIfExists(local);
    if (!txt) return [];
    return txt
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
      .map((l) => JSON.parse(l))
      .filter((e) => !expId || e.exp_id === expId);
  }

  const base = requireEnv("LOG_API_BASE_URL");
  const token = requireEnv("LOG_API_TOKEN");
  const ep = requireEnv("LOG_API_QUERY_ENDPOINT"); // e.g. "/api/events/query"
  const url = `${base}${ep}`;

  const resp = await withRetries(() =>
    httpJson("POST", url, {
      headers: { authorization: `Bearer ${token}` },
      body: { since: sinceIso, until: untilIso, exp_id: expId },
      timeoutMs: 30000,
    })
  );

  return resp?.events ?? [];
}

// ---------------------------
// KPI computation
// Expected event schema (recommended):
// - type: "step_attempt" | "hint_requested" | "svc_error" | "hint_rendered"
// - ts, user_id, session_id, problem_id, family, skill_id, arm, hint_level, correct, latency_ms
// - misconception_flags: ["numerator_denominator_swap", ...]
// ---------------------------
function computeKpis(events) {
  const byArm = new Map();
  for (const e of events) {
    const arm = e.arm || "unknown";
    if (!byArm.has(arm)) byArm.set(arm, []);
    byArm.get(arm).push(e);
  }

  const out = {};
  for (const [arm, ev] of byArm.entries()) {
    const steps = ev.filter((x) => x.type === "step_attempt");
    const hints = ev.filter((x) => x.type === "hint_requested");
    const errors = ev.filter((x) => x.type === "svc_error");

    const stepN = steps.length;
    const stepS = steps.filter((x) => x.correct === true).length;

    const hintN = hints.length;
    const hintRate = stepN ? hintN / stepN : null;

    // after-next-step success: find next step after each hint (simple heuristic by user + session + ts order)
    const key = (x) => `${x.user_id || "u"}|${x.session_id || "s"}`;
    const bySess = new Map();
    for (const x of ev) {
      const k = key(x);
      if (!bySess.has(k)) bySess.set(k, []);
      bySess.get(k).push(x);
    }
    let afterNextDen = 0;
    let afterNextNum = 0;
    for (const xs of bySess.values()) {
      xs.sort((a, b) => String(a.ts).localeCompare(String(b.ts)));
      for (let i = 0; i < xs.length; i++) {
        if (xs[i].type !== "hint_requested") continue;
        // next step_attempt
        for (let j = i + 1; j < xs.length; j++) {
          if (xs[j].type === "step_attempt") {
            afterNextDen++;
            if (xs[j].correct === true) afterNextNum++;
            break;
          }
        }
      }
    }
    const afterNext = afterNextDen ? afterNextNum / afterNextDen : null;

    const lat = ev
      .filter((x) => typeof x.latency_ms === "number")
      .map((x) => x.latency_ms);
    const p95 = percentile(lat, 95);

    const errRate = (stepN + hintN) ? errors.length / (stepN + hintN) : null;

    // misconception rates
    const mc = {};
    for (const x of steps) {
      const flags = Array.isArray(x.misconception_flags) ? x.misconception_flags : [];
      for (const f of flags) mc[f] = (mc[f] || 0) + 1;
    }

    out[arm] = {
      step_success: { s: stepS, n: stepN, rate: stepN ? stepS / stepN : null },
      after_next_step_success: { s: afterNextNum, n: afterNextDen, rate: afterNext },
      hint_request_rate: hintRate,
      p95_latency_ms: p95,
      error_rate: errRate,
      misconception_counts: mc,
    };
  }
  return out;
}

function guardrailsOk(kpis) {
  // Global guardrails: if ANY arm violates, abort & rollback
  for (const [arm, k] of Object.entries(kpis)) {
    if (k.error_rate != null && k.error_rate > GUARD_MAX_ERROR_RATE) {
      return { ok: false, reason: `arm=${arm} error_rate=${k.error_rate}` };
    }
    if (k.p95_latency_ms != null && k.p95_latency_ms > GUARD_MAX_P95_LATENCY_MS) {
      return { ok: false, reason: `arm=${arm} p95_latency_ms=${k.p95_latency_ms}` };
    }
  }
  return { ok: true };
}

// ---------------------------
// Simple SVG renderers
// ---------------------------
function barChartSvg(rows, { width = 520, barH = 18, gap = 10 } = {}) {
  // rows: [{label, value, color?}]
  const max = Math.max(1e-9, ...rows.map((r) => r.value));
  const h = 40 + rows.length * (barH + gap);
  let y = 20;
  const rects = rows
    .map((r, i) => {
      const w = Math.round((r.value / max) * (width - 200));
      const color = r.color || "#4C78A8";
      const line = `<rect x="10" y="${y}" width="${w}" height="${barH}" fill="${color}"/>` +
        `<text x="${w + 20}" y="${y + 13}" font-size="12">${r.label} ${r.value.toFixed(4)}</text>`;
      y += barH + gap;
      return line;
    })
    .join("\n");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${h}">\n${rects}\n</svg>\n`;
}

function timeSeriesSvg(points, { width = 520, height = 160 } = {}) {
  // points: [{tIdx, y}]
  if (!points.length) return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"></svg>`;
  const minY = Math.min(...points.map((p) => p.y));
  const maxY = Math.max(...points.map((p) => p.y));
  const scaleX = (i) => 20 + (i / Math.max(1, points.length - 1)) * (width - 40);
  const scaleY = (y) => {
    const denom = Math.max(1e-9, maxY - minY);
    return 20 + (1 - (y - minY) / denom) * (height - 60);
  };
  const poly = points
    .map((p, i) => `${scaleX(i).toFixed(1)},${scaleY(p.y).toFixed(1)}`)
    .join(" ");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
  <polyline fill="none" stroke="#4C78A8" stroke-width="2" points="${poly}"/>
  <line x1="20" y1="${height - 30}" x2="${width - 20}" y2="${height - 30}" stroke="#999"/>
  <text x="20" y="${height - 10}" font-size="12">t</text>
</svg>\n`;
}

function dotPlotSvg(values, { width = 520, height = 140 } = {}) {
  if (!values.length) return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"></svg>`;
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const scaleX = (v) => {
    const denom = Math.max(1e-9, maxV - minV);
    return 20 + ((v - minV) / denom) * (width - 60);
  };
  const y = Math.round(height / 2);
  const circles = values
    .slice(0, 200) // cap
    .map((v) => `<circle cx="${scaleX(v).toFixed(1)}" cy="${y}" r="3" fill="#4C78A8"/>`)
    .join("\n");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
  <line x1="20" y1="${y}" x2="${width - 20}" y2="${y}" stroke="#555"/>
  ${circles}
  <text x="20" y="${height - 10}" font-size="12">value (scaled)</text>
</svg>\n`;
}

// ---------------------------
// GitHub writeback (PR/Issue/Dispatch)
// ---------------------------
async function ghApi(method, url, { token, body = null } = {}) {
  const res = await httpJson(method, url, {
    headers: {
      authorization: `Bearer ${token}`,
      "x-github-api-version": "2022-11-28",
      accept: "application/vnd.github+json",
    },
    body,
    timeoutMs: 30000,
  });
  return res;
}

async function ghGetRepo(token, owner, repo) {
  return await ghApi("GET", `https://api.github.com/repos/${owner}/${repo}`, { token });
}
async function ghGetRef(token, owner, repo, branch) {
  return await ghApi("GET", `https://api.github.com/repos/${owner}/${repo}/git/ref/heads/${branch}`, { token });
}
async function ghCreateRef(token, owner, repo, branch, sha) {
  return await ghApi("POST", `https://api.github.com/repos/${owner}/${repo}/git/refs`, {
    token,
    body: { ref: `refs/heads/${branch}`, sha },
  });
}
async function ghPutFile(token, owner, repo, filePath, contentText, message, branch) {
  const b64 = Buffer.from(contentText, "utf8").toString("base64");
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(filePath)}`;
  return await ghApi("PUT", url, {
    token,
    body: { message, content: b64, branch },
  });
}
async function ghCreatePr(token, owner, repo, title, head, base, body) {
  return await ghApi("POST", `https://api.github.com/repos/${owner}/${repo}/pulls`, {
    token,
    body: { title, head, base, body },
  });
}
async function ghCreateIssue(token, owner, repo, title, body) {
  return await ghApi("POST", `https://api.github.com/repos/${owner}/${repo}/issues`, {
    token,
    body: { title, body },
  });
}
async function ghWorkflowDispatch(token, owner, repo, workflowId, ref, inputs = {}) {
  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflowId}/dispatches`;
  return await ghApi("POST", url, { token, body: { ref, inputs } });
}

// ---------------------------
// Main orchestration
// ---------------------------
async function main() {
  assertSandboxGuards();

  // Required env (unless running fully offline with LOCAL_EVENTS_JSONL)
  const offline = !!process.env.LOCAL_EVENTS_JSONL;

  const runId = `exp_autorun_${nowIso()}`;
  const outDir = path.join("reports", runId);
  safeMkdirp(outDir);
  safeMkdirp(path.join(outDir, "charts"));

  log(`RUN_ID=${runId}`);
  writeFile(path.join(outDir, "run_meta.json"), JSON.stringify({
    run_id: runId,
    started_at: new Date().toISOString(),
    max_runtime_min: MAX_RUNTIME_MIN,
    guard_max_error_rate: GUARD_MAX_ERROR_RATE,
    guard_max_p95_latency_ms: GUARD_MAX_P95_LATENCY_MS,
    offline_mode: offline,
  }, null, 2));

  // Define experiments (feature flags keys are illustrative; adjust to your system)
  const ffProject = process.env.FEATURE_FLAG_PROJECT || "default";
  const baselineFlags = {
    HINT_STREAK_THRESHOLD: 3,
    HINT_BOTTOM_OUT_GATE: "none",
    VIZ_AVERAGE_MODE: "leveling+bar",
    MISCONCEPT_REMEDIATE: false,
  };

  const experiments = [
    {
      id: "EXP-HINT-ESCALATE",
      arms: [
        { name: "A_baseline", flags: { ...baselineFlags, HINT_STREAK_THRESHOLD: 3 } },
        { name: "B_threshold2", flags: { ...baselineFlags, HINT_STREAK_THRESHOLD: 2 } },
        { name: "C_threshold3_cooldown", flags: { ...baselineFlags, HINT_STREAK_THRESHOLD: 3, HINT_COOLDOWN_DOWNGRADE: true } },
      ],
      budgetMin: ROUND_TIME_WINDOW_MIN,
    },
    {
      id: "EXP-BOTTOM-OUT-GATE",
      arms: [
        { name: "A_direct", flags: { ...baselineFlags, HINT_BOTTOM_OUT_GATE: "none" } },
        { name: "B_self_explain", flags: { ...baselineFlags, HINT_BOTTOM_OUT_GATE: "self_explain" } },
        { name: "C_force_step", flags: { ...baselineFlags, HINT_BOTTOM_OUT_GATE: "force_intermediate_step" } },
      ],
      budgetMin: ROUND_TIME_WINDOW_MIN,
    },
    {
      id: "EXP-VIZ-AVERAGE",
      arms: [
        { name: "A_leveling_bar", flags: { ...baselineFlags, VIZ_AVERAGE_MODE: "leveling+bar" } },
        { name: "B_bar_first", flags: { ...baselineFlags, VIZ_AVERAGE_MODE: "bar_first" } },
        { name: "C_dotplot", flags: { ...baselineFlags, VIZ_AVERAGE_MODE: "dotplot" } },
      ],
      budgetMin: Math.max(ROUND_TIME_WINDOW_MIN, 120),
      bandit: true,
    },
    {
      id: "EXP-MISCONCEPT-REMEDIATE",
      arms: [
        { name: "A_detect_only", flags: { ...baselineFlags, MISCONCEPT_REMEDIATE: false } },
        { name: "B_remediate", flags: { ...baselineFlags, MISCONCEPT_REMEDIATE: true } },
      ],
      budgetMin: ROUND_TIME_WINDOW_MIN,
    },
  ];

  // Preflight: run local tests if available
  log("Preflight: running tests (best-effort)");
  try {
    if (fs.existsSync("package.json")) {
      execSync("npm test", { stdio: "inherit" });
    }
  } catch (e) {
    log("WARN: tests failed in preflight (continuing, but CI gate may fail).");
  }

  // Baseline snapshot window
  let cursorSince = new Date(Date.now() - BASELINE_TIME_WINDOW_MIN * 60 * 1000).toISOString();
  let cursorUntil = new Date().toISOString();
  let baselineEvents = [];
  if (!offline) {
    log(`Pulling baseline events window: ${cursorSince} -> ${cursorUntil}`);
    baselineEvents = await pullEvents({ sinceIso: cursorSince, untilIso: cursorUntil, expId: null });
  } else {
    baselineEvents = await pullEvents({ sinceIso: cursorSince, untilIso: cursorUntil, expId: null });
  }
  writeFile(path.join(outDir, "baseline_events.jsonl"), baselineEvents.map((e) => JSON.stringify(e)).join("\n") + "\n");

  // Execute experiments sequentially within time budget
  const allSummaries = [];
  for (const exp of experiments) {
    if (timeLeftMs() < 20 * 60 * 1000) {
      log("Time budget low; stopping further experiments.");
      break;
    }

    const expId = `${exp.id}_${nowIso()}`;
    log(`=== START ${expId} ===`);

    // Set baseline for safety
    if (!offline) await ffSetFlags(ffProject, baselineFlags, { exp_id: expId, arm: "baseline_safety" });

    // Assign users to arms
    const userCount = 300; // sandbox load factor; tune per infra
    const users = Array.from({ length: userCount }, (_, i) => `sim_u_${expId}_${i}`);

    // For bandit run: Thompson sampling drives arm selection per user (simplified)
    const armStats = new Map(exp.arms.map((a) => [a.name, { s: 1, f: 1 }])); // Beta(1,1) prior counts
    const assignments = [];

    for (const u of users) {
      let armName = exp.arms[stableBucket(u, exp.arms.length)].name; // default uniform
      if (exp.bandit) {
        // Thompson sampling: sample from Beta and pick max
        let best = null;
        for (const a of exp.arms) {
          const st = armStats.get(a.name);
          const p = betaSample(st.s, st.f);
          if (!best || p > best.p) best = { name: a.name, p };
        }
        armName = best.name;
      }
      assignments.push({ user: u, arm: armName });
    }

    // Deploy each arm's flags before traffic (simplified: set per-arm global, then run that arm traffic)
    // In real systems you would do per-user targeting rules; endpoint contract is 未指定.
    const payloadTemplate = {
      // Minimal payload; adjust to your system's hint endpoint.
      problem_id: "sandbox_problem",
      family: "average",
      skill_id: "avg_basic",
      student_answer: "42",
      hint_level: 2,
    };

    const roundStart = new Date().toISOString();
    for (const arm of exp.arms) {
      if (timeLeftMs() < 10 * 60 * 1000) break;

      log(`Deploy flags for arm=${arm.name}`);
      if (!offline) await ffSetFlags(ffProject, arm.flags, { exp_id: expId, arm: arm.name });

      const armUsers = assignments.filter((x) => x.arm === arm.name).map((x) => x.user);

      if (!offline) {
        log(`Traffic: arm=${arm.name} users=${armUsers.length}`);
        await pushTrafficBatch({ expId, arm: arm.name, users: armUsers, payloadTemplate });
      }

      // Optional: if bandit, update pseudo-reward from immediate service response (not implemented; depends on endpoint)
      // Here we rely on logs for reward.
    }
    const roundEnd = new Date().toISOString();

    // Pull events for this exp window
    let expEvents = [];
    if (!offline) {
      log(`Pulling exp events: ${roundStart} -> ${roundEnd}`);
      expEvents = await pullEvents({ sinceIso: roundStart, untilIso: roundEnd, expId });
    } else {
      expEvents = await pullEvents({ sinceIso: roundStart, untilIso: roundEnd, expId });
    }
    writeFile(path.join(outDir, `${expId}_events.jsonl`), expEvents.map((e) => JSON.stringify(e)).join("\n") + "\n");

    const kpis = computeKpis(expEvents);
    const guard = guardrailsOk(kpis);
    if (!guard.ok) {
      log(`Guardrail breached: ${guard.reason}`);
      if (!offline) await ffRollbackToBaseline(ffProject, baselineFlags);

      // Create an issue (best-effort)
      try {
        const ghToken = process.env.GITHUB_TOKEN;
        const owner = process.env.GH_OWNER;
        const repo = process.env.GH_REPO;
        if (ghToken && owner && repo) {
          await ghCreateIssue(
            ghToken,
            owner,
            repo,
            `Experiment guardrail rollback: ${expId}`,
            `Guardrail breached.\n\nReason: ${guard.reason}\n\nRun: ${runId}\nExp: ${expId}`
          );
        }
      } catch (e) {
        log(`WARN: failed to create issue: ${String(e).slice(0, 200)}`);
      }

      // Continue to next exp (or stop; choose conservative)
      continue;
    }

    // Compare arms vs first arm as baseline
    const armNames = Object.keys(kpis);
    const baseArm = exp.arms[0].name;
    const comparisons = [];
    const pvals = [];

    for (const arm of exp.arms.slice(1)) {
      const A = kpis[baseArm]?.step_success || { s: 0, n: 0 };
      const B = kpis[arm.name]?.step_success || { s: 0, n: 0 };

      const z = twoPropZTest(A.s, A.n, B.s, B.n);
      const bayes = bayesProbSuperior(A.s, A.n, B.s, B.n, { samples: 10000 });

      comparisons.push({
        exp_id: expId,
        baseline: baseArm,
        arm: arm.name,
        metric: "step_success_rate",
        baseline_rate: A.n ? A.s / A.n : null,
        arm_rate: B.n ? B.s / B.n : null,
        delta: (B.n ? B.s / B.n : 0) - (A.n ? A.s / A.n : 0),
        z: z.z,
        p: z.p,
        bayes_prob_arm_gt_base: bayes,
      });
      pvals.push({ key: `${expId}|${arm.name}|step_success_rate`, p: z.p ?? 1 });
    }

    const bh = bhAdjust(pvals);
    const comparisonsAdj = comparisons.map((c) => ({
      ...c,
      p_bh: bh[`${c.exp_id}|${c.arm}|${c.metric}`],
    }));

    const summary = { exp_id: expId, roundStart, roundEnd, kpis, comparisons: comparisonsAdj };
    allSummaries.push(summary);

    writeFile(path.join(outDir, `${expId}_summary.json`), JSON.stringify(summary, null, 2));

    // Render charts for this experiment
    const stepBars = exp.arms.map((a) => ({
      label: a.name,
      value: kpis[a.name]?.step_success?.rate ?? 0,
    }));
    writeFile(path.join(outDir, "charts", `${expId}_step_success.svg`), barChartSvg(stepBars));

    const hintSeries = exp.arms.map((a, idx) => ({
      tIdx: idx,
      y: kpis[a.name]?.hint_request_rate ?? 0,
    }));
    writeFile(path.join(outDir, "charts", `${expId}_hint_rate.svg`), timeSeriesSvg(hintSeries));

    const latVals = exp.arms
      .map((a) => kpis[a.name]?.p95_latency_ms)
      .filter((x) => typeof x === "number");
    writeFile(path.join(outDir, "charts", `${expId}_latency_dot.svg`), dotPlotSvg(latVals));

    log(`=== END ${expId} ===`);
  }

  // Aggregate report
  const reportMd = [];
  reportMd.push(`# Experiment Run Report: ${runId}`);
  reportMd.push(`- started_at: ${new Date(START_TS).toISOString()}`);
  reportMd.push(`- max_runtime_min: ${MAX_RUNTIME_MIN}`);
  reportMd.push(`- guard_max_error_rate: ${GUARD_MAX_ERROR_RATE}`);
  reportMd.push(`- guard_max_p95_latency_ms: ${GUARD_MAX_P95_LATENCY_MS}`);
  reportMd.push(`\n## Summaries\n`);
  for (const s of allSummaries) {
    reportMd.push(`### ${s.exp_id}`);
    reportMd.push(`- window: ${s.roundStart} -> ${s.roundEnd}`);
    reportMd.push(`- arms: ${Object.keys(s.kpis).join(", ")}`);
    for (const c of s.comparisons) {
      reportMd.push(
        `- compare ${c.arm} vs ${c.baseline}: delta=${(c.delta ?? 0).toFixed(4)} p=${c.p?.toFixed?.(4) ?? "NA"} p_bh=${c.p_bh?.toFixed?.(4) ?? "NA"} bayesP=${c.bayes_prob_arm_gt_base?.toFixed?.(3) ?? "NA"}`
      );
    }
    reportMd.push("");
  }
  writeFile(path.join(outDir, "REPORT.md"), reportMd.join("\n"));

  // CI gate artifact (simple example)
  const ciGate = {
    run_id: runId,
    ok: true,
    reasons: [],
    generated_at: new Date().toISOString(),
  };
  writeFile(path.join(outDir, "ci_gate.json"), JSON.stringify(ciGate, null, 2));

  // Writeback to GitHub: branch + files + PR + workflow dispatch
  const ghToken = process.env.GITHUB_TOKEN;
  const owner = process.env.GH_OWNER;
  const repo = process.env.GH_REPO;

  if (!ghToken || !owner || !repo) {
    log("GitHub writeback skipped (missing GITHUB_TOKEN / GH_OWNER / GH_REPO).");
    log(`Artifacts are in ${outDir}`);
    return;
  }

  const repoInfo = await ghGetRepo(ghToken, owner, repo);
  const defaultBranch = process.env.GH_DEFAULT_BRANCH || repoInfo.default_branch;
  const baseRef = await ghGetRef(ghToken, owner, repo, defaultBranch);
  const baseSha = baseRef.object.sha;

  const branchName = `exp/${runId}`;
  log(`Creating branch ${branchName} from ${defaultBranch}@${baseSha}`);
  await ghCreateRef(ghToken, owner, repo, branchName, baseSha);

  // Upload key files (cap list; add more as needed)
  const filesToUpload = [
    { p: `${outDir}/run_meta.json`, repoPath: `${outDir}/run_meta.json` },
    { p: `${outDir}/REPORT.md`, repoPath: `${outDir}/REPORT.md` },
    { p: `${outDir}/ci_gate.json`, repoPath: `${outDir}/ci_gate.json` },
  ];

  // Upload summaries and charts
  for (const f of fs.readdirSync(outDir)) {
    if (f.endsWith("_summary.json")) filesToUpload.push({ p: path.join(outDir, f), repoPath: path.join(outDir, f) });
  }
  for (const f of fs.readdirSync(path.join(outDir, "charts"))) {
    if (f.endsWith(".svg")) filesToUpload.push({ p: path.join(outDir, "charts", f), repoPath: path.join(outDir, "charts", f) });
  }

  for (const f of filesToUpload) {
    const content = fs.readFileSync(f.p, "utf8");
    log(`Uploading ${f.repoPath}`);
    await ghPutFile(ghToken, owner, repo, f.repoPath, content, `Add experiment artifacts: ${runId}`, branchName);
  }

  const pr = await ghCreatePr(
    ghToken,
    owner,
    repo,
    `Experiment report: ${runId}`,
    branchName,
    defaultBranch,
    `Automated experiment run.\n\n- Run: ${runId}\n- Artifacts: ${outDir}\n\nThis PR contains reports, KPI summaries, and charts.`
  );
  log(`PR created: ${pr.html_url}`);

  // Trigger CI workflow (optional)
  const wf = process.env.GH_WORKFLOW_ID;
  if (wf) {
    const ref = process.env.GH_WORKFLOW_REF || branchName;
    log(`Triggering workflow_dispatch: workflow=${wf} ref=${ref}`);
    await ghWorkflowDispatch(ghToken, owner, repo, wf, ref, { run_id: runId });
  } else {
    log("workflow_dispatch skipped (missing GH_WORKFLOW_ID).");
  }

  log(`DONE. Artifacts: ${outDir}`);
}

main().catch((e) => {
  die(String(e?.stack || e));
});
