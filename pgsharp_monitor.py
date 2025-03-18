# 程式碼來自 Grok 2025/03/05
# 此程式只在 synology DS215J 執行
# 在 DSM 套件中心安裝 python 3.9
# root 以 ssh key 連線手動安裝 pip3
# /bin/pip3 install requests
# 以 ssh 連線測試執行程式，沒問題後再以 DSM 內的 任務排程表 執行 

import requests
import re
import os
from datetime import datetime
import logging
from requests.exceptions import RequestException

# Messaging API 設定 (請將 YOUR_CHANNEL_ACCESS_TOKEN 替換為您的 LINE Messaging API Channel Access Token)
CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'

# 設定接收通知的 LINE 使用者 ID (請替換為您的 LINE User ID)
# 目前設定為 Provider：PGSharp_Notify 下的 Channel：PGSharp更版通知 Messaging API 創建的 LINE Official Account 的 UserID ）
TARGET_USER_ID = 'LINE User ID'

MESSAGING_API_URL = 'https://api.line.me/v2/bot/message/push'

# 設定日誌
log_file = '/volume1/././././PGSharp/pgsharp_monitor_log.txt'

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 儲存版本的文件路徑
VERSION_FILE = '/volume1/././././PGSharp/pgsharp_version.txt'

def get_latest_version():
    """從網頁獲取最新版本號"""
    try:
        url = 'https://www.pgsharp.com/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        pattern = r'Latest Version: (.*?) \(Android Only\)'
        match = re.search(pattern, response.text)
        
        if match:
            version = match.group(1).strip()
            #logging.info(f"獲取: {version}")
            return version
        else:
            logging.error("無法找到版本號模式")
            return None
            
    except RequestException as e:
        logging.error(f"獲取網頁內容失敗: {str(e)}")
        return None

def read_stored_version():
    """讀取之前儲存的版本號"""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                return f.read().strip()
        return None
    except Exception as e:
        logging.error(f"讀取版本文件失敗: {str(e)}")
        return None

def write_version(version):
    """寫入新的版本號到文件"""
    try:
        with open(VERSION_FILE, 'w') as f:
            f.write(version)
        logging.info(f"已更新版本文件: {version}")
    except Exception as e:
        logging.error(f"寫入版本文件失敗: {str(e)}")

def send_line_message(user_id, message):
    """使用 Messaging API 發送 LINE 訊息"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
        payload = {
            'to': user_id,
            'messages': [{
                'type': 'text',
                'text': message
            }]
        }
        response = requests.post(MESSAGING_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logging.info("Messaging API 訊息發送成功")
    except RequestException as e:
        logging.error(f"Messaging API 訊息發送失敗: {str(e)}")

def main():
    """主程式"""
    #logging.info("開始")
    
    # 獲取當前最新版本
    current_version = get_latest_version()
    if not current_version:
        logging.error("無法獲取最新版本，程式結束")
        return
    
    # 讀取之前儲存的版本
    stored_version = read_stored_version()
    
    # 比對版本
    if stored_version is None:
        # 第一次執行，儲存版本但不發送通知
        write_version(current_version)
        logging.info("首次執行，已儲存初始版本")
    elif current_version != stored_version:
        # 版本有變更，更新文件並發送通知
        message = f"版本更新\n舊版本: {stored_version}\n新版本: {current_version}\n時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        write_version(current_version)
        send_line_message(TARGET_USER_ID, message)
        logging.info(f"版本更新: {stored_version} -> {current_version}")
    else:
        logging.info("無更新")
    
    #logging.info("結束")

if __name__ == "__main__":
    main()
