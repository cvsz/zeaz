#!/usr/bin/env python3
"""Moo Piw Piw: secure, dependency-free preorder and operations server.

Uses SQLite (WAL mode) for durable order, menu, setting and audit data.  On
first start it imports legacy data/orders.json and data/settings.json safely.
"""
from __future__ import annotations

import json
import math
import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import ssl
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from cryptography.fernet import Fernet, InvalidToken
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from html import escape as escape_html
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from migrations.runner import apply_migrations

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("DATABASE_PATH", DATA / "moopiew.sqlite3"))
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change-me-before-production")
EMPLOYEE_KEY = os.environ.get("EMPLOYEE_KEY", "change-me-employee-key")
KITCHEN_KEY = os.environ.get("KITCHEN_KEY", "change-me-kitchen-key")
TRUST_CF_CONNECTING_IP = (
    os.environ.get("TRUST_CF_CONNECTING_IP", "false").lower() == "true"
)
STORE_LOCK, RATE_LOCK = Lock(), Lock()
RATE_BUCKETS: dict[tuple[str, str], list[float]] = {}
RATE_WINDOW_SECONDS, RATE_LIMITS = 60, {"public": 120, "order": 12, "lookup": 20, "quote": 30, "rider": 8, "webhook": 60, "admin": 60, "staff": 90}
STATUS = ("new", "confirmed", "ready", "completed", "cancelled")
PAYMENT_STATUSES, PAYMENT_METHODS = ("pending", "paid", "refunded"), ("cash", "transfer", "scb_qr")
AUTO_CONFIRM_ORDERS = os.environ.get("AUTO_CONFIRM_ORDERS", "false").lower() == "true"
PAYMENTS_ENABLED = os.environ.get("PAYMENTS_ENABLED", "false").lower() == "true"
SCB_ENABLED = os.environ.get("SCB_ENABLED", "false").lower() == "true"
SCB_TOKEN_CACHE: dict[str, object] = {}
SCB_SERVICE_TOKEN_CACHE: dict[str, object] = {}
SCB_TOKEN_LOCK = Lock()
HF_MODEL_CACHE: dict[str, object] = {"models": [], "expires": 0.0}
HF_MODEL_LOCK = Lock()
HF_ROUTER_DEFAULT = "https://router.huggingface.co/v1"
HF_MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.:-]*")
PROVIDER_MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]*")
AI_MODEL_CACHE: dict[str, object] = {"catalog": {}, "expires": 0.0}
AI_MODEL_LOCK = Lock()
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"
NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"
ZAI_API_BASE = "https://api.z.ai/api/paas/v4"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENCODE_API_BASE = "https://opencode.ai/zen/v1"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
BYTEPLUS_API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
FIREWORKS_API_BASE = "https://api.fireworks.ai/inference/v1"
OPENAI_API_BASE = "https://api.openai.com/v1"
KIMI_API_BASE = "https://api.moonshot.ai/v1"
SCALEWAY_API_BASE = "https://api.scaleway.ai/v1"
TOGETHER_API_BASE = "https://api.together.xyz/v1"
GITHUB_MODELS_API_BASE = "https://models.github.ai"
CEREBRAS_API_BASE = "https://api.cerebras.ai/v1"
ZEAZ_GATEWAY_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
AI_PROVIDER_NAMES = {"local","zai","kimi","scaleway","together","github","openrouter","opencode","huggingface","groq","cerebras","gemini","nvidia","byteplus","fireworks","openai","zeaz_gateway"}
AI_PROVIDER_PRIORITY = ("local","zai","kimi","scaleway","together","github","openrouter","opencode","huggingface","groq","cerebras","gemini","nvidia","byteplus","fireworks","openai","zeaz_gateway")
AI_SYSTEM_PROMPT = "You are MooPiew's operator assistant. Do not request or reveal secrets, payment credentials, or customer personal data. Answer concisely in the language used by the operator."
DEFAULT_SETTINGS = {
    "store_name": "หมูปิ้ววว", "slot_capacity": 80, "advance_days": 14,
    "pickup_slots": ["09:00–10:00", "10:00–11:00", "11:00–12:00", "12:00–13:00"],
    "business_profile": {"legal_name":"", "tax_id":"", "address":"", "branch":"สำนักงานใหญ่", "vat_registered":False, "vat_rate":7},
    "delivery_pricing": {"mode":"distance","base_fee":55,"per_km_fee":9,"maximum_km":15,"store_latitude":None,"store_longitude":None},
}
DEFAULT_MENU = [
    {"id": "classic", "name": "หมูปิ้ววว ต้นตำรับ", "description": "หมูหมักนุ่ม ย่างหอมถ่าน", "price": 10, "available": True},
    {"id": "milk-tender", "name": "หมูปิ้ววว นมสุดดด", "description": "หมูหมักนมเนื้อนุ่ม ย่างหอมถ่าน", "price": 10, "available": True},
    {"id": "fatty", "name": "หมูปิ้ววว ติดมันส์", "description": "หมูติดมันย่างหอมถ่าน นุ่มฉ่ำ", "price": 10, "available": True},
    {"id": "spicy", "name": "หมูปิ้ววว เผ็ดนัว", "description": "รสจัดจ้าน กลมกล่อม", "price": 10, "available": True},
    {"id": "sticky-rice", "name": "ข้าวเหนียว", "description": "ห่อละกำลังดี", "price": 10, "available": True},
]
DELIVERY_STATUSES = ("queued", "assigned", "picked_up", "on_the_way", "delivered", "failed", "cancelled")
ACTIVE_DELIVERY_STATUSES = ("assigned", "picked_up", "on_the_way")

def utcnow() -> str: return datetime.now(timezone.utc).isoformat()

def header_secret(headers, name: str) -> str:
    """Read an ASCII-safe Base64 UTF-8 credential, retaining legacy headers."""
    encoded=headers.get(f"{name}-B64")
    if encoded is not None:
        try: return base64.b64decode(encoded, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError): return ""
    return headers.get(name, "")

def load_legacy(path: Path, fallback):
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except (OSError, json.JSONDecodeError): return fallback

@contextmanager
def db(*, immediate: bool = False):
    DATA.mkdir(mode=0o700, parents=True, exist_ok=True); DATA.chmod(0o700)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        if immediate:
            connection.execute("BEGIN IMMEDIATE")
        yield connection; connection.commit()
    except Exception:
        connection.rollback(); raise
    finally: connection.close()

def initialise_database() -> None:
    with db() as con:
        apply_migrations(con)
        con.execute("INSERT OR IGNORE INTO menu_display_order(menu_item_id,position) SELECT id,CASE id WHEN 'classic' THEN 1 WHEN 'milk-tender' THEN 2 WHEN 'fatty' THEN 3 WHEN 'spicy' THEN 4 WHEN 'sticky-rice' THEN 5 END FROM menu_items WHERE id IN ('classic','milk-tender','fatty','spicy','sticky-rice')")
        now=utcnow()
        con.execute("INSERT OR IGNORE INTO delivery_zones VALUES (?,?,?,?,?,?,?)", ("central", "พื้นที่จัดส่งหลัก", 30, 0, 1, now, now))
        seed_document_requirements(con)
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

