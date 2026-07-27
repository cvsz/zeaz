#!/usr/bin/env python3
"""Dependency-free preorder server for Moo Piw Piw."""

from __future__ import annotations

import json
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
WEB, DATA = ROOT / "web", ROOT / "data"
ORDERS_FILE, SETTINGS_FILE = DATA / "orders.json", DATA / "settings.json"
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change-me-before-production")
STORE_LOCK = Lock()
DEFAULT_SETTINGS = {
    "store_name": "หมูปิ้ววว",
    "slot_capacity": 80,
    "advance_days": 14,
    "pickup_slots": ["09:00–10:00", "10:00–11:00", "11:00–12:00", "12:00–13:00"],
    "menu": [
        {"id": "classic", "name": "หมูปิ้ววว ต้นตำรับ", "description": "หมูหมักนุ่ม ย่างหอมถ่าน", "price": 15, "available": True},
        {"id": "spicy", "name": "หมูปิ้ววว เผ็ดนัว", "description": "รสจัดจ้าน กลมกล่อม", "price": 18, "available": True},
        {"id": "sticky-rice", "name": "ข้าวเหนียว", "description": "ห่อละกำลังดี", "price": 10, "available": True},
    ],
}
STATUS = {"new", "confirmed", "ready", "completed", "cancelled"}
PAYMENT_METHODS = {"cash", "transfer"}


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def save_json(path: Path, value) -> None:
    DATA.mkdir(exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def settings() -> dict:
    saved = load_json(SETTINGS_FILE, {})
    merged = {**DEFAULT_SETTINGS, **saved}
    return merged


def orders() -> list[dict]:
    return load_json(ORDERS_FILE, [])


def public_order(order: dict) -> dict:
    return {key: order[key] for key in ("id", "status", "pickup", "items", "total", "payment", "created_at", "notes")}


def slots_for(day: str, current_orders: list[dict], config: dict) -> list[dict]:
    used = {slot: 0 for slot in config["pickup_slots"]}
    for order in current_orders:
        if order["status"] != "cancelled" and order["pickup"]["date"] == day:
            used[order["pickup"]["slot"]] = used.get(order["pickup"]["slot"], 0) + sum(item["quantity"] for item in order["items"])
    return [{"time": slot, "remaining": max(0, config["slot_capacity"] - used[slot]), "available": used[slot] < config["slot_capacity"]} for slot in config["pickup_slots"]]


def valid_pickup(day: str, config: dict) -> bool:
    try:
        picked = date.fromisoformat(day)
    except ValueError:
        return False
    return date.today() <= picked <= date.today() + timedelta(days=int(config["advance_days"]))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def json(self, payload: object, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 100_000:
            raise ValueError("ขนาดข้อมูลไม่ถูกต้อง")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("ข้อมูลที่ส่งมาไม่ถูกต้อง")
        if not isinstance(payload, dict):
            raise ValueError("ข้อมูลที่ส่งมาไม่ถูกต้อง")
        return payload

    def is_admin(self) -> bool:
        return secrets.compare_digest(self.headers.get("X-Admin-Key", ""), ADMIN_KEY)

    def require_admin(self) -> bool:
        if self.is_admin():
            return True
        self.json({"error": "ไม่ได้รับอนุญาต"}, HTTPStatus.UNAUTHORIZED)
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)
        config, all_orders = settings(), orders()
        if path == "/api/menu":
            day = query.get("date", [date.today().isoformat()])[0]
            if not valid_pickup(day, config):
                return self.json({"error": "วันรับสินค้าไม่พร้อมให้บริการ"}, HTTPStatus.BAD_REQUEST)
            return self.json({"store_name": config["store_name"], "items": [item for item in config["menu"] if item.get("available")], "slots": slots_for(day, all_orders, config), "date": day, "advance_days": config["advance_days"]})
        if path == "/api/admin/dashboard":
            if not self.require_admin(): return
            active = [order for order in all_orders if order["status"] != "cancelled"]
            return self.json({"summary": {"orders": len(all_orders), "active_orders": len(active), "revenue": sum(order["total"] for order in active), "ready": sum(order["status"] == "ready" for order in active)}, "orders": all_orders, "settings": config})
        if path == "/api/admin/menu":
            if not self.require_admin(): return
            return self.json({"menu": config["menu"], "settings": {key: config[key] for key in ("slot_capacity", "advance_days", "pickup_slots")}})
        if path.startswith("/api/"):
            return self.json({"error": "ไม่พบ API"}, HTTPStatus.NOT_FOUND)
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            form = self.body()
            if path == "/api/orders":
                return self.create_order(form)
            if path == "/api/order-lookup":
                return self.lookup_order(form)
            if path == "/api/admin/menu":
                if not self.require_admin(): return
                return self.create_menu_item(form)
            if path.endswith("/cancel") and re.fullmatch(r"/api/orders/MPP-[A-Z0-9-]+/cancel", path):
                return self.cancel_order(path.split("/")[3], form)
        except ValueError as error:
            return self.json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        return self.json({"error": "ไม่พบ API"}, HTTPStatus.NOT_FOUND)

    def create_order(self, form: dict) -> None:
        config = settings()
        name = str(form.get("name", "")).strip()
        phone = re.sub(r"[^0-9+]", "", str(form.get("phone", "")))
        pickup_date, pickup_slot = str(form.get("pickup_date", "")), str(form.get("pickup_slot", ""))
        payment_method = str(form.get("payment_method", "cash"))
        notes, requested = str(form.get("notes", "")).strip()[:300], form.get("items", [])
        if not 2 <= len(name) <= 80: raise ValueError("กรุณาระบุชื่ออย่างน้อย 2 ตัวอักษร")
        if not re.fullmatch(r"(?:\+66|0)\d{8,9}", phone): raise ValueError("กรุณาระบุเบอร์โทรศัพท์ที่ถูกต้อง")
        if not valid_pickup(pickup_date, config): raise ValueError("เลือกรับสินค้าได้เฉพาะวันที่เปิดให้สั่งล่วงหน้า")
        if pickup_slot not in config["pickup_slots"]: raise ValueError("กรุณาเลือกรอบรับที่มีให้บริการ")
        if payment_method not in PAYMENT_METHODS: raise ValueError("วิธีชำระเงินไม่ถูกต้อง")
        by_id = {item["id"]: item for item in config["menu"] if item.get("available")}
        items, total = [], 0
        if not isinstance(requested, list): raise ValueError("รายการสั่งไม่ถูกต้อง")
        for line in requested:
            if not isinstance(line, dict): raise ValueError("รายการสั่งไม่ถูกต้อง")
            item, quantity = by_id.get(str(line.get("id", ""))), int(line.get("quantity", 0))
            if item and 0 < quantity <= 100:
                items.append({"id": item["id"], "name": item["name"], "quantity": quantity, "unit_price": item["price"]})
                total += item["price"] * quantity
        if not items: raise ValueError("กรุณาเลือกอย่างน้อย 1 รายการ")
        with STORE_LOCK:
            all_orders = orders()
            remaining = next(slot["remaining"] for slot in slots_for(pickup_date, all_orders, config) if slot["time"] == pickup_slot)
            if sum(item["quantity"] for item in items) > remaining: raise ValueError(f"รอบนี้เหลือรับได้ {remaining} ชิ้น กรุณาลดจำนวนหรือเลือกรอบอื่น")
            order = {"id": f"MPP-{datetime.now():%y%m%d}-{secrets.token_hex(3).upper()}", "created_at": datetime.now(timezone.utc).isoformat(), "status": "new", "customer": {"name": name, "phone": phone}, "pickup": {"date": pickup_date, "slot": pickup_slot}, "items": items, "total": total, "notes": notes, "payment": {"method": payment_method, "status": "pending"}, "history": [{"at": datetime.now(timezone.utc).isoformat(), "status": "new", "by": "customer"}]}
            all_orders.insert(0, order)
            save_json(ORDERS_FILE, all_orders)
        self.json({"order": public_order(order)}, HTTPStatus.CREATED)

    def lookup_order(self, form: dict) -> None:
        order_id = str(form.get("order_id", "")).upper().strip()
        phone = re.sub(r"[^0-9+]", "", str(form.get("phone", "")))
        for order in orders():
            if order["id"] == order_id and secrets.compare_digest(order["customer"]["phone"], phone):
                return self.json({"order": public_order(order), "can_cancel": order["status"] in {"new", "confirmed"}})
        self.json({"error": "ไม่พบออเดอร์ หรือเบอร์โทรศัพท์ไม่ตรงกัน"}, HTTPStatus.NOT_FOUND)

    def cancel_order(self, order_id: str, form: dict) -> None:
        phone = re.sub(r"[^0-9+]", "", str(form.get("phone", "")))
        with STORE_LOCK:
            all_orders = orders()
            for order in all_orders:
                if order["id"] == order_id and secrets.compare_digest(order["customer"]["phone"], phone):
                    if order["status"] not in {"new", "confirmed"}: raise ValueError("ออเดอร์นี้ไม่สามารถยกเลิกทางออนไลน์ได้")
                    order["status"] = "cancelled"
                    order["history"].append({"at": datetime.now(timezone.utc).isoformat(), "status": "cancelled", "by": "customer"})
                    save_json(ORDERS_FILE, all_orders)
                    return self.json({"order": public_order(order)})
        self.json({"error": "ไม่พบออเดอร์ หรือเบอร์โทรศัพท์ไม่ตรงกัน"}, HTTPStatus.NOT_FOUND)

    def create_menu_item(self, form: dict) -> None:
        name, description = str(form.get("name", "")).strip(), str(form.get("description", "")).strip()
        price = int(form.get("price", 0))
        if not 2 <= len(name) <= 80 or not 0 <= price <= 10_000: raise ValueError("ข้อมูลเมนูไม่ถูกต้อง")
        with STORE_LOCK:
            config = settings()
            item = {"id": f"item-{secrets.token_hex(3)}", "name": name, "description": description[:160], "price": price, "available": True}
            config["menu"].append(item)
            save_json(SETTINGS_FILE, config)
        self.json({"item": item}, HTTPStatus.CREATED)

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        if not self.require_admin(): return
        try: form = self.body()
        except ValueError as error: return self.json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        order_match = re.fullmatch(r"/api/admin/orders/(MPP-[A-Z0-9-]+)", path)
        menu_match = re.fullmatch(r"/api/admin/menu/([a-z0-9-]+)", path)
        try:
            if order_match: return self.update_order(order_match.group(1), form)
            if menu_match: return self.update_menu_item(menu_match.group(1), form)
            if path == "/api/admin/settings": return self.update_settings(form)
        except ValueError as error:
            return self.json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        self.json({"error": "ไม่พบ API"}, HTTPStatus.NOT_FOUND)

    def update_order(self, order_id: str, form: dict) -> None:
        status, payment_status = str(form.get("status", "")), str(form.get("payment_status", ""))
        if status and status not in STATUS: return self.json({"error": "สถานะไม่ถูกต้อง"}, HTTPStatus.BAD_REQUEST)
        if payment_status and payment_status not in {"pending", "paid", "refunded"}: return self.json({"error": "สถานะชำระเงินไม่ถูกต้อง"}, HTTPStatus.BAD_REQUEST)
        with STORE_LOCK:
            all_orders = orders()
            for order in all_orders:
                if order["id"] == order_id:
                    if status and status != order["status"]:
                        order["status"] = status; order["history"].append({"at": datetime.now(timezone.utc).isoformat(), "status": status, "by": "admin"})
                    if payment_status: order["payment"]["status"] = payment_status
                    save_json(ORDERS_FILE, all_orders); return self.json({"order": order})
        self.json({"error": "ไม่พบออเดอร์"}, HTTPStatus.NOT_FOUND)

    def update_menu_item(self, item_id: str, form: dict) -> None:
        with STORE_LOCK:
            config = settings()
            for item in config["menu"]:
                if item["id"] == item_id:
                    for key in ("name", "description"):
                        if key in form: item[key] = str(form[key]).strip()[:160]
                    if "price" in form:
                        price = int(form["price"])
                        if not 0 <= price <= 10_000: raise ValueError("ราคาไม่ถูกต้อง")
                        item["price"] = price
                    if "available" in form: item["available"] = bool(form["available"])
                    save_json(SETTINGS_FILE, config); return self.json({"item": item})
        self.json({"error": "ไม่พบเมนู"}, HTTPStatus.NOT_FOUND)

    def update_settings(self, form: dict) -> None:
        with STORE_LOCK:
            config = settings()
            for key in ("slot_capacity", "advance_days"):
                if key in form:
                    value = int(form[key])
                    if not 1 <= value <= (500 if key == "slot_capacity" else 60): raise ValueError("ค่าการตั้งค่าไม่ถูกต้อง")
                    config[key] = value
            save_json(SETTINGS_FILE, config)
        self.json({"settings": config})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Moo Piw Piw preorder is running at http://127.0.0.1:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
