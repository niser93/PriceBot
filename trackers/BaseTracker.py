import re


class BaseTracker:
    def __init__(self, db_handler, notifier=None):
        self.db = db_handler
        self.notifier = notifier

    def validate_url(self, url):
        raise NotImplementedError

    def get_product_data(self, url):
        """
        Deve restituire:
        {
            "price": float | None,
            "available": bool,
            "title": str | None
        }
        """
        raise NotImplementedError

    def normalize_price(self, price_text):
        if not price_text:
            return None
        # trova primo numero con eventuale decimale
        match = re.search(r"(\d+[.,]?\d*)", price_text)
        if not match:
            return None
        price_str = match.group(1).replace(",", ".")
        try:
            return float(price_str)
        except:
            return None