import requests
import time

class TelegramBotController:
    def __init__(self, token, tracker, db):
        self.token = token
        self.tracker = tracker
        self.db = db
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = None

    def get_updates(self):
        url = f"{self.base_url}/getUpdates"
        params = {}
        if self.last_update_id:
            params["offset"] = self.last_update_id + 1
        r = requests.get(url, params=params).json()
        return r.get("result", [])

    def send_message(self, text, chat_id):
        url = f"{self.base_url}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text})

    def handle_command(self, text, chat_id):
        parts = text.strip().split(maxsplit=2)
        if not parts: return
        command = parts[0]

        # ---------------- /start ----------------
        if command == "/start":
            self.db.add_user(chat_id)  # registra l'utente
            welcome_msg = (
                "👋 Benvenuto! Ora puoi monitorare i prezzi Amazon.\n\n"
                "Comandi disponibili:\n"
                "/add <URL> <target> - aggiungi un prodotto\n"
                "/remove <URL> - rimuovi un prodotto\n"
                "/list - lista prodotti\n"
                "/history <URL> - storico prezzi\n"
                "/help - mostra questo messaggio"
            )
            self.send_message(welcome_msg, chat_id)
            return

        # ---------------- verifica registrazione ----------------
        c = self.db.conn.cursor()
        c.execute("SELECT 1 FROM users WHERE chat_id=?", (chat_id,))
        if not c.fetchone():
            self.send_message("❗ Devi prima inviare /start per registrarti.", chat_id)
            return

        # ---------------- /help ----------------
        if command == "/help":
            help_msg = (
                "ℹ️ Comandi disponibili:\n"
                "/add <URL> <target> - aggiungi un prodotto\n"
                "/remove <URL> - rimuovi un prodotto\n"
                "/list - lista prodotti\n"
                "/history <URL> - storico prezzi\n"
                "/start - inizializza bot\n"
                "/help - mostra questo messaggio"
            )
            self.send_message(help_msg, chat_id)
            return

        # ---------------- /add ----------------
        # dentro handle_command
        if command == "/add":
            if len(parts) < 3:
                self.send_message("❌ /add <URL> <target>", chat_id)
                return
            url = parts[1];
            price_text = parts[2].replace(",", ".")
            try:
                price = float(price_text)
            except:
                self.send_message("❌ Prezzo non valido", chat_id)
                return

            tracker = self.tracker.get_tracker_for_url(url)
            if tracker:
                self.db.add_product(chat_id, url, price)
                # salva primo prezzo senza notificare
                initial_price = tracker.get_price(url)
                if initial_price:
                    self.db.add_price(url, initial_price)
                self.send_message(f"✅ Aggiunto: {url} ({price}€)\nPrimo prezzo registrato senza notifica.", chat_id)
            else:
                self.send_message("❌ URL non valido o sito non supportato", chat_id)

        # ---------------- /remove ----------------
        elif command == "/remove":
            if len(parts) < 2: self.send_message("❌ /remove <URL>", chat_id); return
            url = parts[1]
            self.db.remove_product(chat_id, url)
            self.send_message(f"🗑️ Rimosso: {url}", chat_id)

        # ---------------- /list ----------------
        elif command == "/list":
            products = self.db.list_products(chat_id)
            if not products:
                self.send_message("📭 Nessun prodotto", chat_id)
            else:
                msg = "📦 Prodotti:\n"
                for u, t in products: msg += f"{u} (target:{t}€)\n"
                self.send_message(msg, chat_id)

        # ---------------- /history ----------------
        elif command == "/history":
            if len(parts) < 2: self.send_message("❌ /history <URL>", chat_id); return
            url = parts[1]
            history = self.db.get_history(url, limit=10)
            if not history:
                self.send_message("📭 Nessuno storico", chat_id)
            else:
                msg = f"📊 Storico {url}:\n"
                for p, t in reversed(history):
                    msg += f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(t))} → {p}€\n"
                self.send_message(msg, chat_id)

        # ---------------- comando non valido ----------------
        else:
            self.send_message("❓ Comando non valido. /start /help /add /remove /list /history", chat_id)

    def run(self):
        while True:
            updates = self.get_updates()
            for u in updates:
                self.last_update_id = u["update_id"]
                try:
                    msg = u["message"]["text"]
                    chat_id = u["message"]["chat"]["id"]
                    self.handle_command(msg, chat_id)
                except:
                    continue
            time.sleep(1)