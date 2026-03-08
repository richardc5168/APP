# Monetization Validation MVP — 專案盤點

> 產生日期：2026-03-08 | 目標：90 天內驗證「台灣國小五六年級數學補弱」能否穩定收費

---

## 1. 現有頁面清單

### 練習模組（17 個，所有有學生登入 + 作答追蹤）

| 模組 | 路徑 | 年級 | 題數 | 主題 |
|------|------|------|------|------|
| 考前衝刺 | exam-sprint/ | G5-6 | 混合 | 進階題 |
| 帝國闖關 | interactive-g5-empire/ | G5 | 320 | 遊戲化綜合 |
| 生活包1帝國 | interactive-g5-life-pack1-empire/ | G5 | 200 | 生活應用 |
| 生活包1+帝國 | interactive-g5-life-pack1plus-empire/ | G5 | 240 | 生活應用+ |
| 生活包2帝國 | interactive-g5-life-pack2-empire/ | G5 | 200 | 生活應用 |
| 生活包2+帝國 | interactive-g5-life-pack2plus-empire/ | G5 | 250 | 生活應用+ |
| 分數應用題 | fraction-word-g5/ | G5 | 160 | ★分數 |
| 分數基礎 | fraction-g5/ | G5 | 123 | ★分數 |
| 小數互動 | interactive-decimal-g5/ | G5 | 240 | ★小數 |
| 小數單元4 | decimal-unit4/ | G5 | 94 | ★小數 |
| 百分率比率 | ratio-percent-g5/ | G5 | 179 | ★百分率 |
| 生活應用 | life-applications-g5/ | G5 | 300 | ★生活應用 |
| 體積 | volume-g5/ | G5 | 147 | 體積 |
| 大滿貫 | g5-grand-slam/ | G5 | 188 | 綜合 |
| 核心基礎 | interactive-g56-core-foundation/ | G5-6 | 24 | 基礎 |
| 商業分數衝刺 | commercial-pack1-fraction-sprint/ | G5 | 200 | 分數（付費） |
| 離線數學 | offline-math/ | G5 | 30 | 混合 |

**總計：2,895 題（驗證通過）**

### 明星場景對應（★ 標記）

| 主題 | 模組 | 題數小計 |
|------|------|---------|
| 分數 | fraction-g5, fraction-word-g5, commercial-pack1 | 483 |
| 小數 | interactive-decimal-g5, decimal-unit4 | 334 |
| 百分率 | ratio-percent-g5 | 179 |
| 生活應用 | life-applications-g5 | 300 |
| **合計** | | **1,296** |

### 報告 / 管理頁面

| 頁面 | 路徑 | 用途 |
|------|------|------|
| 家長遠端報告 | parent-report/ | 雲端週報（name+PIN） |
| 本機週報 | report/ | CSV 匯出 |
| 教練日誌 | coach/ | 教練介面 |
| 學習地圖 | learning-map/ | 課綱地圖 |
| 任務中心 | task-center/ | 任務列表 |

### 行銷 / 資訊頁

| 頁面 | 路徑 |
|------|------|
| 首頁 | index.html |
| 定價 | pricing/ |
| 關於 | about/ |
| 隱私 | privacy/ |
| 條款 | terms/ |
| QA | qa/ |

---

## 2. 資料結構現況

### 學生登入（student_auth.js）
- 方式：暱稱 + 家長密碼（4-6 位數字）
- 儲存：`localStorage` key `aimath_student_auth_v1`
- 欄位：`{ version, name, pin, created_at }`
- **缺少**：plan_type, plan_status, trial_start, expire_at

### 雲端同步（GitHub Gist）
- Gist registry: `{ entries: { NAME: { pin, data, cloud_ts } } }`
- 同步頻率：20 秒 + 每次答題
- 已修復：lookupStudentReport 使用 auth token 避免 CDN cache

### 作答追蹤（attempt_telemetry.js）
- 儲存：`ai_math_attempts_v1::<user_id>`
- 欄位：ts, question_id, ok, time_ms, max_hint, unit_id, topic_id, kind, error_type
- 上限：5000 筆 / 學生

### 每日限制（daily_limit.js）
- 儲存：`aimath_daily_limit_v1`
- 免費 10 題/天
- 到限後顯示升級 CTA

### 升級提醒（upgrade_banner.js + completion_upsell.js）
- 底部 banner：5 次點擊或 2 分鐘後
- 完成 upsell：作答結束後
- 都指向 pricing/ 或 mailto

---

## 3. 收費現況

### 定價頁（pricing/）
- 免費版 NT$0：考前衝刺 + 基礎偵測 + 三層提示 + 本地週報
- 標準版 NT$299/月：2,900+ 題 + 大滿貫 + 帝國 + 遠端週報 + 每日挑戰
- 進階版 NT$499/月：必殺技 + 進階題 + 國中先修 + 四層提示
- 年繳 8 折

### 付款方式
- **目前**：mailto 聯繫 → 人工開通
- **後端**：server.py 有 subscriptions 資料表（account_id, status, plan, seats）
- **Stripe**：程式碼有 TODO 註解但尚未串接
- **前端**：daily_limit.js 做軟性限制，無硬性訂閱驗證

---

## 4. MVP 缺口分析

| 缺口 | 嚴重度 | 說明 |
|------|--------|------|
| 無前端訂閱狀態 | 🔴 高 | student profile 沒有 plan_type 欄位 |
| 無自助付款流程 | 🔴 高 | 只有 mailto，無法自動開通 |
| 每日限制可繞過 | 🟡 中 | 清 localStorage 就重設 |
| 無事件追蹤系統 | 🟡 中 | 只有 attempt 追蹤，無漏斗事件 |
| 週報無付費差異 | 🟡 中 | 免費/付費看到一樣的報告 |
| 無補救建議引擎 | 🟡 中 | 有弱點排序但無推薦題組 |
| 首頁無明確轉換漏斗 | 🟡 中 | CTA 不夠聚焦 |
| 無 A/B 測試機制 | 🟢 低 | 後續再加 |

---

## 5. 90 天路線圖

### Week 1-2：收費閉環
- 建立前端訂閱狀態（localStorage + Gist 同步）
- Mock payment flow（free → checkout → paid → expired）
- Feature gating（免費版限制）
- 至少 3 個升級入口

### Week 3-4：事件追蹤與 KPI
- 定義 16 個核心事件
- Event logger（localStorage + 批次上傳 Gist）
- 開發者 KPI 儀表板頁面

### Week 5-6：明星場景內容包
- Star Pack 機制（分數/小數/百分率/生活應用）
- 題型標籤 + 難度 + 常見錯誤分類
- 家長端主題包摘要

### Week 7-8：家長週報 V2
- 四區重新設計（表現、雷達、診斷、建議）
- 規則式補救建議引擎
- 付費 gating（完整報告 = 付費功能）

### Week 9-10：Landing Page 改版
- Hero/痛點/解法/場景/方案/FAQ
- 每個 CTA 掛追蹤事件

### Week 11-12：A/B Testing + 優化
- 5 個可配置測試項
- variant 追蹤 + 轉換差異統計
