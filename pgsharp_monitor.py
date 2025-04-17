# 程式碼來自 Google AI Studio 2025/04/16
# 此程式只在 synology DS215J 執行
# 在 DSM 套件中心安裝 python 3.9
# root 以 ssh key 連線手動安裝 pip3
# /bin/pip3 install requests python-dotenv # 增加 dotenv 方便管理設定
# 以 ssh 連線測試執行程式，沒問題後再以 DSM 內的 任務排程表 執行 

import requests
import re
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from requests.exceptions import RequestException
from typing import Optional, Dict, Any # 用於型別提示
from dotenv import load_dotenv # 讀取 .env 檔案

# --- 設定區 ---

# 讀取環境變數 (建議方式)
# 建立一個與此 .py 檔案同目錄的 .env 檔案，內容如下:
# CHANNEL_ACCESS_TOKEN="您的LINE_CHANNEL_ACCESS_TOKEN"
# TARGET_USER_ID="您的LINE_USER_ID"
# SCRIPT_BASE_DIR="/volume1/homes/ken/git/python3/PGSharp" # 可選，腳本相關檔案的基礎路徑

# 載入 .env 檔案中的環境變數
# 指定 .env 檔案路徑，如果 .env 與 .py 在同一目錄，可以省略 dotenv_path
script_dir = Path(__file__).parent # 取得此腳本所在的目錄
dotenv_path = script_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

# 從環境變數讀取設定，若環境變數不存在則使用預設值或報錯
# 如果使用 DSM 任務排程，可以直接在排程設定中定義環境變數，就不一定需要 .env 檔案
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
TARGET_USER_ID = os.getenv('TARGET_USER_ID')
BASE_DIR = Path(os.getenv('SCRIPT_BASE_DIR', '/volume1/homes/ken/git/python3/PGSharp')) # 預設路徑

# 檢查必要的環境變數是否存在
if not CHANNEL_ACCESS_TOKEN:
    raise ValueError("環境變數 'CHANNEL_ACCESS_TOKEN' 未設定")
if not TARGET_USER_ID:
    raise ValueError("環境變數 'TARGET_USER_ID' 未設定")

# 使用 pathlib 設定檔案路徑
LOG_FILE: Path = BASE_DIR / 'pgsharp_monitor.log'
VERSION_FILE: Path = BASE_DIR / 'pgsharp_version.txt'

# --- 其他常數 ---
PGSHARP_URL: str = 'https://www.pgsharp.com/'
MESSAGING_API_URL: str = 'https://api.line.me/v2/bot/message/push'
REQUEST_TIMEOUT: int = 15 # 稍微增加超時時間
USER_AGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 PGSharpMonitor/1.0' # 加入自訂識別

# --- 設定日誌 ---
# 使用 RotatingFileHandler，限制單檔大小與備份數量
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1*1024*1024, # 1 MB
    backupCount=3,        # 保留 3 個備份檔
    encoding='utf-8'      # 指定編碼
)
log_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
# 如果希望在控制台也看到輸出 (手動執行時)，可以取消下面兩行的註解
# console_handler = logging.StreamHandler()
# logger.addHandler(console_handler)

# --- 核心功能函式 ---

def get_latest_version(url: str, pattern: str) -> Optional[str]:
    """從指定 URL 獲取符合正則表達式的最新版本號"""
    logger.info(f"嘗試從 {url} 獲取版本資訊...")
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # 檢查 HTTP 錯誤 (4xx or 5xx)
        logger.debug(f"成功獲取網頁內容 (狀態碼: {response.status_code})")

        match = re.search(pattern, response.text)
        if match:
            version = match.group(1).strip()
            logger.info(f"成功解析到版本號: {version}")
            return version
        else:
            logger.warning("在網頁內容中未找到符合條件的版本號模式")
            # 可以考慮記錄部分 response.text 以便除錯
            # logger.debug(f"部分網頁內容: {response.text[:500]}")
            return None

    except RequestException as e:
        logger.error(f"獲取網頁內容時發生網路錯誤: {e}")
        return None
    except Exception as e:
        logger.error(f"解析版本時發生未預期錯誤: {e}")
        return None

