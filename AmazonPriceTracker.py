import requests
from bs4 import BeautifulSoup
import random
import re
import time

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
        """
        Restituisce True se URL è valido amazon.it
        Supporta link completi e link brevi risolti
        """
        url_no_query = self.resolve_amzn_short_url(url)
        if not url_no_query:
            return False

        # regex per URL amazon.it valido, anche senza titolo prima di /dp/
        pattern = r"^https?://(www\.)?amazon\.it/(?:.*?/)?dp/[A-Z0-9]{10}$"
        return bool(re.search(pattern, url_no_query))

    def get_asin(self, url):
        """
        Estrae ASIN dall'URL amazon.it (senza query string)
        """
        url = self.resolve_amzn_short_url(url)
        if not url:
            return None
        # ora regex funziona correttamente
        m = re.search(r"/dp/([A-Z0-9]{10})", url)
        return m.group(1) if m else None

    def resolve_amzn_short_url(self, url):
        """
        Risolve link brevi amzn.eu/d/... in URL amazon.it completo
        Rimuove query string
        """
        # se non è link breve, restituisco originale
        if "amzn.eu/d/" in url:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"
            }
            try:
                r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                url = r.url
            except requests.exceptions.RequestException:
                return None

        # rimuovo query string
        url_no_query = url.split("?")[0]
        return url_no_query

    def monitor(self, interval=1800):
        while True:
            c = self.db.conn.cursor()
            c.execute("SELECT chat_id, url, target_price, last_notified_price FROM products")
            products = c.fetchall()
            for chat_id, url, target, last_notified in products:
                price = self.get_price(url)
                if price is None:
                    continue
                self.db.add_price(url, price)  # aggiunge sempre allo storico

                # notifiche solo se prezzo < last_notified OR prezzo <= target
                send_alert = False
                if last_notified is None:
                    send_alert = False  # primo prezzo non genera notifica
                elif price < last_notified or price <= target:
                    send_alert = True

                if send_alert and self.notifier:
                    self.notifier.send_price_alert(url, price, chat_id)
                    self.db.update_last_notified(chat_id, url, price)

            time.sleep(interval)