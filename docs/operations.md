# MooPiew operations

`/ops.html` is the owner operations console. Enter the admin key there; it is
sent only as an ASCII-safe Base64 request header and is never stored by the
page.

## Fulfilment

- Customers choose **pickup** or **delivery** at checkout.
- Delivery areas define a fixed fee and optional minimum order. The default
  `central` area is 30 THB and should be replaced with the shop's actual zone.
- Each delivery receives an opaque tracking code. An order lookup opens a
  Server-Sent Events live tracking stream at
  `/api/tracking/{tracking_code}/events`; its public payload intentionally
  excludes the delivery address and phone number. The customer page requests a
  browser notification permission once and can alert on live status changes.
- Owners can add riders, assign a rider, and progress the state from queued to
  picked up, on the way, and delivered. Marking delivered completes the order.

## Inventory and recipes

- Add ingredients and record adjustments in the operations console.
- Set recipes with `POST /api/admin/inventory/recipes` using `menu_item_id`,
  `inventory_item_id`, and `quantity`.
- When an order is completed, recipe quantities are deducted once and stored
  as immutable inventory movements. Review thresholds are available through
`GET /api/admin/operations`.

For onboarding, copy `templates/store-master-data.json`, fill in verified shop
details, and use it as the source of truth while entering the same records in
`/ops.html`. Do not commit the completed file because it can contain personal
phone numbers and tax-registration information.

## Customers, coupons, POS

- A customer record is created from their phone number. Completed orders earn
  one point per 25 THB after discount and delivery fee. Customers can redeem
  points at checkout at 1 point = 1 THB; a cancelled order returns any
  reserved points and coupon redemption atomically.
- Coupons can be fixed THB discounts or percentages, with optional minimum
  order and redemption limit. Validation and redemption happen atomically when
  the order is created.
- Issue an immutable receipt from the operations page or
  `POST /api/admin/orders/{order_id}/receipt`. It stores totals, optional
  customer tax details, issue time, and issuer. Set the seller legal name,
  address, 13-digit tax ID and VAT registration in the operations page before
  issuing a sequential tax invoice. The printable receipt is protected by the
  admin key. Have an accountant validate the legal workflow, retention period,
  and any e-Tax Invoice / e-Receipt submission obligations before production.

## Database and backup

The supported runtime is a single application instance using SQLite at
`/home/cvsz/zeaz/data/moopiew.sqlite3`. Both `DATA_DIR` and `DATABASE_PATH`
are explicit in `.env.production`; the systemd service permits writes only to
that data directory. Back up the complete `data/` directory while the service
is stopped, or use SQLite's online backup facility.
