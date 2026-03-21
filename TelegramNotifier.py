import requests

class TelegramNotifier:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, text, chat_id):
        url = f"{self.base_url}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text})

    def send_price_alert(self, url, price, chat_id, title=None):
        msg = f"🔥 Prezzo sceso!\n{price}€\n{url}"
        if title:
            msg = f"🔥 {title}\n{price}€\n{url}"
        self.send_message(msg, chat_id)