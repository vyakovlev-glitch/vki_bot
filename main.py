import os
import time
import requests
from bs4 import BeautifulSoup

# === НАЛАШТУВАННЯ ===
URL = "https://vki.vin.ua/%d0%b7%d0%b0%d0%bc%d1%96%d0%bd%d0%b8-%d0%b7%d0%b0%d0%bd%d1%8f%d1%82%d1%8c/"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 1800  # 1800 секунд = 30 хвилин
# ====================

def get_page_content():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            if main_content:
                return " ".join(main_content.get_text().split())
        else:
            print(f"Помилка доступу до сайту: {response.status_code}")
    except Exception as e:
        print(f"Помилка при запиті: {e}")
    return None

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(telegram_url, json=payload)
    except Exception as e:
        print(f"Не вдалося надіслати повідомлення: {e}")

def main():
    print("Бот запущений на Render Web Service...")
    send_telegram_message("🤖 Бот успішно запущений у хмарі та починає цілодобовий моніторинг!")
    
    # Отримуємо початковий стан сторінки
    last_content = get_page_content()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        current_content = get_page_content()
        if current_content is None:
            continue
            
        # Якщо вміст змінився
        if current_content != last_content:
            msg = f"🔔 **На сайті ВКІ оновлено заміни занять!**\n\n🔗 Перевірити: {URL}"
            send_telegram_message(msg)
            last_content = current_content
            print("Виявлено зміни, повідомлення надіслано!")

if __name__ == "__main__":
    main()
