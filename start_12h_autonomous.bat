@echo off
REM ============================================================
REM  12 小時自主優化 — 一鍵啟動
REM  雙擊此檔案即可啟動，不需要 VS Code 或 Copilot
REM
REM  功能：
REM    - 每 20 分鐘自動迴圈：出題 → 解題 → 驗證提示 → 優化 → 驗證 → 提交
REM    - 失敗自動 self-heal + 重試
REM    - 3 次連續失敗自動 backoff（避免浪費 CPU）
REM    - 12 小時後自動停止
REM
REM  可選參數：
REM    start_12h_autonomous.bat                     預設 12 小時
REM    start_12h_autonomous.bat --hours 8           8 小時
REM    start_12h_autonomous.bat --dry-run           模擬（不提交）
REM    start_12h_autonomous.bat --no-push           提交但不推送
REM ============================================================

cd /d "%~dp0.."
title AI Math 12H Autonomous Runner

echo.
echo ============================================================
echo   AI 數學自主優化已啟動
echo   工作目錄: %CD%
echo   時間: %DATE% %TIME%
echo   按 Ctrl+C 可隨時安全停止
echo ============================================================
echo.

node tools/run_12h_autonomous.cjs --hours 12 --interval-min 20 --auto-push %*

echo.
echo ============================================================
echo   自主優化已結束
echo   報告: artifacts\autonomous_run_summary.json
echo   歷史: artifacts\autonomous_history.jsonl
echo ============================================================
pause
