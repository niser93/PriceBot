import requests

class TelegramNotifier:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, text, chat_id):
        url = f"{self.base_url}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text})

    def send_price_alert(self, url, price, chat_id):
        self.send_message(f"🔥 Prezzo sceso!\n{price}€\n{url}", chat_id)