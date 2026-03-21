import requests

class TelegramNotifier:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, text, chat_id, parse_mode=None):
        """
        Invia un messaggio a Telegram.
        parse_mode può essere "HTML", "MarkdownV2", o None
        """
        data = {
            "chat_id": chat_id,
            "text": text
        }
        if parse_mode:
            data["parse_mode"] = parse_mode

        requests.post(f"{self.base_url}/sendMessage", data=data)

    def send_price_alert(self, url, price, chat_id, title=None):
        msg = f"🔥 Prezzo sceso!\n{price}€\n{url}"
        if title:
            msg = f"🔥 {title}\n{price}€\n{url}"
        self.send_message(msg, chat_id)