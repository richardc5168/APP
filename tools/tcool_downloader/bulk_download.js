#!/usr/bin/env node
/**
 * tcool bulk downloader (authorized use only)
 *
 * Features:
 * - Read target pages from urls.txt
 * - Load login session via storageState
 * - Crawl page and collect download targets
 * - Download files to downloads/
 * - Write manifest.json with success/failed result
 * - Retry up to 3 times
 * - Random rate limit delay (2~5s)
 * - Stop immediately on verification page/challenge
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const BASE_DIR = path.join(ROOT, 'tools', 'tcool_downloader');
const URLS_FILE = path.join(BASE_DIR, 'urls.txt');
const STORAGE_STATE = path.join(BASE_DIR, 'storageState.json');
const DOWNLOAD_DIR = path.join(ROOT, 'downloads');
const MANIFEST_PATH = path.join(DOWNLOAD_DIR, 'manifest.json');
const MAX_RETRY = 3;
const AUTO_FILTER_PRESET = true;
const MAX_API_TARGETS = Number(process.env.TCOOL_MAX_API_TARGETS || 20);

class VerificationStopError extends Error {
  constructor(message) {
    super(message);
    this.name = 'VerificationStopError';
  }
}

function nowIso() {
  return new Date().toISOString();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomDelayMs(minSec = 2, maxSec = 5) {
  const min = Math.floor(minSec * 1000);
  const max = Math.floor(maxSec * 1000);
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

async function rateLimitDelay(label = 'operation') {
  const ms = randomDelayMs(2, 5);
  console.log(`⏳ Rate limit (${label}): wait ${ms}ms`);
  await sleep(ms);
}

function normalizeName(name) {
  return String(name || 'download')
    .replace(/[\\/:*?"<>|]/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 140);
}

function looksLikeVerification(url, title = '', bodyText = '') {
  const s = `${url} ${title} ${bodyText}`.toLowerCase();
  return (
    s.includes('captcha') ||
    s.includes('challenge') ||
    s.includes('cloudflare') ||
    s.includes('attention required') ||
    s.includes('verify you are human')
  );
}

function isDownloadUrl(url) {
  const u = String(url || '').toLowerCase();
  return (
    u.includes('.pdf') ||
    u.includes('/d/q/') ||
    u.includes('/d/a/') ||
    u.includes('download')
  );
}

function safeFileNameFromUrl(url, fallback = 'download.bin') {
  try {
    const parsed = new URL(url);
    const last = parsed.pathname.split('/').filter(Boolean).pop();
    return normalizeName(last || fallback);
  } catch {
    return normalizeName(fallback);
  }
}

function extractTcoolIdentityFromUrl(url) {
  try {
    const m = String(url || '').match(/\/d\/(q|a)\/([^/?#]+)/i);
    if (!m) return { paperType: 'unknown', examId: null };
    const paperType = m[1].toLowerCase() === 'q' ? 'question' : 'answer';
    const examId = String(m[2] || '').replace(/\.pdf$/i, '');
    return { paperType, examId: examId || null };
  } catch {
    return { paperType: 'unknown', examId: null };
  }
}

function buildPreferredFileName(fileUrl, fallbackName, contentType = '') {
  const { paperType, examId } = extractTcoolIdentityFromUrl(fileUrl);
  if (examId) {
    const ext = String(contentType || '').includes('pdf') ? '.pdf' : path.extname(fallbackName || '') || '.bin';
    return normalizeName(`tcool_${examId}_${paperType}${ext}`);
  }
  return normalizeName(fallbackName || safeFileNameFromUrl(fileUrl));
}

async function ensureDirs() {
  await fs.mkdir(DOWNLOAD_DIR, { recursive: true });
  await fs.mkdir(BASE_DIR, { recursive: true });
}

async function readUrls() {
  const raw = await fs.readFile(URLS_FILE, 'utf8');
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));
}

async function writeManifest(manifest) {
  await fs.writeFile(MANIFEST_PATH, JSON.stringify(manifest, null, 2), 'utf8');
}

async function appendManifest(manifest, item) {
  manifest.push(item);
  await writeManifest(manifest);
}

async function detectVerificationOrStop(page) {
  const url = page.url();
  const title = await page.title();
  const bodyText = await page.locator('body').innerText().catch(() => '');

  if (looksLikeVerification(url, title, bodyText)) {
    return {
      blocked: true,
      reason: `verification_detected: ${title || url}`,
    };
  }
  return { blocked: false, reason: '' };
}

async function applyTcoolPresetFilters(page) {
  console.log('🧩 Apply tcool preset filters: 5年級 / 數學 / 下學期 / 第一次段考 / 有答案卷');

  const ensureSelect = async (selector, value) => {
    const el = page.locator(selector).first();
    if (await el.count()) {
      await el.selectOption(value).catch(() => {});
      await rateLimitDelay(`set ${selector}=${value}`);
    }
  };

  await ensureSelect('select[name="grade"]', '5');
  await ensureSelect('select[name="subject"]', '數學');
  await ensureSelect('select[name="semester"]', '2');
  await ensureSelect('select[name="period"]', '1');
  await ensureSelect('select[name="has_answer"]', '1');

  const searchBtn = page
    .locator('button:has-text("搜尋考卷"), input[type="button"][value*="搜尋"], input[type="submit"][value*="搜尋"]')
    .first();

  if ((await searchBtn.count()) > 0) {
    await rateLimitDelay('click 搜尋考卷');
    await searchBtn.click({ timeout: 20000 }).catch(() => {});
    await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(1500);
  }
}

async function collectTargets(page) {
  const targetSet = new Map();

  const hrefs = await page.$$eval('a[href]', (nodes) =>
    nodes.map((n) => ({
      href: n.getAttribute('href') || '',
      text: (n.textContent || '').trim(),
      absHref: n.href || '',
    }))
  );

  for (const item of hrefs) {
    const href = item.href || '';
    const text = item.text || '';
    const absHref = item.absHref || '';
    if (!href) continue;
    const abs = absHref || href;
    const matchText = /題目卷|答案卷|下載|pdf/i.test(text);
    if (isDownloadUrl(abs) || matchText) {
      targetSet.set(abs, {
        mode: 'direct',
        fileUrl: abs,
        text,
      });
    }
  }

  const onclickLinks = await page.$$eval('[onclick]', (nodes) =>
    nodes.map((n) => ({
      onclick: n.getAttribute('onclick') || '',
      text: (n.textContent || '').trim(),
      origin: location.origin,
    }))
  );

  for (const item of onclickLinks) {
    const raw = String(item.onclick || '');
    const re = /\/d\/[qa]\/[^'"\s)]+/gi;
    let m;
    while ((m = re.exec(raw)) !== null) {
      const href = m[0].startsWith('http') ? m[0] : `${item.origin}${m[0]}`;
      targetSet.set(href, {
        mode: 'direct',
        fileUrl: href,
        text: item.text || 'onclick-target',
      });
    }
  }

  const buttonMeta = await page.$$eval('button, [role="button"]', (nodes) =>
    nodes.map((n) => ({ text: (n.textContent || '').trim() }))
  );

  const buttonCandidates = buttonMeta
    .map((b) => b.text)
    .filter((t) => /題目卷|答案卷|下載|pdf/i.test(t));

  return {
    directTargets: Array.from(targetSet.values()),
    buttonCandidates,
  };
}

async function fetchTargetsViaTcoolApi(page) {
  const results = [];
  const seen = new Set();
  let p = 1;

  while (true) {
    const payload = {
      action: 'exam_data',
      p,
      pp: 20,
      grade: '5',
      subject: '數學',
      semester: '2',
      period: '1',
      has_answer: '1',
    };

    const data = await page.evaluate(async (params) => {
      try {
        const r = await fetch('https://www.tcool.cc/api-exam.php', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
        });
        return await r.json();
      } catch (e) {
        return { error: String(e && e.message ? e.message : e) };
      }
    }, payload);

    if (data?.error) {
      console.warn(`⚠️ tcool api fallback error (page ${p}): ${data.error}`);
      break;
    }

    const exams = Array.isArray(data?.data) ? data.data : [];
    const totalPages = Number(data?.pagination?.totalPages || 1);

    for (const exam of exams) {
      const q = String(exam?.question || '').trim();
      const a = String(exam?.answer || '').trim();
      if (q && q !== 'null') {
        const qUrl = `https://tcool.cc/d/q/${q}`;
        if (!seen.has(qUrl)) {
          seen.add(qUrl);
          results.push({ mode: 'direct', fileUrl: qUrl, text: 'api-question', examId: String(exam?.id || ''), paperType: 'question' });
        }
      }
      if (a && a !== 'null') {
        const aUrl = `https://tcool.cc/d/a/${a}`;
        if (!seen.has(aUrl)) {
          seen.add(aUrl);
          results.push({ mode: 'direct', fileUrl: aUrl, text: 'api-answer', examId: String(exam?.id || ''), paperType: 'answer' });
        }
      }

      if (results.length >= MAX_API_TARGETS) {
        break;
      }
    }

    if (results.length >= MAX_API_TARGETS) break;
    if (p >= totalPages || exams.length === 0) break;
    p += 1;
    await rateLimitDelay('api pagination');
  }

  return results;
}

async function tryDirectDownload({ request, fileUrl, sourcePage, manifest, examId = null, paperType = null }) {
  for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
    await rateLimitDelay(`direct download attempt ${attempt}`);
    try {
      const resp = await request.get(fileUrl, { timeout: 120000 });
      if (!resp.ok()) {
        throw new Error(`HTTP ${resp.status()}`);
      }

      const headers = resp.headers();
      const ct = String(headers['content-type'] || '').toLowerCase();
      const cd = String(headers['content-disposition'] || '');

      let filename = '';
      const m = cd.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i);
      if (m?.[1]) filename = decodeURIComponent(m[1].replace(/"/g, ''));
      if (!filename) filename = safeFileNameFromUrl(fileUrl, ct.includes('pdf') ? 'download.pdf' : 'download.bin');
      filename = buildPreferredFileName(fileUrl, filename, ct);

      const body = Buffer.from(await resp.body());
      if (ct.includes('text/html')) {
        const sample = body.toString('utf8').slice(0, 20000);
        if (looksLikeVerification(fileUrl, '', sample)) {
          throw new VerificationStopError('verification_detected_in_download_response');
        }
      }

      const outPath = path.join(DOWNLOAD_DIR, filename);
      await fs.writeFile(outPath, body);

      await appendManifest(manifest, {
        filename,
        source_page: sourcePage,
        file_url: fileUrl,
        exam_id: examId,
        paper_type: paperType,
        downloaded_at: nowIso(),
        status: 'success',
        attempts: attempt,
        failed_reason: null,
      });

      console.log(`✅ Downloaded: ${filename}`);
      return { ok: true, blocked: false, reason: '' };
    } catch (err) {
      const failedReason = err?.message || String(err);
      console.warn(`⚠️ direct download failed (${attempt}/${MAX_RETRY}): ${fileUrl} -> ${failedReason}`);

      if (err instanceof VerificationStopError) {
        await appendManifest(manifest, {
          filename: safeFileNameFromUrl(fileUrl),
          source_page: sourcePage,
          file_url: fileUrl,
          exam_id: examId,
          paper_type: paperType,
          downloaded_at: nowIso(),
          status: 'failed',
          attempts: attempt,
          failed_reason: failedReason,
        });
        return { ok: false, blocked: true, reason: failedReason };
      }

      if (attempt === MAX_RETRY) {
        await appendManifest(manifest, {
          filename: safeFileNameFromUrl(fileUrl),
          source_page: sourcePage,
          file_url: fileUrl,
          exam_id: examId,
          paper_type: paperType,
          downloaded_at: nowIso(),
          status: 'failed',
          attempts: attempt,
          failed_reason: failedReason,
        });
      }
    }
  }
  return { ok: false, blocked: false, reason: '' };
}

async function tryClickDownload({ page, buttonText, sourcePage, manifest, examId = null, paperType = null }) {
  const locator = page.locator(`button:has-text("${buttonText}"), [role="button"]:has-text("${buttonText}"), a:has-text("${buttonText}")`).first();
  const exists = (await locator.count()) > 0;
  if (!exists) {
    await appendManifest(manifest, {
      filename: null,
      source_page: sourcePage,
      file_url: null,
      exam_id: examId,
      paper_type: paperType,
      downloaded_at: nowIso(),
      status: 'failed',
      attempts: 1,
      failed_reason: `button_not_found: ${buttonText}`,
    });
    return { ok: false, blocked: false, reason: '' };
  }

  for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
    await rateLimitDelay(`click download attempt ${attempt}`);
    try {
      const waitDownload = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);
      const waitPopup = page.waitForEvent('popup', { timeout: 15000 }).catch(() => null);

      await locator.click({ timeout: 15000 });

      const dl = await waitDownload;
      if (dl) {
        const suggested = buildPreferredFileName(dl.url() || '', dl.suggestedFilename() || 'download.bin', 'application/octet-stream');
        const outPath = path.join(DOWNLOAD_DIR, suggested);
        await dl.saveAs(outPath);

        await appendManifest(manifest, {
          filename: suggested,
          source_page: sourcePage,
          file_url: dl.url() || null,
          exam_id: examId,
          paper_type: paperType,
          downloaded_at: nowIso(),
          status: 'success',
          attempts: attempt,
          failed_reason: null,
        });
        console.log(`✅ Click downloaded: ${suggested}`);
        return { ok: true, blocked: false, reason: '' };
      }

      const popup = await waitPopup;
      if (popup) {
        const url = popup.url();
        const popupTitle = await popup.title().catch(() => '');
        await popup.close().catch(() => {});
        if (looksLikeVerification(url, popupTitle, '')) {
          return { ok: false, blocked: true, reason: `verification_detected_in_popup: ${popupTitle || url}` };
        }
        if (isDownloadUrl(url)) {
          const directResult = await tryDirectDownload({
            request: page.context().request,
            fileUrl: url,
            sourcePage,
            manifest,
            examId,
            paperType,
          });
          if (directResult.blocked) return directResult;
          if (directResult.ok) return directResult;
        }
      }

      throw new Error('no_download_event_or_popup');
    } catch (err) {
      const failedReason = err?.message || String(err);
      console.warn(`⚠️ click download failed (${attempt}/${MAX_RETRY}): ${buttonText} -> ${failedReason}`);

      if (attempt === MAX_RETRY) {
        await appendManifest(manifest, {
          filename: null,
          source_page: sourcePage,
          file_url: null,
          exam_id: examId,
          paper_type: paperType,
          downloaded_at: nowIso(),
          status: 'failed',
          attempts: attempt,
          failed_reason: `click_failed:${buttonText}:${failedReason}`,
        });
      }
    }
  }
  return { ok: false, blocked: false, reason: '' };
}

async function main() {
  await ensureDirs();

  const manifest = [];
  await writeManifest(manifest);

  const urls = await readUrls();
  if (!urls.length) {
    throw new Error(`urls.txt is empty: ${URLS_FILE}`);
  }

  const hasState = await fs
    .access(STORAGE_STATE)
    .then(() => true)
    .catch(() => false);

  if (!hasState) {
    throw new Error(`storageState not found: ${STORAGE_STATE}\n請先執行 npm run login:once`);
  }

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    acceptDownloads: true,
    storageState: STORAGE_STATE,
  });
  const page = await context.newPage();

  const seenFileUrls = new Set();

  try {
    for (const sourcePage of urls) {
      await rateLimitDelay('open page');
      console.log(`\n🌐 Open: ${sourcePage}`);
      await page.goto(sourcePage, { waitUntil: 'domcontentloaded', timeout: 120000 });

      if (AUTO_FILTER_PRESET && /tcool\.cc/i.test(sourcePage)) {
        await applyTcoolPresetFilters(page);
      }

      const check = await detectVerificationOrStop(page);
      if (check.blocked) {
        await appendManifest(manifest, {
          filename: null,
          source_page: sourcePage,
          file_url: null,
          downloaded_at: nowIso(),
          status: 'failed',
          attempts: 1,
          failed_reason: check.reason,
        });
        console.error(`⛔ Stop: ${check.reason}`);
        break;
      }

      const { directTargets, buttonCandidates } = await collectTargets(page);
      console.log(`Found direct targets: ${directTargets.length}, button candidates: ${buttonCandidates.length}`);

      let mergedDirectTargets = [...directTargets];
      if (mergedDirectTargets.length === 0 && /tcool\.cc/i.test(sourcePage)) {
        const apiTargets = await fetchTargetsViaTcoolApi(page);
        if (apiTargets.length > 0) {
          console.log(`Found API fallback targets: ${apiTargets.length}`);
          mergedDirectTargets = apiTargets;
        }
      }

      for (const t of mergedDirectTargets) {
        if (seenFileUrls.has(t.fileUrl)) continue;
        seenFileUrls.add(t.fileUrl);
        const directResult = await tryDirectDownload({
          request: context.request,
          fileUrl: t.fileUrl,
          sourcePage,
          manifest,
          examId: t.examId || null,
          paperType: t.paperType || null,
        });
        if (directResult.blocked) {
          console.error(`⛔ Stop: ${directResult.reason}`);
          return;
        }
      }

      for (const btnText of buttonCandidates) {
        const clickResult = await tryClickDownload({
          page,
          buttonText: btnText,
          sourcePage,
          manifest,
          examId: null,
          paperType: null,
        });
        if (clickResult?.blocked) {
          await appendManifest(manifest, {
            filename: null,
            source_page: sourcePage,
            file_url: null,
            downloaded_at: nowIso(),
            status: 'failed',
            attempts: 1,
            failed_reason: clickResult.reason,
          });
          console.error(`⛔ Stop: ${clickResult.reason}`);
          return;
        }
      }
    }
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
    console.log(`\nManifest written: ${MANIFEST_PATH}`);
    console.log(`Downloads folder: ${DOWNLOAD_DIR}`);
  }
}

main().catch((err) => {
  console.error('bulk_download failed:', err?.message || err);
  process.exit(1);
});
