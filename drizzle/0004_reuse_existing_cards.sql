INSERT INTO supplier_prices(product_id,cost_minor,sale_minor,unit,revision,supplier,approved_at) SELECT 'demo-1b57980d9bbaa6de',cost_minor,sale_minor,unit,revision,supplier,approved_at FROM supplier_prices WHERE product_id='forel-795b5b7f1ee7f058' ON CONFLICT(product_id) DO NOTHING;
--> statement-breakpoint
INSERT INTO supplier_prices(product_id,cost_minor,sale_minor,unit,revision,supplier,approved_at) SELECT 'demo-34dd5651e152b023',cost_minor,sale_minor,unit,revision,supplier,approved_at FROM supplier_prices WHERE product_id='forel-83f91fe0ec3c6e01' ON CONFLICT(product_id) DO NOTHING;
