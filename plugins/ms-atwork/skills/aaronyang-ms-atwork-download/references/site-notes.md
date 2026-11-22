## 網站機制與踩過的坑

- 文件點擊會讓 iframe 導向 `userCommonPrivateDynamicFileDownload.do`。攔截時要回 204，不能 abort，否則 iframe 會掉到 `chrome-error://`。
- 報表跑完會跳對話框，要點「click here」才會導向下載網址。
- Account Summary 以導覽回傳 PDF，事後讀不到內容，要用 route.fetch 當下取得。只有網頁和 PDF 兩種格式。
- ESPP 報表沒有日期區間欄位，檔名標「截至日期」。
- 授予明細頁用瀏覽器導覽會卡住，改為 GET HTML、去掉 script 後離線轉 PDF。
- 部分文件（如 Malaysia）用站內 pdf.js 檢視器開啟，會留下空白分頁，可能讓 CDP 連線卡住；連不上時先關掉空白分頁。
- 同一文件每次下載約有 10 個位元組不同（應為產檔時間戳），雜湊比不出重複，要比 PDF 內文。
- Sync API 的等待迴圈不能用 `time.sleep`，否則 `page.url` 不會更新。
- 介面語言是帳號設定（Profile 設定頁），不是瀏覽器語言決定；2026-11 曾變成中文（zh_HK），各階段因而逾時。改 `UserLocale` cookie 或 Accept-Language 都無效。選擇器、日期格式（`30-Sep-2026` vs `30-9月-2026`）和下載記錄鍵值都依賴英文，所以腳本登入後若分頁標題不是英文就停下。`generalConditions.do` 不論語言都含中文，不能拿來判斷。
