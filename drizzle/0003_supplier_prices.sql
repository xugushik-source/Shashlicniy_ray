CREATE TABLE supplier_prices (
 product_id TEXT PRIMARY KEY,
 cost_minor INTEGER NOT NULL CHECK(cost_minor>=0),
 sale_minor INTEGER NOT NULL CHECK(sale_minor>0),
 unit TEXT NOT NULL CHECK(unit IN ('portion','kg')),
 revision TEXT NOT NULL,
 supplier TEXT NOT NULL,
 approved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
--> statement-breakpoint
CREATE TABLE order_costs (
 order_id TEXT PRIMARY KEY REFERENCES orders(id),
 cost_minor INTEGER NOT NULL CHECK(cost_minor>=0),
 cost_lines TEXT NOT NULL,
 currency TEXT NOT NULL DEFAULT 'GEL',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
