import requests
from bs4 import BeautifulSoup

from trackers.BaseTracker import BaseTracker


class MagicMerchantPriceTracker(BaseTracker):
    def __init__(self, db_handler, notifier=None):
        super().__init__(db_handler, notifier)

    def validate_url(self, url):
        return "magicmerchant.it" in url

    def get_product_data(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "it-IT,it;q=0.9"
        }

        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
        except:
            return {"price": None, "available": False, "title": None}

        # selettori prezzi (fallback)
        price = None
        selectors = [
            ".product-price",
            ".price",
            ".current-price",
            "[class*=price]"
        ]

        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                price = self.normalize_price(el.get_text())
                if price:
                    break

        # titolo prodotto
        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # disponibilità: se c'è prezzo lo consideriamo disponibile
        available = price is not None

        return {
            "price": price,
            "available": available,
            "title": title
        }