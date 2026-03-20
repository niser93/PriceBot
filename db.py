import os
import psycopg2
import time

# variabili d'ambiente fornite da Railway
DB_HOST = os.environ.get("PGHOST")
DB_PORT = os.environ.get("PGPORT", 5432)
DB_USER = os.environ.get("PGUSER")
DB_PASSWORD = os.environ.get("PGPASSWORD")
DB_NAME = os.environ.get("PGDATABASE")

class DBHandler:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        self.conn.autocommit = True
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # utenti
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id TEXT PRIMARY KEY
            )
        """)
        # prodotti
        c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                chat_id TEXT,
                url TEXT,
                target_price REAL,
                last_notified_price REAL DEFAULT NULL,
                PRIMARY KEY(chat_id, url)
            )
        """)
        # storico prezzi
        c.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                url TEXT,
                price REAL,
                timestamp BIGINT
            )
        """)

    # ---------------- utenti ----------------
    def add_user(self, chat_id):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO users (chat_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (chat_id,)
        )

    # ---------------- prodotti ----------------
    def add_product(self, chat_id, url, target_price):
        self.add_user(chat_id)
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO products (chat_id, url, target_price)
            VALUES (%s,%s,%s)
            ON CONFLICT (chat_id, url) DO UPDATE SET target_price = EXCLUDED.target_price
        """, (chat_id, url, target_price))

    def remove_product(self, chat_id, url):
        c = self.conn.cursor()
        c.execute("DELETE FROM products WHERE chat_id=%s AND url=%s", (chat_id, url))

    def list_products(self, chat_id):
        c = self.conn.cursor()
        c.execute("SELECT url, target_price FROM products WHERE chat_id=%s", (chat_id,))
        return c.fetchall()

    def users_for_product(self, url):
        c = self.conn.cursor()
        c.execute("SELECT chat_id FROM products WHERE url=%s", (url,))
        return [row[0] for row in c.fetchall()]

    def update_last_notified(self, chat_id, url, price):
        c = self.conn.cursor()
        c.execute("""
            UPDATE products
            SET last_notified_price=%s
            WHERE chat_id=%s AND url=%s
        """, (price, chat_id, url))

    # ---------------- storico prezzi ----------------
    def add_price(self, url, price):
        ts = int(time.time())
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO price_history (url, price, timestamp) VALUES (%s,%s,%s)",
            (url, price, ts)
        )

    def get_history(self, url, limit=100):
        c = self.conn.cursor()
        c.execute("""
            SELECT price, timestamp
            FROM price_history
            WHERE url=%s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (url, limit))
        return c.fetchall()