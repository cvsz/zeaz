import { StrictMode, useCallback, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type ModuleKey = "overview" | "accounting" | "inventory" | "mrp" | "crm" | "hrm";
type InventoryItem = { id: string; name: string; unit: string; on_hand: number; reorder_level: number };
type LedgerEntry = { id: string; entry_date: string; reference: string; journal: string; state: string; lines: Array<{ account_code: string; account_name: string; debit: number; credit: number }>; total_debit: number; total_credit: number; balanced: boolean };
type StockMove = { id: string; product_id: string; product_name: string; quantity: number; uom: string; source_location: string; destination_location: string; lot_number?: string | null; state: string; delta: number; reason: string; order_id?: string | null; note: string; created_at: string };
type Operations = {
  inventory: InventoryItem[];
  deliveries: Array<{ order_id: string; status: string; customer_name?: string; total: number }>;
  receipts: Array<{ id: string; receipt_number: string; order_id: string; total: number }>;
  riders: Array<{ id: string; name: string; available: number | boolean; active: number | boolean }>;
  recipes: Array<{ menu_name: string; inventory_name: string; quantity: number; unit: string }>;
  menu: Array<{ id: string; name: string; price: number; available: boolean }>;
  merchant_applications: Array<{ status: string }>;
  rider_applications: Array<{ status: string }>;
  tax_invoices: Array<{ receipt_id: string; tax_invoice_number: string }>;
  ledger_entries: LedgerEntry[];
  stock_moves: StockMove[];
};

const money = (value: number) => new Intl.NumberFormat("th-TH", { style: "currency", currency: "THB", maximumFractionDigits: 0 }).format(value);
const jsonHeaders = (key: string) => ({ Accept: "application/json", "X-Admin-Key-B64": btoa(key) });

async function loadOperations(key: string): Promise<Operations> {
  const response = await fetch(`${import.meta.env.VITE_API_URL || window.location.origin}/api/admin/operations`, { headers: jsonHeaders(key) });
  const body = (await response.json()) as Operations & { error?: string };
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function exportCSV(filename: string, headers: string[], rows: string[][]) {
  const content = [headers.join(","), ...rows.map(row => row.map(cell => `"${(cell || "").replace(/"/g, '""')}"`).join(","))].join("\n");
  const blob = new Blob(["\ufeff" + content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = filename; link.click();
  URL.revokeObjectURL(url);
}

function App() {
  const [active, setActive] = useState<ModuleKey>("overview");
  const [key, setKey] = useState("");
  const [data, setData] = useState<Operations>();
  const [status, setStatus] = useState("ใส่ Owner key เพื่อเชื่อมต่อข้อมูลจริง");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!key.trim()) { setStatus("กรุณาใส่ Owner key"); return; }
    setBusy(true); setStatus("กำลังโหลดข้อมูลจาก operations API…");
    try { setData(await loadOperations(key)); setStatus("เชื่อมต่อแล้ว · ข้อมูลล่าสุดจากระบบ"); }
    catch (error) { setData(undefined); setStatus(error instanceof Error ? error.message : "เชื่อมต่อไม่สำเร็จ"); }
    finally { setBusy(false); }
  }, [key]);

  const pending = useMemo(() => data ? [...data.merchant_applications, ...data.rider_applications].filter(item => item.status === "pending").length : 0, [data]);
  const lowStock = data?.inventory.filter(item => item.on_hand <= item.reorder_level).length ?? 0;

  return (
    <div className="zerp-shell">
      <header className="zerp-header">
        <a className="zerp-brand" href="/">zERP <span>Windows Desktop</span></a>
        <nav className="zerp-nav" aria-label="ERP modules">
          {(["overview", "accounting", "inventory", "mrp", "crm", "hrm"] as ModuleKey[]).map(module => (
            <button key={module} className={active === module ? "active" : ""} onClick={() => setActive(module)}>
              {module === "overview" ? "Overview" : module === "mrp" ? "Manufacturing" : module === "crm" ? "CRM & Sales" : module === "hrm" ? "HRM" : module[0].toUpperCase() + module.slice(1)}
            </button>
          ))}
        </nav>
      </header>

      <main className="zerp-main">
        <section className="zerp-hero">
          <div>
            <p className="eyebrow">ZEAZ ENTERPRISE RESOURCE PLANNING · WINDOWS 11</p>
            <h1>{active === "overview" ? "ศูนย์ควบคุมองค์กร" : active === "mrp" ? "Manufacturing" : active === "crm" ? "CRM & Sales" : active.toUpperCase()}</h1>
            <p>ข้อมูลจากแหล่งเดียวกับ MooPiew operations API พร้อมสิทธิ์ owner และระบบ Export รายงาน Windows</p>
          </div>
          <form className="zerp-gate" onSubmit={event => { event.preventDefault(); void refresh(); }}>
            <label>Owner key<input type="password" value={key} onChange={event => setKey(event.target.value)} autoComplete="current-password" /></label>
            <button disabled={busy}>{busy ? "กำลังโหลด…" : data ? "รีเฟรชข้อมูล" : "เชื่อมต่อ"} →</button>
            <small role="status">{status}</small>
          </form>
        </section>

        {data && (
          <>
            <section className="zerp-metrics">
              <Metric label="PENDING APPLICATIONS" value={pending} />
              <Metric label="LOW STOCK" value={lowStock} />
              <Metric label="DELIVERIES" value={data.deliveries.length} />
              <Metric label="RECEIPTS" value={data.receipts.length} />
            </section>
            <ModulePanel module={active} data={data} />
          </>
        )}

        {!data && (
          <section className="zerp-empty">
            <h2>เชื่อมต่อเพื่อเปิด workspace</h2>
            <p>ระบบจะเรียกเฉพาะ protected API ด้วย Owner key ที่อยู่ใน memory ของแท็บนี้</p>
          </section>
        )}
      </main>

      <footer>ZEAZ zERP Windows 11 Desktop · <a href="https://moopiew.zeaz.dev/">MooPiew</a> · <a href="/api/health">API health</a></footer>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <article className="zerp-metric"><span>{label}</span><strong>{value}</strong></article>;
}

function ModulePanel({ module, data }: { module: ModuleKey; data: Operations }) {
  if (module === "inventory") {
    const handleExportStock = () => {
      exportCSV("inventory_stock.csv", ["ID", "วัตถุดิบ", "คงเหลือ", "หน่วย", "จุดเตือน"], data.inventory.map(item => [item.id, item.name, String(item.on_hand), item.unit, String(item.reorder_level)]));
    };
    return (
      <section className="zerp-panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Inventory & WMS</h2>
          <button className="export-btn" onClick={handleExportStock}>Export CSV</button>
        </div>
        <p className="panel-note">สต็อกจริงและ movement journal จาก operations API</p>
        <div className="table-wrap">
          <table>
            <thead><tr><th>วัตถุดิบ</th><th>คงเหลือ</th><th>จุดเตือน</th><th>สถานะ</th></tr></thead>
            <tbody>{data.inventory.map(item => <tr key={item.id}><td>{item.name}</td><td>{item.on_hand} {item.unit}</td><td>{item.reorder_level}</td><td><span className={item.on_hand <= item.reorder_level ? "badge danger" : "badge"}>{item.on_hand <= item.reorder_level ? "LOW" : "OK"}</span></td></tr>)}</tbody>
          </table>
        </div>
        <h3 className="subheading">Stock movements</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>เวลา</th><th>สินค้า</th><th>เส้นทาง</th><th>จำนวน</th><th>เหตุผล</th></tr></thead>
            <tbody>{data.stock_moves.map(move => <tr key={move.id}><td>{move.created_at.slice(0, 16).replace("T", " ")}</td><td>{move.product_name}</td><td>{move.source_location} → {move.destination_location}</td><td>{move.delta > 0 ? "+" : ""}{move.delta} {move.uom}</td><td>{move.reason}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    );
  }

  if (module === "mrp") {
    return (
      <section className="zerp-panel">
        <h2>Manufacturing (MRP)</h2>
        <p className="panel-note">สูตรการผลิตที่กำหนดไว้ในระบบร้าน</p>
        <div className="table-wrap">
          <table>
            <thead><tr><th>เมนู</th><th>วัตถุดิบ</th><th>ปริมาณ</th></tr></thead>
            <tbody>{data.recipes.map((recipe, index) => <tr key={`${recipe.menu_name}-${recipe.inventory_name}-${index}`}><td>{recipe.menu_name}</td><td>{recipe.inventory_name}</td><td>{recipe.quantity} {recipe.unit}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    );
  }

  if (module === "crm") {
    return (
      <section className="zerp-panel">
        <h2>CRM & Sales</h2>
        <p className="panel-note">สรุป funnel จากใบสมัครและเมนูที่เปิดขาย</p>
        <div className="card-grid">
          <Info title="ใบสมัครร้านค้า" value={String(data.merchant_applications.length)} />
          <Info title="ร้านค้าที่รอตรวจ" value={String(data.merchant_applications.filter(item => item.status === "pending").length)} />
          <Info title="เมนูพร้อมขาย" value={String(data.menu.filter(item => item.available).length)} />
        </div>
      </section>
    );
  }

  if (module === "hrm") {
    return (
      <section className="zerp-panel">
        <h2>HRM & Workforce</h2>
        <p className="panel-note">สถานะ workforce จากข้อมูลไรเดอร์ที่ได้รับอนุมัติ</p>
        <div className="table-wrap">
          <table>
            <thead><tr><th>ชื่อ</th><th>สถานะบัญชี</th><th>พร้อมรับงาน</th></tr></thead>
            <tbody>{data.riders.map(rider => <tr key={rider.id}><td>{rider.name}</td><td>{rider.active ? "Active" : "Inactive"}</td><td>{rider.available ? "พร้อม" : "พัก"}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    );
  }

  if (module === "accounting") {
    const handleExportLedger = () => {
      exportCSV("financial_ledger.csv", ["ID", "วันที่", "อ้างอิง", "Journal", "Total Debit", "Total Credit", "Balanced"], data.ledger_entries.map(entry => [entry.id, entry.entry_date, entry.reference, entry.journal, String(entry.total_debit), String(entry.total_credit), entry.balanced ? "BALANCED" : "UNBALANCED"]));
    };
    return (
      <section className="zerp-panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Accounting & Financial Ledger</h2>
          <button className="export-btn" onClick={handleExportLedger}>Export CSV</button>
        </div>
        <p className="panel-note">รายการบัญชี double-entry ที่สร้างจากใบเสร็จ immutable และตรวจยอด debit/credit ทุก entry</p>
        <div className="table-wrap">
          <table>
            <thead><tr><th>วันที่</th><th>อ้างอิง</th><th>รายการ</th><th>Debit</th><th>Credit</th><th>สถานะ</th></tr></thead>
            <tbody>{data.ledger_entries.map(entry => <tr key={entry.id}><td>{entry.entry_date}</td><td>{entry.reference}</td><td>{entry.lines.map(line => <div key={`${entry.id}-${line.account_code}`}>{line.account_code} · {line.account_name}</div>)}</td><td>{money(entry.total_debit)}</td><td>{money(entry.total_credit)}</td><td><span className={entry.balanced ? "badge" : "badge danger"}>{entry.balanced ? "BALANCED" : "UNBALANCED"}</span></td></tr>)}</tbody>
          </table>
        </div>
      </section>
    );
  }

  return (
    <section className="zerp-panel">
      <h2>Operational Overview</h2>
      <p className="panel-note">ภาพรวมธุรกิจจากข้อมูล live ของ MooPiew</p>
      <div className="card-grid">
        <Info title="ยอดใบเสร็จล่าสุด" value={money(data.receipts.reduce((total, receipt) => total + receipt.total, 0))} />
        <Info title="Ledger entries" value={String(data.ledger_entries.length)} />
        <Info title="งานจัดส่ง" value={String(data.deliveries.length)} />
        <Info title="ไรเดอร์ active" value={String(data.riders.filter(rider => rider.active).length)} />
      </div>
    </section>
  );
}

function Info({ title, value }: { title: string; value: string }) {
  return <article className="zerp-info"><span>{title}</span><strong>{value}</strong></article>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
