# Analytics Event Schema

目的：用最小可用事件追蹤，驗證「免費試用 -> 持續使用 -> 願意付費 -> 願意續訂」是否成立。

## 1. 儲存方式

- 前端事件儲存：`localStorage` key `aimath_analytics_v1`
- session id：`sessionStorage` key `aimath_session_id`
- 實作檔案：`docs/shared/analytics.js`
- 目前模式：純前端本地記錄，可匯出 JSON，方便後續接 API 或資料倉儲

## 2. 基本事件格式

```json
{
  "event": "question_submit",
  "ts": 1741363200000,
  "user_id": "小明",
  "role": "student",
  "session_id": "s_m84abc_12xyzz",
  "page": "/ai-math-web/docs/fraction-g5/",
  "data": {
    "topic": "fraction",
    "grade": 5,
    "question_id": "u3_frac_add_001"
  }
}
```

## 3. 標準欄位

所有新事件至少要帶：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `event` | string | 事件名稱 |
| `ts` | number | Unix epoch ms |
| `user_id` | string | 學生名或匿名識別 |
| `role` | string | `student` / `parent` / `coach` |
| `session_id` | string | 同一瀏覽 session 識別 |
| `page` | string | 當前頁面路徑 |
| `data.topic` | string | 主題，例如 `fraction` / `decimal` / `percent` / `life` |
| `data.grade` | number | 年級，主要為 5 或 6 |

備註：目前實作已穩定提供 `user_id`、`role`、`session_id`、`page`。`topic` / `grade` 由各功能頁逐步補進 `data`。

## 4. 核心事件清單

| 事件 | 目的 | 主要 data 欄位 |
|------|------|---------------|
| `landing_page_view` | 首頁進站量 | `entry`, `referrer` |
| `pricing_view` | 定價頁瀏覽 | `source` |
| `trial_start` | 開始試用 | `plan`, `expire` |
| `upgrade_click` | 點擊升級 CTA | `source`, `context`, `plan` |
| `checkout_start` | 開始結帳 | `plan` |
| `checkout_success` | 付款成功 | `plan`, `expire` |
| `question_start` | 開始作答 | `question_id`, `topic`, `module` |
| `question_submit` | 送出答案 | `question_id`, `topic`, `module`, `correct:false` |
| `question_correct` | 答對 | `question_id`, `topic`, `module`, `correct:true` |
| `hint_open` | 打開提示 | `question_id`, `hint_level`, `topic` |
| `retry_start` | 錯題重做 | `question_id`, `topic` |
| `session_complete` | 完成一段練習 | `module`, `count`, `accuracy` |
| `weekly_report_view` | 家長週報瀏覽 | `student_name`, `report_level` |
| `remedial_recommendation_click` | 點推薦題組 | `module`, `priority`, `concept` |
| `return_next_day` | 次日回流 | `days_since_last` |
| `return_next_week` | 次週回流 | `days_since_last` |

## 5. 已實作事件

目前 repo 已實作或部分實作：

- `landing_page_view`
- `pricing_view`
- `trial_start`
- `upgrade_click`
- `checkout_start`
- `checkout_success`
- `question_submit`
- `question_correct`
- `hint_open`
- `weekly_report_view`
- `ab_assign`
- `ab_conversion`
- `star_pack_view`
- `star_pack_module_click`
- `subscription_expired`
- `subscription_cancel`

## 6. 命名規則

- 一律用 snake_case
- 動詞放後面，物件放前面：`pricing_view`, `checkout_success`
- 不用 page-specific 命名污染核心事件；頁面資訊放 `page` 或 `data.context`

## 7. 事件掛載原則

- 每個新 CTA 上線前，先掛 `upgrade_click` 或對應 conversion 事件
- 每個會改變權限或狀態的動作，都要有明確事件
- 不做「隱性成功」：trial、checkout、expired 都必須可查

## 8. Acceptance Criteria

- 所有商業漏斗關鍵節點都可被記錄
- 事件資料可在本地儀表板查詢與匯出
- 新功能如未掛事件，不視為完成
