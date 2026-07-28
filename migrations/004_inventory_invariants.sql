CREATE UNIQUE INDEX IF NOT EXISTS idx_inventory_order_consumption
ON inventory_movements(order_id, inventory_item_id, reason)
WHERE order_id IS NOT NULL AND reason = 'order_completed';
