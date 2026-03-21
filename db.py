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
        chat_id = str(chat_id)
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO users (chat_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (chat_id,)
        )

    # ---------------- prodotti ----------------
    def add_product(self, chat_id, url, target_price, title=None):
        chat_id = str(chat_id)
        self.add_user(chat_id)
        c = self.conn.cursor()
        c.execute("""
                  INSERT INTO products (chat_id, url, target_price, title)
                  VALUES (%s, %s, %s, %s) ON CONFLICT (chat_id, url) DO
                  UPDATE SET
                      target_price = EXCLUDED.target_price,
                      title = COALESCE (EXCLUDED.title, products.title)
                  """, (chat_id, url, target_price, title))

    def remove_product(self, chat_id, url):
        chat_id = str(chat_id)
        c = self.conn.cursor()
        c.execute("DELETE FROM products WHERE chat_id=%s AND url=%s", (chat_id, url))

    def list_products(self, chat_id):
        chat_id = str(chat_id)
        c = self.conn.cursor()
        c.execute("SELECT url, target_price FROM products WHERE chat_id=%s", (chat_id,))
        return c.fetchall()

    def users_for_product(self, url):
        c = self.conn.cursor()
        c.execute("SELECT chat_id FROM products WHERE url=%s", (url,))
        return [row[0] for row in c.fetchall()]

    def update_last_notified(self, chat_id, url, price):
        chat_id = str(chat_id)
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
            "INSERT INTO price_history (url, price, timestamp) VALUES (%s, %s, %s)",
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

    def list_products_with_last_price(self, chat_id):
        """
        Restituisce per ogni prodotto dell'utente:
        [(url, target_price, last_notified_price)]
        """
        chat_id = str(chat_id)
        c = self.conn.cursor()
        c.execute("""
                  SELECT url, target_price, last_notified_price
                  FROM products
                  WHERE chat_id = %s
                  """, (chat_id,))
        return c.fetchall()

    def get_last_price_with_date(self, url):
        """
        Ritorna (price, timestamp) più recente dallo storico prezzi
        """
        c = self.conn.cursor()
        c.execute("""
                  SELECT price, timestamp
                  FROM price_history
                  WHERE url=%s
                  ORDER BY timestamp DESC
                      LIMIT 1
                  """, (url,))
        row = c.fetchone()
        if row:
            return row
        return (None, None)

    def list_products_full(self, chat_id):
        """
        Restituisce tutti i prodotti dell'utente con:
        (url, target_price, last_notified_price, last_price, last_timestamp, title)
        """
        chat_id = str(chat_id)
        c = self.conn.cursor()
        c.execute("""
                  SELECT p.url,
                         p.target_price,
                         p.last_notified_price,
                         ph.price,
                         ph.timestamp,
                         p.title
                  FROM products p
                           LEFT JOIN LATERAL (
                      SELECT price, timestamp
                  FROM price_history
                  WHERE url = p.url
                  ORDER BY timestamp DESC
                      LIMIT 1
                      ) ph
                  ON TRUE
                  WHERE p.chat_id=%s
                  """, (chat_id,))
        return c.fetchall()

    def get_product_title_and_history(self, url, limit=10):
        """
        Restituisce:
        - title del prodotto (colonna title)
        - lista degli ultimi prezzi [(price, timestamp), ...]
        """
        c = self.conn.cursor()
        c.execute("SELECT title FROM products WHERE url=%s LIMIT 1", (url,))
        row = c.fetchone()
        title = row[0] if row and row[0] else None

        c.execute("""
                  SELECT price, timestamp
                  FROM price_history
                  WHERE url=%s
                  ORDER BY timestamp DESC
                      LIMIT %s
                  """, (url, limit))
        history = c.fetchall()
        return title, history

    def reset_database(self):
        """
        Svuota completamente il DB riportando le tabelle allo stato iniziale.
        ATTENZIONE: cancella TUTTI gli utenti, prodotti e storici prezzi!
        """
        c = self.conn.cursor()
        # svuota le tabelle
        c.execute("TRUNCATE TABLE price_history RESTART IDENTITY CASCADE;")
        c.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE;")
        c.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")