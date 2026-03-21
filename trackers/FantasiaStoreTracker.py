import requests
from bs4 import BeautifulSoup

from trackers.BaseTracker import BaseTracker


class FantasiastorePriceTracker(BaseTracker):
    def validate_url(self, url):
        return "fantasiastore.it" in url

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

        # prezzo
        price = None
        for sel in [".current-price", ".price", "[class*=price]"]:
            el = soup.select_one(sel)
            if el:
                price = self.normalize_price(el.get_text())
                if price:
                    break

        # disponibilità
        text = soup.get_text().lower()
        available = not any(k in text for k in [
            "non disponibile",
            "esaurito",
            "out of stock"
        ])

        # titolo
        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        return {
            "price": price,
            "available": available,
            "title": title
        }