def seed_document_requirements(con: sqlite3.Connection) -> None:
    """Seed provider requirements from published Thailand provider pages."""
    now = utcnow()
    providers = [
        ("grab", "Grab", "https://www.grab.com/th/driver/drive/", "https://www.grab.com/th/merchant/"),
        ("bolt", "Bolt", "https://bolt.eu/th-th/support/articles/4406002078610/", "https://bolt.eu/en-th/driver/"),
        ("lineman", "LINE MAN", "https://lineman.line.me/rider/", "https://lineman.line.me/"),
        ("lalamove", "Lalamove", "https://www.lalamove.com/th-th/driver", "https://www.lalamove.com/th-th/")
    ]
    for slug, name, rider_url, merchant_url in providers:
        pid=f"provider-{slug}"
        con.execute("INSERT OR IGNORE INTO providers(id,slug,name,country,status,metadata,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)", (pid,slug,name,"TH","active",json.dumps({"rider_reference":rider_url,"merchant_reference":merchant_url}),now,now))
        for service,label in (("rider","Rider registration"),("merchant","Merchant registration")):
            con.execute("INSERT OR IGNORE INTO provider_services(id,provider_id,slug,name,metadata) VALUES (?,?,?,?,?)", (f"{slug}-{service}",pid,service,label,json.dumps({"country":"TH"})))
    for slug,name in [("individual","Individual"),("company","Company"),("restaurant","Restaurant"),("cloud-kitchen","Cloud Kitchen"),("cafe","Cafe"),("retail","Retail"),("grocery","Grocery")]:
        con.execute("INSERT OR IGNORE INTO merchant_types(id,slug,name) VALUES (?,?,?)", (f"merchant-type-{slug}",slug,name))
    for slug,name in [("motorcycle","Motorcycle"),("car","Car"),("van","Van"),("truck","Truck"),("bicycle","Bicycle")]:
        con.execute("INSERT OR IGNORE INTO vehicle_types(id,slug,name) VALUES (?,?,?)", (f"vehicle-type-{slug}",slug,name))
    types=[
        ("national-id","National ID card","both"),("driver-license","Driving license","rider"),("vehicle-registration","Vehicle registration","rider"),("vehicle-photo","Vehicle photo","rider"),("profile-photo","Driver profile photo","rider"),("bank-account","Bank account or passbook","both"),("ror-yor-17-18","Ror Yor 17 / Ror Yor 18","rider"),("power-of-attorney","Vehicle owner power of attorney","rider"),("relationship-proof","Proof of relationship to vehicle owner","rider"),("company-certificate","Company certificate","merchant"),("vat-certificate","VAT registration ( ภพ.20 )","merchant"),("shareholder-list","Shareholder list ( บอจ.5 )","merchant"),("director-id","Company director ID","merchant"),("business-bank-account","Business bank account","merchant"),("proof-of-address","Proof of residence or business address","merchant"),("foreign-work-permit","Thai work permit","merchant"),("foreign-business-certificate","Foreign business certificate","merchant")
    ]
    image_pdf=json.dumps(["image/jpeg","image/png","application/pdf"])
    for slug,name,subject in types:
        con.execute("INSERT OR IGNORE INTO document_types(id,slug,name,subject_type,allowed_mime_types,metadata) VALUES (?,?,?,?,?,?)", (f"document-type-{slug}",slug,name,subject,image_pdf,json.dumps({"retention":"operator_policy"})))
    def req(rid,provider,service,subject,doc,required,optional,order,source,merchant_type_id=None,vehicle_type_id=None,extra=None):
        metadata={"source":source,"source_confidence":"published"}|(extra or {})
        con.execute("INSERT OR IGNORE INTO provider_document_requirements(id,provider_id,service_id,subject_type,merchant_type_id,vehicle_type_id,document_type_id,country,effective_from,metadata,is_required,is_optional,display_order,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (rid,f"provider-{provider}",f"{provider}-{service}",subject,merchant_type_id,vehicle_type_id,f"document-type-{doc}","TH","2024-01-01",json.dumps(metadata,ensure_ascii=False),required,optional,order,now,now))
    rider_sets={
        "grab":["national-id","driver-license","vehicle-registration","vehicle-photo","profile-photo","bank-account"],
        "bolt":["national-id","driver-license","vehicle-registration","vehicle-photo","profile-photo"],
        "lalamove":["national-id","driver-license","vehicle-registration","vehicle-photo","profile-photo","bank-account"]
    }
    rider_sources={"grab":"https://www.grab.com/th/driver/drive/","bolt":"https://bolt.eu/th-th/support/articles/4406002078610/","lalamove":"https://www.lalamove.com/th-th/driver"}
    for provider,docs in rider_sets.items():
        for order,doc in enumerate(docs,1): req(f"{provider}-rider-{doc}",provider,"rider","rider",doc,1,0,order,rider_sources[provider])
    for order,doc in enumerate(["ror-yor-17-18","power-of-attorney","relationship-proof"],1):
        req(f"bolt-rider-optional-{doc}","bolt","rider","rider",doc,0,1,order+20,"https://bolt.eu/th-th/support/articles/4406002078610/")
    for merchant_type,docs in {"individual":["national-id","bank-account"],"company":["company-certificate","vat-certificate","shareholder-list","director-id","business-bank-account"]}.items():
        for order,doc in enumerate(docs,1):
            req(f"grab-merchant-{merchant_type}-{doc}","grab","merchant","merchant",doc,1,0,order,"https://www.grab.com/th/merchant/",merchant_type_id=f"merchant-type-{merchant_type}")
            con.execute("INSERT OR IGNORE INTO merchant_document_requirements(id,merchant_type_id,document_type_id,country,effective_from,metadata,is_required,is_optional,display_order,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (f"merchant-{merchant_type}-{doc}",f"merchant-type-{merchant_type}",f"document-type-{doc}","TH","2024-01-01",json.dumps({"source":"https://www.grab.com/th/merchant/","source_confidence":"published","provider_override":"grab"},ensure_ascii=False),1,0,order,now,now))

def config(con: sqlite3.Connection) -> dict:
    result = DEFAULT_SETTINGS | {row["key"]: json.loads(row["value"]) for row in con.execute("SELECT key,value FROM settings")}
    result["menu"] = [dict(row) | {"available": bool(row["available"])} for row in con.execute("SELECT m.id,m.name,m.description,m.price,m.available FROM menu_items m LEFT JOIN menu_display_order o ON o.menu_item_id=m.id ORDER BY COALESCE(o.position,9999),m.created_at")]
    return result

def provider_rows(con: sqlite3.Connection, slug: str | None = None):
    query="SELECT * FROM providers WHERE status='active'"; args=()
    if slug: query += " AND slug=?"; args=(slug,)
    return [dict(row) | {"metadata":json.loads(row["metadata"])} for row in con.execute(query+" ORDER BY name",args)]

def requirement_rows(con: sqlite3.Connection, provider_slug: str, subject: str, country: str, merchant_type: str = "", vehicle_type: str = ""):
    if subject not in {"rider","merchant"}: raise ValueError("ประเภทเอกสารไม่ถูกต้อง")
    params=[provider_slug,subject,country]
    query="""SELECT r.*,p.slug AS provider_slug,p.name AS provider_name,s.slug AS service_slug,
                    d.slug AS document_slug,d.name AS document_name,d.allowed_mime_types,d.max_size_bytes,
                    mt.slug AS merchant_type_slug,vt.slug AS vehicle_type_slug
             FROM provider_document_requirements r JOIN providers p ON p.id=r.provider_id
             LEFT JOIN provider_services s ON s.id=r.service_id JOIN document_types d ON d.id=r.document_type_id
             LEFT JOIN merchant_types mt ON mt.id=r.merchant_type_id LEFT JOIN vehicle_types vt ON vt.id=r.vehicle_type_id
             WHERE p.slug=? AND r.subject_type=? AND r.country=? AND r.status='active'
               AND datetime(r.effective_from)<=datetime('now')
               AND (r.effective_to='' OR datetime(r.effective_to)>datetime('now'))"""
    if merchant_type: query += " AND (mt.slug=? OR r.merchant_type_id IS NULL)"; params.append(merchant_type)
    if vehicle_type: query += " AND (vt.slug=? OR r.vehicle_type_id IS NULL)"; params.append(vehicle_type)
    rows=[]
    for row in con.execute(query+" ORDER BY r.display_order,r.id",params):
        item=dict(row); item["metadata"]=json.loads(item["metadata"]); item["allowed_mime_types"]=json.loads(item["allowed_mime_types"]); item["is_required"]=bool(item["is_required"]); item["is_optional"]=bool(item["is_optional"]); rows.append(item)
    return rows

def document_public(row):
    item=dict(row)
    for key in ("metadata",):
        try: item[key]=json.loads(item[key])
        except (TypeError,json.JSONDecodeError): item[key]={}
    item.pop("storage_path",None)
    return item

def document_cipher() -> Fernet:
    key=env("DOCUMENT_ENCRYPTION_KEY")
    if not key:raise ValueError("ยังไม่ได้ตั้งค่า DOCUMENT_ENCRYPTION_KEY")
    try:return Fernet(key.encode())
    except (TypeError,ValueError) as error:raise ValueError("DOCUMENT_ENCRYPTION_KEY ไม่ถูกต้อง") from error

def store_document(doc_id: str, raw: bytes) -> Path:
    root=DATA/"documents";root.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=root/f"{doc_id}.fernet";tmp=root/f".{doc_id}.{secrets.token_hex(4)}.tmp"
    try:
        tmp.write_bytes(document_cipher().encrypt(raw));os.chmod(tmp,0o600);os.replace(tmp,path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return path

def set_setting(con, key, value): con.execute("INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value, ensure_ascii=False)))
def audit(con, role, action, entity_type, entity_id, details=None): con.execute("INSERT INTO audit_logs(at,actor_role,action,entity_type,entity_id,details) VALUES (?,?,?,?,?,?)", (utcnow(), role, action, entity_type, entity_id, json.dumps(details or {}, ensure_ascii=False)))

def ensure_receipt_ledger(con: sqlite3.Connection) -> None:
    """Materialize a balanced posted journal for each issued receipt.

    Receipts are immutable snapshots, so this idempotent projection gives the
    ERP read model a stable double-entry record without changing checkout or
    tax-invoice behavior. Corrections must create a reviewed adjustment entry.
    """
    receipts = con.execute("SELECT * FROM pos_receipts ORDER BY issued_at, id").fetchall()
    for receipt in receipts:
        entry_id = f"JRN-{receipt['id']}"
        if con.execute("SELECT 1 FROM ledger_entries WHERE id=?", (entry_id,)).fetchone():
            continue
        total = int(receipt["total"])
        subtotal = int(receipt["subtotal"]) - int(receipt["discount"])
        delivery = int(receipt["delivery_fee"])
        if total <= 0 or subtotal < 0 or delivery < 0 or subtotal + delivery != total:
            raise ValueError("ใบเสร็จไม่สมดุล ไม่สามารถสร้างรายการบัญชีได้")
        created = str(receipt["issued_at"])
        con.execute(
            "INSERT INTO ledger_entries(id,entry_date,reference,journal,state,source_type,source_id,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (entry_id, created[:10], str(receipt["receipt_number"]), "Sales", "posted", "pos_receipt", str(receipt["id"]), created),
        )
        lines = [("1100", "เงินสด/เงินรับชำระ", total, 0)]
        if subtotal:
            lines.append(("4100", "รายได้จากการขาย", 0, subtotal))
        if delivery:
            lines.append(("4200", "รายได้ค่าจัดส่ง", 0, delivery))
        con.executemany(
            "INSERT INTO ledger_lines(entry_id,account_code,account_name,debit,credit) VALUES (?,?,?,?,?)",
            [(entry_id, *line) for line in lines],
        )

def ledger_entries_public(con: sqlite3.Connection) -> list[dict]:
    ensure_receipt_ledger(con)
    entries = []
    for entry in con.execute("SELECT * FROM ledger_entries ORDER BY entry_date DESC, id DESC"):
        lines = [dict(row) for row in con.execute("SELECT account_code,account_name,debit,credit FROM ledger_lines WHERE entry_id=? ORDER BY id", (entry["id"],))]
        debit = sum(int(line["debit"]) for line in lines)
        credit = sum(int(line["credit"]) for line in lines)
        entries.append({**dict(entry), "lines": lines, "total_debit": debit, "total_credit": credit, "balanced": debit == credit})
    return entries

def stock_moves_public(con: sqlite3.Connection) -> list[dict]:
    """Expose the existing inventory movement journal in ERP stock-move shape."""
    rows = con.execute(
        """SELECT m.id,m.inventory_item_id,m.delta,m.reason,m.order_id,m.note,
                  m.created_at,i.name AS product_name,i.unit
           FROM inventory_movements m
           JOIN inventory_items i ON i.id=m.inventory_item_id
           ORDER BY m.created_at DESC,m.id DESC LIMIT 500"""
    )
    moves = []
    for row in rows:
        delta = float(row["delta"])
        moves.append({
            "id": row["id"],
            "product_id": row["inventory_item_id"],
            "product_name": row["product_name"],
            "quantity": abs(delta),
            "uom": row["unit"],
            "source_location": "stock" if delta < 0 else "external",
            "destination_location": "consumption" if delta < 0 else "stock",
            "lot_number": None,
            "state": "done",
            "delta": delta,
            "reason": row["reason"],
            "order_id": row["order_id"],
            "note": row["note"],
            "created_at": row["created_at"],
        })
    return moves

def payment_public(row: dict) -> dict:
    return {key: row[key] for key in ("id", "provider", "provider_reference", "provider_order_id", "amount", "status", "qr_image", "qr_type", "expires_at", "created_at", "confirmed_at")}

def row_payment(con, payment_id: str) -> dict | None:
    row = con.execute("SELECT * FROM payment_attempts WHERE id=?", (payment_id,)).fetchone()
    return dict(row) if row else None

def active_payment(con, order_id: str) -> dict | None:
    row = con.execute("SELECT * FROM payment_attempts WHERE order_id=? AND provider='scb_maemanee' AND status IN ('created','pending') ORDER BY created_at DESC LIMIT 1", (order_id,)).fetchone()
    if not row: return None
    payment=dict(row)
    if payment["expires_at"]:
        try:
            if datetime.fromisoformat(payment["expires_at"]) <= datetime.now(timezone.utc):
                con.execute("UPDATE payment_attempts SET status='expired',updated_at=? WHERE id=? AND status IN ('created','pending')",(utcnow(),payment["id"]))
                return None
        except ValueError: return None
    return payment

def record_verified_scb_payment(
    con: sqlite3.Connection,
    payment: dict,
    response: dict,
    actor_role: str,
    confirmed_action: str,
    audit_details: dict | None = None,
) -> None:
    """Persist provider truth while keeping a cancelled order cancelled."""
    if payment["status"] not in {"created","pending"}:
        return
    order=con.execute(
        "SELECT status FROM orders WHERE id=?",
        (payment["order_id"],),
    ).fetchone()
    if not order:
        raise ValueError("ไม่พบออเดอร์ของ payment attempt")
    now=utcnow()
    updated=con.execute(
        """UPDATE payment_attempts
           SET status='paid',confirmed_at=?,updated_at=?,provider_response=?
           WHERE id=? AND status IN ('created','pending')""",
        (now,now,json.dumps(response,ensure_ascii=False),payment["id"]),
    )
    if updated.rowcount != 1:
        return
    details={"order_id":payment["order_id"],**(audit_details or {})}
    if order["status"]=="cancelled":
        audit(
            con,
            actor_role,
            "payment_received_cancelled_order",
            "payment_attempt",
            payment["id"],
            {**details,"requires_reconciliation":True},
        )
        return
    con.execute(
        "UPDATE orders SET payment_status='paid' WHERE id=? AND status!='cancelled'",
        (payment["order_id"],),
    )
    audit(
        con,
        actor_role,
        confirmed_action,
        "payment_attempt",
        payment["id"],
        details,
    )

def env(name: str, default="") -> str: return os.environ.get(name, default).strip()
def parse_bool(value, default=False) -> bool:
    if value is None: return default
    if isinstance(value,bool): return value
    if isinstance(value,(int,float)): return value != 0
    normalized=str(value).strip().lower()
    if normalized in {"true","1","yes","on"}: return True
    if normalized in {"false","0","no","off",""}: return False
    raise ValueError("ค่าบูลีนไม่ถูกต้อง")

def finite_float(value, error_message: str) -> float:
    try: result=float(value)
    except (TypeError,ValueError): raise ValueError(error_message)
    if not math.isfinite(result): raise ValueError(error_message)
    return result

def integer_value(value, error_message: str) -> int:
    if isinstance(value,bool):raise ValueError(error_message)
    if isinstance(value,int):return value
    if isinstance(value,float):
        if math.isfinite(value) and value.is_integer():return int(value)
        raise ValueError(error_message)
    if isinstance(value,str) and re.fullmatch(r"[+-]?\d+",value.strip()):
        return int(value)
    raise ValueError(error_message)

def optional_utc_timestamp(value, error_message: str) -> str:
    raw=str(value or "").strip()
    if not raw:return ""
    try: parsed=datetime.fromisoformat(raw.replace("Z","+00:00"))
    except ValueError:raise ValueError(error_message)
    if parsed.tzinfo is None:raise ValueError(error_message)
    return parsed.astimezone(timezone.utc).isoformat()

def hf_enabled() -> bool:
    return env("HF_ENABLED", "false").lower() == "true" and bool(env("HF_TOKEN"))

def hf_router_base() -> str:
    """Return the fixed Hugging Face router base; never use this as a user URL."""
    base=env("HF_ROUTER_BASE_URL", HF_ROUTER_DEFAULT).rstrip("/")
    parsed=urlparse(base)
    if parsed.scheme != "https" or parsed.hostname != "router.huggingface.co" or parsed.path != "/v1":
        raise ValueError("HF_ROUTER_BASE_URL ต้องเป็น https://router.huggingface.co/v1")
    return base

def hf_public_config() -> dict:
    return {"enabled":hf_enabled(),"provider":"huggingface","catalog":"router","chat_only":True,"token_configured":bool(env("HF_TOKEN"))}

def ai_provider_keys() -> dict[str,str]:
    """Read only named AI provider credentials from the local ignored environment."""
    raw=env("AI_PROVIDER_KEYS_JSON")
    if not raw: return {}
    try: parsed=json.loads(raw)
    except json.JSONDecodeError: return {}
    if not isinstance(parsed,dict): return {}
    disabled={
        name.strip().lower()
        for name in env("AI_DISABLED_PROVIDERS").split(",")
        if name.strip().lower() in AI_PROVIDER_NAMES
    }
    return {
        name:value.strip()
        for name,value in parsed.items()
        if name in AI_PROVIDER_NAMES
        and name not in disabled
        and isinstance(value,str)
        and value.strip()
        and not value.startswith("replace-with-")
    }

def local_ai_base() -> str:
    base=env("LOCAL_AI_BASE_URL").rstrip("/")
    if not base: return ""
    parsed=urlparse(base)
    if parsed.query or parsed.fragment or parsed.username or parsed.password or not parsed.hostname:
        raise ValueError("LOCAL_AI_BASE_URL ไม่ถูกต้อง")
    if parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname.lower() in ZEAZ_GATEWAY_LOOPBACK_HOSTS): return base
    raise ValueError("LOCAL_AI_BASE_URL ต้องเป็น HTTPS หรือ HTTP บน loopback เท่านั้น")

def zeaz_gateway_config() -> tuple[str,str] | None:
    """Return the explicitly configured, server-only ZeaZ gateway endpoint.

    The gateway is an optional consolidation layer for the operator AI console.
    It is not a browser proxy: its endpoint and credential come only from the
    ignored service environment.  Plain HTTP is restricted to loopback so an
    operator cannot accidentally send the gateway client key over a network.
    """
    base,token=env("ZEAZ_AI_GATEWAY_URL").rstrip("/"),env("AI_GATEWAY_PROVIDER_TOKEN")
    # AI_GATEWAY_PROVIDER_TOKEN existed before this optional integration as a
    # vault field.  Treat it as inactive until an explicit gateway URL is set.
    if not base: return None
    if not token: raise ValueError("ZEAZ gateway ต้องตั้งค่า URL และ client key ให้ครบ")
    parsed=urlparse(base)
    if parsed.query or parsed.fragment or parsed.username or parsed.password or not parsed.hostname:
        raise ValueError("ZEAZ gateway URL ไม่ถูกต้อง")
    if parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname.lower() in ZEAZ_GATEWAY_LOOPBACK_HOSTS):
        return base,token
    raise ValueError("ZEAZ gateway ต้องใช้ HTTPS หรือ HTTP บน loopback เท่านั้น")

def ai_public_config() -> dict:
    keys=ai_provider_keys()
    try: gateway=bool(zeaz_gateway_config())
    except ValueError: gateway=False
    try: local=bool(local_ai_base())
    except ValueError: local=False
    return {"enabled":bool(keys) or hf_enabled() or gateway or local,"providers":{name:bool(keys.get(name)) for name in ("gemini","nvidia","zai","opencode","openrouter","groq","byteplus","fireworks","openai","kimi","scaleway","together","github","cerebras")}|{"local":local,"huggingface":hf_enabled(),"zeaz_gateway":gateway},"catalog":"live","chat_only":True,"fallback":True}

def ai_http(endpoint: str, headers: dict[str,str], payload: dict | None = None, allow_list=False) -> dict | list:
    """Call a fixed provider endpoint without exposing credentials or acting as a proxy."""
    try:
        # Several provider gateways reject urllib's default user agent. Keep a
        # fixed server identity; it is not supplied by, or controllable from,
        # the browser request.
        request_headers={"Accept":"application/json","User-Agent":"MooPiew-ZEAZ/1.0",**headers}
        body=None
        if payload is not None:
            request_headers["Content-Type"]="application/json"; body=json.dumps(payload,ensure_ascii=False).encode()
        with urlopen(Request(endpoint,data=body,headers=request_headers,method="POST" if payload is not None else "GET"),timeout=30) as response:
            raw=response.read(2_000_000)
    except HTTPError as error: raise ValueError(f"AI provider ปฏิเสธคำขอ ({error.code})") from error
    except (URLError,OSError) as error: raise ValueError("ไม่สามารถเชื่อมต่อ AI provider ได้") from error
    try: data=json.loads(raw.decode())
    except (UnicodeDecodeError,json.JSONDecodeError) as error: raise ValueError("AI provider ตอบกลับไม่ใช่ JSON") from error
    if not isinstance(data,dict) and not (allow_list and isinstance(data,list)): raise ValueError("AI provider ตอบกลับไม่ถูกต้อง")
    return data

def gemini_models(token: str) -> list[dict]:
    rows=[]; page_token=""
    while True:
        suffix="?pageSize=1000" + (f"&pageToken={quote(page_token)}" if page_token else "")
        data=ai_http(f"{GEMINI_MODELS_URL}{suffix}",{"x-goog-api-key":token})
        for model in data.get("models",[]):
            if not isinstance(model,dict) or not isinstance(model.get("name"),str): continue
            identifier=model["name"].removeprefix("models/")
            if "generateContent" in model.get("supportedGenerationMethods",[]) and HF_MODEL_ID.fullmatch(f"google/{identifier}"):
                rows.append({"id":f"gemini:{identifier}","provider":"gemini","model":identifier,"display_name":model.get("displayName",identifier)})
        page_token=data.get("nextPageToken","")
        if not isinstance(page_token,str) or not page_token: break
    return rows

def nvidia_models(token: str) -> list[dict]:
    data=ai_http(f"{NVIDIA_API_BASE}/models",{"Authorization":f"Bearer {token}"})
    rows=[]
    for model in data.get("data",[]):
        if not isinstance(model,dict) or not isinstance(model.get("id"),str) or not PROVIDER_MODEL_ID.fullmatch(model["id"]): continue
        rows.append({"id":f"nvidia:{model['id']}","provider":"nvidia","model":model["id"],"display_name":model["id"]})
    return rows

def zai_models(token: str) -> list[dict]:
    data=ai_http(f"{ZAI_API_BASE}/models",{"Authorization":f"Bearer {token}"})
    rows=[]
    for model in data.get("data",[]):
        if not isinstance(model,dict) or not isinstance(model.get("id"),str): continue
        identifier=model["id"]
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*",identifier): rows.append({"id":f"zai:{identifier}","provider":"zai","model":identifier,"display_name":identifier})
    return rows

def zero_pricing(value) -> bool:
    """Accept only a provider model whose declared input/output pricing is zero."""
    if not isinstance(value,dict): return False
    prices=[value[key] for key in ("prompt","completion","input","output") if key in value]
    if not prices: return False
    try: return all(float(price) == 0 for price in prices)
    except (TypeError,ValueError): return False

def openrouter_models(token: str) -> list[dict]:
    data=ai_http(f"{OPENROUTER_API_BASE}/models",{"Authorization":f"Bearer {token}"})
    rows=[]
    for model in data.get("data",[]):
        if not isinstance(model,dict) or not isinstance(model.get("id"),str) or not HF_MODEL_ID.fullmatch(model["id"]): continue
        if not zero_pricing(model.get("pricing")): continue
        rows.append({"id":f"openrouter:{model['id']}","provider":"openrouter","model":model["id"],"display_name":model.get("name",model["id"]),"free":True})
    return rows

def opencode_models(token: str) -> list[dict]:
    data=ai_http(f"{OPENCODE_API_BASE}/models",{"Authorization":f"Bearer {token}"})
    source=data.get("data",data.get("models",[])); rows=[]
    for model in source if isinstance(source,list) else []:
        if not isinstance(model,dict) or not isinstance(model.get("id"),str): continue
        identifier=model["id"].removeprefix("opencode/")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*",identifier): continue
        if not (identifier.endswith("-free") or zero_pricing(model.get("pricing"))): continue
        rows.append({"id":f"opencode:{identifier}","provider":"opencode","model":identifier,"display_name":model.get("name",identifier),"free":True})
    return rows

def groq_models(token: str) -> list[dict]:
    """List models available to the configured Groq project.

    Groq publishes Free Plan rate limits per model. The API does not expose the
    account's billing tier, so this marks availability under the Free Plan—not
    a permanent, account-independent zero-price guarantee.
    """
    data=ai_http(f"{GROQ_API_BASE}/models",{"Authorization":f"Bearer {token}"})
    rows=[]
    for model in data.get("data",[]):
        if not isinstance(model,dict) or not isinstance(model.get("id"),str) or not PROVIDER_MODEL_ID.fullmatch(model["id"]): continue
        if model.get("active") is False: continue
        identifier=model["id"]
        rows.append({"id":f"groq:{identifier}","provider":"groq","model":identifier,"display_name":identifier,"free":True,"free_tier":True})
    return rows

def byteplus_models(token: str) -> list[dict]:
    """List models accessible to the configured BytePlus ModelArk project."""
    data=ai_http(f"{BYTEPLUS_API_BASE}/models",{"Authorization":f"Bearer {token}"})
    rows=[]
    for model in data.get("data",[]):
        if not isinstance(model,dict) or not isinstance(model.get("id"),str) or not PROVIDER_MODEL_ID.fullmatch(model["id"]): continue
        rows.append({"id":f"byteplus:{model['id']}","provider":"byteplus","model":model["id"],"display_name":model.get("name",model["id"])})
    return rows

def openai_compatible_models(base: str, token: str, provider: str) -> list[dict]:
    """List models from a fixed OpenAI-compatible provider endpoint."""
    headers={"Authorization":f"Bearer {token}"} if token else {}
    data=ai_http(f"{base}/models",headers,allow_list=True)
    source=data if isinstance(data,list) else data.get("data",[])
    rows=[]
    for model in source:
        if not isinstance(model,dict) or not isinstance(model.get("id"),str) or not PROVIDER_MODEL_ID.fullmatch(model["id"]): continue
        rows.append({"id":f"{provider}:{model['id']}","provider":provider,"model":model["id"],"display_name":model.get("name",model["id"])})
    return rows

def fireworks_models(token: str) -> list[dict]: return openai_compatible_models(FIREWORKS_API_BASE,token,"fireworks")
def openai_models(token: str) -> list[dict]: return openai_compatible_models(OPENAI_API_BASE,token,"openai")
def kimi_models(token: str) -> list[dict]: return openai_compatible_models(KIMI_API_BASE,token,"kimi")
def scaleway_models(token: str) -> list[dict]: return openai_compatible_models(SCALEWAY_API_BASE,token,"scaleway")
def together_models(token: str) -> list[dict]: return openai_compatible_models(TOGETHER_API_BASE,token,"together")
def github_models(token: str) -> list[dict]:
    data=ai_http(f"{GITHUB_MODELS_API_BASE}/catalog/models",{"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"},allow_list=True)
    source=data if isinstance(data,list) else data.get("data",[]); rows=[]
    for model in source:
        if isinstance(model,dict) and isinstance(model.get("id"),str) and PROVIDER_MODEL_ID.fullmatch(model["id"]): rows.append({"id":f"github:{model['id']}","provider":"github","model":model["id"],"display_name":model.get("name",model["id"]),"free_tier":True})
    return rows
def cerebras_models(token: str) -> list[dict]: return [{**item,"free_tier":True} for item in openai_compatible_models(CEREBRAS_API_BASE,token,"cerebras")]
def local_models(base: str) -> list[dict]:
    listed=openai_compatible_models(base,env("LOCAL_AI_API_KEY"),"local")
    configured=env("LOCAL_AI_MODEL")
    if configured and PROVIDER_MODEL_ID.fullmatch(configured) and not any(row["model"] == configured for row in listed):
        listed.insert(0,{"id":f"local:{configured}","provider":"local","model":configured,"display_name":configured,"free":True})
    return listed

def zeaz_gateway_models(base: str, token: str) -> list[dict]:
    data=ai_http(f"{base}/models",{"Authorization":f"Bearer {token}"})
    rows=[]
    for model in data.get("data",[]):
        if not isinstance(model,dict) or not isinstance(model.get("id"),str) or not PROVIDER_MODEL_ID.fullmatch(model["id"]): continue
        identifier=model["id"]
        rows.append({"id":f"zeaz_gateway:{identifier}","provider":"zeaz_gateway","model":identifier,"display_name":model.get("name",identifier)})
    return rows

def ai_catalog() -> dict:
    """Return every live chat model the configured provider keys can enumerate."""
    now=time.monotonic()
    with AI_MODEL_LOCK:
        cached=AI_MODEL_CACHE.get("catalog",{})
        if isinstance(cached,dict) and cached and float(AI_MODEL_CACHE.get("expires",0)) > now: return cached
        keys=ai_provider_keys(); providers={}; models=[]
        try:
            base=local_ai_base()
            if base:
                listed=local_models(base); models.extend(listed); providers["local"]={"enabled":True,"models":len(listed)}
        except ValueError as error: providers["local"]={"enabled":False,"models":0,"error":str(error)}
        for name, loader in (("zai",zai_models),("kimi",kimi_models),("scaleway",scaleway_models),("together",together_models),("github",github_models),("openrouter",openrouter_models),("opencode",opencode_models),("groq",groq_models),("cerebras",cerebras_models),("gemini",gemini_models),("nvidia",nvidia_models),("byteplus",byteplus_models),("fireworks",fireworks_models),("openai",openai_models)):
            if not keys.get(name): providers[name]={"enabled":False,"models":0}; continue
            try:
                listed=loader(keys[name]); models.extend(listed); providers[name]={"enabled":True,"models":len(listed)}
            except ValueError as error: providers[name]={"enabled":False,"models":0,"error":str(error)}
        try:
            gateway=zeaz_gateway_config()
            if gateway:
                listed=zeaz_gateway_models(*gateway); models.extend(listed); providers["zeaz_gateway"]={"enabled":True,"models":len(listed)}
        except ValueError as error: providers["zeaz_gateway"]={"enabled":False,"models":0,"error":str(error)}
        if hf_enabled():
            try:
                listed=[{"id":f"huggingface:{item['id']}","provider":"huggingface","model":item["id"],"display_name":item["id"]} for item in hf_models()]
                models.extend(listed); providers["huggingface"]={"enabled":True,"models":len(listed)}
            except ValueError as error: providers["huggingface"]={"enabled":False,"models":0,"error":str(error)}
        models.sort(key=lambda item:(AI_PROVIDER_PRIORITY.index(item["provider"]) if item["provider"] in AI_PROVIDER_PRIORITY else 999,item["model"].casefold()))
        catalog={"models":models,"providers":providers}
        if not models: raise ValueError("ไม่พบ AI model ที่ใช้งานได้จาก provider keys ที่ตั้งค่าไว้")
        AI_MODEL_CACHE.update(catalog=catalog,expires=now+max(30,min(3600,int(env("AI_MODEL_CATALOG_TTL",env("HF_MODEL_CATALOG_TTL","300")) or 300))))
        return catalog

def gemini_chat(token: str, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
    data=ai_http(f"{GEMINI_MODELS_URL}/{quote(model,safe='-._')}:generateContent",{"x-goog-api-key":token},{"systemInstruction":{"parts":[{"text":AI_SYSTEM_PROMPT}]},"contents":[{"role":"user","parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":max_tokens,"temperature":temperature}})
    candidates=data.get("candidates",[]); content=candidates[0].get("content",{}) if isinstance(candidates,list) and candidates and isinstance(candidates[0],dict) else {}
    parts=content.get("parts",[]) if isinstance(content,dict) else []
    text="".join(part.get("text","") for part in parts if isinstance(part,dict) and isinstance(part.get("text"),str))
    if not text: raise ValueError("Gemini model ไม่ได้ส่งข้อความตอบกลับ")
    return text

def nvidia_chat(token: str, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
    data=ai_http(f"{NVIDIA_API_BASE}/chat/completions",{"Authorization":f"Bearer {token}"},{"model":model,"messages":[{"role":"system","content":AI_SYSTEM_PROMPT},{"role":"user","content":prompt}],"max_tokens":max_tokens,"temperature":temperature,"stream":False})
    choices=data.get("choices",[]); message=choices[0].get("message",{}) if isinstance(choices,list) and choices and isinstance(choices[0],dict) else {}; text=message.get("content") if isinstance(message,dict) else ""
    if not isinstance(text,str) or not text: raise ValueError("NVIDIA model ไม่ได้ส่งข้อความตอบกลับ")
    return text

def zai_chat(token: str, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
    data=ai_http(f"{ZAI_API_BASE}/chat/completions",{"Authorization":f"Bearer {token}"},{"model":model,"messages":[{"role":"system","content":AI_SYSTEM_PROMPT},{"role":"user","content":prompt}],"max_tokens":max_tokens,"temperature":temperature,"stream":False})
    choices=data.get("choices",[]); message=choices[0].get("message",{}) if isinstance(choices,list) and choices and isinstance(choices[0],dict) else {}; text=message.get("content") if isinstance(message,dict) else ""
    if not isinstance(text,str) or not text: raise ValueError("Z.AI model ไม่ได้ส่งข้อความตอบกลับ")
    return text

def openai_compatible_chat(base: str, token: str, model: str, prompt: str, max_tokens: int, temperature: float, provider: str) -> str:
    headers={"Authorization":f"Bearer {token}"} if token else {}
    data=ai_http(f"{base}/chat/completions",headers,{"model":model,"messages":[{"role":"system","content":AI_SYSTEM_PROMPT},{"role":"user","content":prompt}],"max_tokens":max_tokens,"temperature":temperature,"stream":False})
    choices=data.get("choices",[]); message=choices[0].get("message",{}) if isinstance(choices,list) and choices and isinstance(choices[0],dict) else {}; text=message.get("content") if isinstance(message,dict) else ""
    if not isinstance(text,str) or not text: raise ValueError(f"{provider} model ไม่ได้ส่งข้อความตอบกลับ")
    return text

def ai_chat(model_id: str, prompt: str, max_tokens=512, temperature=0.2) -> dict:
    if not isinstance(model_id,str) or ":" not in model_id: raise ValueError("ชื่อ AI model ไม่ถูกต้อง")
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>12_000: raise ValueError("ข้อความ AI ต้องมี 1–12,000 ตัวอักษร")
    try: tokens=max(1,min(2048,int(max_tokens))); temp=max(0,min(2,float(temperature)))
    except (TypeError,ValueError) as error: raise ValueError("พารามิเตอร์ AI ไม่ถูกต้อง") from error
    catalog=ai_catalog(); selected=next((item for item in catalog["models"] if item["id"] == model_id),None)
    if not selected: raise ValueError("โมเดลนี้ไม่อยู่ใน live AI catalog")
    keys=ai_provider_keys()
    def invoke(item):
        provider,model=item["provider"],item["model"]
        if provider=="local": return openai_compatible_chat(local_ai_base(),env("LOCAL_AI_API_KEY"),model,prompt.strip(),tokens,temp,"Local AI")
        if provider=="gemini": return gemini_chat(keys["gemini"],model,prompt.strip(),tokens,temp)
        if provider=="nvidia": return nvidia_chat(keys["nvidia"],model,prompt.strip(),tokens,temp)
        if provider=="zai": return zai_chat(keys["zai"],model,prompt.strip(),tokens,temp)
        bases={"opencode":(OPENCODE_API_BASE,"OpenCode"),"openrouter":(OPENROUTER_API_BASE,"OpenRouter"),"groq":(GROQ_API_BASE,"Groq"),"byteplus":(BYTEPLUS_API_BASE,"BytePlus"),"fireworks":(FIREWORKS_API_BASE,"Fireworks"),"openai":(OPENAI_API_BASE,"OpenAI"),"kimi":(KIMI_API_BASE,"Kimi"),"scaleway":(SCALEWAY_API_BASE,"Scaleway"),"together":(TOGETHER_API_BASE,"Together AI"),"github":(GITHUB_MODELS_API_BASE,"GitHub Models"),"cerebras":(CEREBRAS_API_BASE,"Cerebras")}
        if provider=="github":
            data=ai_http(f"{GITHUB_MODELS_API_BASE}/inference/chat/completions",{"Authorization":f"Bearer {keys[provider]}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"},{"model":model,"messages":[{"role":"system","content":AI_SYSTEM_PROMPT},{"role":"user","content":prompt.strip()}],"max_tokens":tokens,"temperature":temp,"stream":False})
            choices=data.get("choices",[]); content=choices[0].get("message",{}).get("content","") if choices else ""
            if not isinstance(content,str) or not content: raise ValueError("GitHub Models ไม่ได้ส่งข้อความตอบกลับ")
            return content
        if provider in bases: return openai_compatible_chat(bases[provider][0],keys[provider],model,prompt.strip(),tokens,temp,bases[provider][1])
        if provider=="zeaz_gateway":
            gateway=zeaz_gateway_config()
            if not gateway: raise ValueError("ZEAZ gateway ยังไม่ได้ตั้งค่า")
            return openai_compatible_chat(*gateway,model,prompt.strip(),tokens,temp,"ZEAZ Gateway")
        if provider=="huggingface": return hf_chat(model,prompt.strip(),tokens,temp)["content"]
        raise ValueError("AI provider ไม่รองรับ")
    free_providers={"local","github","cerebras","groq","huggingface"}
    candidates=[selected]+[item for item in catalog["models"] if item["id"] != model_id and (item.get("free") is True or item.get("free_tier") is True or item["provider"] in free_providers)]
    try: fallback_limit=max(1,min(8,int(env("AI_FALLBACK_MAX_ATTEMPTS","3"))))
    except ValueError: fallback_limit=3
    candidates=candidates[:fallback_limit]
    failures=[]
    for item in candidates:
        try:
            text=invoke(item)
            return {"id":item["id"],"requested_id":model_id,"provider":item["provider"],"model":item["model"],"content":text,"fallback":item["id"] != model_id}
        except (ValueError, HTTPError, URLError, OSError):
            failures.append(item["provider"])
    raise ValueError("AI ไม่มี provider ที่ตอบกลับได้: " + ", ".join(dict.fromkeys(failures)))

def hf_request(path: str, payload: dict | None = None) -> dict:
    """Call the official HF Router with a server-only token and bounded body."""
    if not hf_enabled(): raise ValueError("Hugging Face AI ยังไม่เปิดใช้ หรือยังไม่ได้ตั้งค่า HF_TOKEN")
    token=env("HF_TOKEN")
    headers={"Authorization":f"Bearer {token}","Accept":"application/json"}
    data=None
    if payload is not None:
        headers["Content-Type"]="application/json"; data=json.dumps(payload,ensure_ascii=False).encode()
    try:
        with urlopen(Request(f"{hf_router_base()}{path}",data=data,headers=headers,method="POST" if payload is not None else "GET"),timeout=30) as response:
            raw=response.read(2_000_000)
    except HTTPError as error:
        # Provider messages can contain account or policy details; keep them out
        # of browser responses while retaining the status for the operator.
        raise ValueError(f"Hugging Face Router ปฏิเสธคำขอ ({error.code})") from error
    except (URLError,OSError) as error:
        raise ValueError("ไม่สามารถเชื่อมต่อ Hugging Face Router ได้") from error
    try: result=json.loads(raw.decode())
    except (UnicodeDecodeError,json.JSONDecodeError) as error: raise ValueError("Hugging Face Router ตอบกลับไม่ใช่ JSON") from error
    if not isinstance(result,dict): raise ValueError("Hugging Face Router ตอบกลับไม่ถูกต้อง")
    return result

def hf_models() -> list[dict]:
    """Discover every chat model currently exposed to this token by the router."""
    now=time.monotonic()
    with HF_MODEL_LOCK:
        cached=HF_MODEL_CACHE.get("models",[])
        if isinstance(cached,list) and float(HF_MODEL_CACHE.get("expires",0)) > now: return cached
        data=hf_request("/models")
        rows=data.get("data",[])
        if not isinstance(rows,list): raise ValueError("Hugging Face Router ไม่ส่งรายการโมเดล")
        models=[]
        for row in rows:
            if not isinstance(row,dict) or not isinstance(row.get("id"),str) or not HF_MODEL_ID.fullmatch(row["id"]): continue
            models.append({key:row[key] for key in ("id","object","owned_by","created") if key in row})
        models.sort(key=lambda item:item["id"].casefold())
        HF_MODEL_CACHE.update(models=models,expires=now+max(30,min(3600,int(env("HF_MODEL_CATALOG_TTL", "300") or 300))))
        return models

def hf_chat(model: str, prompt: str, max_tokens=512, temperature=0.2) -> dict:
    if not isinstance(model,str) or not HF_MODEL_ID.fullmatch(model): raise ValueError("ชื่อ Hugging Face model ไม่ถูกต้อง")
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>12_000: raise ValueError("ข้อความ AI ต้องมี 1–12,000 ตัวอักษร")
    try: tokens=max(1,min(2048,int(max_tokens))); temp=max(0,min(2,float(temperature)))
    except (TypeError,ValueError) as error: raise ValueError("พารามิเตอร์ AI ไม่ถูกต้อง") from error
    available={item["id"] for item in hf_models()}
    if model not in available: raise ValueError("โมเดลนี้ไม่อยู่ใน Hugging Face Router catalog สำหรับ token นี้")
    response=hf_request("/chat/completions",{"model":model,"messages":[{"role":"system","content":"You are MooPiew's operator assistant. Do not request or reveal secrets, payment credentials, or customer personal data. Answer concisely in the language used by the operator."},{"role":"user","content":prompt.strip()}],"max_tokens":tokens,"temperature":temp})
    choices=response.get("choices",[])
    message=choices[0].get("message",{}) if isinstance(choices,list) and choices and isinstance(choices[0],dict) else {}
    content=message.get("content") if isinstance(message,dict) else None
    if not isinstance(content,str): raise ValueError("Hugging Face model ไม่ได้ส่งข้อความตอบกลับ")
    return {"model":model,"content":content,"usage":response.get("usage",{}) if isinstance(response.get("usage",{}),dict) else {}}
def scb_feature_enabled(feature: str, default="false") -> bool:
    products={item.strip() for item in env("SCB_ENABLED_PRODUCTS", "maemanee_qr").split(",") if item.strip()}
    return feature in products and env(f"SCB_{feature.upper()}_ENABLED",default).lower()=="true"
def scb_active() -> bool:
    # Existing deployments did not have the feature-gate variable. Preserve
    # their qr_api behaviour until the reviewed .env.payment template is adopted.
    return PAYMENTS_ENABLED and SCB_ENABLED and env("SCB_PRODUCT") == "qr_api" and scb_feature_enabled("maemanee_qr", "true")
def scb_config_public() -> dict: return {"enabled":scb_active(), "provider":"scb_maemanee", "method":"scb_qr", "payment_types":[value for value in env("SCB_QR_PAYMENT_TYPES", "T30").split(",") if value], "environment":env("PAYMENT_ENVIRONMENT", "sandbox")}

def iso_millis() -> str: return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def scb_cipher() -> Fernet:
    key=env("SCB_TOKEN_ENCRYPTION_KEY")
    if not key: raise ValueError("ยังไม่ได้ตั้งค่า SCB_TOKEN_ENCRYPTION_KEY")
    try: return Fernet(key.encode())
    except (ValueError, TypeError) as error: raise ValueError("SCB_TOKEN_ENCRYPTION_KEY ไม่ถูกต้อง") from error

def scb_ssl_context() -> ssl.SSLContext | None:
    """Load SCB mTLS credentials only from local, ignored files."""
    required=env("SCB_MTLS_REQUIRED", "false").lower()=="true"
    certificate,key=env("SCB_CLIENT_CERT_FILE"),env("SCB_CLIENT_KEY_FILE")
    if not required: return None
    if not certificate and not key: raise ValueError("ยังไม่ได้ตั้งค่า SCB client certificate และ private key")
    if not certificate or not key: raise ValueError("SCB mTLS configuration ไม่ครบ")
    cert_path=Path(certificate) if Path(certificate).is_absolute() else ROOT / certificate
    key_path=Path(key) if Path(key).is_absolute() else ROOT / key
    if not cert_path.is_file() or not key_path.is_file(): raise ValueError("ไม่พบไฟล์ SCB client certificate หรือ private key")
    try:
        context=ssl.create_default_context(); context.load_cert_chain(str(cert_path),str(key_path)); return context
    except ssl.SSLError as error: raise ValueError("SCB client certificate หรือ private key ไม่ถูกต้อง") from error

def scb_urlopen(request: Request): return urlopen(request, timeout=15, context=scb_ssl_context())

def scb_store_token(access_token: str, refresh_token: str, owner: str, expires_in=1800, refresh_expires_in=3600) -> None:
    cipher=scb_cipher(); now=datetime.now(timezone.utc)
    access_until=now+timedelta(seconds=max(60,int(expires_in or 1800))); refresh_until=now+timedelta(seconds=max(60,int(refresh_expires_in or 3600)))
    encrypted=lambda value:cipher.encrypt(value.encode()).decode()
    with db() as con: con.execute("INSERT INTO oauth_tokens(subject,access_cipher,refresh_cipher,owner_cipher,access_expires_at,refresh_expires_at,updated_at) VALUES ('scb_merchant',?,?,?,?,?,?) ON CONFLICT(subject) DO UPDATE SET access_cipher=excluded.access_cipher,refresh_cipher=excluded.refresh_cipher,owner_cipher=excluded.owner_cipher,access_expires_at=excluded.access_expires_at,refresh_expires_at=excluded.refresh_expires_at,updated_at=excluded.updated_at",(encrypted(access_token),encrypted(refresh_token) if refresh_token else "",encrypted(owner),access_until.isoformat(),refresh_until.isoformat() if refresh_token else "",utcnow()))
    SCB_TOKEN_CACHE.update(token=access_token,owner=owner,expires=time.monotonic()+max(60,int(expires_in or 1800)-60))

def scb_saved_token() -> tuple[str, str] | None:
    with db() as con: row=con.execute("SELECT * FROM oauth_tokens WHERE subject='scb_merchant'").fetchone()
    if not row or datetime.fromisoformat(row["access_expires_at"]) <= datetime.now(timezone.utc)+timedelta(seconds=60): return None
    try:
        cipher=scb_cipher(); return cipher.decrypt(row["access_cipher"].encode()).decode(),cipher.decrypt(row["owner_cipher"].encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as error: raise ValueError("ไม่สามารถอ่าน SCB token ที่เข้ารหัสไว้ได้") from error

def scb_token_response(data: dict, headers: dict) -> tuple[str, str, str, int, int]:
    body=data.get("data",data) if isinstance(data,dict) else {}
    token=body.get("accessToken") or data.get("accessToken"); refresh=body.get("refreshToken") or data.get("refreshToken") or ""
    owner=headers.get("resourceownerid") or body.get("resourceOwnerId") or data.get("resourceOwnerId") or env("SCB_API_KEY")
    if not isinstance(token,str) or not token: raise ValueError("SCB OAuth ไม่ได้ส่ง access token")
    return token, str(refresh), str(owner), int(body.get("expiresIn",data.get("expiresIn",1800)) or 1800), int(body.get("refreshExpiresIn",data.get("refreshExpiresIn",3600)) or 3600)

def scb_exchange_auth_code(code: str, verifier: str = "") -> None:
    key,secret,endpoint=env("SCB_API_KEY"),env("SCB_API_SECRET"),env("SCB_OAUTH_TOKEN_ENDPOINT")
    if not key or not secret or not endpoint: raise ValueError("ยังไม่ได้ตั้งค่า SCB OAuth credentials")
    payload={"applicationKey":key,"applicationSecret":secret,"authCode":code}
    if verifier:
        field=env("SCB_OAUTH_PKCE_TOKEN_FIELD","codeVerifier")
        if field not in {"codeVerifier","code_verifier"}: raise ValueError("SCB OAuth PKCE token field ไม่ถูกต้อง")
        payload[field]=verifier
    data,headers=scb_http(endpoint,payload,{"resourceOwnerId":key,"accept-language":"EN"})
    scb_store_token(*scb_token_response(data,headers))

def scb_refresh_saved_token() -> tuple[str,str] | None:
    with db() as con: row=con.execute("SELECT * FROM oauth_tokens WHERE subject='scb_merchant'").fetchone()
    if not row or not row["refresh_cipher"] or not row["refresh_expires_at"] or datetime.fromisoformat(row["refresh_expires_at"]) <= datetime.now(timezone.utc)+timedelta(seconds=60): return None
    try: refresh=scb_cipher().decrypt(row["refresh_cipher"].encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as error: raise ValueError("ไม่สามารถอ่าน SCB refresh token ที่เข้ารหัสไว้ได้") from error
    key,secret,endpoint=env("SCB_API_KEY"),env("SCB_API_SECRET"),env("SCB_OAUTH_REFRESH_ENDPOINT")
    if not key or not secret or not endpoint: return None
    data,headers=scb_http(endpoint,{"applicationKey":key,"applicationSecret":secret,"refreshToken":refresh},{"resourceOwnerId":key,"accept-language":"EN"})
    scb_store_token(*scb_token_response(data,headers)); return scb_saved_token()

def scb_token() -> tuple[str, str]:
    """Return the merchant-payment token; profile consent is kept separate."""
    now=time.monotonic()
    with SCB_TOKEN_LOCK:
        mode=env("SCB_PAYMENT_OAUTH_MODE", "client_credentials")
        if mode == "client_credentials":
            if SCB_SERVICE_TOKEN_CACHE.get("token") and float(SCB_SERVICE_TOKEN_CACHE.get("expires", 0)) > now:
                return str(SCB_SERVICE_TOKEN_CACHE["token"]), str(SCB_SERVICE_TOKEN_CACHE["owner"])
            key, secret, endpoint=env("SCB_API_KEY"),env("SCB_API_SECRET"),env("SCB_OAUTH_TOKEN_ENDPOINT")
            if not key or not secret or not endpoint: raise ValueError("ยังไม่ได้ตั้งค่า SCB merchant OAuth credentials")
            data,headers=scb_http(endpoint,{"applicationKey":key,"applicationSecret":secret},{"resourceOwnerId":key,"accept-language":"EN"})
            token,_,owner,expires,_=scb_token_response(data,headers)
            SCB_SERVICE_TOKEN_CACHE.update(token=token,owner=owner,expires=now+max(60,expires-60))
            return token,owner
        if mode != "authorization_code": raise ValueError("SCB_PAYMENT_OAUTH_MODE ต้องเป็น client_credentials หรือ authorization_code")
        if SCB_TOKEN_CACHE.get("token") and float(SCB_TOKEN_CACHE.get("expires", 0)) > now:
            return str(SCB_TOKEN_CACHE["token"]), str(SCB_TOKEN_CACHE["owner"])
        saved=scb_saved_token()
        if saved:
            SCB_TOKEN_CACHE.update(token=saved[0],owner=saved[1],expires=now+600); return saved
        refreshed=scb_refresh_saved_token()
        if refreshed:
            SCB_TOKEN_CACHE.update(token=refreshed[0],owner=refreshed[1],expires=now+600); return refreshed
        key, secret, endpoint = env("SCB_API_KEY"), env("SCB_API_SECRET"), env("SCB_OAUTH_TOKEN_ENDPOINT")
        if not key or not secret or not endpoint: raise ValueError("ยังไม่ได้ตั้งค่า SCB OAuth credentials")
        raise ValueError("กรุณาเชื่อมต่อ SCB EASY จาก Owner dashboard ก่อนสร้าง QR")

def scb_http(endpoint: str, payload: dict, extra_headers=None) -> tuple[dict, dict]:
    request_id=str(uuid4()); headers={"Content-Type":"application/json","accept-language":"th","requestUId":request_id, **(extra_headers or {})}
    try:
        request=Request(endpoint, data=json.dumps(payload, ensure_ascii=False).encode(), headers=headers, method="POST")
        with scb_urlopen(request) as response:
            raw=response.read(1_000_000); response_headers={key.lower():value for key,value in response.headers.items()}
    except HTTPError as error:
        raw=error.read(100_000)
        try: description=json.loads(raw.decode()).get("status",{}).get("description","SCB ปฏิเสธคำขอ")
        except (UnicodeDecodeError,json.JSONDecodeError): description="SCB ปฏิเสธคำขอ"
        raise ValueError(f"SCB API error ({error.code}): {description}") from error
    except (URLError, OSError) as error: raise ValueError("ไม่สามารถเชื่อมต่อ SCB API ได้") from error
    try: return json.loads(raw.decode()), response_headers
    except (UnicodeDecodeError,json.JSONDecodeError) as error: raise ValueError("SCB gateway ตอบกลับไม่ใช่ JSON; ตรวจสอบสิทธิ์ product และการตั้งค่า Sandbox กับ SCB") from error

def scb_http_get(endpoint: str, extra_headers=None) -> tuple[dict, dict]:
    request_id=str(uuid4()); headers={"accept-language":"th","requestUId":request_id, **(extra_headers or {})}
    try:
        with scb_urlopen(Request(endpoint, headers=headers, method="GET")) as response:
            raw=response.read(1_000_000); response_headers={key.lower():value for key,value in response.headers.items()}
    except HTTPError as error:
        raw=error.read(100_000)
        try: description=json.loads(raw.decode()).get("status",{}).get("description","SCB ปฏิเสธคำขอ")
        except (UnicodeDecodeError,json.JSONDecodeError): description="SCB ปฏิเสธคำขอ"
        raise ValueError(f"SCB API error ({error.code}): {description}") from error
    except (URLError, OSError) as error: raise ValueError("ไม่สามารถเชื่อมต่อ SCB API ได้") from error
    try: return json.loads(raw.decode()), response_headers
    except (UnicodeDecodeError,json.JSONDecodeError) as error: raise ValueError("SCB gateway ตอบกลับไม่ใช่ JSON; ตรวจสอบสิทธิ์ product และการตั้งค่า Sandbox กับ SCB") from error

def scb_authorize() -> str:
    endpoint,key,secret=env("SCB_AUTHORIZE_ENDPOINT"),env("SCB_API_KEY"),env("SCB_API_SECRET")
    if not endpoint or not key or not secret: raise ValueError("ยังไม่ได้ตั้งค่า SCB authorization configuration")
    headers={"accept-language":"EN","apikey":key,"apisecret":secret,"endState":"mobile_app","requestUId":str(uuid4()),"resourceOwnerId":key,"response-channel":"mobile"}
    try:
        with scb_urlopen(Request(endpoint,headers=headers,method="GET")) as response: raw=response.read(100_000)
    except (HTTPError,URLError,OSError) as error: raise ValueError("ไม่สามารถเริ่ม SCB authorization ได้") from error
    try: data=json.loads(raw.decode()).get("data",{})
    except (UnicodeDecodeError,json.JSONDecodeError) as error: raise ValueError("SCB authorization ตอบกลับไม่ถูกต้อง") from error
    callback=data.get("callbackUrl") if isinstance(data,dict) else ""
    if not isinstance(callback,str) or not callback: raise ValueError("SCB authorization ไม่ได้ส่ง callback URL")
    parsed=urlparse(callback)
    if parsed.scheme!="https" or not parsed.netloc: raise ValueError("SCB authorization callback URL ต้องเป็น HTTPS")
    state=secrets.token_urlsafe(32)
    verifier=""
    query_values={"state":state}
    if env("SCB_OAUTH_PKCE_ENABLED","false").lower()=="true":
        verifier=secrets.token_urlsafe(64)
        challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        query_values.update(code_challenge=challenge,code_challenge_method="S256")
    verifier_cipher=scb_cipher().encrypt(verifier.encode()).decode() if verifier else ""
    with db(immediate=True) as con:
        con.execute("DELETE FROM oauth_states WHERE expires_at < ? OR used_at != ''",(utcnow(),))
        con.execute("INSERT INTO oauth_states(state,expires_at,verifier_cipher) VALUES (?,?,?)",(state,(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat(),verifier_cipher))
    query=parse_qs(parsed.query,keep_blank_values=True)
    for name,value in query_values.items(): query[name]=[value]
    encoded="&".join(f"{quote(key)}={quote(value)}" for key,values in query.items() for value in values)
    return parsed._replace(query=encoded).geturl()

def scb_consume_oauth_state(state: str) -> str | None:
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}",state):return None
    now=utcnow()
    with db(immediate=True) as con:
        row=con.execute(
            """UPDATE oauth_states SET used_at=?
            WHERE state=? AND used_at='' AND expires_at>=?
            RETURNING verifier_cipher""",
            (now,state,now),
        ).fetchone()
    if not row:return None
    if not row["verifier_cipher"]:return ""
    try:return scb_cipher().decrypt(row["verifier_cipher"].encode()).decode()
    except (InvalidToken,UnicodeDecodeError) as error:raise ValueError("ไม่สามารถอ่าน SCB OAuth PKCE verifier ได้") from error

def scb_create_qr(order: dict) -> dict:
    if not scb_active(): raise ValueError("SCB QR ยังไม่เปิดให้บริการ")
    wallet, endpoint=env("SCB_BILLER_ID"),env("SCB_QR_CREATE_ENDPOINT")
    if not wallet or not endpoint: raise ValueError("SCB QR configuration ไม่ครบ")
    token, owner=scb_token(); reference=f"{order['id']}-{secrets.token_hex(3).upper()}"
    products=[{"customField1":line["id"][:255],"customField2":line["name"][:255],"customField3":"Moopiew","customField4":str(line["quantity"]),"customField5":f"{line['unit_price']:.2f}"} for line in order["items"][:20]]
    payload={"partnerReferenceNo":reference,"walletId":wallet,"paymentType":scb_config_public()["payment_types"],"amount":float(order["total"]),"partnerOrderDate":iso_millis(),"partnerMetaData":{"product":products}}
    response,_=scb_http(endpoint,payload,{"authorization":f"Bearer {token}","resourceOwnerId":owner})
    data=response.get("data",{}) if isinstance(response,dict) else {}; tag30=data.get("tag30",{}) if isinstance(data,dict) else {}; result=tag30.get("result",{}) if isinstance(tag30,dict) else {}
    if response.get("status",{}).get("code") not in (1000,"1000") or result.get("status") != "SUCCESS" or not isinstance(tag30.get("qrImage"),str): raise ValueError(result.get("moreInfo") or response.get("status",{}).get("description") or "SCB สร้าง QR ไม่สำเร็จ")
    expiry=tag30.get("expiryDateTime") or data.get("expiryDateTime")
    try: expires_at=datetime.fromisoformat(str(expiry).replace("Z","+00:00")).astimezone(timezone.utc).isoformat() if expiry else (datetime.now(timezone.utc)+timedelta(seconds=max(60,int(env("SCB_QR_TTL_SECONDS","900"))))).isoformat()
    except ValueError: expires_at=(datetime.now(timezone.utc)+timedelta(seconds=900)).isoformat()
    return {"id":f"PAY-SCB-{secrets.token_hex(6).upper()}","provider":"scb_maemanee","provider_reference":reference,"provider_order_id":str(data.get("orderId", "")),"amount":order["total"],"status":"pending","qr_image":tag30["qrImage"],"qr_type":"T30","expires_at":expires_at,"created_at":utcnow(),"updated_at":utcnow(),"confirmed_at":"","provider_response":json.dumps({"orderId":data.get("orderId"),"tag30":{"ref1":tag30.get("ref1"),"ref2":tag30.get("ref2"),"ref3":tag30.get("ref3")}},ensure_ascii=False)}

def scb_inquiry_response(payment: dict, token: str, owner: str) -> dict:
    """Call only the SCB inquiry API belonging to this stored payment product."""
    qr_type=str(payment.get("qr_type","")).upper(); reference=str(payment.get("provider_reference", "")); provider_id=str(payment.get("provider_order_id", ""))
    if not reference or not provider_id: raise ValueError("ข้อมูล SCB payment ไม่ครบสำหรับตรวจสอบ")
    headers={"authorization":f"Bearer {token}","resourceOwnerId":owner}
    if qr_type == "T30":
        endpoint,wallet=env("SCB_QR_INQUIRY_ENDPOINT"),env("SCB_BILLER_ID")
        if not endpoint or not wallet: raise ValueError("SCB QR 30 inquiry configuration ไม่ครบ")
        response,_=scb_http(endpoint,{"walletId":wallet,"partnerReferenceNo":reference,"orderId":provider_id},headers)
        return response
    if qr_type == "QRCS":
        endpoint=env("SCB_QRCS_INQUIRY_ENDPOINT")
        if not endpoint or "{qrId}" not in endpoint: raise ValueError("SCB QR CS inquiry configuration ไม่ครบ")
        response,_=scb_http_get(endpoint.replace("{qrId}",quote(provider_id,safe="")),headers)
        return response
    if qr_type in {"SCB_EASY", "DEEPLINK"}:
        endpoint=env("SCB_EASY_TRANSACTION_INQUIRY_ENDPOINT")
        if not endpoint or "{transactionId}" not in endpoint: raise ValueError("SCB EASY inquiry configuration ไม่ครบ")
        response,_=scb_http_get(endpoint.replace("{transactionId}",quote(provider_id,safe="")),headers)
        return response
    if qr_type in {"ALIPAY", "WECHAT"}: raise ValueError("SCB e-wallet inquiry ต้องตั้ง request contract ที่อนุมัติโดย SCB ก่อนเปิดใช้งาน")
    if qr_type == "BILLPAYMENT": raise ValueError("SCB Bill Payment inquiry ต้องตั้ง query parameter contract ที่อนุมัติโดย SCB ก่อนเปิดใช้งาน")
    raise ValueError("ไม่รู้จักชนิด SCB payment สำหรับตรวจสอบ")

def scb_inquire_payment(payment: dict) -> tuple[dict, bool]:
    if not scb_active(): raise ValueError("SCB QR ยังไม่เปิดให้บริการ")
    token,owner=scb_token(); response=scb_inquiry_response(payment,token,owner)
    def payment_states(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in {"paymentStatus","transactionStatus","paymentResult","transactionResult"} and isinstance(item,str): yield item.upper()
                elif key != "status": yield from payment_states(item)
        elif isinstance(value,list):
            for item in value: yield from payment_states(item)
    return response, bool({"SUCCESS","PAID","COMPLETED"} & set(payment_states(response)))

def row_order(con, order_id: str) -> dict | None:
    row = con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row: return None
    order = dict(row)
    order["customer"] = {"name": order.pop("customer_name"), "phone": order.pop("customer_phone")}
    order["pickup"] = {"date": order.pop("pickup_date"), "slot": order.pop("pickup_slot")}
    order["payment"] = {"method": order.pop("payment_method"), "status": order.pop("payment_status")}
    order["items"] = [dict(item) for item in con.execute("SELECT menu_item_id AS id,name,quantity,unit_price FROM order_items WHERE order_id=?", (order_id,))]
    order["history"] = [dict(event) for event in con.execute("SELECT at,status,actor_role AS by,note FROM order_history WHERE order_id=? ORDER BY id", (order_id,))]
    financial=con.execute("SELECT subtotal,delivery_fee,discount,total,coupon_code,points_earned,points_redeemed FROM order_financials WHERE order_id=?", (order_id,)).fetchone()
    order["financial"] = dict(financial) if financial else {"subtotal":order["total"],"delivery_fee":0,"discount":0,"total":order["total"],"coupon_code":"","points_earned":0,"points_redeemed":0}
    delivery=con.execute("SELECT d.*,z.name AS zone_name,r.name AS rider_name,r.phone AS rider_phone FROM deliveries d JOIN delivery_zones z ON z.id=d.zone_id LEFT JOIN riders r ON r.id=d.rider_id WHERE d.order_id=?", (order_id,)).fetchone()
    if delivery:
        detail=dict(delivery); detail.pop("order_id",None); detail.pop("rider_id",None)
        order["fulfillment"]={"type":"delivery","delivery":detail}
    else: order["fulfillment"]={"type":"pickup"}
    receipt=con.execute("SELECT id,receipt_number,issued_at,customer_tax_name,customer_tax_id FROM pos_receipts WHERE order_id=?", (order_id,)).fetchone()
    if receipt: order["receipt"]=dict(receipt)
    return order

def all_orders(con, pickup_date=None):
    query, args = "SELECT id FROM orders", []
    if pickup_date: query += " WHERE pickup_date=?"; args.append(pickup_date)
    query += " ORDER BY pickup_date DESC, created_at DESC"
    return [row_order(con, row["id"]) for row in con.execute(query, args)]

def public_order(order): return {key: order[key] for key in ("id", "status", "pickup", "items", "total", "payment", "created_at", "notes", "financial", "fulfillment") if key in order} | ({"receipt":order["receipt"]} if "receipt" in order else {})

def active_coupon(con, code: str, subtotal: int) -> dict | None:
    now=utcnow(); row=con.execute("SELECT * FROM coupons WHERE upper(code)=? AND active=1", (code.upper(),)).fetchone()
    if not row: return None
    coupon=dict(row)
    if coupon["minimum_order"]>subtotal or (coupon["maximum_uses"] and coupon["used_count"]>=coupon["maximum_uses"]): return None
    if coupon["starts_at"] and coupon["starts_at"]>now or coupon["ends_at"] and coupon["ends_at"]<now: return None
    return coupon

def delivery_zones(con):
    return [dict(row) for row in con.execute("SELECT id,name,fee,minimum_order FROM delivery_zones WHERE active=1 ORDER BY fee,name")]

def valid_coordinate(value, low, high):
    value=finite_float(value,"พิกัดตำแหน่งไม่ถูกต้อง")
    if not low<=value<=high: raise ValueError("พิกัดตำแหน่งไม่ถูกต้อง")
    return value

def distance_km(lat1, lon1, lat2, lon2):
    radius=6371.0088; phi1,phi2=math.radians(lat1),math.radians(lat2); dphi=math.radians(lat2-lat1); dlambda=math.radians(lon2-lon1)
    a=math.sin(dphi/2)**2+math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return radius*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def quote_delivery(pricing, latitude, longitude):
    store_lat,store_lon=pricing.get("store_latitude"),pricing.get("store_longitude")
    if store_lat is None or store_lon is None: raise ValueError("ร้านยังไม่ได้ตั้งพิกัดสำหรับคำนวณค่าส่ง")
    customer_lat=valid_coordinate(latitude,-90,90);customer_lon=valid_coordinate(longitude,-180,180);km=distance_km(float(store_lat),float(store_lon),customer_lat,customer_lon)
    if km>float(pricing["maximum_km"]):raise ValueError(f"อยู่นอกพื้นที่จัดส่ง ({pricing['maximum_km']} กม.)")
    fee=math.ceil(int(pricing["base_fee"])+float(pricing["per_km_fee"])*km)
    return round(km,2),fee
def valid_pickup(day, conf):
    try: picked = date.fromisoformat(day)
    except ValueError: return False
    return date.today() <= picked <= date.today() + timedelta(days=int(conf["advance_days"]))
def valid_email(value: str) -> bool:
    """Validate the small contact-email subset without a user-controlled regex."""
    if not 3 <= len(value) <= 160 or any(character.isspace() for character in value):
        return False
    local, marker, domain = value.rpartition("@")
    return bool(
        marker
        and local
        and domain
        and "." in domain
        and not domain.startswith((".", "-"))
        and not domain.endswith((".", "-"))
        and ".." not in domain
    )
def slots_for(day, rows, conf):
    used = {slot: 0 for slot in conf["pickup_slots"]}
    for order in rows:
        if order["status"] != "cancelled" and order["pickup"]["date"] == day: used[order["pickup"]["slot"]] = used.get(order["pickup"]["slot"], 0) + sum(line["quantity"] for line in order["items"])
    return [{"time": slot, "remaining": max(0, int(conf["slot_capacity"]) - used[slot]), "available": used[slot] < int(conf["slot_capacity"])} for slot in conf["pickup_slots"]]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(WEB), **kwargs)
    def log_message(self, format, *args): print(f"[{self.log_date_time_string()}] {format % args}")
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("X-Frame-Options", "DENY"); self.send_header("Referrer-Policy", "strict-origin-when-cross-origin"); self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
        nonce=getattr(self,"_script_nonce","")
        script_source="script-src 'self'" + (f" 'nonce-{nonce}'" if nonce else "")
        self.send_header("Content-Security-Policy", f"default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; {script_source}; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        if urlparse(self.path).path in {
            "/admin.html",
            "/ai.html",
            "/api-monitor.html",
            "/document-admin.html",
            "/documents.html",
            "/ops.html",
            "/platform/admin.html",
            "/platform/ai.html",
            "/platform/api-monitor.html",
            "/platform/document-admin.html",
            "/platform/documents.html",
            "/platform/ops.html",
        }:
            self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()
    def json(self, payload, status=200):
        encoded=json.dumps(payload, ensure_ascii=False).encode(); self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(encoded))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(encoded)
    def html(self, content, status=200, script_nonce=""):
        # Only trusted server-rendered pages may opt into one nonce-bound
        # inline script.  Static pages keep the strict no-inline-script CSP.
        self._script_nonce=script_nonce
        try:
            encoded=content.encode(); self.send_response(status); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length",str(len(encoded))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(encoded)
        finally:
            self._script_nonce=""
    def body(self, max_length=100_000):
        try: length=int(self.headers.get("Content-Length", "0"))
        except ValueError: raise ValueError("ขนาดข้อมูลไม่ถูกต้อง")
        if not 0 < length <= max_length: raise ValueError("ขนาดข้อมูลไม่ถูกต้อง")
        raw=self.rfile.read(length); self.raw_body=raw
        try: value=json.loads(raw.decode())
        except (UnicodeDecodeError,json.JSONDecodeError): raise ValueError("ข้อมูลที่ส่งมาไม่ถูกต้อง")
        if not isinstance(value,dict): raise ValueError("ข้อมูลที่ส่งมาไม่ถูกต้อง")
        return value
    def role(self):
        checks=(("admin", "X-Admin-Key", ADMIN_KEY), ("employee", "X-Employee-Key", EMPLOYEE_KEY), ("kitchen", "X-Kitchen-Key", KITCHEN_KEY))
        for role, header, key in checks:
            supplied=header_secret(self.headers,header)
            if key and secrets.compare_digest(supplied, key): return role
        return None
    def client_key(self):
        peer=self.client_address[0]
        forwarded = (
            self.headers.get("CF-Connecting-IP", "")
            if TRUST_CF_CONNECTING_IP and peer in {"127.0.0.1", "::1"}
            else ""
        )
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
    def provider_requirements(self, provider_slug, subject, query):
        with db() as con:
            if not con.execute("SELECT 1 FROM providers WHERE slug=? AND status='active'",(provider_slug,)).fetchone(): return self.json({"error":"ไม่พบ provider"},404)
            country=(query.get("country") or ["TH"])[0].upper()[:2]
            merchant_type=(query.get("merchant_type") or [""])[0].lower()
            vehicle_type=(query.get("vehicle_type") or [""])[0].lower()
            return self.json({"provider":provider_slug,"subject_type":subject,"country":country,"requirements":requirement_rows(con,provider_slug,subject,country,merchant_type,vehicle_type)})
    def upload_document(self, form, role):
        provider=str(form.get("provider","")).strip().lower(); subject=str(form.get("subject_type","")).strip().lower(); subject_id=str(form.get("subject_id","")).strip(); requirement_id=str(form.get("requirement_id","")).strip(); filename=os.path.basename(str(form.get("filename","")))[:180]; mime=str(form.get("mime_type","")).strip().lower(); encoded=form.get("content_base64","")
        if not re.fullmatch(r"[a-z0-9-]{2,40}",provider) or subject not in {"rider","merchant"} or not re.fullmatch(r"[A-Za-z0-9_-]{2,100}",subject_id) or not filename or not isinstance(encoded,str): raise ValueError("ข้อมูลเอกสารไม่ถูกต้อง")
        with db(immediate=True) as con:
            prow=con.execute("SELECT id FROM providers WHERE slug=? AND status='active'",(provider,)).fetchone()
            req=con.execute(
                """SELECT r.*,d.allowed_mime_types,d.max_size_bytes
                   FROM provider_document_requirements r
                   JOIN providers p ON p.id=r.provider_id
                   JOIN document_types d ON d.id=r.document_type_id
                   WHERE r.id=? AND p.slug=? AND r.subject_type=?
                     AND r.status='active'
                     AND datetime(r.effective_from)<=datetime('now')
                     AND (r.effective_to='' OR datetime(r.effective_to)>datetime('now'))""",
                (requirement_id,provider,subject),
            ).fetchone()
            if not prow or not req: raise ValueError("ไม่พบ requirement ของเอกสาร")
            allowed=json.loads(req["allowed_mime_types"])
            if mime not in allowed: raise ValueError("ชนิดไฟล์นี้ไม่อยู่ในรายการที่อนุญาต")
            try: raw=base64.b64decode(encoded,validate=True)
            except (ValueError,TypeError): raise ValueError("ไฟล์เอกสารต้องเป็น base64 ที่ถูกต้อง")
            if not raw or len(raw)>min(int(req["max_size_bytes"]),10*1024*1024): raise ValueError("ขนาดไฟล์ไม่ถูกต้อง")
            if (mime=="application/pdf" and not raw.startswith(b"%PDF")) or (mime=="image/png" and not raw.startswith(b"\x89PNG\r\n\x1a\n")) or (mime=="image/jpeg" and not raw.startswith(b"\xff\xd8\xff")): raise ValueError("เนื้อไฟล์ไม่ตรงกับชนิดไฟล์")
            doc_id=f"DOC-{secrets.token_hex(8).upper()}";digest=hashlib.sha256(raw).hexdigest()
            try:path=store_document(doc_id,raw)
            except (OSError,ValueError) as error:raise ValueError("ไม่สามารถจัดเก็บเอกสารแบบเข้ารหัสได้") from error
            metadata={"uploaded_by":role,"storage_encryption":"fernet-v1"}
            now=utcnow(); con.execute("INSERT INTO uploaded_documents(id,provider_id,subject_type,subject_id,requirement_id,original_filename,storage_path,mime_type,size_bytes,sha256,status,metadata,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(doc_id,prow["id"],subject,subject_id,requirement_id,filename,str(path),mime,len(raw),digest,"pending",json.dumps(metadata),now,now)); con.execute("INSERT INTO document_verification(document_id,status) VALUES (?,?)",(doc_id,"pending")); con.execute("INSERT INTO verification_history VALUES (?,?,?,?,?,?,?)",(f"VER-{secrets.token_hex(8).upper()}",doc_id,"pending",role,"",json.dumps({}),now)); audit(con,role,"upload","document",doc_id,{"provider":provider,"subject_type":subject,"requirement_id":requirement_id,"size_bytes":len(raw),"mime_type":mime,"storage_encryption":"fernet-v1"})
            row=con.execute("SELECT * FROM uploaded_documents WHERE id=?",(doc_id,)).fetchone()
            response={"document":document_public(row)}
        return self.json(response,201)
    def update_document(self, document_id, form, role):
        status=str(form.get("status","")).strip().lower(); reason=str(form.get("reason","")).strip()[:500]
        if status not in {"pending","approved","rejected","expired"}: raise ValueError("สถานะเอกสารไม่ถูกต้อง")
        with db(immediate=True) as con:
            row=con.execute("SELECT * FROM uploaded_documents WHERE id=? AND status!='deleted'",(document_id,)).fetchone()
            if not row:return self.json({"error":"ไม่พบเอกสาร"},404)
            now=utcnow(); con.execute("UPDATE uploaded_documents SET status=?,updated_at=? WHERE id=?",(status,now,document_id)); con.execute("UPDATE document_verification SET status=?,verified_by=?,reason=?,verified_at=?,metadata=? WHERE document_id=?",(status,role,reason,now,json.dumps({}),document_id)); con.execute("INSERT INTO verification_history VALUES (?,?,?,?,?,?,?)",(f"VER-{secrets.token_hex(8).upper()}",document_id,status,role,reason,json.dumps({}),now)); audit(con,role,"verify","document",document_id,{"status":status}); response={"document":document_public(con.execute("SELECT * FROM uploaded_documents WHERE id=?",(document_id,)).fetchone())}
        return self.json(response)
    def delete_document(self, document_id, role):
        with db(immediate=True) as con:
            row=con.execute("SELECT * FROM uploaded_documents WHERE id=? AND status!='deleted'",(document_id,)).fetchone()
            if not row:return self.json({"error":"ไม่พบเอกสาร"},404)
            storage_path=Path(row["storage_path"])
            now=utcnow(); con.execute("UPDATE uploaded_documents SET status='deleted',updated_at=? WHERE id=?",(now,document_id)); con.execute("INSERT INTO verification_history VALUES (?,?,?,?,?,?,?)",(f"VER-{secrets.token_hex(8).upper()}",document_id,"deleted",role,"ลบเอกสาร",json.dumps({}),now)); audit(con,role,"delete","document",document_id)
        try: storage_path.unlink(missing_ok=True)
        except OSError: pass
        return self.json({"deleted":True,"id":document_id})
    def admin_document_requirements(self, form, requirement_id, role):
        with db(immediate=True) as con:
            row=con.execute("SELECT * FROM provider_document_requirements WHERE id=?",(requirement_id,)).fetchone()
            if not row:return self.json({"error":"ไม่พบ requirement"},404)
            if row["effective_to"]:
                raise ValueError("แก้ไข historical requirement ไม่ได้")
            required=parse_bool(form.get("is_required"),bool(row["is_required"])); optional=parse_bool(form.get("is_optional"),bool(row["is_optional"]))
            if required and optional: raise ValueError("requirement เป็น required และ optional พร้อมกันไม่ได้")
            try: order=int(form.get("display_order",row["display_order"]))
            except (TypeError,ValueError): raise ValueError("ลำดับไม่ถูกต้อง")
            if order<0: raise ValueError("ลำดับไม่ถูกต้อง")
            status=str(form.get("status",row["status"])).strip().lower()
            if status not in {"active","inactive"}: raise ValueError("สถานะ requirement ไม่ถูกต้อง")
            metadata=json.loads(row["metadata"])
            supplied=form.get("metadata")
            if supplied is not None:
                if not isinstance(supplied,dict): raise ValueError("metadata ไม่ถูกต้อง")
                metadata.update(supplied)
            try:
                encoded_metadata=json.dumps(metadata,ensure_ascii=False,separators=(",",":"))
            except (TypeError,ValueError):
                raise ValueError("metadata ไม่ถูกต้อง")
            if len(encoded_metadata.encode("utf-8"))>16_384:
                raise ValueError("metadata มีขนาดใหญ่เกินไป")
            now=utcnow(); new_id=f"{requirement_id}-v{secrets.token_hex(3).upper()}"
            updated=con.execute(
                "UPDATE provider_document_requirements SET effective_to=?,updated_at=? WHERE id=? AND effective_to=''",
                (now,now,requirement_id),
            )
            if updated.rowcount != 1:
                raise ValueError("requirement ถูกสร้างเวอร์ชันแล้ว")
            con.execute("INSERT INTO provider_document_requirements(id,provider_id,service_id,subject_type,merchant_type_id,vehicle_type_id,document_type_id,country,effective_from,effective_to,metadata,is_required,is_optional,display_order,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(new_id,row["provider_id"],row["service_id"],row["subject_type"],row["merchant_type_id"],row["vehicle_type_id"],row["document_type_id"],row["country"],now,"",encoded_metadata,int(required),int(optional),order,status,now,now))
            audit(con,role,"version","provider_document_requirement",new_id,{"previous_id":requirement_id,"status":status,"is_required":required,"is_optional":optional,"display_order":order})
            response={"requirement_id":new_id,"previous_id":requirement_id,"effective_from":now}
        return self.json(response,201)
    def do_GET(self):
        parsed=urlparse(self.path); path, query=parsed.path, parse_qs(parsed.query)
        if path == "/auth/scb/callback":
            code=(query.get("code") or query.get("authCode") or [""])[0]
            state=(query.get("state") or [""])[0]
            if not code or not state or len(code)>4096 or len(state)>128:return self.html("<h1>SCB connection failed</h1><p>Authorization code or state is missing or invalid.</p>",400)
            try: verifier=scb_consume_oauth_state(state)
            except ValueError as error:return self.html(f"<h1>SCB connection failed</h1><p>{escape_html(str(error))}</p>",400)
            if verifier is None:return self.html("<h1>SCB connection failed</h1><p>Authorization state is invalid or expired.</p>",400)
            try: scb_exchange_auth_code(code,verifier)
            except ValueError as error: return self.html(f"<h1>SCB connection failed</h1><p>{escape_html(str(error))}</p>",400)
            return self.html("<h1>SCB connected</h1><p>Return to MooPiew Owner dashboard to enable and test QR payment.</p>")
        if path == "/api/health":
            return self.json({"status": "ok", "service": "moopiew", "time": utcnow()})
        if path == "/api/payments/scb/config": return self.json(scb_config_public())
        if path == "/api/admin/ai/config":
            if not self.require("admin"): return
            return self.json(ai_public_config())
        if path == "/api/admin/ai/models":
            if not self.require("admin"): return
            try:
                catalog=ai_catalog()
                return self.json({**catalog,"catalog":"live-provider","cached_seconds":max(0,int(float(AI_MODEL_CACHE.get("expires",0))-time.monotonic()))})
            except ValueError as error: return self.json({"error":str(error)},503)
        if path in {"/providers","/api/providers"}:
            with db() as con: return self.json({"providers":provider_rows(con)})
        provider_match=re.fullmatch(r"(?:/api)?/providers/([a-z0-9-]+)",path)
        if provider_match:
            with db() as con:
                rows=provider_rows(con,provider_match.group(1))
                if not rows:return self.json({"error":"ไม่พบ provider"},404)
                services=[dict(row) | {"metadata":json.loads(row["metadata"])} for row in con.execute("SELECT * FROM provider_services WHERE provider_id=? AND status='active' ORDER BY name",(rows[0]["id"],))]
                return self.json({"provider":rows[0],"services":services})
        requirements_match=re.fullmatch(r"(?:/api)?/providers/([a-z0-9-]+)/requirements(?:/(rider|merchant))?",path)
        if requirements_match:
            provider_slug,subject=requirements_match.groups(); subject=subject or (query.get("subject_type") or ["rider"])[0]
            return self.provider_requirements(provider_slug,subject,query)
        if path in {"/api/documents/status","/documents/status"}:
            if not self.require("admin"): return
            with db() as con:
                subject=(query.get("subject_type") or [""])[0]; subject_id=(query.get("subject_id") or [""])[0]; params=[]; where=["status!='deleted'"]
                if subject in {"rider","merchant"}: where.append("subject_type=?"); params.append(subject)
                if subject_id: where.append("subject_id=?"); params.append(subject_id)
                rows=[document_public(row) for row in con.execute(f"SELECT * FROM uploaded_documents WHERE {' AND '.join(where)} ORDER BY created_at DESC",params)]
                return self.json({"documents":rows})
        if path in {"/api/documents/history","/documents/history"}:
            if not self.require("admin"): return
            with db() as con:
                doc_id=(query.get("document_id") or [""])[0]; params=[]; where=""
                if doc_id: where=" WHERE h.document_id=?"; params=[doc_id]
                rows=[dict(row) | {"metadata":json.loads(row["metadata"])} for row in con.execute(f"SELECT h.* FROM verification_history h{where} ORDER BY h.created_at DESC",params)]
                return self.json({"history":rows})
        if path == "/api/admin/document-requirements":
            if not self.require("admin"): return
            with db() as con:
                rows=[]
                for row in con.execute("SELECT r.*,p.slug provider_slug,p.name provider_name,s.slug service_slug,d.slug document_slug,d.name document_name,mt.slug merchant_type_slug,vt.slug vehicle_type_slug FROM provider_document_requirements r JOIN providers p ON p.id=r.provider_id LEFT JOIN provider_services s ON s.id=r.service_id JOIN document_types d ON d.id=r.document_type_id LEFT JOIN merchant_types mt ON mt.id=r.merchant_type_id LEFT JOIN vehicle_types vt ON vt.id=r.vehicle_type_id ORDER BY p.name,r.subject_type,r.display_order,r.effective_from"):
                    item=dict(row); item["metadata"]=json.loads(item["metadata"]); item["is_required"]=bool(item["is_required"]); item["is_optional"]=bool(item["is_optional"]); item["is_current"]=not bool(item["effective_to"]); rows.append(item)
                return self.json({"requirements":rows})
        tracking=re.fullmatch(r"/api/tracking/(TRK-[A-F0-9]{32})/events",path)
        if tracking:return self.stream_tracking(tracking.group(1))
        tracking=re.fullmatch(r"/api/tracking/(TRK-[A-F0-9]{32})",path)
        if tracking:
            if not self.rate("lookup"): return self.json({"error":"คำขอมากเกินไป"},429)
            return self.tracking_snapshot(tracking.group(1))
        if path == "/api/admin/scb/auth/start":
            if not self.require("admin"): return
            try: return self.json({"authorization_url":scb_authorize()})
            except ValueError as error: return self.json({"error":str(error)},400)
        if path == "/api/admin/scb/auth/status":
            if not self.require("admin"): return
            with db() as con: row=con.execute("SELECT access_expires_at,refresh_expires_at,updated_at FROM oauth_tokens WHERE subject='scb_merchant'").fetchone()
            now=datetime.now(timezone.utc)
            access_valid=bool(row and datetime.fromisoformat(row["access_expires_at"])>now)
            refresh_valid=bool(row and row["refresh_expires_at"] and datetime.fromisoformat(row["refresh_expires_at"])>now)
            return self.json({"connected":access_valid or refresh_valid,"access_valid":access_valid,"refresh_valid":refresh_valid,"access_expires_at":row["access_expires_at"] if row else "","refresh_expires_at":row["refresh_expires_at"] if row else "","updated_at":row["updated_at"] if row else ""})
        with db() as con:
            conf=config(con)
            if path == "/api/ready":
                con.execute("SELECT 1 FROM settings LIMIT 1").fetchone()
                return self.json({"status": "ready", "database": "ok"})
            if path == "/api/status":
                return self.json({"status":"operational","service":"moopiew","time":utcnow(),"database":"ok","api_version":"1.1","endpoints":{"health":"/api/health","ready":"/api/ready","menu":"/api/menu"}})
            if path=="/api/menu":
                if not self.rate("public"): return self.json({"error":"คำขอมากเกินไป"},429)
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
                    "delivery_zones":delivery_zones(con),
                    "delivery_pricing":{"mode":conf["delivery_pricing"]["mode"],"base_fee":conf["delivery_pricing"]["base_fee"],"per_km_fee":conf["delivery_pricing"]["per_km_fee"],"maximum_km":conf["delivery_pricing"]["maximum_km"],"configured":conf["delivery_pricing"].get("store_latitude") is not None},
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
            if path=="/api/admin/operations":
                if not self.require("admin"): return
                ensure_receipt_ledger(con)
                inventory=[dict(row) for row in con.execute("SELECT * FROM inventory_items ORDER BY name")]
                riders=[dict(row) for row in con.execute("SELECT * FROM riders ORDER BY active DESC,name")]
                applications=[dict(row) for row in con.execute("SELECT * FROM rider_applications ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,created_at DESC")]
                merchant_applications=[dict(row) for row in con.execute("SELECT * FROM merchant_applications ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,created_at DESC")]
                coupons=[dict(row) for row in con.execute("SELECT * FROM coupons ORDER BY created_at DESC")]
                deliveries=[dict(row) for row in con.execute("SELECT d.*,o.id AS order_id,o.customer_name,o.total,z.name AS zone_name,r.name AS rider_name FROM deliveries d JOIN orders o ON o.id=d.order_id JOIN delivery_zones z ON z.id=d.zone_id LEFT JOIN riders r ON r.id=d.rider_id ORDER BY d.updated_at DESC")]
                receipts=[dict(row) for row in con.execute("SELECT * FROM pos_receipts ORDER BY issued_at DESC LIMIT 100")]
                invoices=[dict(row) for row in con.execute("SELECT * FROM tax_invoices ORDER BY issued_at DESC LIMIT 100")]
                recipes=[dict(row) for row in con.execute("SELECT r.menu_item_id,r.inventory_item_id,r.quantity,m.name AS menu_name,i.name AS inventory_name,i.unit FROM menu_recipes r JOIN menu_items m ON m.id=r.menu_item_id JOIN inventory_items i ON i.id=r.inventory_item_id ORDER BY m.name,i.name")]
                return self.json({"delivery_zones":delivery_zones(con),"delivery_pricing":conf["delivery_pricing"],"deliveries":deliveries,"riders":riders,"rider_applications":applications,"merchant_applications":merchant_applications,"inventory":inventory,"menu":conf["menu"],"recipes":recipes,"coupons":coupons,"receipts":receipts,"tax_invoices":invoices,"ledger_entries":ledger_entries_public(con),"stock_moves":stock_moves_public(con),"business_profile":conf["business_profile"]})
            if path=="/api/admin/zerp/accounting/entries":
                if not self.require("admin"): return
                return self.json({"entries": ledger_entries_public(con), "currency": "THB"})
            if path=="/api/admin/zerp/inventory/moves":
                if not self.require("admin"): return
                return self.json({"moves": stock_moves_public(con), "currency": "THB"})
            printable=re.fullmatch(r"/api/admin/receipts/(RCT-[A-Z0-9-]+)/print",path)
            if printable:
                if not self.require("admin"): return
                return self.print_receipt(con,printable.group(1),conf)
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
        try: form=self.body(15_000_000 if path in {"/api/documents/upload","/documents/upload"} else 100_000)
        except ValueError as error: return self.json({"error":str(error)},400)
        try:
            if path=="/api/orders":
                if not self.rate("order"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.create_order(form)
            if path=="/api/riders/register":
                if not self.rate("rider"):return self.json({"error":"คำขอมากเกินไป"},429)
                return self.register_rider(form)
            if path=="/api/merchants/register":
                if not self.rate("rider"):return self.json({"error":"คำขอมากเกินไป"},429)
                return self.register_merchant(form)
            if path in {"/api/documents/upload","/documents/upload"}:
                role=self.require("admin")
                if not role:return
                return self.upload_document(form,role)
            if path=="/api/delivery/quote":
                if not self.rate("quote"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.delivery_quote(form)
            qr=re.fullmatch(r"/api/orders/(MPP-[A-Z0-9-]+)/payments/scb/qr",path)
            if qr:
                if not self.rate("order"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.create_scb_qr(qr.group(1),form)
            if path=="/api/scb/payment/confirm":
                if not self.rate("webhook"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.scb_payment_callback(form, getattr(self,"raw_body",b""))
            if path=="/api/order-lookup":
                if not self.rate("lookup"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.lookup_order(form)
            if path=="/api/admin/ai/chat":
                role=self.require("admin")
                if not role:return
                return self.ai_chat(form,role)
            if path=="/api/admin/menu":
                role=self.require("admin")
                if not role:return
                return self.create_menu_item(form,role)
            admin_actions={
                "/api/admin/riders":self.create_rider,
                "/api/admin/delivery-zones":self.create_delivery_zone,
                "/api/admin/inventory":self.create_inventory_item,
                "/api/admin/inventory/adjust":self.adjust_inventory,
                "/api/admin/inventory/recipes":self.set_menu_recipe,
                "/api/admin/coupons":self.create_coupon,
                "/api/admin/business-profile":self.update_business_profile,
                "/api/admin/delivery-pricing":self.update_delivery_pricing,
            }
            if path in admin_actions:
                role=self.require("admin")
                if not role:return
                return admin_actions[path](form,role)
            receipt=re.fullmatch(r"/api/admin/orders/(MPP-[A-Z0-9-]+)/receipt",path)
            if receipt:
                role=self.require("admin")
                if not role:return
                return self.issue_receipt(receipt.group(1),form,role)
            invoice=re.fullmatch(r"/api/admin/receipts/(RCT-[A-Z0-9-]+)/tax-invoice",path)
            if invoice:
                role=self.require("admin")
                if not role:return
                return self.issue_tax_invoice(invoice.group(1),form,role)
            inquiry=re.fullmatch(r"/api/admin/payments/scb/(PAY-SCB-[A-Z0-9-]+)/inquire",path)
            if inquiry:
                role=self.require("admin")
                if not role:return
                return self.inquire_scb_payment(inquiry.group(1),role)
            if path.endswith("/cancel") and re.fullmatch(r"/api/orders/MPP-[A-Z0-9-]+/cancel",path):
                if not self.rate("lookup"): return self.json({"error":"คำขอมากเกินไป"},429)
                return self.cancel_order(path.split("/")[3],form)
        except ValueError as error: return self.json({"error":str(error)},400)
        return self.json({"error":"ไม่พบ API"},404)
    def do_PATCH(self):
        try:
            return self._do_PATCH()
        except ValueError as error:
            return self.json({"error":str(error)},400)
    def _do_PATCH(self):
        path=urlparse(self.path).path
        try: form=self.body()
        except ValueError as error: return self.json({"error":str(error)},400)
        requirement=re.fullmatch(r"/api/admin/document-requirements/([A-Za-z0-9_-]+)",path)
        if requirement:
            role=self.require("admin")
            if role:return self.admin_document_requirements(form,requirement.group(1),role)
            return
        document=re.fullmatch(r"(?:/api)?/documents/(DOC-[A-F0-9]+)",path)
        if document:
            role=self.require("admin")
            if role:return self.update_document(document.group(1),form,role)
            return
        match=re.fullmatch(r"/api/(admin|staff|kitchen)/orders/(MPP-[A-Z0-9-]+)",path)
        if match:
            area, order_id=match.groups(); expected={"admin":"admin","staff":"employee","kitchen":"kitchen"}[area]; role=self.require(expected)
            if role: return self.update_order(order_id,form,role,area)
            return
        delivery=re.fullmatch(r"/api/(admin|staff)/deliveries/(MPP-[A-Z0-9-]+)",path)
        if delivery:
            area,order_id=delivery.groups(); role=self.require("admin" if area=="admin" else "employee")
            if role:return self.update_delivery(order_id,form,role,area)
            return
        rider=re.fullmatch(r"/api/admin/riders/(RDR-[A-Z0-9-]+)",path)
        if rider:
            role=self.require("admin")
            if role:return self.update_rider(rider.group(1),form,role)
            return
        application=re.fullmatch(r"/api/admin/rider-applications/(RAP-[A-Z0-9-]+)",path)
        if application:
            role=self.require("admin")
            if role:return self.review_rider_application(application.group(1),form,role)
            return
        merchant_application=re.fullmatch(r"/api/admin/merchant-applications/(MAP-[A-Z0-9-]+)",path)
        if merchant_application:
            role=self.require("admin")
            if role:return self.review_merchant_application(merchant_application.group(1),form,role)
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
    def do_DELETE(self):
        path=urlparse(self.path).path
        document=re.fullmatch(r"(?:/api)?/documents/(DOC-[A-F0-9]+)",path)
        if document:
            role=self.require("admin")
            if role:return self.delete_document(document.group(1),role)
            return
        return self.json({"error":"ไม่พบ API"},404)
    def ai_chat(self,form,role):
        try:
            result=ai_chat(form.get("model",""),form.get("prompt",""),form.get("max_tokens",512),form.get("temperature",0.2))
        except ValueError as error:
            return self.json({"error":str(error)},400)
        # Never persist a prompt or model output: both can contain operational or
        # customer data. Audit only the model and response size.
        with db() as con:
            audit(con,role,"ai_chat","ai",result["id"],{"provider":result["provider"],"response_characters":len(result["content"])})
        return self.json(result)
    def admin_dashboard(self,con,conf):
        orders=all_orders(con); recent=[dict(row) for row in con.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10")]
        payments=[payment_public(dict(row)) for row in con.execute("SELECT * FROM payment_attempts WHERE provider LIKE 'scb_%' ORDER BY created_at DESC LIMIT 50")]
        return self.json({"summary":summary(orders),"orders":orders,"settings":conf,"payments":payments,"audit":recent})
    def create_order(self,form):
        name=str(form.get("name","")).strip(); phone=re.sub(r"[^0-9+]","",str(form.get("phone", ""))); pickup_date,pickup_slot=str(form.get("pickup_date", "")),str(form.get("pickup_slot", "")); payment=str(form.get("payment_method","cash")); notes=str(form.get("notes","")).strip()[:300]; requested=form.get("items",[])
        fulfillment=str(form.get("fulfillment_type","pickup")); coupon_code=str(form.get("coupon_code","")).strip().upper()
        if not 2<=len(name)<=80:raise ValueError("กรุณาระบุชื่ออย่างน้อย 2 ตัวอักษร")
        if not re.fullmatch(r"(?:\+66|0)\d{8,9}",phone):raise ValueError("กรุณาระบุเบอร์โทรศัพท์ที่ถูกต้อง")
        if fulfillment not in {"pickup","delivery"}: raise ValueError("รูปแบบการรับสินค้าไม่ถูกต้อง")
        with STORE_LOCK,db(immediate=True) as con:
            conf=config(con)
            if fulfillment=="pickup":
                if not valid_pickup(pickup_date,conf):raise ValueError("เลือกรับสินค้าได้เฉพาะวันที่เปิดให้สั่งล่วงหน้า")
                if pickup_slot not in conf["pickup_slots"]:raise ValueError("กรุณาเลือกรอบรับที่มีให้บริการ")
            else:
                pickup_date=date.today().isoformat(); pickup_slot="จัดส่งตามลำดับคิว"
            if payment not in PAYMENT_METHODS or (payment=="scb_qr" and not scb_active()):raise ValueError("วิธีชำระเงินไม่ถูกต้อง")
            if not isinstance(requested,list):raise ValueError("รายการสั่งไม่ถูกต้อง")
            by_id={item["id"]:item for item in conf["menu"] if item["available"]}; lines=[]; total=0
            seen=set()
            for line in requested:
                if not isinstance(line,dict):raise ValueError("รายการสั่งไม่ถูกต้อง")
                item_id=str(line.get("id","")).strip(); item=by_id.get(item_id)
                try: quantity=int(line.get("quantity",0))
                except (TypeError,ValueError):raise ValueError("รายการสั่งไม่ถูกต้อง")
                if not item or item_id in seen or not 0<quantity<=100: raise ValueError("รายการสั่งมีเมนูหรือจำนวนไม่ถูกต้อง")
                seen.add(item_id); lines.append((item,quantity)); total+=item["price"]*quantity
            if not lines:raise ValueError("กรุณาเลือกอย่างน้อย 1 รายการ")
            if fulfillment=="pickup":
                remaining=next(slot["remaining"] for slot in slots_for(pickup_date,all_orders(con),conf) if slot["time"]==pickup_slot)
                if sum(q for _,q in lines)>remaining:raise ValueError(f"รอบนี้เหลือรับได้ {remaining} ชิ้น กรุณาลดจำนวนหรือเลือกรอบอื่น")
            delivery_fee=0; delivery=None; delivery_distance=0
            if fulfillment=="delivery":
                zone_id=str(form.get("delivery_zone_id","")).strip(); zone=con.execute("SELECT * FROM delivery_zones WHERE id=? AND active=1",(zone_id,)).fetchone()
                recipient=str(form.get("recipient_name",name)).strip()[:80]; recipient_phone=re.sub(r"[^0-9+]","",str(form.get("recipient_phone",phone))); address=str(form.get("delivery_address","")).strip()[:500]; landmark=str(form.get("delivery_landmark","")).strip()[:160]
                if not zone or not address or not 2<=len(recipient)<=80 or not re.fullmatch(r"(?:\+66|0)\d{8,9}",recipient_phone): raise ValueError("กรุณาระบุข้อมูลจัดส่งให้ครบถ้วน")
                if total<int(zone["minimum_order"]): raise ValueError(f"ยอดสั่งขั้นต่ำสำหรับพื้นที่นี้คือ {zone['minimum_order']} บาท")
                pricing=conf["delivery_pricing"]
                if pricing.get("mode")=="distance": delivery_distance,delivery_fee=quote_delivery(pricing,form.get("delivery_latitude"),form.get("delivery_longitude"))
                else: delivery_fee=int(zone["fee"])
                delivery=(zone_id,recipient,recipient_phone,address,landmark)
            now=utcnow(); con.execute("INSERT INTO customers(phone,name,points_balance,created_at,updated_at) VALUES (?,?,?,?,?) ON CONFLICT(phone) DO UPDATE SET name=excluded.name,updated_at=excluded.updated_at",(phone,name,0,now,now))
            customer=con.execute("SELECT points_balance FROM customers WHERE phone=?",(phone,)).fetchone()
            coupon=active_coupon(con,coupon_code,total) if coupon_code else None
            if coupon_code and not coupon: raise ValueError("คูปองใช้ไม่ได้หรือไม่เข้าเงื่อนไข")
            coupon_discount=min(total, int(coupon["value"]) if coupon and coupon["kind"]=="fixed" else total*int(coupon["value"])//100 if coupon else 0)
            try: points_redeemed=int(form.get("points_to_redeem",0))
            except (ValueError,TypeError):raise ValueError("จำนวนแต้มไม่ถูกต้อง")
            if points_redeemed<0 or points_redeemed>int(customer["points_balance"]) or points_redeemed>total-coupon_discount:raise ValueError("แต้มคงเหลือไม่เพียงพอหรือใช้เกินยอดสินค้า")
            discount=coupon_discount+points_redeemed; final_total=total+delivery_fee-discount; points_earned=final_total//25
            oid=f"MPP-{datetime.now():%y%m%d}-{secrets.token_hex(3).upper()}"; status="confirmed" if AUTO_CONFIRM_ORDERS else "new"
            con.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",(oid,now,status,name,phone,pickup_date,pickup_slot,final_total,notes,payment,"pending"))
            con.executemany("INSERT INTO order_items(order_id,menu_item_id,name,quantity,unit_price) VALUES (?,?,?,?,?)",[(oid,i["id"],i["name"],q,i["price"]) for i,q in lines])
            con.execute("INSERT INTO order_financials VALUES (?,?,?,?,?,?,?,?)",(oid,total,delivery_fee,discount,final_total,coupon_code,points_earned,points_redeemed))
            if points_redeemed:
                con.execute("UPDATE customers SET points_balance=points_balance-?,updated_at=? WHERE phone=?",(points_redeemed,now,phone));con.execute("INSERT INTO loyalty_ledger VALUES (?,?,?,?,?,?)",(f"LOY-{secrets.token_hex(4).upper()}",phone,-points_redeemed,"order_redeemed",oid,now))
            if delivery:
                tracking=f"TRK-{secrets.token_hex(16).upper()}"; con.execute("INSERT INTO deliveries(order_id,zone_id,recipient_name,recipient_phone,address,landmark,tracking_code,updated_at,distance_km) VALUES (?,?,?,?,?,?,?,?,?)",(oid,*delivery,tracking,now,delivery_distance))
            if coupon:
                con.execute("UPDATE coupons SET used_count=used_count+1 WHERE id=?",(coupon["id"],)); con.execute("INSERT INTO coupon_redemptions VALUES (?,?,?,?,?)",(coupon["id"],oid,phone,discount,now))
            con.execute("INSERT INTO order_history(order_id,at,status,actor_role,note) VALUES (?,?,?,?,?)",(oid,now,status,"automation" if AUTO_CONFIRM_ORDERS else "customer","auto_confirmed" if AUTO_CONFIRM_ORDERS else "")); audit(con,"automation" if AUTO_CONFIRM_ORDERS else "customer","create","order",oid,{"total":final_total,"status":status,"fulfillment":fulfillment})
            order=row_order(con,oid)
        self.json({"order":public_order(order)},201)
    def tracking_snapshot(self,tracking_code):
        with db() as con:
            row=con.execute("SELECT d.tracking_code,d.status,d.updated_at,d.assigned_at,d.picked_up_at,d.delivered_at,z.name AS zone_name,r.name AS rider_name FROM deliveries d JOIN delivery_zones z ON z.id=d.zone_id LEFT JOIN riders r ON r.id=d.rider_id WHERE d.tracking_code=?",(tracking_code,)).fetchone()
            if not row:return self.json({"error":"ไม่พบรหัสติดตาม"},404)
            return self.json({"tracking":dict(row)})
    def stream_tracking(self,tracking_code):
        if not self.rate("lookup"):return self.json({"error":"คำขอมากเกินไป"},429)
        self.send_response(200);self.send_header("Content-Type","text/event-stream; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Connection","keep-alive");self.end_headers(); previous=""
        try:
            for _ in range(20):
                with db() as con:
                    row=con.execute("SELECT d.tracking_code,d.status,d.updated_at,d.assigned_at,d.picked_up_at,d.delivered_at,z.name AS zone_name,r.name AS rider_name FROM deliveries d JOIN delivery_zones z ON z.id=d.zone_id LEFT JOIN riders r ON r.id=d.rider_id WHERE d.tracking_code=?",(tracking_code,)).fetchone()
                if not row:break
                payload=json.dumps({"tracking":dict(row)},ensure_ascii=False)
                if payload!=previous:self.wfile.write(f"event: tracking\ndata: {payload}\n\n".encode());self.wfile.flush();previous=payload
                time.sleep(3)
        except (BrokenPipeError,ConnectionResetError):pass
    def delivery_quote(self,form):
        try: subtotal=int(form.get("subtotal",0))
        except (ValueError,TypeError): raise ValueError("ยอดสั่งไม่ถูกต้อง")
        if subtotal < 0: raise ValueError("ยอดสั่งต้องไม่ติดลบ")
        zone_id=str(form.get("zone_id","")).strip()
        with db() as con:
            zone=con.execute("SELECT id,name,fee,minimum_order FROM delivery_zones WHERE id=? AND active=1",(zone_id,)).fetchone()
            if not zone:return self.json({"error":"ไม่พบพื้นที่จัดส่ง"},404)
            if subtotal<int(zone["minimum_order"]):raise ValueError(f"ยอดสั่งขั้นต่ำสำหรับพื้นที่นี้คือ {zone['minimum_order']} บาท")
            pricing=config(con)["delivery_pricing"]
            if pricing.get("mode")=="distance": distance,fee=quote_delivery(pricing,form.get("latitude"),form.get("longitude"))
            else:distance,fee=0,int(zone["fee"])
            return self.json({"zone":dict(zone),"subtotal":subtotal,"distance_km":distance,"delivery_fee":fee,"total":subtotal+fee})
    def create_scb_qr(self,oid,form):
        phone=re.sub(r"[^0-9+]","",str(form.get("phone","")))
        if not scb_active(): raise ValueError("SCB QR ยังไม่เปิดให้บริการ")
        with STORE_LOCK:
            with db() as con:
                order=row_order(con,oid)
                if not order or not secrets.compare_digest(order["customer"]["phone"],phone): return self.json({"error":"ไม่พบออเดอร์ หรือเบอร์โทรศัพท์ไม่ตรงกัน"},404)
                if order["status"]=="cancelled": raise ValueError("ออเดอร์ถูกยกเลิกแล้ว")
                if order["payment"]["method"]!="scb_qr": raise ValueError("ออเดอร์นี้ไม่ได้เลือกชำระผ่าน SCB QR")
                existing=active_payment(con,oid)
                if existing: return self.json({"payment":payment_public(existing)})
            payment=scb_create_qr(order)
            with db() as con:
                con.execute("INSERT INTO payment_attempts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(payment["id"],oid,payment["provider"],payment["provider_reference"],payment["provider_order_id"],payment["amount"],payment["status"],payment["qr_image"],payment["qr_type"],payment["expires_at"],payment["created_at"],payment["updated_at"],payment["confirmed_at"],payment["provider_response"]))
                audit(con,"customer","create","payment_attempt",payment["id"],{"provider":"scb_maemanee","order_id":oid,"amount":payment["amount"]})
            self.json({"payment":payment_public(payment)},201)
    def scb_payment_callback(self,form,raw):
        secret=env("SCB_WEBHOOK_SECRET"); signature=self.headers.get(env("SCB_WEBHOOK_SIGNATURE_HEADER","X-SCB-Signature"),"")
        if SCB_ENABLED and not secret: return self.json({"error":"SCB webhook secret ยังไม่ได้ตั้งค่า"},503)
        if not secret or not signature: return self.json({"error":"SCB callback ไม่มีลายเซ็น"},401)
        expected=hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest(); supplied=signature.removeprefix("sha256=")
        if not secrets.compare_digest(expected,supplied): return self.json({"error":"ลายเซ็น SCB ไม่ถูกต้อง"},401)
        data=form.get("data",form) if isinstance(form.get("data",form),dict) else form
        provider_order=str(data.get("orderId") or data.get("transactionId") or "")
        if not provider_order: return self.json({"error":"SCB callback ไม่มี order identifier"},400)
        with db() as con:
            payment=con.execute("SELECT * FROM payment_attempts WHERE provider LIKE 'scb_%' AND provider_order_id=?",(provider_order,)).fetchone()
            if not payment: return self.json({"error":"ไม่พบ payment attempt"},404)
            payment=dict(payment)
        try: response,paid=scb_inquire_payment(payment)
        except ValueError as error: return self.json({"error":str(error)},503)
        with STORE_LOCK,db(immediate=True) as con:
            current=row_payment(con,payment["id"])
            if paid and current["status"] in {"created","pending"}:
                record_verified_scb_payment(
                    con,
                    current,
                    response,
                    "scb_webhook",
                    "payment_confirmed",
                    {
                        "provider_order_id":provider_order,
                        "signature_verified":True,
                    },
                )
            elif not paid: con.execute("UPDATE payment_attempts SET updated_at=?,provider_response=? WHERE id=?",(utcnow(),json.dumps(response,ensure_ascii=False),current["id"]));audit(con,"scb_webhook","payment_callback_pending","payment_attempt",current["id"],{"provider_order_id":provider_order})
        self.json({"status":"paid" if paid else "pending"})
    def inquire_scb_payment(self,payment_id,role):
        with db() as con:
            payment=row_payment(con,payment_id)
            if not payment or not payment["provider"].startswith("scb_"): return self.json({"error":"ไม่พบ SCB payment attempt"},404)
            if payment["status"]=="paid": return self.json({"payment":payment_public(payment),"inquiry":"already_paid"})
        response,paid=scb_inquire_payment(payment)
        with STORE_LOCK,db(immediate=True) as con:
            current=row_payment(con,payment_id)
            if paid and current["status"] in {"created","pending"}:
                record_verified_scb_payment(
                    con,current,response,role,"payment_inquiry_paid"
                )
            elif not paid: con.execute("UPDATE payment_attempts SET updated_at=?,provider_response=? WHERE id=?",(utcnow(),json.dumps(response,ensure_ascii=False),payment_id));audit(con,role,"payment_inquiry_pending","payment_attempt",payment_id)
            result={"payment":payment_public(row_payment(con,payment_id)),"inquiry":"paid" if paid else "pending"}
        return self.json(result)
    def lookup_order(self,form):
        oid=str(form.get("order_id","")).upper().strip(); phone=re.sub(r"[^0-9+]","",str(form.get("phone","")))
        with db() as con:
            order=row_order(con,oid)
            if order and secrets.compare_digest(order["customer"]["phone"],phone):
                customer=con.execute("SELECT points_balance FROM customers WHERE phone=?",(phone,)).fetchone()
                return self.json({"order":public_order(order),"can_cancel":order["status"] in {"new","confirmed"} and order["payment"]["status"]!="paid","loyalty":{"points_balance":int(customer["points_balance"]) if customer else 0,"point_value_thb":1}})
        self.json({"error":"ไม่พบออเดอร์ หรือเบอร์โทรศัพท์ไม่ตรงกัน"},404)
    def cancel_order(self,oid,form):
        phone=re.sub(r"[^0-9+]","",str(form.get("phone","")))
        with STORE_LOCK,db(immediate=True) as con:
            order=row_order(con,oid)
            if not order or not secrets.compare_digest(order["customer"]["phone"],phone):return self.json({"error":"ไม่พบออเดอร์ หรือเบอร์โทรศัพท์ไม่ตรงกัน"},404)
            if order["status"] not in {"new","confirmed"}:raise ValueError("ออเดอร์นี้ไม่สามารถยกเลิกทางออนไลน์ได้")
            if order["payment"]["status"] == "paid":raise ValueError("ออเดอร์นี้ชำระเงินแล้ว กรุณาติดต่อร้านเพื่อดำเนินการคืนเงิน")
            now=utcnow();self.reverse_order_redemptions(con,oid,order,phone,now)
            con.execute("UPDATE orders SET status='cancelled' WHERE id=?",(oid,));con.execute("UPDATE payment_attempts SET status='cancelled',updated_at=? WHERE order_id=? AND status IN ('created','pending')",(now,oid));con.execute("INSERT INTO order_history(order_id,at,status,actor_role) VALUES (?,?,?,?)",(oid,now,"cancelled","customer"));audit(con,"customer","cancel","order",oid)
            response={"order":public_order(row_order(con,oid))}
        return self.json(response)
    def create_menu_item(self,form,role):
        name,description=str(form.get("name","")).strip(),str(form.get("description","")).strip()[:160]
        try:price=int(form.get("price",0))
        except (TypeError,ValueError):raise ValueError("ราคาไม่ถูกต้อง")
        if not 2<=len(name)<=80 or not 0<=price<=10000:raise ValueError("ข้อมูลเมนูไม่ถูกต้อง")
        item={"id":f"item-{secrets.token_hex(3)}","name":name,"description":description,"price":price,"available":True}
        with db() as con: con.execute("INSERT INTO menu_items VALUES (?,?,?,?,?,?,?)",(item["id"],name,description,price,1,utcnow(),utcnow()));audit(con,role,"create","menu_item",item["id"],item)
        self.json({"item":item},201)
    def create_rider(self,form,role):
        name=str(form.get("name","")).strip()[:80]; phone=re.sub(r"[^0-9+]","",str(form.get("phone", "")))
        if len(name)<2: raise ValueError("กรุณาระบุชื่อไรเดอร์")
        rider={"id":f"RDR-{secrets.token_hex(3).upper()}","name":name,"phone":phone}; now=utcnow()
        with db() as con: con.execute("INSERT INTO riders VALUES (?,?,?,?,?,?,?)",(rider["id"],name,phone,1,1,now,now)); audit(con,role,"create","rider",rider["id"],rider)
        self.json({"rider":rider},201)
    def register_rider(self,form):
        name=str(form.get("name","")).strip()[:80]; phone=re.sub(r"[^0-9+]","",str(form.get("phone", ""))); vehicle_type=str(form.get("vehicle_type","")).strip()[:40]; vehicle_plate=str(form.get("vehicle_plate","")).strip()[:20]; note=str(form.get("note","")).strip()[:300]
        if len(name)<2 or not re.fullmatch(r"(?:\+66|0)\d{8,9}",phone) or vehicle_type not in {"motorcycle","bicycle","car"}:raise ValueError("กรุณากรอกข้อมูลสมัครไรเดอร์ให้ครบถ้วน")
        with db(immediate=True) as con:
            pending=con.execute("SELECT 1 FROM rider_applications WHERE phone=? AND status='pending'",(phone,)).fetchone()
            if pending:raise ValueError("มีใบสมัครที่รอตรวจสอบสำหรับเบอร์นี้แล้ว")
            application={"id":f"RAP-{secrets.token_hex(4).upper()}","name":name,"phone":phone,"vehicle_type":vehicle_type,"vehicle_plate":vehicle_plate,"note":note,"status":"pending","created_at":utcnow()}
            con.execute("INSERT INTO rider_applications(id,name,phone,vehicle_type,vehicle_plate,note,status,created_at) VALUES (?,?,?,?,?,?,?,?)",tuple(application[key] for key in ("id","name","phone","vehicle_type","vehicle_plate","note","status","created_at")));audit(con,"rider","register","rider_application",application["id"],{"vehicle_type":vehicle_type})
        self.json({"application":{"id":application["id"],"status":"pending"}},201)
    def update_rider(self,rider_id,form,role):
        if not any(key in form for key in ("active","available")):raise ValueError("ไม่มีข้อมูลไรเดอร์ที่ต้องอัปเดต")
        with db(immediate=True) as con:
            rider=con.execute("SELECT * FROM riders WHERE id=?",(rider_id,)).fetchone()
            if not rider:return self.json({"error":"ไม่พบไรเดอร์"},404)
            active=int(parse_bool(form.get("active"),bool(rider["active"])));available=int(parse_bool(form.get("available"),bool(rider["available"]))) if active else 0
            has_active_delivery=con.execute(
                "SELECT 1 FROM deliveries WHERE rider_id=? AND status IN (?,?,?) LIMIT 1",
                (rider_id,*ACTIVE_DELIVERY_STATUSES),
            ).fetchone()
            if has_active_delivery and (not active or available):raise ValueError("ไรเดอร์ยังมีงานจัดส่งที่ต้องโอนย้ายหรือปิดก่อน")
            con.execute("UPDATE riders SET active=?,available=?,updated_at=? WHERE id=?",(active,available,utcnow(),rider_id));audit(con,role,"update","rider",rider_id,{"active":bool(active),"available":bool(available)})
            response={"rider":dict(con.execute("SELECT * FROM riders WHERE id=?",(rider_id,)).fetchone())}
        return self.json(response)
    def review_rider_application(self,application_id,form,role):
        decision=str(form.get("status","")).strip()
        if decision not in {"approved","rejected"}:raise ValueError("สถานะการสมัครไม่ถูกต้อง")
        with db(immediate=True) as con:
            application=con.execute("SELECT * FROM rider_applications WHERE id=?",(application_id,)).fetchone()
            if not application:return self.json({"error":"ไม่พบใบสมัครไรเดอร์"},404)
            if application["status"]!="pending":raise ValueError("ใบสมัครนี้ได้รับการพิจารณาแล้ว")
            rider_id=""
            if decision=="approved":
                rider_id=f"RDR-{secrets.token_hex(3).upper()}"; now=utcnow();con.execute("INSERT INTO riders VALUES (?,?,?,?,?,?,?)",(rider_id,application["name"],application["phone"],1,1,now,now))
            con.execute("UPDATE rider_applications SET status=?,rider_id=?,reviewed_at=?,reviewed_by=? WHERE id=?",(decision,rider_id,utcnow(),role,application_id));audit(con,role,decision,"rider_application",application_id,{"rider_id":rider_id})
            response={"application":dict(con.execute("SELECT * FROM rider_applications WHERE id=?",(application_id,)).fetchone())}
        return self.json(response)
    def register_merchant(self,form):
        business_name=str(form.get("business_name","")).strip()[:160];owner_name=str(form.get("owner_name","")).strip()[:80];phone=re.sub(r"[^0-9+]","",str(form.get("phone", "")));email=str(form.get("email","")).strip()[:160];address=str(form.get("address","")).strip()[:500];category=str(form.get("category","")).strip()[:80];note=str(form.get("note","")).strip()[:300]
        if len(business_name)<2 or len(owner_name)<2 or not re.fullmatch(r"(?:\+66|0)\d{8,9}",phone) or len(address)<5 or len(category)<2:raise ValueError("กรุณากรอกข้อมูลสมัครร้านค้าให้ครบถ้วน")
        if email and not valid_email(email):raise ValueError("อีเมลไม่ถูกต้อง")
        with db(immediate=True) as con:
            pending=con.execute("SELECT 1 FROM merchant_applications WHERE phone=? AND status='pending'",(phone,)).fetchone()
            if pending:raise ValueError("มีใบสมัครร้านค้าที่รอตรวจสอบสำหรับเบอร์นี้แล้ว")
            application={"id":f"MAP-{secrets.token_hex(4).upper()}","business_name":business_name,"owner_name":owner_name,"phone":phone,"email":email,"address":address,"category":category,"note":note,"status":"pending","created_at":utcnow()}
            con.execute("INSERT INTO merchant_applications(id,business_name,owner_name,phone,email,address,category,note,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",tuple(application[key] for key in ("id","business_name","owner_name","phone","email","address","category","note","status","created_at")));audit(con,"merchant","register","merchant_application",application["id"],{"category":category})
        self.json({"application":{"id":application["id"],"status":"pending"}},201)
    def review_merchant_application(self,application_id,form,role):
        decision=str(form.get("status","")).strip()
        if decision not in {"approved","rejected"}:raise ValueError("สถานะการสมัครไม่ถูกต้อง")
        with db(immediate=True) as con:
            application=con.execute("SELECT * FROM merchant_applications WHERE id=?",(application_id,)).fetchone()
            if not application:return self.json({"error":"ไม่พบใบสมัครร้านค้า"},404)
            if application["status"]!="pending":raise ValueError("ใบสมัครนี้ได้รับการพิจารณาแล้ว")
            con.execute("UPDATE merchant_applications SET status=?,reviewed_at=?,reviewed_by=? WHERE id=?",(decision,utcnow(),role,application_id));audit(con,role,decision,"merchant_application",application_id)
            response={"application":dict(con.execute("SELECT * FROM merchant_applications WHERE id=?",(application_id,)).fetchone())}
        return self.json(response)
    def create_delivery_zone(self,form,role):
        if set(form)-{"name","fee","minimum_order"} or not isinstance(form.get("name"),str):raise ValueError("ข้อมูลพื้นที่จัดส่งไม่ถูกต้อง")
        name=" ".join(form.get("name","").split())[:80]
        fee=integer_value(form.get("fee",0),"ค่าจัดส่งไม่ถูกต้อง")
        minimum=integer_value(form.get("minimum_order",0),"ค่าจัดส่งไม่ถูกต้อง")
        if len(name)<2 or fee<0 or minimum<0: raise ValueError("ข้อมูลพื้นที่จัดส่งไม่ถูกต้อง")
        zone={"id":f"ZONE-{secrets.token_hex(3).upper()}","name":name,"fee":fee,"minimum_order":minimum}; now=utcnow()
        with db(immediate=True) as con:
            names=(row["name"].casefold() for row in con.execute("SELECT name FROM delivery_zones WHERE active=1"))
            if name.casefold() in names:raise ValueError("มีพื้นที่จัดส่งชื่อนี้แล้ว")
            con.execute("INSERT INTO delivery_zones VALUES (?,?,?,?,?,?,?)",(zone["id"],name,fee,minimum,1,now,now));audit(con,role,"create","delivery_zone",zone["id"],zone)
        return self.json({"zone":zone},201)
    def create_inventory_item(self,form,role):
        name=str(form.get("name","")).strip()[:100]; unit=str(form.get("unit","")).strip()[:20]
        on_hand=finite_float(form.get("on_hand",0),"จำนวนสต็อกไม่ถูกต้อง")
        reorder=finite_float(form.get("reorder_level",0),"จำนวนสต็อกไม่ถูกต้อง")
        if len(name)<2 or not unit or on_hand<0 or reorder<0:raise ValueError("ข้อมูลวัตถุดิบไม่ถูกต้อง")
        item={"id":f"INV-{secrets.token_hex(3).upper()}","name":name,"unit":unit,"on_hand":on_hand,"reorder_level":reorder};now=utcnow()
        with db() as con:
            con.execute("INSERT INTO inventory_items VALUES (?,?,?,?,?,?,?,?)",(item["id"],name,unit,on_hand,reorder,1,now,now));con.execute("INSERT INTO inventory_movements VALUES (?,?,?,?,?,?,?,?)",(f"MOV-{secrets.token_hex(4).upper()}",item["id"],on_hand,"opening",None,"ยอดยกมา",now,role));audit(con,role,"create","inventory_item",item["id"],item)
        self.json({"item":item},201)
    def adjust_inventory(self,form,role):
        iid=str(form.get("inventory_item_id","")).strip()
        delta=finite_float(form.get("delta",0),"จำนวนปรับสต็อกไม่ถูกต้อง")
        reason=str(form.get("reason","adjustment")).strip()[:80]; note=str(form.get("note","")).strip()[:200]
        if not iid or not delta or not reason:raise ValueError("กรุณาระบุรายการ จำนวน และเหตุผลที่ต้องการปรับ")
        with db(immediate=True) as con:
            item=con.execute("SELECT * FROM inventory_items WHERE id=?",(iid,)).fetchone()
            if not item:return self.json({"error":"ไม่พบวัตถุดิบ"},404)
            next_value=float(item["on_hand"])+delta
            if next_value<0:raise ValueError("สต็อกคงเหลือติดลบไม่ได้")
            now=utcnow();con.execute("UPDATE inventory_items SET on_hand=?,updated_at=? WHERE id=?",(next_value,now,iid));con.execute("INSERT INTO inventory_movements VALUES (?,?,?,?,?,?,?,?)",(f"MOV-{secrets.token_hex(4).upper()}",iid,delta,reason,None,note,now,role));audit(con,role,"adjust","inventory_item",iid,{"delta":delta,"reason":reason})
            response={"item":dict(con.execute("SELECT * FROM inventory_items WHERE id=?",(iid,)).fetchone())}
        return self.json(response)
    def set_menu_recipe(self,form,role):
        menu_item_id=str(form.get("menu_item_id","")).strip(); inventory_item_id=str(form.get("inventory_item_id","")).strip()
        quantity=finite_float(form.get("quantity",0),"จำนวนในสูตรไม่ถูกต้อง")
        if quantity<=0:raise ValueError("จำนวนในสูตรต้องมากกว่า 0")
        with db() as con:
            if not con.execute("SELECT 1 FROM menu_items WHERE id=?",(menu_item_id,)).fetchone() or not con.execute("SELECT 1 FROM inventory_items WHERE id=?",(inventory_item_id,)).fetchone():raise ValueError("ไม่พบเมนูหรือวัตถุดิบ")
            con.execute("INSERT INTO menu_recipes VALUES (?,?,?) ON CONFLICT(menu_item_id,inventory_item_id) DO UPDATE SET quantity=excluded.quantity",(menu_item_id,inventory_item_id,quantity));audit(con,role,"set_recipe","menu_item",menu_item_id,{"inventory_item_id":inventory_item_id,"quantity":quantity})
            response={"recipe":{"menu_item_id":menu_item_id,"inventory_item_id":inventory_item_id,"quantity":quantity}}
        return self.json(response)
    def create_coupon(self,form,role):
        code=str(form.get("code","")).strip().upper(); kind=str(form.get("kind","fixed"))
        try:value,minimum,maximum=int(form.get("value",0)),int(form.get("minimum_order",0)),int(form.get("maximum_uses",0))
        except (ValueError,TypeError):raise ValueError("ข้อมูลคูปองไม่ถูกต้อง")
        starts_at=optional_utc_timestamp(form.get("starts_at"),"ช่วงเวลาคูปองไม่ถูกต้อง")
        ends_at=optional_utc_timestamp(form.get("ends_at"),"ช่วงเวลาคูปองไม่ถูกต้อง")
        if not re.fullmatch(r"[A-Z0-9_-]{3,32}",code) or kind not in {"fixed","percent"} or value<=0 or minimum<0 or maximum<0 or (kind=="percent" and value>100):raise ValueError("ข้อมูลคูปองไม่ถูกต้อง")
        if starts_at and ends_at and starts_at>=ends_at:raise ValueError("เวลาสิ้นสุดคูปองต้องอยู่หลังเวลาเริ่มต้น")
        if ends_at and ends_at<=utcnow():raise ValueError("เวลาสิ้นสุดคูปองต้องอยู่ในอนาคต")
        coupon={"id":f"CPN-{secrets.token_hex(3).upper()}","code":code,"kind":kind,"value":value,"minimum_order":minimum,"maximum_uses":maximum,"starts_at":starts_at,"ends_at":ends_at};
        try:
            with db(immediate=True) as con:con.execute("INSERT INTO coupons VALUES (?,?,?,?,?,?,?,?,?,?,?)",(coupon["id"],code,kind,value,minimum,maximum,0,starts_at,ends_at,1,utcnow()));audit(con,role,"create","coupon",coupon["id"],coupon)
        except sqlite3.IntegrityError:raise ValueError("รหัสคูปองนี้มีอยู่แล้ว")
        self.json({"coupon":coupon},201)
    def update_delivery(self,oid,form,role,area):
        status=str(form.get("status","")).strip(); rider_id=str(form.get("rider_id","")).strip()
        if status and status not in DELIVERY_STATUSES:raise ValueError("สถานะจัดส่งไม่ถูกต้อง")
        if not status and not rider_id:raise ValueError("ไม่มีข้อมูลงานจัดส่งที่ต้องอัปเดต")
        if status and rider_id:raise ValueError("กรุณามอบหมายไรเดอร์และอัปเดตสถานะแยกคำขอ")
        if rider_id and area!="admin":raise ValueError("เฉพาะผู้ดูแลระบบที่มอบหมายไรเดอร์ได้")
        with STORE_LOCK,db(immediate=True) as con:
            delivery=con.execute("SELECT * FROM deliveries WHERE order_id=?",(oid,)).fetchone()
            if not delivery:return self.json({"error":"ไม่พบงานจัดส่ง"},404)
            transitions={"queued":{"assigned","cancelled"},"assigned":{"picked_up","cancelled"},"picked_up":{"on_the_way","failed"},"on_the_way":{"delivered","failed"},"failed":{"queued"},"delivered":set(),"cancelled":set()}
            if status and status != delivery["status"] and status not in transitions.get(delivery["status"],set()): raise ValueError("ลำดับสถานะจัดส่งไม่ถูกต้อง")
            if rider_id:
                if delivery["status"] not in {"queued","assigned"}:raise ValueError("ไม่สามารถเปลี่ยนไรเดอร์หลังเริ่มจัดส่ง")
                rider=con.execute("SELECT * FROM riders WHERE id=? AND active=1",(rider_id,)).fetchone()
                if not rider:raise ValueError("ไม่พบไรเดอร์")
                if rider_id!=delivery["rider_id"]:
                    already_assigned=con.execute(
                        "SELECT 1 FROM deliveries WHERE rider_id=? AND status IN (?,?,?) AND order_id<>? LIMIT 1",
                        (rider_id,*ACTIVE_DELIVERY_STATUSES,oid),
                    ).fetchone()
                    if not rider["available"] or already_assigned:raise ValueError("ไรเดอร์ไม่พร้อมรับงาน")
                    now=utcnow()
                    if delivery["rider_id"]:
                        con.execute("UPDATE riders SET available=1,updated_at=? WHERE id=?",(now,delivery["rider_id"]))
                    con.execute("UPDATE riders SET available=0,updated_at=? WHERE id=?",(now,rider_id))
                    con.execute("UPDATE deliveries SET rider_id=?,status='assigned',assigned_at=?,updated_at=? WHERE order_id=?",(rider_id,now,now,oid))
                status="assigned"
            if status:
                now=utcnow(); columns={"picked_up":"picked_up_at","delivered":"delivered_at"};sql="UPDATE deliveries SET status=?,updated_at=?";params=[status,now]
                if status in columns:sql+=f",{columns[status]}=?";params.append(now)
                if status=="delivered":
                    if not delivery["rider_id"]: raise ValueError("ต้องมอบหมายไรเดอร์ก่อนปิดงานจัดส่ง")
                    order=row_order(con,oid)
                    if not order:return self.json({"error":"ไม่พบออเดอร์"},404)
                    if order["status"] in {"cancelled","completed"}:raise ValueError("ออเดอร์นี้ปิดแล้ว ไม่สามารถส่งสำเร็จซ้ำได้")
                    if order["payment"]["status"]!="paid":raise ValueError("ต้องยืนยันการชำระเงินก่อนปิดงานจัดส่ง")
                if status in {"failed","cancelled"}:sql+=",rider_id=NULL"
                sql+=" WHERE order_id=?";params.append(oid);con.execute(sql,params)
                if status in {"delivered","failed","cancelled"} and delivery["rider_id"]:
                    con.execute("UPDATE riders SET available=1,updated_at=? WHERE id=?",(now,delivery["rider_id"]))
                if status=="delivered":
                    con.execute("UPDATE orders SET status='completed' WHERE id=?",(oid,)); con.execute("INSERT INTO order_history(order_id,at,status,actor_role,note) VALUES (?,?,?,?,?)",(oid,now,"completed",role,"delivery_delivered")); self.complete_order_effects(con,oid,order,role)
            audit(con,role,"delivery_update","delivery",oid,{"status":status,"rider_id":rider_id});response={"order":row_order(con,oid)}
        return self.json(response)
    def issue_receipt(self,oid,form,role):
        with db(immediate=True) as con:
            order=row_order(con,oid)
            if not order:return self.json({"error":"ไม่พบออเดอร์"},404)
            existing=con.execute("SELECT * FROM pos_receipts WHERE order_id=?",(oid,)).fetchone()
            if existing:return self.json({"receipt":dict(existing)})
            if order["status"]=="cancelled":raise ValueError("ออเดอร์ถูกยกเลิกแล้ว ไม่สามารถออกใบเสร็จได้")
            if order["payment"]["status"]!="paid":raise ValueError("ต้องยืนยันการชำระเงินก่อนออกใบเสร็จ")
            finance=order["financial"]; now=utcnow(); receipt={"id":f"RCT-{secrets.token_hex(4).upper()}","receipt_number":f"MP-{datetime.now():%Y%m%d}-{secrets.token_hex(3).upper()}","order_id":oid,"customer_tax_name":str(form.get("customer_tax_name","")).strip()[:160],"customer_tax_id":re.sub(r"[^0-9]","",str(form.get("customer_tax_id", "")))[:13],"subtotal":finance["subtotal"],"discount":finance["discount"],"delivery_fee":finance["delivery_fee"],"total":finance["total"],"issued_at":now,"issued_by":role}
            con.execute("INSERT INTO pos_receipts VALUES (?,?,?,?,?,?,?,?,?,?,?)",tuple(receipt[key] for key in ("id","order_id","receipt_number","customer_tax_name","customer_tax_id","subtotal","discount","delivery_fee","total","issued_at","issued_by")));audit(con,role,"issue","pos_receipt",receipt["id"],{"order_id":oid})
        return self.json({"receipt":receipt},201)
    def update_business_profile(self,form,role):
        text_fields=("legal_name","tax_id","address","branch")
        if not {"legal_name","address","vat_registered"}<=set(form) or set(form)-set(text_fields)-{"vat_registered"}:raise ValueError("ข้อมูลผู้ขายไม่ถูกต้อง")
        if any(key in form and not isinstance(form[key],str) for key in text_fields):raise ValueError("ข้อมูลผู้ขายไม่ถูกต้อง")
        legal_name=" ".join(form.get("legal_name","").split())
        tax_id=form.get("tax_id","").strip()
        address=form.get("address","").strip()
        branch=" ".join(form.get("branch","สำนักงานใหญ่").split()) or "สำนักงานใหญ่"
        vat_registered=parse_bool(form.get("vat_registered"),False)
        if not 2<=len(legal_name)<=160 or not 5<=len(address)<=500 or len(branch)>80:raise ValueError("กรุณาระบุชื่อกิจการและที่อยู่ให้ถูกต้อง")
        if tax_id and not re.fullmatch(r"\d{13}",tax_id):raise ValueError("เลขประจำตัวผู้เสียภาษีต้องมี 13 หลัก")
        if vat_registered and not tax_id:raise ValueError("เลขประจำตัวผู้เสียภาษีต้องมี 13 หลัก")
        profile={"legal_name":legal_name,"tax_id":tax_id,"address":address,"branch":branch,"vat_registered":vat_registered,"vat_rate":7}
        with db(immediate=True) as con:
            set_setting(con,"business_profile",profile)
            audit(con,role,"update","business_profile","store",{"fields":["legal_name","tax_id","address","branch","vat_registered"],"vat_registered":vat_registered})
        return self.json({"business_profile":profile})
    def update_delivery_pricing(self,form,role):
        try:
            base_fee=int(form.get("base_fee",0))
        except (ValueError,TypeError):raise ValueError("อัตราค่าส่งไม่ถูกต้อง")
        per_km_fee=finite_float(form.get("per_km_fee",0),"อัตราค่าส่งไม่ถูกต้อง")
        maximum_km=finite_float(form.get("maximum_km",0),"อัตราค่าส่งไม่ถูกต้อง")
        if base_fee<0 or per_km_fee<0 or not 0<maximum_km<=100:raise ValueError("อัตราค่าส่งไม่ถูกต้อง")
        mode=str(form.get("mode","distance")).strip().lower()
        if mode not in {"distance","zone"}: raise ValueError("โหมดค่าส่งไม่ถูกต้อง")
        profile={"mode":mode,"base_fee":base_fee,"per_km_fee":per_km_fee,"maximum_km":maximum_km,"store_latitude":valid_coordinate(form.get("store_latitude"),-90,90) if mode=="distance" else None,"store_longitude":valid_coordinate(form.get("store_longitude"),-180,180) if mode=="distance" else None}
        with db() as con:set_setting(con,"delivery_pricing",profile);audit(con,role,"update","delivery_pricing","store",{key:profile[key] for key in ("base_fee","per_km_fee","maximum_km")})
        self.json({"delivery_pricing":profile})
    def issue_tax_invoice(self,receipt_id,form,role):
        with STORE_LOCK,db(immediate=True) as con:
            receipt=con.execute("SELECT * FROM pos_receipts WHERE id=?",(receipt_id,)).fetchone()
            if not receipt:return self.json({"error":"ไม่พบใบเสร็จ"},404)
            existing=con.execute("SELECT * FROM tax_invoices WHERE receipt_id=?",(receipt_id,)).fetchone()
            created=not existing
            if existing:invoice=dict(existing)
            else:
                profile=config(con)["business_profile"]
                if not profile.get("vat_registered") or len(profile.get("tax_id", ""))!=13 or not profile.get("legal_name") or not profile.get("address"):raise ValueError("กรุณาตั้งค่าข้อมูลผู้ขายจด VAT ให้ครบก่อนออกใบกำกับภาษี")
                buyer_name=str(form.get("buyer_name",receipt["customer_tax_name"])).strip()[:160];buyer_tax_id=re.sub(r"[^0-9]","",str(form.get("buyer_tax_id",receipt["customer_tax_id"])))[:13];buyer_address=str(form.get("buyer_address","")).strip()[:500]
                if not buyer_name:raise ValueError("กรุณาระบุชื่อผู้ซื้อสำหรับใบกำกับภาษี")
                total=int(receipt["total"]); vat_rate=int(profile["vat_rate"]); before_vat=round(total*100/(100+vat_rate)); vat_amount=total-before_vat; today=datetime.now().strftime("%Y%m%d"); sequence=con.execute("SELECT COUNT(*) FROM tax_invoices WHERE tax_invoice_number LIKE ?",(f"TIV-{today}-%",)).fetchone()[0]+1
                invoice={"receipt_id":receipt_id,"tax_invoice_number":f"TIV-{today}-{sequence:04d}","seller_name":profile["legal_name"],"seller_tax_id":profile["tax_id"],"seller_address":profile["address"],"seller_branch":profile["branch"],"buyer_name":buyer_name,"buyer_tax_id":buyer_tax_id,"buyer_address":buyer_address,"amount_before_vat":before_vat,"vat_rate":vat_rate,"vat_amount":vat_amount,"total":total,"issued_at":utcnow()}
                con.execute("INSERT INTO tax_invoices VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",tuple(invoice.values()));audit(con,role,"issue","tax_invoice",invoice["tax_invoice_number"],{"receipt_id":receipt_id})
        return self.json({"tax_invoice":invoice},201 if created else 200)
    def print_receipt(self,con,receipt_id,conf):
        receipt=con.execute("SELECT * FROM pos_receipts WHERE id=?",(receipt_id,)).fetchone()
        if not receipt:return self.html("<h1>Receipt not found</h1>",404)
        invoice=con.execute("SELECT * FROM tax_invoices WHERE receipt_id=?",(receipt_id,)).fetchone(); order=row_order(con,receipt["order_id"])
        lines="".join(f"<tr><td>{escape_html(item['name'])}</td><td>{item['quantity']}</td><td>{item['unit_price']}</td><td>{item['quantity']*item['unit_price']}</td></tr>" for item in order["items"])
        tax="" if not invoice else f"<h2>ใบกำกับภาษี / TAX INVOICE</h2><p>เลขที่ {escape_html(invoice['tax_invoice_number'])}<br>ผู้ขาย: {escape_html(invoice['seller_name'])}<br>เลขประจำตัวผู้เสียภาษี: {escape_html(invoice['seller_tax_id'])}<br>ที่อยู่: {escape_html(invoice['seller_address'])}<br>ผู้ซื้อ: {escape_html(invoice['buyer_name'])}</p><p>มูลค่าก่อน VAT {invoice['amount_before_vat']} · VAT {invoice['vat_rate']}% {invoice['vat_amount']} · รวม {invoice['total']} บาท</p>"
        nonce=secrets.token_urlsafe(18)
        return self.html(f"<!doctype html><meta charset='utf-8'><title>{escape_html(receipt['receipt_number'])}</title><style>body{{font-family:sans-serif;max-width:720px;margin:32px auto}}table{{width:100%;border-collapse:collapse}}td,th{{padding:7px;border-bottom:1px solid #ddd;text-align:left}}@media print{{button{{display:none}}}}</style><button id='print-receipt' type='button'>พิมพ์</button><h1>{escape_html(conf['store_name'])}</h1><h2>ใบเสร็จรับเงิน / RECEIPT</h2><p>เลขที่ {escape_html(receipt['receipt_number'])}<br>ออเดอร์ {escape_html(receipt['order_id'])}<br>ออกเมื่อ {escape_html(receipt['issued_at'])}</p><table><tr><th>รายการ</th><th>จำนวน</th><th>ราคา</th><th>รวม</th></tr>{lines}</table><p>สินค้า {receipt['subtotal']} · ส่วนลด {receipt['discount']} · ค่าส่ง {receipt['delivery_fee']}<br><strong>รวมทั้งสิ้น {receipt['total']} บาท</strong></p>{tax}<script nonce='{nonce}'>document.getElementById('print-receipt').addEventListener('click',()=>window.print());</script>",script_nonce=nonce)
    def update_order(self,oid,form,role,area):
        allowed={"admin":set(STATUS),"staff":{"confirmed","ready","completed"},"kitchen":{"ready"}}[area]
        status=str(form.get("status", "")); payment=str(form.get("payment_status", ""))
        if status and status not in allowed:raise ValueError("คุณไม่มีสิทธิ์เปลี่ยนสถานะนี้")
        if payment and (area!="admin" or payment not in PAYMENT_STATUSES):raise ValueError("สถานะชำระเงินไม่ถูกต้อง")
        with STORE_LOCK,db(immediate=True) as con:
            order=row_order(con,oid)
            if not order:return self.json({"error":"ไม่พบออเดอร์"},404)
            if status=="cancelled" and order["payment"]["status"]=="paid":raise ValueError("ออเดอร์นี้ชำระเงินแล้ว กรุณาดำเนินการคืนเงินก่อนยกเลิก")
            if status=="cancelled" and order["status"]=="completed":raise ValueError("ออเดอร์ที่เสร็จแล้วไม่สามารถยกเลิกได้")
            if status=="completed" and order["status"] in {"cancelled","completed"}:raise ValueError("ออเดอร์นี้ปิดแล้ว ไม่สามารถปิดซ้ำได้")
            current_payment=order["payment"]["status"]
            if payment and current_payment=="refunded" and payment!="refunded":raise ValueError("การชำระเงินที่คืนเงินแล้วไม่สามารถเปลี่ยนกลับได้")
            if payment=="refunded" and current_payment!="paid":raise ValueError("ต้องยืนยันยอดชำระเงินก่อนบันทึกการคืนเงิน")
            if payment=="pending" and current_payment in {"paid","refunded"}:raise ValueError("สถานะชำระเงินถอยกลับไม่ได้")
            if status=="completed" and (payment or current_payment)!="paid":raise ValueError("ต้องยืนยันการชำระเงินก่อนปิดออเดอร์")
            transitions={"staff": {("new","confirmed"), ("ready","completed")}, "kitchen": {("confirmed","ready")}}
            if status and area in transitions and (order["status"], status) not in transitions[area]:
                raise ValueError("ลำดับสถานะไม่ถูกต้อง")
            if status and status!=order["status"]:
                con.execute("UPDATE orders SET status=? WHERE id=?",(status,oid));con.execute("INSERT INTO order_history(order_id,at,status,actor_role) VALUES (?,?,?,?)",(oid,utcnow(),status,role));audit(con,role,"status_change","order",oid,{"from":order["status"],"to":status})
                if status=="completed": self.complete_order_effects(con,oid,order,role)
                if status=="cancelled": self.reverse_order_redemptions(con,oid,order,order["customer"]["phone"],utcnow())
            if payment:
                now=utcnow(); con.execute("UPDATE orders SET payment_status=? WHERE id=?",(payment,oid))
                if order["payment"]["method"]=="scb_qr" and payment in {"paid","refunded"}:
                    con.execute("UPDATE payment_attempts SET status=?,confirmed_at=CASE WHEN ?='paid' THEN COALESCE(NULLIF(confirmed_at,''),?) ELSE confirmed_at END,updated_at=? WHERE order_id=? AND provider LIKE 'scb_%' AND status NOT IN ('cancelled','expired')",(payment,payment,now,now,oid))
                audit(con,role,"payment_change","order",oid,{"to":payment})
            response={"order":row_order(con,oid)}
        return self.json(response)
    def complete_order_effects(self,con,oid,order,role):
        """Award points and consume recipe stock once, only when the order closes."""
        exists=con.execute("SELECT 1 FROM loyalty_ledger WHERE order_id=? AND reason='order_completed'",(oid,)).fetchone()
        points=int(order["financial"]["points_earned"])
        if points and not exists:
            phone=order["customer"]["phone"]; now=utcnow();con.execute("UPDATE customers SET points_balance=points_balance+?,updated_at=? WHERE phone=?",(points,now,phone));con.execute("INSERT INTO loyalty_ledger VALUES (?,?,?,?,?,?)",(f"LOY-{secrets.token_hex(4).upper()}",phone,points,"order_completed",oid,now))
        consumed=con.execute("SELECT 1 FROM inventory_movements WHERE order_id=? AND reason='order_completed' LIMIT 1",(oid,)).fetchone()
        if consumed:return
        for line in order["items"]:
            for recipe in con.execute("SELECT inventory_item_id,quantity FROM menu_recipes WHERE menu_item_id=?",(line["id"],)):
                delta=-float(recipe["quantity"])*int(line["quantity"]); item=con.execute("SELECT on_hand FROM inventory_items WHERE id=?",(recipe["inventory_item_id"],)).fetchone()
                if item:
                    if float(item["on_hand"])+delta < 0: raise ValueError("สต็อกสินค้าไม่เพียงพอสำหรับปิดออเดอร์")
                    con.execute("UPDATE inventory_items SET on_hand=?,updated_at=? WHERE id=?",(float(item["on_hand"])+delta,utcnow(),recipe["inventory_item_id"]));con.execute("INSERT INTO inventory_movements VALUES (?,?,?,?,?,?,?,?)",(f"MOV-{secrets.token_hex(4).upper()}",recipe["inventory_item_id"],delta,"order_completed",oid,"ตัดตามสูตรอาหาร",utcnow(),role))
    def reverse_order_redemptions(self,con,oid,order,phone,now):
        """Return reserved points and coupon use exactly once when an order is cancelled."""
        points=int(order["financial"]["points_redeemed"])
        restored=con.execute("SELECT 1 FROM loyalty_ledger WHERE order_id=? AND reason='order_cancelled_restore'",(oid,)).fetchone()
        if points and not restored:
            con.execute("UPDATE customers SET points_balance=points_balance+?,updated_at=? WHERE phone=?",(points,now,phone));con.execute("INSERT INTO loyalty_ledger VALUES (?,?,?,?,?,?)",(f"LOY-{secrets.token_hex(4).upper()}",phone,points,"order_cancelled_restore",oid,now))
        redemption=con.execute("SELECT coupon_id FROM coupon_redemptions WHERE order_id=?",(oid,)).fetchone()
        if redemption:con.execute("UPDATE coupons SET used_count=MAX(0,used_count-1) WHERE id=?",(redemption["coupon_id"],));con.execute("DELETE FROM coupon_redemptions WHERE order_id=?",(oid,))
    def update_menu_item(self,iid,form,role):
        supported=("name","description","price","available")
        changed=[key for key in supported if key in form]
        if not changed:raise ValueError("ไม่มีข้อมูลเมนูที่รองรับให้อัปเดต")
        with db(immediate=True) as con:
            item=con.execute("SELECT * FROM menu_items WHERE id=?",(iid,)).fetchone()
            if not item:return self.json({"error":"ไม่พบเมนู"},404)
            name=str(form.get("name",item["name"])).strip()[:80];desc=str(form.get("description",item["description"])).strip()[:160]
            try:price=int(form.get("price",item["price"]))
            except (TypeError,ValueError):raise ValueError("ราคาไม่ถูกต้อง")
            available=int(parse_bool(form.get("available"),bool(item["available"])))
            if len(name)<2 or not 0<=price<=10000:raise ValueError("ข้อมูลเมนูไม่ถูกต้อง")
            con.execute("UPDATE menu_items SET name=?,description=?,price=?,available=?,updated_at=? WHERE id=?",(name,desc,price,available,utcnow(),iid));audit(con,role,"update","menu_item",iid,{"keys":changed})
            response={"item":{"id":iid,"name":name,"description":desc,"price":price,"available":bool(available)}}
        return self.json(response)
    def update_settings(self,form,role):
        supported=("slot_capacity","advance_days")
        changed=[key for key in supported if key in form]
        if not changed:raise ValueError("ไม่มีการตั้งค่าที่รองรับให้อัปเดต")
        with db() as con:
            for key, maximum in (("slot_capacity",500),("advance_days",60)):
                if key in form:
                    try:value=int(form[key])
                    except (TypeError,ValueError):raise ValueError("ค่าการตั้งค่าไม่ถูกต้อง")
                    if not 1<=value<=maximum:raise ValueError("ค่าการตั้งค่าไม่ถูกต้อง")
                    set_setting(con,key,value)
            audit(con,role,"update","settings","store",{"keys":changed})
            response={"settings":config(con)}
        return self.json(response)

class BoundedHTTPServer(ThreadingHTTPServer):
    daemon_threads=True
    request_queue_size=64
    def get_request(self):
        request, address = super().get_request()
        request.settimeout(30)
        return request, address

def summary(rows):
    active=[row for row in rows if row["status"]!="cancelled"]
    return {"orders":len(rows),"active_orders":len(active),"revenue":sum(row["total"] for row in active),"ready":sum(row["status"]=="ready" for row in active),"new":sum(row["status"]=="new" for row in active),"completed":sum(row["status"]=="completed" for row in active)}

if __name__=="__main__":
    host=os.environ.get("HOST","127.0.0.1")
    defaults=(ADMIN_KEY=="change-me-before-production" or EMPLOYEE_KEY=="change-me-employee-key" or KITCHEN_KEY=="change-me-kitchen-key")
    if defaults and (os.environ.get("REQUIRE_ADMIN_KEY","false").lower()=="true" or host not in {"127.0.0.1","::1","localhost"}):raise SystemExit("Production requires ADMIN_KEY, EMPLOYEE_KEY and KITCHEN_KEY")
    initialise_database(); port=int(os.environ.get("PORT","8000"));print(f"Moo Piw Piw is running at http://{host}:{port}");BoundedHTTPServer((host,port),Handler).serve_forever()
