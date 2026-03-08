# Metrics Dashboard

目的：讓開發與產品能直接在本地看到 monetization MVP 是否有效。

## 1. Dashboard 位置

- 開發者頁面：`docs/kpi/index.html`
- 實作檔：`docs/kpi/index.html`
- 資料來源：`docs/shared/analytics.js`

## 2. 已提供的面板

### KPI Cards

- 總事件數
- 獨立使用者
- 答題數
- 正確率
- 提示使用量
- 試用開通數
- 付費成功數
- Trial -> 付費轉換率
- Landing 瀏覽
- Pricing 瀏覽
- 週報瀏覽
- 升級點擊

### Funnel

- Landing 瀏覽
- Pricing 瀏覽
- 升級點擊
- 試用開通
- 結帳開始
- 付費成功

### Event Breakdown

- 前 15 名事件分佈
- 最近 50 筆事件清單

### A/B Dashboard

- 每個測試的 A/B assignment 次數
- conversion 次數
- conversion rate
- 樣本不足提示
- 當前領先 variant 判定

## 3. KPI 定義

| KPI | 定義 |
|-----|------|
| 免費 -> 試用轉換率 | `trial_start / landing_page_view` |
| 試用 -> 付費轉換率 | `checkout_success / trial_start` |
| 每週作答題數 | 7 天內 `question_submit + question_correct` / 活躍學生數 |
| 平均提示開啟率 | `hint_open / (question_submit + question_correct)` |
| 週報瀏覽率 | `weekly_report_view / active_parent_sessions` |
| 明星場景主題完成率 | 需以 `star_pack_module_click + session_complete` 補齊 |
| 主題弱點分布 | 需由作答 telemetry 的 module/topic 聚合 |

## 4. 待補強 KPI

以下 KPI 需求已定義，但目前仍屬下一步優化：

- 7 日留存
- 30 日留存
- 完成家長週報後回流率
- 明星場景主題完成率（精準版）
- 主題弱點分布趨勢

原因：目前事件資料已足夠做基礎觀察，但 cohort retention 與主題 completion 還需要更一致的 topic/module 標註。

## 5. 使用方式

1. 進入 `docs/kpi/`
2. 切換 7 天 / 30 天 / 全部
3. 點 `匯出 JSON` 可取得原始事件資料
4. 若要重算最新資料，點 `重新整理`

## 6. 驗收標準

- 能看出從首頁到付費的主要漏斗
- 能看到主要事件是否有觸發
- 能查 A/B 測試效果差異
- 不需後端即可本地使用
