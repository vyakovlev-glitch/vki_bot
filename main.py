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

class FakeServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive and tracking PDF!")

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), FakeServer)
    server.serve_forever()

def get_page_state():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Збираємо звичайний текст сторінки
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            page_text = " ".join(main_content.get_text().split()) if main_content else ""
            
            # Шукаємо всі посилання на PDF файли на сторінці
            pdf_links = []
            for a in soup.find_all('a', href=True):
                if '.pdf' in a['href'].lower():
                    pdf_links.append(a['href'])
            
            # Шукаємо вбудовані iframe (іноді PDF вставляють через них)
            iframes = [iframe['src'] for iframe in soup.find_all('iframe', src=True)]
            
            # Об'єднуємо все в один рядок для відстеження будь-яких змін
            state_snapshot = f"TEXT:{page_text} | PDFs:{','.join(pdf_links)} | IFRAMES:{','.join(iframes)}"
            return state_snapshot
    except Exception as e:
        print(f"Помилка парсингу: {e}")
    return None

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(telegram_url, json=payload)
    except: pass

def main():
    threading.Thread(target=run_fake_server, daemon=True).start()
    
    print("Бот запущений із трекером PDF...")
    send_telegram_message("🤖 Оновлений бот запущений! Тепер він відстежує текст, PDF-посилання та фрейми заміноок.")
    
    last_state = get_page_state()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        current_state = get_page_state()
        
        if current_state is None:
            continue
            
        if current_state != last_state:
            msg = f"🔔 **На сайті ВКІ знайдено оновлення (змінився текст або PDF з замінами)!**\n\n🔗 Перевірити: {URL}"
            send_telegram_message(msg)
            last_state = current_state
            print("Виявлено зміни в структурі або файлах сторінки!")

if __name__ == "__main__":
    main()
