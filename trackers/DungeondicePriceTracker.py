import requests
from bs4 import BeautifulSoup

from BaseTracker import BaseTracker


# ---------------- DungeonDice Tracker ----------------
class DungeondicePriceTracker(BaseTracker):
    def __init__(self, db_handler, notifier=None):
        super().__init__(db_handler, notifier)

    def validate_url(self, url):
        return "dungeondice.it/" in url

    def get_price(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "it-IT,it;q=0.9"
        }

        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
        except:
            return None

        price_tag = soup.select_one(".product-price")
        if not price_tag:
            return None

        return self.normalize_price(price_tag.get_text())