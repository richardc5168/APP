#!/usr/bin/env node
/**
 * login_once.js
 *
 * Purpose:
 * - Open tcool page in a visible browser.
 * - Let user manually complete legal login/verification.
 * - Save Playwright storageState for later bulk downloading.
 *
 * No anti-bot / captcha bypass is implemented.
 */
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const STATE_PATH = path.join(ROOT, 'tools', 'tcool_downloader', 'storageState.json');
const START_URL = process.env.TCOOL_START_URL || 'https://www.tcool.cc/';

function looksLikeVerificationPage(url, title = '') {
  const s = `${url} ${title}`.toLowerCase();
  return (
    s.includes('captcha') ||
    s.includes('challenge') ||
    s.includes('cloudflare') ||
    s.includes('verify') ||
    s.includes('attention required')
  );
}

async function main() {
  // --- runtime info ---
  console.log('=== tcool login_once ===');
  console.log('用途：手動登入一次，儲存可重用 session (storageState)。');
  console.log('注意：不做任何 anti-bot / captcha 繞過。');
  console.log(`Start URL: ${START_URL}`);
  console.log(`Storage state output: ${STATE_PATH}`);

  // --- launch browser for manual login ---
  const browser = await chromium.launch({ headless: false, slowMo: 80 });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto(START_URL, { waitUntil: 'domcontentloaded', timeout: 120000 });

  const title = await page.title();
  const currentUrl = page.url();
  if (looksLikeVerificationPage(currentUrl, title)) {
    console.error('偵測到驗證頁（captcha/challenge）。請先在瀏覽器手動完成驗證後再按 Enter。');
  }

  // --- prompt user to finish manual login flow ---
  console.log('\n請在開啟的瀏覽器中完成：');
  console.log('1) 合法登入（若網站需要）');
  console.log('2) 確認可正常開啟下載頁面');
  console.log('3) 回到終端按 Enter 儲存 session');

  const rl = readline.createInterface({ input, output });
  await rl.question('\n完成後按 Enter 繼續...');
  rl.close();

  // --- persist session to storageState.json ---
  await context.storageState({ path: STATE_PATH });
  console.log(`\n✅ Session 已儲存：${STATE_PATH}`);

  await browser.close();
  console.log('完成。');
}

main().catch((err) => {
  console.error('login_once 失敗:', err?.message || err);
  process.exit(1);
});
