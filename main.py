import os
import threading

from AmazonPriceTracker import AmazonPriceTracker
from TelegramBotController import TelegramBotController
from TelegramNotifier import TelegramNotifier
from db import DBHandler

def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 1800))

    db = DBHandler()
    notifier = TelegramNotifier(BOT_TOKEN)
    tracker = AmazonPriceTracker(db_handler=db, notifier=notifier)

    bot = TelegramBotController(token=BOT_TOKEN, tracker=tracker, db=db)
    t = threading.Thread(target=bot.run)
    t.daemon = True
    t.start()

    tracker.monitor(CHECK_INTERVAL)

if __name__=="__main__":
    main()