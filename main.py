import os
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from bs4 import BeautifulSoup

# === НАЛАШТУВАННЯ ===
URL = "https://vki.vin.ua/%d0%b7%d0%b0%d0%bc%d1%96%d0%bd%d0%b8-%d0%b7%d0%b0%d0%bd%d1%8f%d1%82%d1%8c/"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 1800  # 30 хвилин
# ====================

# --- ХИТРИЙ ФІКС ДЛЯ RENDER WEB SERVICE ---
# Створюємо фейковий веб-сервер, щоб Render не лаявся на порти
class FakeServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), FakeServer)
    server.serve_forever()
# ------------------------------------------

def get_page_content():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            if main_content:
                return " ".join(main_content.get_text().split())
    except Exception as e:
        print(f"Помилка парсингу: {e}")
    return None

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(telegram_url, json=payload)
    except: pass

def main():
    # Запускаємо фейковий сервер в окремому потоці
    threading.Thread(target=run_fake_server, daemon=True).start()
    
    print("Бот запущений...")
    send_telegram_message("🤖 Бот успішно запущений БЕЗКОШТОВНО на Render Web Service!")
    
    last_content = get_page_content()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        current_content = get_page_content()
        if current_content and current_content != last_content:
            msg = f"🔔 **На сайті ВКІ оновлено заміни занять!**\n\n🔗 Перевірити: {URL}"
            send_telegram_message(msg)
            last_content = current_content

if __name__ == "__main__":
    main()
