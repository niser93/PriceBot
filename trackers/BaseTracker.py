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
        try:
            return float(
                price_text
                .replace("€", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
        except:
            return None