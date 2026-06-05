import os
import requests
import redis
from bs4 import BeautifulSoup

# === НАЛАШТУВАННЯ ===
URL = "https://vki.vin.ua/%d0%b7%d0%b0%d0%bc%d1%96%d0%bd%d0%b8-%d0%b7%d0%b0%d0%bd%d1%8f%d1%82%d1%8c/"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
REDIS_URL = os.environ.get("REDIS_URL")
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
    current_content = get_page_content()
    if current_content is None:
        return

    # Підключаємось до бази даних Redis на Render
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    last_content = r.get("last_vki_content")

    if last_content is None:
        # Перший запуск
        r.set("last_vki_content", current_content)
        send_telegram_message("🤖 Бот успішно запущений на Render та підключений до бази даних!")
        return

    # Якщо вміст змінився
    if current_content != last_content:
        msg = f"🔔 **На сайті ВКІ оновлено заміни занять!**\n\n🔗 Перевірити: {URL}"
        send_telegram_message(msg)
        r.set("last_vki_content", current_content)

if __name__ == "__main__":
    main()