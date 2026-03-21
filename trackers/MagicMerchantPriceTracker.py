import requests
from bs4 import BeautifulSoup

from .BaseTracker import BaseTracker


class MagicMerchantPriceTracker(BaseTracker):
    def __init__(self, db_handler, notifier=None):
        super().__init__(db_handler, notifier)

    def validate_url(self, url):
        return "magicmerchant.it" in url

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

        # vari selettori possibili (fallback)
        selectors = [
            ".price .current",
            ".special-price",
            ".product-price",
        ]

        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                price = self.normalize_price(el.get_text())
                if price:
                    return price

        return None