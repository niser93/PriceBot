import requests
from bs4 import BeautifulSoup

class DungeondicePriceTracker:
    def __init__(self, db_handler, notifier=None):
        self.db = db_handler
        self.notifier = notifier

    def validate_url(self, url: str) -> bool:
        return "dungeondice.it/" in url

    def get_price(self, url: str) -> float | None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "it-IT,it;q=0.9"
        }
        try:
            r = requests.get(url, headers=headers, timeout=10)
            html = r.text
        except Exception:
            return None

        soup = BeautifulSoup(html, "html.parser")
        price_tag = soup.select_one(".product-price")  # prende solo il prezzo finale
        if not price_tag:
            return None

        price_text = price_tag.get_text(strip=True).replace("€", "").replace(".", "").replace(",", ".")
        try:
            return float(price_text)
        except ValueError:
            return None