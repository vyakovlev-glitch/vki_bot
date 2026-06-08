import os
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# === НАЛАШТУВАННЯ ===
# Використовуємо офіційне WordPress API сайту для сторінки 662
URL_API = "https://vki.vin.ua/wp-json/wp/v2/pages/662"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 900  # Перевіряємо кожні 15 хвилин (через API це безпечно і швидко)
# ====================

# Фейковий сервер для обходу обмежень Render Web Service
class FakeServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is tracking WordPress page 662 successfully!")

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), FakeServer)
    server.serve_forever()

def get_page_modification_date():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        # Запитуємо дані сторінки в JSON форматі
        response = requests.get(URL_API, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Беремо точну дату та час останньої зміни (включаючи правки в Elementor)
            modified_date = data.get("modified")
            return modified_date
        else:
            print(f"API Error: Status {response.status_code}")
    except Exception as e:
        print(f"Помилка запиту до API: {e}")
    return None

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(telegram_url, json=payload)
    except: pass

def main():
    threading.Thread(target=run_fake_server, daemon=True).start()
    
    print("Бот-монітор API запущений...")
    send_telegram_message("🤖 **Бот успішно підключився до WordPress API!**\nТепер я миттєво відстежую будь-які збереження сторінки 'Заміни занять' (ID: 662) в адмінці.")
    
    last_modified = get_page_modification_date()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        current_modified = get_page_modification_date()
        
        if current_modified is None:
            continue
            
        # Якщо дата зміни в базі даних відрізняється від попередньої
        if current_modified != last_modified:
            msg = f"⚠️ **Увага! На сайті ВКІ щойно оновили сторінку заміни занять!**\n\n📅 Дата редагування в системі: `{current_modified}`\n🔗 Посилання: https://vki.vin.ua/%d0%b7%d0%b0%d0%bc%d1%96%d0%bd%d0%b8-%d0%b7%d0%b0%d0%bd%d1%8f%d1%82%d1%8c/"
            send_telegram_message(msg)
            last_modified = current_modified
            print(f"Виявлено збереження сторінки: {current_modified}")

if __name__ == "__main__":
    main()
