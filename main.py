import os
import time
import requests
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
        self.wfile.write(b"Bot is scanning PDF size and content successfully!")

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), FakeServer)
    server.serve_forever()

def get_pdf_details():
    """Знаходить PDF або iframe на сторінці та повертає його унікальні характеристики (url та розмір)"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(URL_TO_SCAN, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_url = None

        # 1. Шукаємо пряме посилання на .pdf
        for a in soup.find_all('a', href=True):
            if '.pdf' in a['href'].lower():
                pdf_url = urljoin(URL_TO_SCAN, a['href'])
                break

        # 2. Якщо прямого посилання немає, шукаємо вбудований iframe (Google Docs Viewer тощо)
        if not pdf_url:
            for iframe in soup.find_all('iframe', src=True):
                if 'url=' in iframe['src'] or '.pdf' in iframe['src'].lower():
                    pdf_url = iframe['src']
                    break
                elif 'drive.google.com' in iframe['src']:
                    pdf_url = iframe['src']
                    break

        # Якщо взагалі нічого не знайшли, беремо хеш всього текстового контенту сторінки
        if not pdf_url:
            text_content = soup.get_text()
            return "text_only", len(text_content)

        # Якщо знайшли посилання на PDF, намагаємось дізнатися його вагу без скачування (через HEAD запит)
        try:
            file_meta = requests.head(pdf_url, headers=headers, timeout=10)
            file_size = file_meta.headers.get('Content-Length', 'unknown')
            # Якщо сервер не віддав розмір, використовуємо довжину самого URL як маркер змін
            if file_size == 'unknown':
                file_size = len(pdf_url)
            return pdf_url, file_size
        except:
            return pdf_url, len(pdf_url)

    except Exception as e:
        print(f"Помилка сканування: {e}")
        return None, None

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(telegram_url, json=payload)
    except: pass

def main():
    threading.Thread(target=run_fake_server, daemon=True).start()
    
    print("Бот-детектор ваги та контенту запущений...")
    send_telegram_message("🤖 **Бот успішно переналаштований на детектор ваги та вмісту PDF!**\nТепер я контролюю розмір файлу та посилання. Навіть якщо адмін просто перезапише документ — я це помічу.")
    
    last_url, last_size = get_pdf_details()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        current_url, current_size = get_pdf_details()
        
        if current_url is None:
            continue
            
        # Якщо змінилося посилання АБО вага файлу в байтах
        if current_url != last_url or current_size != last_size:
            msg = f"⚠️ **Виявлено оновлення файлу заміни занять!**\n\n🔎 Що змінилося: "
            if current_size != last_size:
                msg += f"вага або вміст документа (стара вага/ідентифікатор: `{last_size}`, нова: `{current_size}`).\n"
            else:
                msg += "завантажено абсолютно новий документ з іншою назвою.\n"
                
            msg += f"\n🔗 Перевірити розклад: {URL_TO_SCAN}"
            
            send_telegram_message(msg)
            
            last_url = current_url
            last_size = current_size

if __name__ == "__main__":
    main()
