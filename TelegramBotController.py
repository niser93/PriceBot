import requests
import time

class TelegramBotController:
    def __init__(self, token, tracker, db, notifier):
        self.token = token
        self.tracker = tracker
        self.db = db
        self.notifier = notifier
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = None

    def get_updates(self):
        url = f"{self.base_url}/getUpdates"
        params = {}
        if self.last_update_id:
            params["offset"] = self.last_update_id + 1
        r = requests.get(url, params=params).json()
        return r.get("result", [])

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
            self.notifier.send_message(welcome_msg, chat_id)
            return

        # ---------------- verifica registrazione ----------------
        c = self.db.conn.cursor()
        chat_id_str = str(chat_id)
        c.execute("SELECT 1 FROM users WHERE chat_id=%s", (chat_id_str,))
        if not c.fetchone():
            self.notifier.send_message("❗ Devi prima inviare /start per registrarti.", chat_id)
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
            self.notifier.send_message(help_msg, chat_id)
            return

        # ---------------- /add ----------------
        # dentro handle_command
        if command == "/add":
            if len(parts) < 3:
                self.notifier.send_message("❌ /add <URL> <target>", chat_id)
                return
            url = parts[1]
            price_text = parts[2].replace(",", ".")
            try:
                target_price = float(price_text)
            except ValueError:
                self.notifier.send_message("❌ Prezzo non valido", chat_id)
                return

            # Ottieni il tracker corretto per questo URL
            tracker = self.tracker.get_tracker_for_url(url)
            if not tracker:
                self.notifier.send_message("❌ URL non valido o sito non supportato", chat_id)
                return

            # ricava subito il titolo dal tracker
            title = None
            data = tracker.get_product_data(url)
            if data:
                title = data.get("title")

            # salva prodotto nel DB con titolo
            self.db.add_product(chat_id, url, target_price, title=title)

            # prova a salvare primo prezzo
            data = tracker.get_product_data(url)
            initial_price = data.get("price")

            if initial_price is not None:
                self.db.add_price(url, initial_price)
                msg_price = f"Primo prezzo registrato senza notifica: {initial_price}€"
            else:
                msg_price = "Impossibile rilevare il prezzo iniziale al momento."

            self.notifier.send_message(
                f"✅ Prodotto aggiunto!\nURL: {url}\nTarget: {target_price}€\n{msg_price}",
                chat_id
            )

        # ---------------- /remove ----------------
        elif command == "/remove":
            if len(parts) < 2: self.send_message("❌ /remove <URL>", chat_id); return
            url = parts[1]
            self.db.remove_product(chat_id, url)
            self.notifier.send_message(f"🗑️ Rimosso: {url}", chat_id)

        # ---------------- /list ----------------
        elif command == "/list":
            products = self.db.list_products_full(chat_id)

            if not products:
                self.notifier.send_message("📭 Nessun prodotto", chat_id)
            else:
                msg = "📦 Prodotti:\n"
                for url, target, last_notified, last_price, ts, title in products:
                    last_price_text = f"{last_price}€ ({time.strftime('%H:%M %d/%m/%Y', time.localtime(ts))})" \
                        if last_price else "non ancora rilevato"
                    display_text = title if title else url.rstrip("/").split("/")[-1]
                    msg += f'- <a href="{url}">{display_text}</a>\n  Target: {target}€, Ultimo prezzo: {last_price_text}\n'

                self.notifier.send_message(msg, chat_id, parse_mode="HTML")

        # ---------------- /history ----------------
        elif command == "/history":
            if len(parts) < 2:
                self.notifier.send_message("❌ /history <URL>", chat_id)
                return

            url = parts[1]
            title, history = self.db.get_product_title_and_history(url, limit=10)

            if not history:
                self.notifier.send_message("📭 Nessuno storico", chat_id)
                return

            display_text = title if title else url.rstrip("/").split("/")[-1]

            msg = f"📊 Storico <a href=\"{url}\">{display_text}</a>:\n"
            for p, t in reversed(history):
                msg += f"{time.strftime('%H:%M %d/%m/%Y', time.localtime(t))} → {p}€\n"

            self.notifier.send_message(msg, chat_id, parse_mode="HTML")

        # ---------------- comando non valido ----------------
        else:
            self.notifier.send_message("❓ Comando non valido. /start /help /add /remove /list /history", chat_id)

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