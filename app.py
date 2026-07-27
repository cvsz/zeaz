#!/usr/bin/env python3
"""Moo Piw Piw: secure, dependency-free preorder and operations server.

Uses SQLite (WAL mode) for durable order, menu, setting and audit data.  On
first start it imports legacy data/orders.json and data/settings.json safely.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("DATABASE_PATH", DATA / "moopiew.sqlite3"))
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change-me-before-production")
EMPLOYEE_KEY = os.environ.get("EMPLOYEE_KEY", "change-me-employee-key")
KITCHEN_KEY = os.environ.get("KITCHEN_KEY", "change-me-kitchen-key")
STORE_LOCK, RATE_LOCK = Lock(), Lock()
RATE_BUCKETS: dict[tuple[str, str], list[float]] = {}
RATE_WINDOW_SECONDS, RATE_LIMITS = 60, {"order": 12, "lookup": 20, "admin": 60, "staff": 90}
STATUS = ("new", "confirmed", "ready", "completed", "cancelled")
PAYMENT_STATUSES, PAYMENT_METHODS = ("pending", "paid", "refunded"), ("cash", "transfer")
DEFAULT_SETTINGS = {
    "store_name": "หมูปิ้ววว", "slot_capacity": 80, "advance_days": 14,
    "pickup_slots": ["09:00–10:00", "10:00–11:00", "11:00–12:00", "12:00–13:00"],
}
DEFAULT_MENU = [
    {"id": "classic", "name": "หมูปิ้ววว ต้นตำรับ", "description": "หมูหมักนุ่ม ย่างหอมถ่าน", "price": 15, "available": True},
    {"id": "spicy", "name": "หมูปิ้ววว เผ็ดนัว", "description": "รสจัดจ้าน กลมกล่อม", "price": 18, "available": True},
    {"id": "sticky-rice", "name": "ข้าวเหนียว", "description": "ห่อละกำลังดี", "price": 10, "available": True},
]

def utcnow() -> str: return datetime.now(timezone.utc).isoformat()

def load_legacy(path: Path, fallback):
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except (OSError, json.JSONDecodeError): return fallback

@contextmanager
def db():
    DATA.mkdir(mode=0o700, parents=True, exist_ok=True); DATA.chmod(0o700)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection; connection.commit()
    except Exception:
        connection.rollback(); raise
    finally: connection.close()

def initialise_database() -> None:
    with db() as con:
        con.executescript("""
        PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS menu_items (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', price INTEGER NOT NULL CHECK(price >= 0), available INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('new','confirmed','ready','completed','cancelled')), customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL, pickup_date TEXT NOT NULL, pickup_slot TEXT NOT NULL, total INTEGER NOT NULL, notes TEXT NOT NULL DEFAULT '', payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'pending');
        CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE, menu_item_id TEXT NOT NULL, name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price INTEGER NOT NULL CHECK(unit_price >= 0));
        CREATE TABLE IF NOT EXISTS order_history (id INTEGER PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE, at TEXT NOT NULL, status TEXT NOT NULL, actor_role TEXT NOT NULL, note TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor_role TEXT NOT NULL, action TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, details TEXT NOT NULL DEFAULT '{}');
        CREATE INDEX IF NOT EXISTS idx_orders_pickup ON orders(pickup_date, pickup_slot);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_audit_at ON audit_logs(at DESC);
        """)
        if con.execute("SELECT COUNT(*) FROM settings").fetchone()[0]: return
        legacy_settings = load_legacy(DATA / "settings.json", {})
        config = {**DEFAULT_SETTINGS, **legacy_settings}
        for key, value in config.items(): con.execute("INSERT INTO settings VALUES (?,?)", (key, json.dumps(value, ensure_ascii=False)))
        for item in config.get("menu", DEFAULT_MENU):
            con.execute("INSERT OR IGNORE INTO menu_items VALUES (?,?,?,?,?,?,?)", (item["id"], item["name"], item.get("description", ""), int(item["price"]), int(item.get("available", True)), utcnow(), utcnow()))
        for order in load_legacy(DATA / "orders.json", []): import_legacy_order(con, order)

def import_legacy_order(con: sqlite3.Connection, order: dict) -> None:
    if not isinstance(order, dict) or not order.get("id"): return
    if con.execute("SELECT 1 FROM orders WHERE id=?", (order["id"],)).fetchone(): return
    customer, pickup, payment = order.get("customer", {}), order.get("pickup", {}), order.get("payment", {})
    values = (order["id"], order.get("created_at", utcnow()), order.get("status", "new"), customer.get("name", ""), customer.get("phone", ""), pickup.get("date", date.today().isoformat()), pickup.get("slot", ""), int(order.get("total", 0)), order.get("notes", ""), payment.get("method", "cash"), payment.get("status", "pending"))
    con.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)", values)
    for item in order.get("items", []): con.execute("INSERT INTO order_items(order_id,menu_item_id,name,quantity,unit_price) VALUES (?,?,?,?,?)", (order["id"], item.get("id", "legacy"), item.get("name", "รายการ"), int(item.get("quantity", 1)), int(item.get("unit_price", 0))))
    for event in order.get("history", [{"at": values[1], "status": values[2], "by": "legacy"}]): con.execute("INSERT INTO order_history(order_id,at,status,actor_role) VALUES (?,?,?,?)", (order["id"], event.get("at", values[1]), event.get("status", values[2]), event.get("by", "legacy")))

def config(con: sqlite3.Connection) -> dict:
    result = {row["key"]: json.loads(row["value"]) for row in con.execute("SELECT key,value FROM settings")}
    result["menu"] = [dict(row) | {"available": bool(row["available"])} for row in con.execute("SELECT id,name,description,price,available FROM menu_items ORDER BY created_at")]
    return result

def set_setting(con, key, value): con.execute("INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value, ensure_ascii=False)))
def audit(con, role, action, entity_type, entity_id, details=None): con.execute("INSERT INTO audit_logs(at,actor_role,action,entity_type,entity_id,details) VALUES (?,?,?,?,?,?)", (utcnow(), role, action, entity_type, entity_id, json.dumps(details or {}, ensure_ascii=False)))

def row_order(con, order_id: str) -> dict | None:
    row = con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row: return None
    order = dict(row)
    order["customer"] = {"name": order.pop("customer_name"), "phone": order.pop("customer_phone")}
    order["pickup"] = {"date": order.pop("pickup_date"), "slot": order.pop("pickup_slot")}
    order["payment"] = {"method": order.pop("payment_method"), "status": order.pop("payment_status")}
    order["items"] = [dict(item) for item in con.execute("SELECT menu_item_id AS id,name,quantity,unit_price FROM order_items WHERE order_id=?", (order_id,))]
    order["history"] = [dict(event) for event in con.execute("SELECT at,status,actor_role AS by,note FROM order_history WHERE order_id=? ORDER BY id", (order_id,))]
    return order

def all_orders(con, pickup_date=None):
    query, args = "SELECT id FROM orders", []
    if pickup_date: query += " WHERE pickup_date=?"; args.append(pickup_date)
    query += " ORDER BY pickup_date DESC, created_at DESC"
    return [row_order(con, row["id"]) for row in con.execute(query, args)]

def public_order(order): return {key: order[key] for key in ("id", "status", "pickup", "items", "total", "payment", "created_at", "notes")}
def valid_pickup(day, conf):
    try: picked = date.fromisoformat(day)
    except ValueError: return False
    return date.today() <= picked <= date.today() + timedelta(days=int(conf["advance_days"]))
def slots_for(day, rows, conf):
    used = {slot: 0 for slot in conf["pickup_slots"]}
    for order in rows:
        if order["status"] != "cancelled" and order["pickup"]["date"] == day: used[order["pickup"]["slot"]] = used.get(order["pickup"]["slot"], 0) + sum(line["quantity"] for line in order["items"])
    return [{"time": slot, "remaining": max(0, int(conf["slot_capacity"]) - used[slot]), "available": used[slot] < int(conf["slot_capacity"])} for slot in conf["pickup_slots"]]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(WEB), **kwargs)
    def log_message(self, format, *args): print(f"[{self.log_date_time_string()}] {format % args}")
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("X-Frame-Options", "DENY"); self.send_header("Referrer-Policy", "strict-origin-when-cross-origin"); self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        super().end_headers()
    def json(self, payload, status=200):
        encoded=json.dumps(payload, ensure_ascii=False).encode(); self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(encoded))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(encoded)
    def body(self):
        try: length=int(self.headers.get("Content-Length", "0"))
        except ValueError: raise ValueError("ขนาดข้อมูลไม่ถูกต้อง")
        if not 0 < length <= 100_000: raise ValueError("ขนาดข้อมูลไม่ถูกต้อง")
        try: value=json.loads(self.rfile.read(length).decode())
        except (UnicodeDecodeError,json.JSONDecodeError): raise ValueError("ข้อมูลที่ส่งมาไม่ถูกต้อง")
        if not isinstance(value,dict): raise ValueError("ข้อมูลที่ส่งมาไม่ถูกต้อง")
        return value
    def role(self):
        checks=(("admin", "X-Admin-Key", ADMIN_KEY), ("employee", "X-Employee-Key", EMPLOYEE_KEY), ("kitchen", "X-Kitchen-Key", KITCHEN_KEY))
        for role, header, key in checks:
            supplied=self.headers.get(header, "")
            if key and secrets.compare_digest(supplied, key): return role
        return None
    def client_key(self):
        peer=self.client_address[0]; forwarded=self.headers.get("CF-Connecting-IP", "") if peer in {"127.0.0.1","::1"} else ""
        return forwarded if re.fullmatch(r"[0-9a-fA-F:.]{3,45}", forwarded) else peer
    def rate(self, bucket):
        now=time.monotonic(); key=(bucket,self.client_key())
        with RATE_LOCK:
            active=[stamp for stamp in RATE_BUCKETS.get(key,[]) if now-stamp<RATE_WINDOW_SECONDS]
            if len(active)>=RATE_LIMITS[bucket]: RATE_BUCKETS[key]=active; return False
            RATE_BUCKETS[key]=active+[now]; return True
    def require(self, *roles):
        if not self.rate("admin" if "admin" in roles else "staff"): self.json({"error":"คำขอมากเกินไป กรุณาลองใหม่ภายหลัง"},429); return None
        role=self.role()
        if role == "admin" or role in roles: return role
        self.json({"error":"ไม่ได้รับอนุญาต"},401); return None
    def do_GET(self):
        parsed=urlparse(self.path); path, query=parsed.path, parse_qs(parsed.query)
        if path == "/api/health":
            return self.json({"status": "ok", "service": "moopiew", "time": utcnow()})
        with db() as con:
            conf=config(con)
            if path == "/api/ready":
                con.execute("SELECT 1 FROM settings LIMIT 1").fetchone()
                return self.json({"status": "ready", "database": "ok"})
            if path == "/api/status":
                return self.json({"status":"operational","service":"moopiew","time":utcnow(),"database":"ok","api_version":"1.1","endpoints":{"health":"/api/health","ready":"/api/ready","menu":"/api/menu"}})
            if path=="/api/menu":
                day=query.get("date",[date.today().isoformat()])[0]
                if not valid_pickup(day,conf): return self.json({"error":"วันรับสินค้าไม่พร้อมให้บริการ"},400)
                available_items=[item for item in conf["menu"] if item["available"]]
                pickup_slots=slots_for(day,all_orders(con),conf)
                return self.json({
                    "api_version":"1.1",
                    "generated_at":utcnow(),
                    "store":{"name":conf["store_name"],"locale":"th-TH","currency":"THB"},
                    "store_name":conf["store_name"],
                    "theme":{"name":"moopiew-food-tech","primary":"#FF6B35","primary_light":"#FF8A4C","secondary":"#FFC107","surface":"#FFF8EF","text":"#211B18"},
                    "items":available_items,
                    "pickup":{"date":day,"slots":pickup_slots,"capacity_per_slot":conf["slot_capacity"],"remaining_total":sum(slot["remaining"] for slot in pickup_slots)},
                    "slots":pickup_slots,
                    "date":day,
                    "advance_days":conf["advance_days"],
                    "links":{"order":"/","dashboard":"/dashboard.html","platform":"/platform/","preview":"/menu-preview.html","health":"/api/health"}
                })
            if path=="/api/admin/dashboard":
                if not self.require("admin"): return
                return self.admin_dashboard(con, conf)
            if path=="/api/admin/menu":
                if not self.require("admin"): return
                return self.json({"menu":conf["menu"],"settings":{k:conf[k] for k in ("slot_capacity","advance_days","pickup_slots")}})
            if path=="/api/admin/audit":
                if not self.require("admin"): return
                logs=[dict(row) | {"details":json.loads(row["details"])} for row in con.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")]
                return self.json({"logs":logs})
            if path in ("/api/staff/dashboard","/api/kitchen/dashboard"):
                expected="employee" if "staff" in path else "kitchen"; role=self.require(expected)
                if not role: return
                picked=query.get("date",[date.today().isoformat()])[0]
                orders=all_orders(con,picked)
                return self.json({"date":picked,"store_name":conf["store_name"],"orders":orders,"summary":summary(orders),"role":role})
        if path.startswith("/api/"): return self.json({"error":"ไม่พบ API"},404)
        return super().do_GET()
    def do_HEAD(self):
        path=urlparse(self.path).path
        if path=="/api/menu": self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Cache-Control","no-store"); return self.end_headers()
        return super().do_HEAD()
    def do_POST(self):
        path=urlparse(self.path).path
        try: form=self.body()
        except ValueError as error: return self.json({"error":str(error)},400)
        try:
            if path=="/api/orders":
                if not self.rate("order"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.create_order(form)
            if path=="/api/order-lookup":
                if not self.rate("lookup"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.lookup_order(form)
            if path=="/api/admin/menu":
                role=self.require("admin")
                if role: return self.create_menu_item(form,role)
            if path.endswith("/cancel") and re.fullmatch(r"/api/orders/MPP-[A-Z0-9-]+/cancel",path):
                if not self.rate("lookup"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.cancel_order(path.split("/")[3],form)
        except ValueError as error: return self.json({"error":str(error)},400)
        return self.json({"error":"ไม่พบ API"},404)
    def do_PATCH(self):
        path=urlparse(self.path).path
        try: form=self.body()
        except ValueError as error: return self.json({"error":str(error)},400)
        match=re.fullmatch(r"/api/(admin|staff|kitchen)/orders/(MPP-[A-Z0-9-]+)",path)
        if match:
            area, order_id=match.groups(); expected={"admin":"admin","staff":"employee","kitchen":"kitchen"}[area]; role=self.require(expected)
            if role: return self.update_order(order_id,form,role,area)
            return
        if not path.startswith("/api/admin/"): return self.json({"error":"ไม่พบ API"},404)
        role=self.require("admin")
        if not role:return
        try:
            menu=re.fullmatch(r"/api/admin/menu/([a-z0-9-]+)",path)
            if menu:return self.update_menu_item(menu.group(1),form,role)
            if path=="/api/admin/settings":return self.update_settings(form,role)
        except ValueError as error:return self.json({"error":str(error)},400)
        self.json({"error":"ไม่พบ API"},404)
    def admin_dashboard(self,con,conf):
        orders=all_orders(con); recent=[dict(row) for row in con.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10")]
        return self.json({"summary":summary(orders),"orders":orders,"settings":conf,"audit":recent})
    def create_order(self,form):
        name=str(form.get("name","")).strip(); phone=re.sub(r"[^0-9+]","",str(form.get("phone", ""))); pickup_date,pickup_slot=str(form.get("pickup_date", "")),str(form.get("pickup_slot", "")); payment=str(form.get("payment_method","cash")); notes=str(form.get("notes","")).strip()[:300]; requested=form.get("items",[])
        if not 2<=len(name)<=80:raise ValueError("กรุณาระบุชื่ออย่างน้อย 2 ตัวอักษร")
        if not re.fullmatch(r"(?:\+66|0)\d{8,9}",phone):raise ValueError("กรุณาระบุเบอร์โทรศัพท์ที่ถูกต้อง")
        with STORE_LOCK,db() as con:
            conf=config(con)
            if not valid_pickup(pickup_date,conf):raise ValueError("เลือกรับสินค้าได้เฉพาะวันที่เปิดให้สั่งล่วงหน้า")
            if pickup_slot not in conf["pickup_slots"]:raise ValueError("กรุณาเลือกรอบรับที่มีให้บริการ")
            if payment not in PAYMENT_METHODS:raise ValueError("วิธีชำระเงินไม่ถูกต้อง")
            if not isinstance(requested,list):raise ValueError("รายการสั่งไม่ถูกต้อง")
            by_id={item["id"]:item for item in conf["menu"] if item["available"]}; lines=[]; total=0
            for line in requested:
                if not isinstance(line,dict):raise ValueError("รายการสั่งไม่ถูกต้อง")
                item=by_id.get(str(line.get("id","")))
                try: quantity=int(line.get("quantity",0))
                except (TypeError,ValueError):raise ValueError("รายการสั่งไม่ถูกต้อง")
                if item and 0<quantity<=100:lines.append((item,quantity));total+=item["price"]*quantity
            if not lines:raise ValueError("กรุณาเลือกอย่างน้อย 1 รายการ")
            remaining=next(slot["remaining"] for slot in slots_for(pickup_date,all_orders(con),conf) if slot["time"]==pickup_slot)
            if sum(q for _,q in lines)>remaining:raise ValueError(f"รอบนี้เหลือรับได้ {remaining} ชิ้น กรุณาลดจำนวนหรือเลือกรอบอื่น")
            oid=f"MPP-{datetime.now():%y%m%d}-{secrets.token_hex(3).upper()}"; now=utcnow()
            con.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",(oid,now,"new",name,phone,pickup_date,pickup_slot,total,notes,payment,"pending"))
            con.executemany("INSERT INTO order_items(order_id,menu_item_id,name,quantity,unit_price) VALUES (?,?,?,?,?)",[(oid,i["id"],i["name"],q,i["price"]) for i,q in lines])
            con.execute("INSERT INTO order_history(order_id,at,status,actor_role) VALUES (?,?,?,?)",(oid,now,"new","customer")); audit(con,"customer","create","order",oid,{"total":total})
            order=row_order(con,oid)
        self.json({"order":public_order(order)},201)
    def lookup_order(self,form):
        oid=str(form.get("order_id","")).upper().strip(); phone=re.sub(r"[^0-9+]","",str(form.get("phone","")))
        with db() as con:
            order=row_order(con,oid)
            if order and secrets.compare_digest(order["customer"]["phone"],phone):return self.json({"order":public_order(order),"can_cancel":order["status"] in {"new","confirmed"}})
        self.json({"error":"ไม่พบออเดอร์ หรือเบอร์โทรศัพท์ไม่ตรงกัน"},404)
    def cancel_order(self,oid,form):
        phone=re.sub(r"[^0-9+]","",str(form.get("phone","")))
        with STORE_LOCK,db() as con:
            order=row_order(con,oid)
            if not order or not secrets.compare_digest(order["customer"]["phone"],phone):return self.json({"error":"ไม่พบออเดอร์ หรือเบอร์โทรศัพท์ไม่ตรงกัน"},404)
            if order["status"] not in {"new","confirmed"}:raise ValueError("ออเดอร์นี้ไม่สามารถยกเลิกทางออนไลน์ได้")
            con.execute("UPDATE orders SET status='cancelled' WHERE id=?",(oid,));con.execute("INSERT INTO order_history(order_id,at,status,actor_role) VALUES (?,?,?,?)",(oid,utcnow(),"cancelled","customer"));audit(con,"customer","cancel","order",oid)
            return self.json({"order":public_order(row_order(con,oid))})
    def create_menu_item(self,form,role):
        name,description=str(form.get("name","")).strip(),str(form.get("description","")).strip()[:160]
        try:price=int(form.get("price",0))
        except (TypeError,ValueError):raise ValueError("ราคาไม่ถูกต้อง")
        if not 2<=len(name)<=80 or not 0<=price<=10000:raise ValueError("ข้อมูลเมนูไม่ถูกต้อง")
        item={"id":f"item-{secrets.token_hex(3)}","name":name,"description":description,"price":price,"available":True}
        with db() as con: con.execute("INSERT INTO menu_items VALUES (?,?,?,?,?,?,?)",(item["id"],name,description,price,1,utcnow(),utcnow()));audit(con,role,"create","menu_item",item["id"],item)
        self.json({"item":item},201)
    def update_order(self,oid,form,role,area):
        allowed={"admin":set(STATUS),"staff":{"confirmed","ready","completed"},"kitchen":{"ready"}}[area]
        status=str(form.get("status", "")); payment=str(form.get("payment_status", ""))
        if status and status not in allowed:raise ValueError("คุณไม่มีสิทธิ์เปลี่ยนสถานะนี้")
        if payment and (area!="admin" or payment not in PAYMENT_STATUSES):raise ValueError("สถานะชำระเงินไม่ถูกต้อง")
        with STORE_LOCK,db() as con:
            order=row_order(con,oid)
            if not order:return self.json({"error":"ไม่พบออเดอร์"},404)
            transitions={"staff": {("new","confirmed"), ("ready","completed")}, "kitchen": {("confirmed","ready")}}
            if status and area in transitions and (order["status"], status) not in transitions[area]:
                raise ValueError("ลำดับสถานะไม่ถูกต้อง")
            if status and status!=order["status"]:
                con.execute("UPDATE orders SET status=? WHERE id=?",(status,oid));con.execute("INSERT INTO order_history(order_id,at,status,actor_role) VALUES (?,?,?,?)",(oid,utcnow(),status,role));audit(con,role,"status_change","order",oid,{"from":order["status"],"to":status})
            if payment:con.execute("UPDATE orders SET payment_status=? WHERE id=?",(payment,oid));audit(con,role,"payment_change","order",oid,{"to":payment})
            return self.json({"order":row_order(con,oid)})
    def update_menu_item(self,iid,form,role):
        with db() as con:
            item=con.execute("SELECT * FROM menu_items WHERE id=?",(iid,)).fetchone()
            if not item:return self.json({"error":"ไม่พบเมนู"},404)
            name=str(form.get("name",item["name"])).strip()[:80];desc=str(form.get("description",item["description"])).strip()[:160]
            try:price=int(form.get("price",item["price"]))
            except (TypeError,ValueError):raise ValueError("ราคาไม่ถูกต้อง")
            available=int(bool(form.get("available",bool(item["available"]))))
            if len(name)<2 or not 0<=price<=10000:raise ValueError("ข้อมูลเมนูไม่ถูกต้อง")
            con.execute("UPDATE menu_items SET name=?,description=?,price=?,available=?,updated_at=? WHERE id=?",(name,desc,price,available,utcnow(),iid));audit(con,role,"update","menu_item",iid)
            return self.json({"item":{"id":iid,"name":name,"description":desc,"price":price,"available":bool(available)}})
    def update_settings(self,form,role):
        with db() as con:
            for key, maximum in (("slot_capacity",500),("advance_days",60)):
                if key in form:
                    try:value=int(form[key])
                    except (TypeError,ValueError):raise ValueError("ค่าการตั้งค่าไม่ถูกต้อง")
                    if not 1<=value<=maximum:raise ValueError("ค่าการตั้งค่าไม่ถูกต้อง")
                    set_setting(con,key,value)
            audit(con,role,"update","settings","store")
            return self.json({"settings":config(con)})

def summary(rows):
    active=[row for row in rows if row["status"]!="cancelled"]
    return {"orders":len(rows),"active_orders":len(active),"revenue":sum(row["total"] for row in active),"ready":sum(row["status"]=="ready" for row in active),"new":sum(row["status"]=="new" for row in active),"completed":sum(row["status"]=="completed" for row in active)}

if __name__=="__main__":
    if os.environ.get("REQUIRE_ADMIN_KEY","false").lower()=="true" and (ADMIN_KEY=="change-me-before-production" or EMPLOYEE_KEY=="change-me-employee-key" or KITCHEN_KEY=="change-me-kitchen-key"):raise SystemExit("Production requires ADMIN_KEY, EMPLOYEE_KEY and KITCHEN_KEY")
    initialise_database(); port=int(os.environ.get("PORT","8000"));host=os.environ.get("HOST","127.0.0.1");print(f"Moo Piw Piw is running at http://{host}:{port}");ThreadingHTTPServer((host,port),Handler).serve_forever()
