# Roadmap 12 Weeks

原則：先驗證商業，再擴產品。所有功能先求能跑、能追蹤、能驗證。

## 兩週版本

### 目標

- 打通最小收費閉環
- 讓家長看得懂免費 / 付費差異

### 功能範圍

- pricing page
- mock payment flow
- subscription status storage
- feature gating
- 至少 3 個 upgrade CTA 入口

### 涉及檔案

- `docs/shared/subscription.js`
- `docs/pricing/index.html`
- `docs/shared/daily_limit.js`
- `docs/index.html`
- `docs/parent-report/index.html`

### 風險

- localStorage 狀態可被重設
- mock payment 不代表真實金流穩定度

### 驗收條件

- 看得到清楚方案差異
- 可從至少 3 個頁面進入升級流程
- status 能影響功能顯示

### 建議順序

- 先做：subscription model -> pricing -> gating -> CTA
- 後做：真金流串接

## 四週版本

### 目標

- 看懂漏斗與基礎轉換

### 功能範圍

- analytics schema
- event logger
- KPI dashboard
- 主要頁面事件掛載

### 涉及檔案

- `docs/shared/analytics.js`
- `docs/shared/attempt_telemetry.js`
- `docs/kpi/index.html`
- `docs/index.html`
- `docs/pricing/index.html`

### 風險

- topic / grade 標記不一致會影響統計品質

### 驗收條件

- 能看 landing -> pricing -> trial -> paid 漏斗
- 能匯出事件 JSON
- 能看到主要事件分布

### 建議順序

- 先做：logger -> core events -> dashboard
- 後做：cohort retention 精算

## 八週版本

### 目標

- 聚焦四大主題，做出付費主打內容與家長可理解的結果頁

### 功能範圍

- Star Pack
- 家長週報 V2
- recommendation engine v1
- 主題包 gating

### 涉及檔案

- `docs/star-pack/index.html`
- `docs/parent-report/index.html`
- `docs/shared/subscription.js`

### 風險

- pack metadata 仍偏模組層，不夠到單題層
- recommendation 邏輯仍為規則式

### 驗收條件

- 首頁能明確導到明星場景
- 家長看得懂弱點與建議
- 免費 / 付費差異明顯

### 建議順序

- 先做：Star Pack -> 報表 V2 -> recommendation
- 後做：更細緻單題標記與自動化推薦

## 十二週版本

### 目標

- 用 landing page 與 A/B 測試優化轉換
- 開始進入商業驗證迭代期

### 功能範圍

- landing page 改版
- A/B testing framework
- KPI A/B dashboard
- 依測試結果優化 CTA、文案、入口位置

### 涉及檔案

- `docs/index.html`
- `docs/shared/abtest.js`
- `docs/pricing/index.html`
- `docs/kpi/index.html`

### 風險

- 流量不足時，A/B 結果容易失真
- 若沒有正式支付，後段轉換仍受限制

### 驗收條件

- CTA 與試用入口都能追蹤
- variant 與 conversion 可關聯
- 能依數據調整首頁與 pricing

### 建議順序

- 先做：首頁關鍵訊息清楚化
- 再做：A/B test 小步快跑
- 最後做：正式金流與 retention 優化

## 總結順序

1. 先把收費閉環打通
2. 再把事件與 KPI 接上
3. 再聚焦四大明星場景
4. 再讓家長週報變成續訂理由
5. 最後用 landing 與 A/B test 優化轉換
