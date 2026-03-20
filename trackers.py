import requests
from bs4 import BeautifulSoup
import random
import re
import time

# ---------------- Amazon Tracker ----------------
class AmazonPriceTracker:
    def __init__(self, db_handler, notifier=None):
        self.db = db_handler
        self.notifier = notifier
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
                    text = el.get_text().replace("€","").replace(".", "").replace(",", ".").strip()
                    try:
                        return float(text)
                    except:
                        continue
        except:
            return None

    def validate_url(self, url):
        url_no_query = self.resolve_amzn_short_url(url)
        if not url_no_query:
            return False
        pattern = r"^https?://(www\.)?amazon\.it/(?:.*?/)?dp/[A-Z0-9]{10}$"
        return bool(re.search(pattern, url_no_query))

    def resolve_amzn_short_url(self, url):
        if "amzn.eu/d/" in url:
            headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"}
            try:
                r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                url = r.url
            except requests.exceptions.RequestException:
                return None
        return url.split("?")[0]

# ---------------- DungeonDice Tracker ----------------
class DungeondicePriceTracker:
    def __init__(self, db_handler, notifier=None):
        self.db = db_handler
        self.notifier = notifier

    def validate_url(self, url):
        return "dungeondice.it/" in url

    def get_price(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "it-IT,it;q=0.9"
        }
        try:
            r = requests.get(url, headers=headers, timeout=10)
            html = r.text
        except:
            return None

        soup = BeautifulSoup(html, "html.parser")
        price_tag = soup.select_one(".product-price")  # prezzo finale visibile
        if not price_tag:
            return None
        price_text = price_tag.get_text(strip=True).replace("€", "").replace(".", "").replace(",", ".")
        try:
            return float(price_text)
        except ValueError:
            return None

# ---------------- MultiTracker ----------------
class MultiTracker:
    """
    Gestisce più tracker e il monitor dei prezzi
    """
    def __init__(self, db_handler, notifier=None):
        self.db = db_handler
        self.notifier = notifier
        self.amazon = AmazonPriceTracker(db_handler, notifier)
        self.dungeondice = DungeondicePriceTracker(db_handler, notifier)

    def get_tracker_for_url(self, url):
        if self.amazon.validate_url(url):
            return self.amazon
        elif self.dungeondice.validate_url(url):
            return self.dungeondice
        else:
            return None

    def validate_url(self, url):
        return self.get_tracker_for_url(url) is not None

    def get_price(self, url):
        tracker = self.get_tracker_for_url(url)
        if tracker:
            return tracker.get_price(url)
        return None

    def monitor(self, interval=1800):
        while True:
            c = self.db.conn.cursor()
            c.execute("SELECT chat_id, url, target_price, last_notified_price FROM products")
            products = c.fetchall()
            for chat_id, url, target, last_notified in products:
                tracker = self.get_tracker_for_url(url)
                if not tracker:
                    continue
                price = tracker.get_price(url)
                if price is None:
                    continue
                self.db.add_price(url, price)  # aggiunge allo storico

                send_alert = False
                if last_notified is not None and (price < last_notified or price <= target):
                    send_alert = True

                if send_alert and self.notifier:
                    self.notifier.send_price_alert(url, price, chat_id)
                    self.db.update_last_notified(chat_id, url, price)

            time.sleep(interval)