import random

import requests
from bs4 import BeautifulSoup

from BaseTracker import BaseTracker


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

    def get_price(self, url):
        try:
            r = requests.get(url, headers=self.get_headers(), timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")

            selectors = [
                ("span", {"id": "priceblock_ourprice"}),
                ("span", {"id": "priceblock_dealprice"}),
                ("span", {"class": "a-offscreen"})
            ]

            for tag, attrs in selectors:
                el = soup.find(tag, attrs=attrs)
                if el:
                    return self.normalize_price(el.get_text())

        except:
            return None