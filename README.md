# 每日股市新聞 Discord Bot

每天早上自動取得美股三大指數與台股加權指數的最新收盤漲跌幅，蒐集近期市場新聞標題，再使用 Gemini API 寫成繁體中文摘要並推送到 Discord。

摘要順序固定為：

1. 美股三大指數、台股加權指數的漲跌幅
2. 全球股市重要動態
3. 美股三大指數與重要個股
4. 台股重點新聞與盤勢焦點
5. 隔日值得留意的財報、經濟數據與重要會議

> 這是新聞摘要工具，不是投資建議。指數資料來自 Yahoo Finance；新聞標題來自 Google News RSS。若市場休市、資料延遲或來源暫不可用，訊息會如實標示。

## 先準備兩項資料

### 1. 建立 Discord Webhook

在 Discord 目標頻道依序開啟：**編輯頻道 → 整合 → Webhooks → 新增 Webhook → 複製 Webhook URL**。這個 URL 等同發送權限，請勿公開或提交到 GitHub。

### 2. 建立 Gemini API Key

到 [Google AI Studio](https://aistudio.google.com/) 建立 Gemini API Key。此專案預設使用 Gemini API 的免費層模型；可用模型與額度請以 [Gemini API 定價頁](https://ai.google.dev/gemini-api/docs/pricing) 為準。

## 在 VS Code 本機測試

1. 用 VS Code 開啟本專案資料夾。
2. 在終端機建立虛擬環境並啟用：

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. 安裝套件：
   ```bash
   pip install -r requirements.txt
   ```
4. 將 `.env.example` 複製一份並命名為 `.env`。
5. 在 `.env` 填入 `GEMINI_API_KEY` 與 `DISCORD_WEBHOOK_URL`。
6. 執行：
   ```bash
   python main.py
   ```

成功後，Discord 頻道會收到一則摘要。`.env` 已在 `.gitignore` 中，不應上傳。

## 部署到 GitHub Actions

1. 在 GitHub 建立新的 **Private repository**，例如 `stock-news-discord-bot`。
2. 將本專案全部檔案推送至該 repository。請確認 `.env` 沒有被加入版本控制。
3. 在 GitHub repository 開啟 **Settings → Secrets and variables → Actions → Secrets**，新增：
   - `GEMINI_API_KEY`：你的 Gemini API Key
   - `DISCORD_WEBHOOK_URL`：你的 Discord Webhook URL
4. （可選）同頁的 **Variables** 新增 `GEMINI_MODEL`，例如 `gemini-3.5-flash`。未設定時使用預設值。
5. 開啟 **Actions → Daily stock news to Discord → Run workflow**，先手動測試一次。
6. 成功後，工作流程會在每個台灣工作日早上約 **07:45** 排程執行。GitHub 的排程可能有數分鐘延遲；遇到假日仍會執行，但內容會顯示最近的可用收盤資料。

## 自訂時間或內容

- 排程在 `.github/workflows/daily-stock-news.yml` 的 `cron` 設定。GitHub Actions 使用 UTC；台灣比 UTC 快 8 小時。
- 想改為每天早上 08:00（台灣時間），請將 cron 改為 `0 0 * * 0-4`，這會是週一至週五早上 08:00。
- 指數、新聞搜尋與摘要規則可在 `main.py` 的 `INDEXES`、`NEWS_FEEDS` 和 `create_briefing()` 中調整。

## 常見問題

**Discord 沒有收到訊息？** 先在 GitHub Actions 手動執行一次，點進失敗的步驟查看錯誤。最常見原因是 Webhook URL 不完整、已被重設，或 Secrets 名稱不完全一致。

**Gemini 出現模型錯誤？** 將 GitHub Variable `GEMINI_MODEL` 改成你的 Gemini API Key 可用模型，或在本機 `.env` 設定該值後再測試。

**為什麼沒有即時盤中數字？** 此專案設計為晨報，使用最近可取得的收盤值，避免盤中訊號造成混淆。