def read_stored_version(filepath: Path) -> Optional[str]:
    """從檔案讀取先前儲存的版本號"""
    logger.info(f"嘗試從 {filepath} 讀取已儲存的版本...")
    try:
        if filepath.exists():
            content = filepath.read_text(encoding='utf-8').strip()
            logger.info(f"讀取到已儲存版本: {content}")
            return content
        else:
            logger.info("版本檔案不存在，視為首次執行")
            return None
    except IOError as e:
        logger.error(f"讀取版本檔案時發生 IO 錯誤 ({filepath}): {e}")
        return None
    except Exception as e:
        logger.error(f"讀取版本檔案時發生未預期錯誤 ({filepath}): {e}")
        return None

def write_version(filepath: Path, version: str) -> bool:
    """將新的版本號寫入檔案"""
    logger.info(f"嘗試將版本 {version} 寫入 {filepath}...")
    try:
        # 確保目錄存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(version, encoding='utf-8')
        logger.info(f"成功將版本 {version} 寫入檔案")
        return True
    except IOError as e:
        logger.error(f"寫入版本檔案時發生 IO 錯誤 ({filepath}): {e}")
        return False
    except Exception as e:
        logger.error(f"寫入版本檔案時發生未預期錯誤 ({filepath}): {e}")
        return False

def send_line_message(user_id: str, message: str, token: str) -> bool:
    """使用 LINE Messaging API 發送推送訊息"""
    logger.info(f"嘗試發送 LINE 訊息給 {user_id}...")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload: Dict[str, Any] = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': message}]
    }
    try:
        response = requests.post(MESSAGING_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.info(f"LINE Messaging API 訊息發送成功 (狀態碼: {response.status_code})")
        # logger.debug(f"LINE API 回應: {response.text}") # 可選，用於除錯
        return True
    except RequestException as e:
        logger.error(f"發送 LINE 訊息時發生網路錯誤: {e}")
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"LINE API 錯誤回應 ({e.response.status_code}): {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"發送 LINE 訊息時發生未預期錯誤: {e}")
        return False

# --- 主程式邏輯 ---
def main():
    """主執行流程"""
    logger.info("="*10 + " 開始執行 PGSharp 版本監控 " + "="*10)

    version_pattern = r'Latest Version: (.*?) \(Android Only\)' # 版本匹配規則
    current_version = get_latest_version(PGSHARP_URL, version_pattern)

    if not current_version:
        logger.error("無法獲取當前最新版本，本次執行結束")
        logger.info("="*10 + " 結束執行 " + "="*10)
        return

    stored_version = read_stored_version(VERSION_FILE)

    if stored_version is None:
        # 首次執行或版本檔案遺失
        logger.info("未找到先前版本紀錄，將儲存目前版本。")
        if write_version(VERSION_FILE, current_version):
           logger.info(f"已成功儲存初始版本: {current_version}")
        else:
           logger.error("儲存初始版本失敗")
           # 考慮是否要發送錯誤通知

    elif current_version != stored_version:
        # 版本有更新
        logger.info(f"偵測到版本更新: {stored_version} -> {current_version}")
        message = f"新版本: {current_version}\n偵測時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # 先發送通知，再更新檔案 (或反過來，取決於哪個失敗的後果比較嚴重)
        if send_line_message(TARGET_USER_ID, message, CHANNEL_ACCESS_TOKEN):
            logger.info("LINE 通知發送成功")
            # 通知成功後才更新版本檔案
            if write_version(VERSION_FILE, current_version):
                logger.info(f"版本檔案已更新至: {current_version}")
            else:
                logger.error("更新版本檔案失敗，但 LINE 通知已發送")
                # 這裡可能需要額外處理，例如下次執行時強制重新發送通知
        else:
            logger.error("LINE 通知發送失敗，本次不更新版本檔案，下次將重試")
            # 不更新本地版本檔案，確保下次執行時會再次檢測到差異並嘗試通知

    else:
        # 版本無變化
        logger.info(f"版本無變化 ({current_version})")

    logger.info("="*10 + " 結束執行 " + "="*10)


if __name__ == "__main__":
    main()