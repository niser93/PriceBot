import random
import re

import requests
from bs4 import BeautifulSoup

from trackers.BaseTracker import BaseTracker


class AgriEuroPriceTracker(BaseTracker):
    def __init__(self, db_handler, notifier=None):
        super().__init__(db_handler, notifier)
        self.headers_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        ]

    def get_headers(self):
        return {
            "User-Agent": random.choice(self.headers_list),
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"
        }

    def validate_url(self, url):
        """
        Valida URL AgriEuro prodotto
        """
        pattern = r"^https?://(www\.)?agrieuro\.com/.+-p-\d+(_\d+)?\.html$"
        return bool(re.search(pattern, url))

    def normalize_price(self, text):
        """
        Converte prezzo stringa -> float
        "1.299,00 €" -> 1299.00
        """
        if not text:
            return None
        text = text.replace("€", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(text)
        except ValueError:
            return None

    def get_product_data(self, url):
        """
        Restituisce:
        {
            'price': float o None,
            'available': True/False,
            'title': string o None
        }
        """
        try:
            r = requests.get(url, headers=self.get_headers(), timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")
        except:
            return {"price": None, "available": False, "title": None}

        # ---------------- PREZZO ----------------
        price = None

        # selettore principale (quello che hai trovato)
        price_container = soup.find("div", class_="product-panel-price-amount")

        if price_container:
            # spesso il prezzo è dentro span
            text = price_container.get_text(strip=True)
            price = self.normalize_price(text)

        # fallback: cerca qualsiasi elemento con €
        if price is None:
            possible_prices = soup.find_all(string=re.compile(r"\d+[\.,]\d+\s*€"))
            for p in possible_prices:
                price = self.normalize_price(p)
                if price:
                    break

        # ---------------- TITOLO ----------------
        title_tag = soup.find("h1", class_="product-title")
        title = title_tag.get_text(strip=True) if title_tag else None

        # ---------------- DISPONIBILITÀ ----------------
        available = price is not None

        return {
            "price": price,
            "available": available,
            "title": title
        }