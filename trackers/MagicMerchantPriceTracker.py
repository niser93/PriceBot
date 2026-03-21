import requests
from bs4 import BeautifulSoup

from trackers.BaseTracker import BaseTracker


class MagicMerchantPriceTracker(BaseTracker):
    def __init__(self, db_handler, notifier=None):
        super().__init__(db_handler, notifier)

    def validate_url(self, url):
        # accetta URL che contengono magicmerchant.it e /catalogue/
        return "magicmerchant.it/catalogue/" in url

    def normalize_price(self, text):
        """
        Estrae un prezzo da una stringa anche se ci sono parole o spazi.
        Esempio:
        "38,94€" o "42,18€ 64,89€" -> 38.94 o 42.18
        """
        if not text:
            return None
        # prende il primo numero con decimali da 0 a 2 cifre
        m = re.search(r"(\d{1,3}(?:[.,]\d{2})?)", text)
        if not m:
            return None
        price_str = m.group(1).replace(".", "").replace(",", ".")
        try:
            return float(price_str)
        except:
            return None

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

        price = None

        # 🎯 Qui cerchiamo nello specifico dove il sito mette i prezzi:
        # - spesso il prezzo scontato e quello originale sono dentro <p> o <span> senza class cross‑site
        possible_price_tags = soup.find_all(["span", "p", "div"])
        for tag in possible_price_tags:
            text = tag.get_text(strip=True)
            # controlla se contiene il simbolo € e un numero
            if "€" in text and re.search(r"\d", text):
                candidate = self.normalize_price(text)
                # se la regex torna un numero valido
                if candidate is not None:
                    # considera il primo prezzo valido rilevato (scontato se presente)
                    price = candidate
                    break

        # titolo
        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # consideriamo disponibile se abbiamo estratto un prezzo
        available = price is not None

        return {
            "price": price,
            "available": available,
            "title": title
        }