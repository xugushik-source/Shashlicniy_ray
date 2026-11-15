CREATE TABLE orders (id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE, fingerprint TEXT NOT NULL, token TEXT NOT NULL UNIQUE, phone TEXT NOT NULL, address TEXT NOT NULL, payment_method TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new', total INTEGER NOT NULL, lines TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
--> statement-breakpoint
CREATE TABLE events (id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(id), status TEXT NOT NULL, actor TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
--> statement-breakpoint
CREATE TABLE telegram_users (chat_id TEXT PRIMARY KEY, role TEXT NOT NULL, lang TEXT NOT NULL DEFAULT 'ru');
--> statement-breakpoint
CREATE TABLE telegram_updates (id INTEGER PRIMARY KEY, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
--> statement-breakpoint
CREATE TABLE notifications (order_id TEXT PRIMARY KEY REFERENCES orders(id), sent_at TEXT);
--> statement-breakpoint
