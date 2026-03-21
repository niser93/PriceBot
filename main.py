import os
import threading
import time

from MultiTracker import MultiTracker
from TelegramBotController import TelegramBotController
from TelegramNotifier import TelegramNotifier
from db import DBHandler # nuova classe aggregatrice dei tracker

def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 1800))

    db = DBHandler()
    db.drop_database()
    notifier = TelegramNotifier(BOT_TOKEN)
    multi_tracker = MultiTracker(db_handler=db, notifier=notifier)

    # bot Telegram
    bot = TelegramBotController(token=BOT_TOKEN, tracker=multi_tracker, db=db, notifier=notifier)
    t = threading.Thread(target=bot.run)
    t.daemon = True
    t.start()

    # monitor prezzi
    multi_tracker.monitor(CHECK_INTERVAL)

if __name__ == "__main__":
    main()