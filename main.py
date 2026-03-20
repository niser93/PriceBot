import argparse
import threading

from AmazonPriceTracker import AmazonPriceTracker
from TelegramBotController import TelegramBotController
from TelegramNotifier import TelegramNotifier
from db import DBHandler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    db = DBHandler()
    notifier = TelegramNotifier(args.token)
    tracker = AmazonPriceTracker(db_handler=db, notifier=notifier)

    bot = TelegramBotController(token=args.token, tracker=tracker, db=db)
    t = threading.Thread(target=bot.run)
    t.daemon = True
    t.start()

    tracker.monitor(300)

if __name__=="__main__":
    main()