class BaseTracker:
    def __init__(self, db_handler, notifier=None):
        self.db = db_handler
        self.notifier = notifier

    def validate_url(self, url):
        """
        Deve restituire True se il tracker supporta l'URL
        """
        raise NotImplementedError

    def get_price(self, url):
        """
        Deve restituire il prezzo come float oppure None
        """
        raise NotImplementedError

    # opzionale ma utile
    def normalize_price(self, price_text):
        """
        Utility comune per convertire stringhe prezzo in float
        """
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

    def get_product_info(self, url):
        return {
            "price": self.get_price(url),
            "available": True,
            "title": None
        }