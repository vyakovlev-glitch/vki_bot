import os
import time
import requests
import hashlib
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from http.server import BaseHTTPRequestHandler, HTTPServer

# === НАЛАШТУВАННЯ ===
URL_TO_SCAN = "https://vki.vin.ua/%d0%b7%d0%b0%d0%bc%d1%96%d0%bd%d0%b8-%d0%b7%d0%b0%d0%bd%d1%8f%d1%82%d1%8c/"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 900  # 15 хвилин
# ====================

class FakeServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is analyzing PDF digital fingerprints successfully!")

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), FakeServer)
    server.serve_forever()

def get_page_or_pdf_fingerprint():
    """Знаходить файл або контент та створює його унікальний цифровий відбиток (хеш)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Завантажуємо сторінку замінок
        response = requests.get(URL_TO_SCAN, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Помилка доступу до сайту: статус {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_url = None

        # 1. Шукаємо пряме посилання на PDF
        for a in soup.find_all('a', href=True):
            if '.pdf' in a['href'].lower():
                pdf_url = urljoin(URL_TO_SCAN, a['href'])
                break

        # 2. Шукаємо вбудований iframe
        if not pdf_url:
            for iframe in soup.find_all('iframe', src=True):
                if 'url=' in iframe['src'] or '.pdf' in iframe['src'].lower() or 'drive.google.com' in iframe['src']:
                    pdf_url = iframe['src']
                    break

        # Якщо знайшли посилання на документ
        if pdf_url:
            print(f"Знайдено посилання на документ: {pdf_url}")
            # Робимо повноцінний GET-запит до файлу, щоб обійти блокування хостингу
            file_res = requests.get(pdf_url, headers=headers, timeout=15)
            if file_res.status_code == 200:
                # Створюємо унікальний MD5-хеш (відбиток) з вмісту самого файлу
                file_hash = hashlib.md5(file_res.content).hexdigest()
                return f"file_{file_hash}"
            else:
                # Якщо файл не скачався, використовуємо як маркер саме посилання
                return f"url_{pdf_url}"
        
        # Якщо документів не виявлено взагалі, аналізуємо чистий текст сторінки
        text_hash = hashlib.md5(soup.get_text().encode('utf-8')).hexdigest()
        return f"text_{text_hash}"

    except Exception as e:
        print(f"Помилка під час сканування: {e}")
        return None

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(telegram_url, json=payload)
    except: pass

def main():
    threading.Thread(target=run_fake_server, daemon=True).start()
    
    print("Бот-сканер цифрових відбитків запущений...")
    send_telegram_message("🤖 **Бот успішно оновлений!**\nТепер я сканую унікальні цифрові відбитки документів (MD5-хеш). Будь-яка зміна всередині файлу буде зафіксована!")
    
    last_fingerprint = get_page_or_pdf_fingerprint()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        current_fingerprint = get_page_or_pdf_fingerprint()
        
        if current_fingerprint is None:
            continue
            
        # Якщо цифровий відбиток контенту чи файлу змінився
        if current_fingerprint != last_fingerprint:
            msg = f"⚠️ **Увага! На сайті ВКІ оновилися заміни занять!**\n\n🔍 Система зафіксувала новий вміст або інший документ.\n🔗 Посилання на сторінку: {URL_TO_SCAN}"
            send_telegram_message(msg)
            last_fingerprint = current_fingerprint
            print(f"Контент змінено! Новий відбиток: {current_fingerprint}")

if __name__ == "__main__":
    main()
