# QA 回饋摘要（尚未產生）

這個檔案會被 [QA 頁面](./index.html) 讀取並顯示。

要產生摘要：
1) 先有外部模型回饋檔：`artifacts/question_reviews.jsonl`
2) 產生摘要：

```powershell
./.venv/Scripts/python.exe scripts/summarize_question_reviews.py --in_jsonl artifacts/question_reviews.jsonl --out_md artifacts/question_reviews_summary.md
```

3) 把產生的 `artifacts/question_reviews_summary.md` 複製/貼上到這個檔案（再重新匯出 web 發佈）。
