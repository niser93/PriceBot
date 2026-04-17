import re
import time

import requests
from bs4 import BeautifulSoup

from trackers.BaseTracker import BaseTracker

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException


class MagicMerchantPriceTracker(BaseTracker):
    def __init__(self, db_handler, notifier=None):
        super().__init__(db_handler, notifier)
        # configura Selenium headless
        self.options = Options()
        self.options.headless = True
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

    def validate_url(self, url):
        return "magicmerchant.it" in url

    def get_product_data(self, url):
        """
        Restituisce un dict con:
        - price: float o None
        - available: bool
        - title: str o None
        """
        try:
            driver = webdriver.Chrome(options=self.options)
            driver.set_page_load_timeout(15)
            driver.get(url)
            # attendi il caricamento del prezzo
            time.sleep(3)  # opzionale: regolare se necessario
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
        except (WebDriverException, TimeoutException):
            return {"price": None, "available": False, "title": None}
        finally:
            try:
                driver.quit()
            except:
                pass

        # Titolo prodotto
        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Prezzo: prova vari selettori
        price = None
        selectors = [
            ".product-price",
            ".price",
            ".current-price",
            "[class*=price]"
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                price = self.normalize_price(el.get_text())
                if price is not None:
                    break

        available = price is not None

        return {
            "price": price,
            "available": available,
            "title": title
        }