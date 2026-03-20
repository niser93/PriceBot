import sqlite3
import time

DB_FILE = "amazon_tracker.db"

class DBHandler:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id TEXT PRIMARY KEY
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                chat_id TEXT,
                url TEXT,
                target_price REAL,
                last_notified_price REAL DEFAULT NULL,
                PRIMARY KEY(chat_id, url)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                url TEXT,
                price REAL,
                timestamp INTEGER
            )
        """)
        self.conn.commit()

    # ---------------- utenti ----------------
    def add_user(self, chat_id):
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        self.conn.commit()

    # ---------------- prodotti ----------------
    def add_product(self, chat_id, url, target_price):
        self.add_user(chat_id)
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO products (chat_id, url, target_price) VALUES (?, ?, ?)",
                  (chat_id, url, target_price))
        self.conn.commit()

    def remove_product(self, chat_id, url):
        c = self.conn.cursor()
        c.execute("DELETE FROM products WHERE chat_id=? AND url=?", (chat_id, url))
        self.conn.commit()

    def list_products(self, chat_id):
        c = self.conn.cursor()
        c.execute("SELECT url, target_price FROM products WHERE chat_id=?", (chat_id,))
        return c.fetchall()

    def users_for_product(self, url):
        c = self.conn.cursor()
        c.execute("SELECT chat_id FROM products WHERE url=?", (url,))
        return [row[0] for row in c.fetchall()]

    def update_last_notified(self, chat_id, url, price):
        c = self.conn.cursor()
        c.execute("UPDATE products SET last_notified_price=? WHERE chat_id=? AND url=?", (price, chat_id, url))
        self.conn.commit()

    # ---------------- storico prezzi ----------------
    def add_price(self, url, price):
        ts = int(time.time())
        c = self.conn.cursor()
        c.execute("INSERT INTO price_history (url, price, timestamp) VALUES (?, ?, ?)", (url, price, ts))
        self.conn.commit()

    def get_history(self, url, limit=100):
        c = self.conn.cursor()
        c.execute("SELECT price, timestamp FROM price_history WHERE url=? ORDER BY timestamp DESC LIMIT ?", (url, limit))
        return c.fetchall()