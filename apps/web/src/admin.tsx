import { FormEvent, StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { MoopiewClient } from "@moopiew/sdk";
import type {
  AdminDashboard,
  AdminOrder,
  PaymentAttempt,
  ScbAuthorizationStatus,
} from "@moopiew/types";
import "./admin.css";

const api = new MoopiewClient({
  baseURL: import.meta.env.VITE_API_URL || window.location.origin,
});
const money = (value: number) =>
  new Intl.NumberFormat("th-TH", {
    style: "currency",
    currency: "THB",
    maximumFractionDigits: 0,
  }).format(value);
const messageOf = (error: unknown) =>
  error instanceof Error ? error.message : "ดำเนินการไม่สำเร็จ";

const orderStatuses: AdminOrder["status"][] = [
  "new", "confirmed", "ready", "completed", "cancelled",
];
const paymentStatuses: AdminOrder["payment"]["status"][] = [
  "pending", "paid", "refunded",
];
function allowedOrderStatuses(order: AdminOrder) {
  const canComplete = order.payment.method !== "scb_qr" || order.payment.status === "paid";
  return orderStatuses.filter(
    (value) =>
      value === order.status ||
      (!["cancelled", "completed"].includes(order.status) &&
        value !== "cancelled" &&
        (value !== "completed" || canComplete)) ||
      (value === "cancelled" && order.payment.status !== "paid"),
  );
}
function allowedPaymentStatuses(order: AdminOrder) {
  return paymentStatuses.filter(
    (value) =>
      value === order.payment.status ||
      (!["paid", "refunded"].includes(order.payment.status) && value === "paid") ||
      (value === "refunded" && order.payment.status === "paid"),
  );
}

function App() {
  const [adminKey, setAdminKey] = useState("");
  const [dashboard, setDashboard] = useState<AdminDashboard>();
  const [notice, setNotice] = useState("กรอก Owner key เพื่อเปิด command center");
  const [busy, setBusy] = useState(false);
  const [scbStatus, setScbStatus] = useState<ScbAuthorizationStatus>();
  const [authorizationUrl, setAuthorizationUrl] = useState("");

  async function load() {
    if (!adminKey) return setNotice("กรุณากรอก Owner key");
    setBusy(true);
    try {
      setDashboard(await api.admin.dashboard(adminKey));
      setNotice("ข้อมูลล่าสุดจาก production API");
    } catch (error) {
      setNotice(messageOf(error));
    } finally {
      setBusy(false);
    }
  }
  async function refreshScb() {
    if (!adminKey) return;
    try {
      setScbStatus(await api.admin.scbAuthorizationStatus(adminKey));
    } catch (error) {
      setNotice(messageOf(error));
    }
  }
  useEffect(() => {
    const visible = () => {
      if (!document.hidden && dashboard) void refreshScb();
    };
    document.addEventListener("visibilitychange", visible);
    return () => document.removeEventListener("visibilitychange", visible);
  }, [dashboard, adminKey]);

  async function mutate(action: () => Promise<unknown>, success = "บันทึกแล้ว") {
    setBusy(true);
    try {
      await action();
      setDashboard(await api.admin.dashboard(adminKey));
      setNotice(success);
    } catch (error) {
      setNotice(messageOf(error));
    } finally {
      setBusy(false);
    }
  }
  async function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await mutate(() => api.admin.updateSettings(adminKey, {
      slot_capacity: Number(form.get("slot_capacity")),
      advance_days: Number(form.get("advance_days")),
    }));
  }
  async function addMenu(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const target = event.currentTarget;
    const form = new FormData(target);
    await mutate(() => api.admin.createMenu(adminKey, {
      name: String(form.get("name")),
      description: String(form.get("description")),
      price: Number(form.get("price")),
    }), "เพิ่มเมนูแล้ว");
    target.reset();
  }
  async function startScb() {
    try {
      const result = await api.admin.startScbAuthorization(adminKey);
      const protocol = new URL(result.authorization_url).protocol;
      if (!["scbeasysim:", "scbeasy:"].includes(protocol)) {
        throw new Error("SCB ส่ง authorization link ที่ไม่รองรับ");
      }
      setAuthorizationUrl(result.authorization_url);
      setNotice("สร้างคำขอ SCB EASY แล้ว กรุณาอนุมัติบนอุปกรณ์");
    } catch (error) {
      setNotice(messageOf(error));
    }
  }

  return (
    <>
      <header className="admin-nav">
        <a href="/">MOOPIEW®</a>
        <nav><a href="/platform/ops.html">Operations</a><a href="/platform/documents.html">Documents</a><a href="/platform/ai.html">Owner AI</a></nav>
      </header>
      <main>
        <section className="admin-hero">
          <div><p className="eyebrow">OWNER COMMAND CENTER</p><h1>ร้านทั้งร้าน<br /><em>ในภาพเดียว</em></h1><p>ออเดอร์ เมนู การชำระเงิน และ audit จากระบบ production โดยตรง</p></div>
          <section className="login-panel">
            <label>Owner key<input type="password" autoComplete="current-password" value={adminKey} onChange={(event) => setAdminKey(event.target.value)} /></label>
            <button disabled={busy} onClick={() => void load()}>{busy ? "กำลังโหลด…" : dashboard ? "รีเฟรชข้อมูล" : "เข้าสู่ระบบ"} <span>→</span></button>
            <p role="status">{notice}</p><small>คีย์อยู่ในหน่วยความจำของหน้านี้เท่านั้น และไม่ถูกใส่ใน URL</small>
          </section>
        </section>
        {dashboard && <>
          <section className="metric-grid">
            {[
              ["ORDERS", dashboard.summary.orders, "ออเดอร์ทั้งหมด"],
              ["ACTIVE", dashboard.summary.active_orders, "กำลังดำเนินการ"],
              ["REVENUE", money(dashboard.summary.revenue), "ยอดจอง"],
              ["READY", dashboard.summary.ready, "พร้อมรับ"],
            ].map(([label, value, detail]) => <article key={label}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>)}
          </section>
          <section className="admin-grid">
            <div className="primary-column">
              <Panel index="01" title="ออเดอร์ทั้งหมด" action={`${dashboard.orders.length} รายการ`}>
                <div className="order-list">{dashboard.orders.length ? dashboard.orders.map((order) => <article className="order-row" key={order.id}><div><small>{order.id} · {order.pickup.date}</small><h3>{order.customer.name}</h3><p>{order.items.map((item) => `${item.name} × ${item.quantity}`).join(" · ")}</p><strong>{money(order.total)}</strong></div><div className="order-controls"><label>ออเดอร์<select value={order.status} disabled={busy} onChange={(event) => void mutate(() => api.admin.updateOrder(adminKey, order.id, { status: event.target.value as AdminOrder["status"] }))}>{allowedOrderStatuses(order).map((status) => <option key={status}>{status}</option>)}</select></label><label>ชำระเงิน<select value={order.payment.status} disabled={busy} onChange={(event) => void mutate(() => api.admin.updateOrder(adminKey, order.id, { payment_status: event.target.value as AdminOrder["payment"]["status"] }))}>{allowedPaymentStatuses(order).map((status) => <option key={status}>{status}</option>)}</select></label></div></article>) : <Empty text="ยังไม่มีออเดอร์" />}</div>
              </Panel>
              <Panel index="02" title="SCB QR payments" action={`${dashboard.payments.length} attempts`}>
                <div className="payment-list">{dashboard.payments.length ? dashboard.payments.map((payment: PaymentAttempt) => <article key={payment.id}><div><small>{payment.id}</small><h3>{payment.status}</h3><p>{payment.provider_order_id || "รอ SCB order ID"} · {money(payment.amount)}</p></div>{payment.status === "pending" && <button disabled={busy} onClick={() => void mutate(() => api.admin.inquirePayment(adminKey, payment.id), "ตรวจสอบสถานะกับ SCB แล้ว")}>ตรวจสอบกับ SCB →</button>}</article>) : <Empty text="ยังไม่มี SCB QR payment" />}</div>
              </Panel>
            </div>
            <aside className="side-column">
              <Panel index="03" title="ตั้งค่าร้าน">
                <form onSubmit={saveSettings}><label>ความจุต่อรอบ<input name="slot_capacity" type="number" min="1" max="500" defaultValue={dashboard.settings.slot_capacity} /></label><label>เปิดรับล่วงหน้า (วัน)<input name="advance_days" type="number" min="1" max="60" defaultValue={dashboard.settings.advance_days} /></label><button disabled={busy}>บันทึกการตั้งค่า →</button></form>
              </Panel>
              <Panel index="04" title="เพิ่มเมนู">
                <form onSubmit={addMenu}><label>ชื่อเมนู<input name="name" required minLength={2} /></label><label>คำอธิบาย<input name="description" maxLength={160} /></label><label>ราคา<input name="price" type="number" min="0" required /></label><button disabled={busy}>เพิ่มเมนู →</button></form>
                <div className="menu-list">{dashboard.settings.menu.map((item) => <article key={item.id}><div><strong>{item.name}</strong><small>{money(item.price)} · {item.available ? "เปิดขาย" : "ปิดขาย"}</small></div><button disabled={busy} onClick={() => void mutate(() => api.admin.updateMenu(adminKey, item.id, { available: !item.available }))}>{item.available ? "ปิด" : "เปิด"}</button></article>)}</div>
              </Panel>
              <Panel index="05" title="SCB EASY profile">
                <div className="scb-actions"><button onClick={() => void startScb()}>1 · สร้างคำขอเชื่อมต่อ</button>{authorizationUrl && <a href={authorizationUrl} rel="noopener">2 · เปิด SCB EASY Simulator ↗</a>}<button onClick={() => void refreshScb()}>3 · ตรวจสอบสถานะ</button><p>{scbStatus?.connected ? `เชื่อมต่อแล้ว · หมดอายุ ${new Date(scbStatus.access_expires_at).toLocaleString("th-TH")}` : "ยังไม่ได้เชื่อมต่อ SCB EASY profile"}</p></div>
              </Panel>
              <Panel index="06" title="กิจกรรมล่าสุด">
                <div className="audit-list">{dashboard.audit.map((item) => <p key={item.id}><strong>{item.actor_role}</strong> · {item.action} {item.entity_type}<code>{item.entity_id}</code><small>{new Date(item.at).toLocaleString("th-TH")}</small></p>)}</div>
              </Panel>
            </aside>
          </section>
        </>}
      </main>
      <footer>MOOPIEW · OWNER-ONLY CONTROL SURFACE <a href="/platform/api-monitor.html">System status</a></footer>
    </>
  );
}

function Panel({ index, title, action, children }: { index: string; title: string; action?: string; children: React.ReactNode }) {
  return <section className="panel"><header><span>{index}</span><h2>{title}</h2>{action && <small>{action}</small>}</header>{children}</section>;
}
function Empty({ text }: { text: string }) { return <p className="empty">{text}</p>; }
createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
