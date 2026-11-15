ALTER TABLE telegram_users ADD COLUMN display_name TEXT;
--> statement-breakpoint
ALTER TABLE orders ADD COLUMN supplier_chat_id TEXT;
--> statement-breakpoint
ALTER TABLE orders ADD COLUMN courier_chat_id TEXT;
--> statement-breakpoint
CREATE TABLE staff_invites (token_hash TEXT PRIMARY KEY, role TEXT NOT NULL, created_by TEXT NOT NULL, expires_at INTEGER NOT NULL, used_by TEXT);
--> statement-breakpoint
CREATE TABLE setup_claims (name TEXT PRIMARY KEY, claimed_by TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
