# external_web_fraction_app_v1

新增題型 `external_web_fraction_app_v1` 採 **additive plugin/registry** 接入，不改既有路由、既有 schema、既有題型邏輯。

## Feature Flag

- 設定環境變數：`EXTERNAL_WEB_QUESTION_BANK=1`
- 預設關閉；未開啟時，題型不會註冊進 `engine.GENERATORS`。

## 檔案結構

- 題型 plugin：`src/question_types/external_web_fraction_app_v1/type.py`
- 來源清單：`data/external_web_notes/sources.yaml`
- notes ingest：`tools/external_web_ingest/collect_external_fraction_notes.py`
- pack build：`tools/external_web_ingest/build_external_fraction_pack.py`
- pack validate：`tools/external_web_ingest/validate_external_fraction_pack.py`
- notes 產出：`data/external_web_notes/external_web_fraction_app_notes.jsonl`
- pack 產出：`data/external_web_fraction_app_v1_pack.json`

## 一鍵命令

```bash
npm run external:web:ingest
npm run external:web:build
npm run external:web:validate
```

## 每小時命令輪詢（自動執行 + 驗證 + 提交）

- 單次執行（讀本地 `ops/hourly_commands.json`）：
```bash
npm run commands:poll:once
```
- 持續輪詢（預設 30 分鐘）：
```bash
npm run commands:poll
```
- 指定讀 GitHub 指令檔（`blob` 或 `raw` URL 都可）：
```bash
npm run commands:poll -- --watch --interval-min 5 --command-url https://github.com/richardc5168/ai-math-web/blob/main/ops/hourly_commands.json
```

說明：
- 每個 command 執行成功後，會跑 `python tools/validate_all_elementary_banks.py` 與 `npm run verify:all`。
- 驗證全過才會自動 `git add -A`、`git commit --no-verify`、`git push origin main`。
- 結果會寫入 `artifacts/hourly_command_runs.jsonl` 與 `artifacts/hourly_command_latest.json`。

## Notes 契約

每則筆記至少包含：

- `source_url`, `title`, `retrieved_at`
- `grade`（`5` 或 `6`）
- `topic_tags`
- `summary`
- `key_steps`
- `common_mistakes`
- `example_patterns`

引用規則：

- 僅保留摘要，不複製原站完整題解。
- 若有逐字引用，單一片段不超過 25 字，並附 `citation`。

## 驗證與測試

- `python tools/validate_all_elementary_banks.py`
- `python -m pytest tests/test_external_web_fraction_pack_loop.py -q`
- `python -m pytest tests/test_external_web_fraction_contract.py -q`
- `python -m pytest tests/test_question_bank_validation.py -q`
