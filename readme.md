## 監控 pgsharp 的最新版本號，並在版本變更時發送 LINE 通知。

### 1. 程式目的
- **功能**：監控 [https://www.pgsharp.com/](https://www.pgsharp.com/) 的最新版本號，並在版本變更時發送 LINE 通知。
- **執行環境**：Synology DS215J NAS，DSM 7.1.1-42962 Update 8，Python 3.8.12。
- **背景執行**：透過 DSM 任務排程器定時運行，無需登入。

### 2. 主要功能
- **版本抓取**：
  - 從網頁提取 "Latest Version: X.XXX.X (Android Only)" 中的版本號（例如 "1.187.0"）。
  - 使用 `requests` 模組和正則表達式（`re`）實現。
- **版本比對**：
  - 將抓取的版本與儲存的版本（`pgsharp_version.txt`）比對。
  - 首次執行時儲存初始版本，無通知。
  - 版本變更時更新檔案並發送通知。
- **LINE 通知**：
  - 使用 LINE Messaging API 取代即將停用的 LINE Notify。
  - 需要 `CHANNEL_ACCESS_TOKEN` 和 `TARGET_USER_ID`。
- **日誌記錄**：
  - 記錄執行過程至 `/volume1/././././PGSharp/pgsharp_monitor_log.txt`。

### 3. 環境配置
- **Python 路徑**：`/bin/python3`
- **Pip 路徑**：`/bin/pip3`
- **模組安裝**：
  - `requests`：透過 `pip3 install requests` 安裝。
  - 修復過程：重新安裝 `pip` 以解決 `pip._internal` 缺失問題。
- **檔案路徑**：
  - 程式：`/volume1/././././PGSharp/pgsharp_monitor.py`
  - 版本檔案：`/volume1/././././PGSharp/pgsharp_version.txt`
  - 日誌檔案：`/volume1/././././PGSharp/pgsharp_monitor.log`

### 4. 執行方式
- **手動測試**：`python3 /volume1/././././PGSharp/pgsharp_monitor.py`
- **排程執行**：DSM 任務排程器設定：`/bin/python3 /volume1/././././PGSharp/pgsharp_monitor.py`

### 5. 注意事項
- **權限**：需確保檔案路徑有寫入權限。
- **Messaging API 配置**：需手動填入 `CHANNEL_ACCESS_TOKEN` 和 `TARGET_USER_ID`。
- **穩定性**：已處理網路錯誤（`RequestException`），並記錄所有操作。