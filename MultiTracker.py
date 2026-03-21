import time

from trackers.AmazonPriceTracker import AmazonPriceTracker
from trackers.DungeondicePriceTracker import DungeondicePriceTracker
from trackers.FantasiaStoreTracker import FantasiastorePriceTracker
from trackers.MagicMerchantPriceTracker import MagicMerchantPriceTracker


class MultiTracker:
    def __init__(self, db_handler, notifier=None):
        self.db = db_handler
        self.notifier = notifier
        self.trackers = []

        # registra tracker qui
        self.register(AmazonPriceTracker(db_handler, notifier))
        self.register(DungeondicePriceTracker(db_handler, notifier))
        self.register(MagicMerchantPriceTracker(db_handler, notifier))
        self.register(FantasiastorePriceTracker(db_handler, notifier))

    def register(self, tracker):
        self.trackers.append(tracker)

    def get_tracker_for_url(self, url):
        for tracker in self.trackers:
            try:
                if tracker.validate_url(url):
                    return tracker
            except:
                continue
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

                data = tracker.get_product_data(url)

                price = data.get("price")
                available = data.get("available")

                if price is None or not available:
                    continue

                self.db.add_price(url, price)

                send_alert = False

                if last_notified is None:
                    if price <= target:
                        send_alert = True
                else:
                    if price < last_notified or price <= target:
                        send_alert = True

                if send_alert and self.notifier:
                    self.notifier.send_price_alert(url, price, chat_id)
                    self.db.update_last_notified(chat_id, url, price)

            time.sleep(interval)