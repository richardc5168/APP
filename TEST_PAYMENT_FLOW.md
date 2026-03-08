# TEST_PAYMENT_FLOW.md — Mock 付費流程測試

## 前置條件
- 開啟 Chrome DevTools Console
- 前往任一練習頁面

## 測試 1：正常免費流程
1. 清除 localStorage：`localStorage.removeItem('aimath_subscription_v1')`
2. 重新整理頁面
3. 驗證：`AIMathSubscription.getPlanInfo()` → `plan_status: "free"`
4. 做 10 題後 → 出現每日限制提示
5. 限制提示有「免費試用 7 天」和「查看方案」按鈕

## 測試 2：開始試用
1. 前往 /pricing/
2. 點擊標準版「🎁 免費試用 7 天」
3. 在彈出視窗點「✅ 立即開始試用」
4. 驗證：`AIMathSubscription.getPlanInfo()` → `plan_status: "trial", plan_type: "standard"`
5. 回到練習頁面 → 每日限制不再出現
6. 驗證事件：`AIMathAnalytics.query({event:'trial_start'})` → 有 1 筆

## 測試 3：模擬付款成功
1. Console 執行：`AIMathSubscription.confirmPayment('standard')`
2. 驗證：`AIMathSubscription.getPlanInfo()` → `plan_status: "paid_active"`
3. 驗證事件：`AIMathAnalytics.query({event:'checkout_success'})` → 有 1 筆

## 測試 4：模擬試用到期
1. Console 手動設定過期時間：
   ```js
   var sub = JSON.parse(localStorage.getItem('aimath_subscription_v1'));
   sub.expire_at = new Date(Date.now() - 1000).toISOString();
   localStorage.setItem('aimath_subscription_v1', JSON.stringify(sub));
   ```
2. 重新整理頁面
3. 驗證：`AIMathSubscription.getPlanInfo()` → `plan_status: "expired"`
4. 每日限制重新出現

## 測試 5：取消訂閱
1. Console: `AIMathSubscription.cancelSubscription()`
2. 驗證：`AIMathSubscription.getPlanInfo()` → `plan_status: "expired"`

## 測試 6：重設為免費
1. Console: `AIMathSubscription.resetToFree()`
2. 驗證：`AIMathSubscription.getPlanInfo()` → `plan_status: "free", plan_type: "free"`

## 測試 7：權限切換驗證
| 狀態 | `isPaid()` | `canAccessStarPack()` | `getDailyLimit()` | `canAccessFullReport()` |
|------|-----------|----------------------|-------------------|------------------------|
| free | false | false | 10 | false |
| trial | true | true | -1 | true |
| paid_active | true | true | -1 | true |
| expired | false | false | 10 | false |

## 測試 8：升級入口驗證
從以下頁面可進入升級流程：
1. **首頁** → pricing 方案區連結
2. **pricing 頁** → 方案卡片 CTA 按鈕
3. **每日限制對話框** → 「免費試用 7 天」按鈕
4. **升級 Banner** → 底部固定 banner
5. **家長週報** → 報告底部升級 CTA

## 未來 Stripe 整合
替換 `confirmPayment()` 為 Stripe Checkout webhook callback。
subscription.js 的 `mock_mode: true` 改為 false 後串接真實 API。
