import { FormEvent, StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { MoopiewClient } from "@moopiew/sdk";
import type {
  CreateOrderInput,
  DeliveryQuote,
  MenuResponse,
  OrderLookupResponse,
  PublicOrder,
  ScbPayment,
  TrackingSnapshot,
} from "@moopiew/types";
import "./styles.css";

const api = new MoopiewClient({
  baseURL: import.meta.env.VITE_API_URL || window.location.origin,
});
const money = (value: number) =>
  new Intl.NumberFormat("th-TH", {
    style: "currency",
    currency: "THB",
    maximumFractionDigits: 0,
  }).format(value);
const tomorrow = () => {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
};
const messageOf = (error: unknown) =>
  error instanceof Error ? error.message : "เกิดข้อผิดพลาด กรุณาลองใหม่";

function OrderSummary({ order }: { order: PublicOrder }) {
  const delivery =
    order.fulfillment.type === "delivery" ? order.fulfillment.delivery : undefined;
  return (
    <div className="order-summary">
      <div>
        <span>ORDER</span>
        <strong>{order.id}</strong>
      </div>
      <p>
        {order.items.map((item) => `${item.name} × ${item.quantity}`).join(" · ")}
      </p>
      <dl>
        <div><dt>สถานะ</dt><dd>{order.status}</dd></div>
        <div><dt>ยอดสุทธิ</dt><dd>{money(order.total)}</dd></div>
        <div>
          <dt>{delivery ? "การจัดส่ง" : "วันและเวลารับ"}</dt>
          <dd>
            {delivery
              ? `${delivery.zone_name} · ${delivery.status}`
              : `${order.pickup.date} · ${order.pickup.slot}`}
          </dd>
        </div>
      </dl>
    </div>
  );
}

function TrackingCard({ code }: { code: string }) {
  const [snapshot, setSnapshot] = useState<TrackingSnapshot>();
  const [reconnecting, setReconnecting] = useState(false);
  useEffect(() => {
    api.delivery.tracking(code).then(setSnapshot).catch(() => undefined);
    return api.delivery.subscribe(
      code,
      (next) => {
        setSnapshot(next);
        setReconnecting(false);
      },
      () => setReconnecting(true),
    );
  }, [code]);
  return (
    <div className="tracking-live" aria-live="polite">
      <span className={`live-dot ${reconnecting ? "waiting" : ""}`} />
      <div>
        <small>{reconnecting ? "กำลังเชื่อมต่อใหม่" : "LIVE DELIVERY"}</small>
        <strong>{snapshot?.tracking.status ?? "กำลังโหลดสถานะ"}</strong>
        {snapshot?.tracking.rider_name && <p>ไรเดอร์ {snapshot.tracking.rider_name}</p>}
      </div>
    </div>
  );
}

function App() {
  const [date, setDate] = useState(tomorrow);
  const [menu, setMenu] = useState<MenuResponse>();
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [fulfillment, setFulfillment] = useState<"pickup" | "delivery">("pickup");
  const [location, setLocation] = useState<{ latitude: number; longitude: number }>();
  const [quote, setQuote] = useState<DeliveryQuote>();
  const [paymentEnabled, setPaymentEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState<PublicOrder>();
  const [payment, setPayment] = useState<ScbPayment>();
  const [lookup, setLookup] = useState<OrderLookupResponse>();
  const [lookupPhone, setLookupPhone] = useState("");

  useEffect(() => {
    setError("");
    api.menus.get(date).then(setMenu).catch((reason) => setError(messageOf(reason)));
  }, [date]);
  useEffect(() => {
    api.payments.scbConfig()
      .then((config) => setPaymentEnabled(config.enabled))
      .catch(() => setPaymentEnabled(false));
  }, []);

  const subtotal = useMemo(
    () =>
      (menu?.items ?? []).reduce(
        (sum, item) => sum + item.price * (quantities[item.id] ?? 0),
        0,
      ),
    [menu, quantities],
  );
  const count = Object.values(quantities).reduce((sum, value) => sum + value, 0);
  const updateQuantity = (id: string, delta: number) =>
    setQuantities((current) => ({
      ...current,
      [id]: Math.max(0, (current[id] ?? 0) + delta),
    }));

  async function requestLocation(zoneId: string) {
    setQuote(undefined);
    setError("");
    if (!zoneId) return;
    if (!navigator.geolocation) {
      setError("เบราว์เซอร์นี้ไม่รองรับการระบุตำแหน่ง");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        const next = { latitude: coords.latitude, longitude: coords.longitude };
        setLocation(next);
        try {
          setQuote(await api.delivery.quote({ zone_id: zoneId, subtotal, ...next }));
        } catch (reason) {
          setError(messageOf(reason));
        }
      },
      () => setError("ไม่สามารถอ่านตำแหน่งได้ กรุณาอนุญาต location แล้วลองใหม่"),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const items = Object.entries(quantities)
      .filter(([, quantity]) => quantity > 0)
      .map(([id, quantity]) => ({ id, quantity }));
    if (!items.length) {
      setError("กรุณาเลือกอย่างน้อย 1 รายการ");
      return;
    }
    const payload: CreateOrderInput = {
      name: String(form.get("name") ?? ""),
      phone: String(form.get("phone") ?? ""),
      fulfillment_type: fulfillment,
      payment_method: String(form.get("payment_method")) as CreateOrderInput["payment_method"],
      items,
      coupon_code: String(form.get("coupon_code") ?? ""),
      points_to_redeem: Number(form.get("points_to_redeem") ?? 0),
      notes: String(form.get("notes") ?? ""),
      ...(fulfillment === "pickup"
        ? { pickup_date: date, pickup_slot: String(form.get("pickup_slot") ?? "") }
        : {
            delivery_zone_id: String(form.get("delivery_zone_id") ?? ""),
            recipient_name:
              String(form.get("recipient_name") ?? "").trim() ||
              String(form.get("name") ?? ""),
            recipient_phone:
              String(form.get("recipient_phone") ?? "").trim() ||
              String(form.get("phone") ?? ""),
            delivery_address: String(form.get("delivery_address") ?? ""),
            delivery_landmark: String(form.get("delivery_landmark") ?? ""),
            delivery_latitude: location?.latitude,
            delivery_longitude: location?.longitude,
          }),
    };
    setBusy(true);
    setError("");
    setPayment(undefined);
    try {
      const result = await api.orders.create(payload);
      setCreated(result.order);
      if (payload.payment_method === "scb_qr") {
        const response = await api.orders.createScbQr(result.order.id, payload.phone);
        setPayment(response.payment);
      }
      setQuantities({});
      setMenu(await api.menus.get(date));
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setBusy(false);
    }
  }

  async function lookupOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const phone = String(form.get("phone") ?? "");
    setLookupPhone(phone);
    setError("");
    try {
      setLookup(await api.orders.lookup(String(form.get("order_id") ?? ""), phone));
    } catch (reason) {
      setLookup(undefined);
      setError(messageOf(reason));
    }
  }

  async function cancelOrder() {
    if (!lookup || !window.confirm("ยืนยันการยกเลิกออเดอร์นี้?")) return;
    try {
      const result = await api.orders.cancel(lookup.order.id, lookupPhone);
      setLookup({ ...lookup, order: result.order, can_cancel: false });
      setMenu(await api.menus.get(date));
    } catch (reason) {
      setError(messageOf(reason));
    }
  }

  return (
    <>
      <header className="topbar">
        <a className="wordmark" href="#top">MOOPIEW<span>®</span></a>
        <nav aria-label="เมนูหลัก">
          <a href="#menu">เมนู</a>
          <a href="#tracking">ติดตามออเดอร์</a>
          <a className="nav-cta" href="#checkout">สั่งเลย · {count}</a>
        </nav>
      </header>
      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">CHARCOAL GRILL · ORDER AHEAD</p>
            <h1>มื้ออร่อย<br /><em>ตรงเวลา</em></h1>
            <p>เลือกเมนูสด จองรอบรับ หรือส่งถึงบ้าน พร้อมคำนวณค่าส่งจากระบบร้านโดยตรง</p>
            <a className="button" href="#menu">เริ่มเลือกเมนู <span>↓</span></a>
          </div>
          <div className="hero-visual">
            <img src="/images/moopiew-hero.png" alt="หมูปิ้งย่างสดบนเตาถ่าน" />
            <div className="hero-ticket"><small>LIVE STORE</small><strong>{menu?.store_name ?? "หมูปิ้ววว"}</strong></div>
          </div>
        </section>

        <form className="commerce-shell" onSubmit={submitOrder}>
          <section id="menu" className="catalog">
            <div className="section-heading">
              <div><p className="eyebrow">01 · SELECT</p><h2>เลือกของอร่อย</h2></div>
              <label className="date-control">วันที่รับ<input type="date" min={tomorrow()} value={date} onChange={(event) => setDate(event.target.value)} /></label>
            </div>
            {!menu && !error && <p className="loading">กำลังโหลดเมนูสดจากร้าน…</p>}
            <div className="menu-grid">
              {menu?.items.filter((item) => item.available).map((item, index) => {
                const quantity = quantities[item.id] ?? 0;
                return <article className={`menu-card ${quantity ? "selected" : ""}`} key={item.id}>
                  <span className="card-index">{String(index + 1).padStart(2, "0")}</span>
                  <div><h3>{item.name}</h3><p>{item.description}</p></div>
                  <div className="menu-card-footer"><strong>{money(item.price)}</strong><div className="stepper"><button type="button" onClick={() => updateQuantity(item.id, -1)} aria-label={`ลด ${item.name}`}>−</button><output>{quantity}</output><button type="button" onClick={() => updateQuantity(item.id, 1)} aria-label={`เพิ่ม ${item.name}`}>+</button></div></div>
                </article>;
              })}
            </div>
          </section>

          <aside id="checkout" className="checkout">
            <div className="checkout-title"><p className="eyebrow">02 · CHECKOUT</p><h2>ยืนยันออเดอร์</h2></div>
            <div className="choice-tabs">
              <button type="button" className={fulfillment === "pickup" ? "active" : ""} onClick={() => { setFulfillment("pickup"); setQuote(undefined); }}>รับที่ร้าน</button>
              <button type="button" className={fulfillment === "delivery" ? "active" : ""} onClick={() => setFulfillment("delivery")}>ส่งถึงบ้าน</button>
            </div>
            <div className="field-grid">
              <label>ชื่อผู้สั่ง<input name="name" minLength={2} required placeholder="ชื่อของคุณ" /></label>
              <label>เบอร์โทร<input name="phone" inputMode="tel" required placeholder="0812345678" /></label>
            </div>
            {fulfillment === "pickup" ? (
              <label>รอบรับ<select name="pickup_slot" required defaultValue=""><option value="" disabled>เลือกรอบที่สะดวก</option>{menu?.slots.map((slot) => <option key={slot.time} value={slot.time} disabled={!slot.available}>{slot.time} · {slot.available ? `เหลือ ${slot.remaining}` : "เต็ม"}</option>)}</select></label>
            ) : (
              <div className="delivery-fields">
                <label>พื้นที่จัดส่ง<select name="delivery_zone_id" required defaultValue="" onChange={(event) => requestLocation(event.target.value)}><option value="" disabled>เลือกพื้นที่และคำนวณค่าส่ง</option>{menu?.delivery_zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name} · เริ่ม {money(zone.fee)}</option>)}</select></label>
                <div className="field-grid"><label>ชื่อผู้รับ<input name="recipient_name" placeholder="ถ้าไม่กรอก ใช้ชื่อผู้สั่ง" /></label><label>เบอร์ผู้รับ<input name="recipient_phone" inputMode="tel" placeholder="ถ้าไม่กรอก ใช้เบอร์ผู้สั่ง" /></label></div>
                <label>ที่อยู่จัดส่ง<textarea name="delivery_address" required rows={3} placeholder="บ้านเลขที่ ซอย ถนน แขวง/ตำบล เขต/อำเภอ" /></label>
                <label>จุดสังเกต<textarea name="delivery_landmark" rows={2} placeholder="เช่น อาคาร A ชั้น 2" /></label>
                <p className="location-state" aria-live="polite">{quote ? `ระยะทาง ${quote.distance_km} กม. · ค่าส่ง ${money(quote.delivery_fee)}` : "เลือกพื้นที่เพื่ออนุญาตตำแหน่งและคำนวณค่าส่ง"}</p>
              </div>
            )}
            <div className="field-grid"><label>คูปอง<input name="coupon_code" placeholder="MOOPIEW10" /></label><label>ใช้แต้ม<input name="points_to_redeem" type="number" min="0" defaultValue="0" /></label></div>
            <label>วิธีชำระเงิน<select name="payment_method" defaultValue="cash"><option value="cash">จ่ายเมื่อรับสินค้า</option><option value="transfer">โอนเงิน</option>{paymentEnabled && <option value="scb_qr">PromptPay / SCB QR</option>}</select></label>
            <label>หมายเหตุ<textarea name="notes" rows={2} maxLength={300} placeholder="เช่น ไม่เอามัน" /></label>
            <div className="total"><span><small>{count} รายการ</small>ยอดรวมโดยประมาณ</span><strong>{money(subtotal + (quote?.delivery_fee ?? 0))}</strong></div>
            {error && <p className="error" role="alert">{error}</p>}
            <button className="submit-button" disabled={busy}>{busy ? "กำลังยืนยัน…" : "ยืนยันคำสั่งซื้อ"}<span>→</span></button>
            <p className="fine-print">ยอดส่วนลด คูปอง และแต้มจะตรวจสอบอีกครั้งโดยเซิร์ฟเวอร์</p>
          </aside>
        </form>

        <section id="tracking" className="tracking-section">
          <div><p className="eyebrow">03 · MY ORDER</p><h2>ค้นหาและ<br />ติดตามออเดอร์</h2><p>ใช้เลขออเดอร์และเบอร์โทรเดียวกับตอนสั่งซื้อ ข้อมูลส่วนตัวจะไม่แสดงในผลลัพธ์</p></div>
          <div className="lookup-panel">
            <form onSubmit={lookupOrder}><label>เลขที่ออเดอร์<input name="order_id" required placeholder="MPP-..." /></label><label>เบอร์โทร<input name="phone" required inputMode="tel" placeholder="0812345678" /></label><button className="outline-button">ค้นหาออเดอร์ →</button></form>
            {lookup && <div className="lookup-result"><OrderSummary order={lookup.order} />{lookup.order.fulfillment.type === "delivery" && <TrackingCard code={lookup.order.fulfillment.delivery.tracking_code} />}<p className="loyalty">แต้มคงเหลือ <strong>{lookup.loyalty.points_balance}</strong> แต้ม</p>{lookup.can_cancel && <button type="button" className="cancel-button" onClick={cancelOrder}>ยกเลิกออเดอร์นี้</button>}</div>}
          </div>
        </section>
      </main>

      {created && <div className="modal-backdrop" role="presentation"><section className="success-modal" role="dialog" aria-modal="true" aria-labelledby="success-title"><button className="modal-close" onClick={() => { setCreated(undefined); setPayment(undefined); }} aria-label="ปิด">×</button><span className="success-mark">✓</span><p className="eyebrow">ORDER RECEIVED</p><h2 id="success-title">รับออเดอร์แล้ว</h2><OrderSummary order={created} />{payment && <div className="qr-panel"><strong>สแกนเพื่อชำระเงิน</strong><img src={payment.qr_image.startsWith("data:") ? payment.qr_image : `data:image/png;base64,${payment.qr_image}`} alt="QR สำหรับชำระเงินผ่าน SCB" /><small>QR หมดอายุ {payment.expires_at}</small></div>}<button className="submit-button" onClick={() => { setCreated(undefined); setPayment(undefined); }}>เสร็จแล้ว</button></section></div>}
      <footer><span>MOOPIEW · ย่างด้วยใจทุกไม้</span><nav><a href="/platform/menu-preview.html">ดูเมนู</a><a href="/platform/api-monitor.html">สถานะระบบ</a><a href="/platform/ai.html">Owner AI</a></nav></footer>
    </>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
