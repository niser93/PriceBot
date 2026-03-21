import random
import re

import requests
from bs4 import BeautifulSoup

from trackers.BaseTracker import BaseTracker


# ---------------- Amazon Tracker ----------------
class AmazonPriceTracker(BaseTracker):
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

    def resolve_amzn_short_url(self, url):
        """
        Risolve i link corti amzn.eu/d/... in link canonici Amazon.it
        """
        if "amzn.eu/d/" in url:
            headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"}
            try:
                r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                url = r.url
            except requests.exceptions.RequestException:
                return None
        # rimuove query string e frammenti
        url = url.split("?")[0].split("#")[0]
        return url

    def validate_url(self, url):
        url_no_query = self.resolve_amzn_short_url(url)
        if not url_no_query:
            return False
        pattern = r"^https?://(www\.)?amazon\.it/(?:.*?/)?dp/[A-Z0-9]{10}$"
        return bool(re.search(pattern, url_no_query))

    def normalize_price(self, text):
        """
        Normalizza un prezzo da stringa a float.
        Esempi:
        "69,99 €" -> 69.99
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
        Restituisce un dict con:
        {
            'price': float o None,
            'available': True/False,
            'title': string o None
        }
        """
        url = self.resolve_amzn_short_url(url)
        if not url:
            return {"price": None, "available": False, "title": None}

        try:
            r = requests.get(url, headers=self.get_headers(), timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")
        except:
            return {"price": None, "available": False, "title": None}

        price = None
        selectors = [
            ("span", {"id": "priceblock_ourprice"}),
            ("span", {"id": "priceblock_dealprice"}),
            ("span", {"class": "a-offscreen"})
        ]
        for tag, attrs in selectors:
            el = soup.find(tag, attrs=attrs)
            if el:
                price = self.normalize_price(el.get_text())
                if price is not None:
                    break

        title_tag = soup.find(id="productTitle")
        title = title_tag.get_text(strip=True) if title_tag else None

        available = price is not None

        return {
            "price": price,
            "available": available,
            "title": title
        }