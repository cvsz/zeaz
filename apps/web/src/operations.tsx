import { FormEvent, StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { MoopiewClient } from "@moopiew/sdk";
import type { DeliveryStatus, OperationsDashboard, Receipt } from "@moopiew/types";
import "./operations.css";

const api = new MoopiewClient({baseURL: import.meta.env.VITE_API_URL || window.location.origin});
const money = (value: number) => new Intl.NumberFormat("th-TH", {style:"currency",currency:"THB",maximumFractionDigits:0}).format(value);
const messageOf = (error: unknown) => error instanceof Error ? error.message : "ดำเนินการไม่สำเร็จ";
const values = (form: HTMLFormElement) => Object.fromEntries(new FormData(form));
const sections = ["Overview","Applications","Delivery","Inventory","Commerce"] as const;
type Section = typeof sections[number];

function App() {
  const [adminKey,setAdminKey]=useState("");
  const [data,setData]=useState<OperationsDashboard>();
  const [notice,setNotice]=useState("กรอก Owner key เพื่อเปิด operations workspace");
  const [busy,setBusy]=useState(false);
  const [section,setSection]=useState<Section>("Overview");
  const [invoiceReceipt,setInvoiceReceipt]=useState<Receipt>();

  async function load(message="ข้อมูลล่าสุดจาก production API") {
    if(!adminKey) return setNotice("กรุณากรอก Owner key");
    setBusy(true);
    try { setData(await api.operations.dashboard(adminKey)); setNotice(message); }
    catch(error){setNotice(messageOf(error));}
    finally{setBusy(false);}
  }
  async function mutate(action:()=>Promise<unknown>,message="บันทึกแล้ว"){
    setBusy(true);
    try{await action();setData(await api.operations.dashboard(adminKey));setNotice(message);}
    catch(error){setNotice(messageOf(error));}
    finally{setBusy(false);}
  }
  async function submit(event:FormEvent<HTMLFormElement>,action:(form:Record<string,FormDataEntryValue>)=>Promise<unknown>,message:string){
    event.preventDefault();const target=event.currentTarget;
    await mutate(()=>action(values(target)),message);target.reset();
  }
  function locate(){
    if(!navigator.geolocation)return setNotice("เบราว์เซอร์นี้ไม่รองรับตำแหน่ง");
    navigator.geolocation.getCurrentPosition(({coords})=>{
      const lat=document.querySelector<HTMLInputElement>("[name=store_latitude]");
      const lng=document.querySelector<HTMLInputElement>("[name=store_longitude]");
      if(lat)lat.value=String(coords.latitude);if(lng)lng.value=String(coords.longitude);
      setNotice("อ่านตำแหน่งร้านแล้ว กรุณาตรวจสอบก่อนบันทึก");
    },()=>setNotice("ไม่สามารถอ่านตำแหน่งได้"),{enableHighAccuracy:true,timeout:10000});
  }
  async function printReceipt(receipt:Receipt){
    try{
      const html=await api.operations.printReceipt(adminKey,receipt.id);
      const url=URL.createObjectURL(new Blob([html],{type:"text/html"}));
      const opened=window.open(url,"_blank");
      if(!opened)throw new Error("เบราว์เซอร์บล็อกหน้าต่างพิมพ์");
      opened.opener=null;
      window.setTimeout(()=>URL.revokeObjectURL(url),60_000);
    }catch(error){setNotice(messageOf(error));}
  }

  const pending=(data?.rider_applications.filter(x=>x.status==="pending").length??0)+(data?.merchant_applications.filter(x=>x.status==="pending").length??0);
  const lowStock=data?.inventory.filter(x=>x.on_hand<=x.reorder_level).length??0;
  return <><header className="ops-nav"><a href="/">MOOPIEW®</a><nav><a href="/platform/admin.html">Owner</a><a href="/platform/documents.html">Documents</a><a href="/platform/ai.html">AI</a></nav></header><main>
    <section className="ops-hero"><div><p className="eyebrow">LIVE OPERATIONS CONTROL</p><h1>หลังบ้าน<br/><em>ที่ทำงานจริง</em></h1><p>จัดการคน ส่งของ สต็อก โปรโมชั่น และเอกสารภาษีจาก API ชุดเดียวกับหน้าร้าน</p></div><section className="gate"><label>Owner key<input type="password" autoComplete="current-password" value={adminKey} onChange={e=>setAdminKey(e.target.value)}/></label><button disabled={busy} onClick={()=>void load()}>{busy?"กำลังประมวลผล…":data?"รีเฟรชข้อมูล":"เปิด workspace"} <span>→</span></button><p role="status" aria-live="polite">{notice}</p><small>Credential อยู่เฉพาะ memory ของแท็บนี้</small></section></section>
    {data&&<><section className="ops-metrics"><article><span>PENDING</span><strong>{pending}</strong><small>ใบสมัครรอตรวจ</small></article><article><span>DELIVERIES</span><strong>{data.deliveries.length}</strong><small>งานจัดส่ง</small></article><article><span>LOW STOCK</span><strong>{lowStock}</strong><small>รายการถึงจุดเตือน</small></article><article><span>RECEIPTS</span><strong>{data.receipts.length}</strong><small>ใบเสร็จล่าสุด</small></article></section>
      <nav className="section-tabs" aria-label="Operations sections">{sections.map(item=><button key={item} className={section===item?"active":""} onClick={()=>setSection(item)}>{item}</button>)}</nav>
      <div className="workspace">
        {section==="Overview"&&<Overview data={data} busy={busy} locate={locate} submit={submit} adminKey={adminKey}/>}
        {section==="Applications"&&<Applications data={data} busy={busy} mutate={mutate} adminKey={adminKey} submit={submit}/>}
        {section==="Delivery"&&<Delivery data={data} busy={busy} mutate={mutate} adminKey={adminKey} submit={submit}/>}
        {section==="Inventory"&&<Inventory data={data} busy={busy} mutate={mutate} adminKey={adminKey} submit={submit}/>}
        {section==="Commerce"&&<Commerce data={data} busy={busy} mutate={mutate} adminKey={adminKey} submit={submit} printReceipt={printReceipt} setInvoiceReceipt={setInvoiceReceipt}/>}
      </div>
    </>}
  </main>
  {invoiceReceipt&&<InvoiceModal receipt={invoiceReceipt} busy={busy} close={()=>setInvoiceReceipt(undefined)} issue={async input=>{await mutate(()=>api.operations.issueTaxInvoice(adminKey,invoiceReceipt.id,input),"ออกใบกำกับภาษีแล้ว");setInvoiceReceipt(undefined);}}/>}
  <footer>MOOPIEW · OWNER OPERATIONS <a href="/platform/api-monitor.html">System status</a></footer></>;
}

type Submit=(event:FormEvent<HTMLFormElement>,action:(form:Record<string,FormDataEntryValue>)=>Promise<unknown>,message:string)=>Promise<void>;
type Mutate=(action:()=>Promise<unknown>,message?:string)=>Promise<void>;
function Panel({number,title,children}:{number:string;title:string;children:React.ReactNode}){return <section className="ops-panel"><header><span>{number}</span><h2>{title}</h2></header>{children}</section>}
function Empty({text}:{text:string}){return <p className="empty">{text}</p>}

function Overview({data,busy,locate,submit,adminKey}:{data:OperationsDashboard;busy:boolean;locate:()=>void;submit:Submit;adminKey:string}){
  const p=data.business_profile,d=data.delivery_pricing;
  return <div className="two-panels"><Panel number="01" title="ข้อมูลผู้ขายและภาษี"><form onSubmit={e=>void submit(e,f=>api.operations.updateBusinessProfile(adminKey,{legal_name:String(f.legal_name),tax_id:String(f.tax_id),address:String(f.address),branch:String(f.branch),vat_registered:f.vat_registered==="on"}),"บันทึกข้อมูลผู้ขายแล้ว")}><label>ชื่อกิจการ<input name="legal_name" required defaultValue={p.legal_name}/></label><label>เลขผู้เสียภาษี<input name="tax_id" inputMode="numeric" defaultValue={p.tax_id}/></label><label>ที่อยู่<textarea name="address" required defaultValue={p.address}/></label><div className="form-row"><label>สาขา<input name="branch" defaultValue={p.branch||"สำนักงานใหญ่"}/></label><label className="check"><input name="vat_registered" type="checkbox" defaultChecked={p.vat_registered}/> จด VAT</label></div><button disabled={busy}>บันทึกข้อมูลผู้ขาย →</button></form></Panel>
  <Panel number="02" title="นโยบายค่าส่ง"><form onSubmit={e=>void submit(e,f=>api.operations.updateDeliveryPricing(adminKey,{mode:"distance",base_fee:Number(f.base_fee),per_km_fee:Number(f.per_km_fee),maximum_km:Number(f.maximum_km),store_latitude:Number(f.store_latitude),store_longitude:Number(f.store_longitude)}),"บันทึกอัตราค่าส่งแล้ว")}><div className="form-row"><label>ค่าตั้งต้น<input name="base_fee" type="number" min="0" defaultValue={d.base_fee}/></label><label>ต่อกิโลเมตร<input name="per_km_fee" type="number" min="0" step=".01" defaultValue={d.per_km_fee}/></label></div><label>ระยะสูงสุด (กม.)<input name="maximum_km" type="number" min="1" step=".1" defaultValue={d.maximum_km}/></label><div className="form-row"><label>ละติจูด<input name="store_latitude" required defaultValue={d.store_latitude??""}/></label><label>ลองจิจูด<input name="store_longitude" required defaultValue={d.store_longitude??""}/></label></div><button type="button" className="secondary" onClick={locate}>ใช้ตำแหน่งอุปกรณ์นี้</button><button disabled={busy}>บันทึกอัตราค่าส่ง →</button></form></Panel></div>
}

function Applications({data,busy,mutate,adminKey,submit}:{data:OperationsDashboard;busy:boolean;mutate:Mutate;adminKey:string;submit:Submit}){
  return <div className="two-panels"><Panel number="03" title="ใบสมัครร้านค้า"><div className="record-list">{data.merchant_applications.length?data.merchant_applications.map(item=><article key={item.id}><div><small>{item.id} · {item.status}</small><h3>{item.business_name}</h3><p>{item.owner_name} · {item.phone} · {item.category}</p><p>{item.address}</p></div>{item.status==="pending"&&<div className="actions"><button disabled={busy} onClick={()=>void mutate(()=>api.operations.reviewMerchantApplication(adminKey,item.id,"approved"),"อนุมัติร้านค้าแล้ว")}>อนุมัติ</button><button className="danger" disabled={busy} onClick={()=>void mutate(()=>api.operations.reviewMerchantApplication(adminKey,item.id,"rejected"),"ปฏิเสธใบสมัครแล้ว")}>ปฏิเสธ</button></div>}</article>):<Empty text="ยังไม่มีใบสมัครร้านค้า"/>}</div></Panel>
  <Panel number="04" title="ไรเดอร์และใบสมัคร"><div className="record-list">{data.rider_applications.map(item=><article key={item.id}><div><small>{item.id} · {item.status}</small><h3>{item.name}</h3><p>{item.phone} · {item.vehicle_type} {item.vehicle_plate}</p></div>{item.status==="pending"&&<div className="actions"><button disabled={busy} onClick={()=>void mutate(()=>api.operations.reviewRiderApplication(adminKey,item.id,"approved"))}>อนุมัติ</button><button className="danger" disabled={busy} onClick={()=>void mutate(()=>api.operations.reviewRiderApplication(adminKey,item.id,"rejected"))}>ปฏิเสธ</button></div>}</article>)}</div><form className="inline-form" onSubmit={e=>void submit(e,f=>api.operations.createRider(adminKey,{name:String(f.name),phone:String(f.phone)}),"เพิ่มไรเดอร์แล้ว")}><input name="name" required placeholder="ชื่อไรเดอร์"/><input name="phone" required placeholder="เบอร์โทร"/><button disabled={busy}>เพิ่มไรเดอร์</button></form><div className="chip-list">{data.riders.map(rider=><article key={rider.id}><div><strong>{rider.name}</strong><small>{rider.available?"พร้อมรับงาน":"พักงาน"}</small></div><button disabled={busy} onClick={()=>void mutate(()=>api.operations.updateRider(adminKey,rider.id,{available:!rider.available}))}>{rider.available?"พัก":"พร้อม"}</button></article>)}</div></Panel></div>
}

const nextStatuses:Record<string,DeliveryStatus[]>= {queued:[],assigned:["picked_up"],picked_up:["on_the_way"],on_the_way:["delivered"],failed:["queued"],delivered:[],cancelled:[]};
function Delivery({data,busy,mutate,adminKey,submit}:{data:OperationsDashboard;busy:boolean;mutate:Mutate;adminKey:string;submit:Submit}){
  return <div className="two-panels"><Panel number="05" title="พื้นที่จัดส่ง"><form className="inline-form zone" onSubmit={e=>void submit(e,f=>api.operations.createZone(adminKey,{name:String(f.name),fee:Number(f.fee),minimum_order:Number(f.minimum_order)}),"เพิ่มพื้นที่แล้ว")}><input name="name" required placeholder="ชื่อพื้นที่"/><input name="fee" type="number" min="0" required placeholder="ค่าส่ง"/><input name="minimum_order" type="number" min="0" defaultValue="0" placeholder="ขั้นต่ำ"/><button disabled={busy}>เพิ่มพื้นที่</button></form><div className="zone-list">{data.delivery_zones.map(zone=><p key={zone.id}><strong>{zone.name}</strong><span>{money(zone.fee)} · ขั้นต่ำ {money(zone.minimum_order)}</span></p>)}</div></Panel>
  <Panel number="06" title="งานจัดส่ง"><div className="record-list">{data.deliveries.length?data.deliveries.map(item=><article key={item.order_id}><div><small>{item.order_id} · {item.status}</small><h3>{item.recipient_name}</h3><p>{item.zone_name} · {item.address}</p><p>ไรเดอร์: {item.rider_name||"ยังไม่มอบหมาย"}</p></div><div className="delivery-actions">{["queued","assigned"].includes(item.status)&&<select defaultValue="" disabled={busy} onChange={e=>{if(e.target.value)void mutate(()=>api.operations.updateDelivery(adminKey,item.order_id,{rider_id:e.target.value}),"มอบหมายไรเดอร์แล้ว")}}><option value="">มอบหมายไรเดอร์</option>{data.riders.filter(r=>r.active&&r.available).map(r=><option key={r.id} value={r.id}>{r.name}</option>)}</select>}{nextStatuses[item.status]?.map(status=><button key={status} disabled={busy} onClick={()=>void mutate(()=>api.operations.updateDelivery(adminKey,item.order_id,{status}),`อัปเดตเป็น ${status}`)}>{status}</button>)}<button className="secondary" disabled={busy} onClick={()=>void mutate(()=>api.operations.issueReceipt(adminKey,item.order_id),"ออกใบเสร็จแล้ว")}>ออกใบเสร็จ</button></div></article>):<Empty text="ยังไม่มีงานจัดส่ง"/>}</div></Panel></div>
}

function Inventory({data,busy,mutate,adminKey,submit}:{data:OperationsDashboard;busy:boolean;mutate:Mutate;adminKey:string;submit:Submit}){
  return <div className="two-panels"><Panel number="07" title="สต็อกวัตถุดิบ"><form className="grid-form" onSubmit={e=>void submit(e,f=>api.operations.createInventory(adminKey,{name:String(f.name),unit:String(f.unit),on_hand:Number(f.on_hand),reorder_level:Number(f.reorder_level)}),"เพิ่มวัตถุดิบแล้ว")}><input name="name" required placeholder="วัตถุดิบ"/><input name="unit" required placeholder="หน่วย"/><input name="on_hand" type="number" step=".01" defaultValue="0" placeholder="คงเหลือ"/><input name="reorder_level" type="number" step=".01" defaultValue="0" placeholder="จุดเตือน"/><button disabled={busy}>เพิ่มวัตถุดิบ</button></form><div className="stock-grid">{data.inventory.map(item=><article className={item.on_hand<=item.reorder_level?"low":""} key={item.id}><small>{item.on_hand<=item.reorder_level?"LOW STOCK":"IN STOCK"}</small><h3>{item.name}</h3><strong>{item.on_hand} {item.unit}</strong><p>เตือนที่ {item.reorder_level}</p><div><button disabled={busy} onClick={()=>void mutate(()=>api.operations.adjustInventory(adminKey,{inventory_item_id:item.id,delta:1,reason:"owner_adjustment"}))}>+1</button><button disabled={busy} onClick={()=>void mutate(()=>api.operations.adjustInventory(adminKey,{inventory_item_id:item.id,delta:-1,reason:"owner_adjustment"}))}>−1</button></div></article>)}</div></Panel>
  <Panel number="08" title="สูตรตัดสต็อก"><form onSubmit={e=>void submit(e,f=>api.operations.setRecipe(adminKey,{menu_item_id:String(f.menu_item_id),inventory_item_id:String(f.inventory_item_id),quantity:Number(f.quantity)}),"บันทึกสูตรแล้ว")}><label>เมนู<select name="menu_item_id" required><option value="">เลือกเมนู</option>{data.menu.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label><label>วัตถุดิบ<select name="inventory_item_id" required><option value="">เลือกวัตถุดิบ</option>{data.inventory.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label><label>ใช้ต่อหนึ่งเมนู<input name="quantity" type="number" min=".01" step=".01" required/></label><button disabled={busy}>บันทึกสูตร →</button></form><div className="recipe-list">{data.recipes.map(x=><p key={`${x.menu_item_id}-${x.inventory_item_id}`}><strong>{x.menu_name}</strong><span>{x.quantity} {x.unit} · {x.inventory_name}</span></p>)}</div></Panel></div>
}

function Commerce({data,busy,mutate,adminKey,submit,printReceipt,setInvoiceReceipt}:{data:OperationsDashboard;busy:boolean;mutate:Mutate;adminKey:string;submit:Submit;printReceipt:(r:Receipt)=>Promise<void>;setInvoiceReceipt:(r:Receipt)=>void}){
  const invoices=new Map(data.tax_invoices.map(x=>[x.receipt_id,x]));
  return <div className="two-panels"><Panel number="09" title="คูปอง"><form className="grid-form" onSubmit={e=>void submit(e,f=>api.operations.createCoupon(adminKey,{code:String(f.code),kind:String(f.kind) as "fixed"|"percent",value:Number(f.value),minimum_order:Number(f.minimum_order),maximum_uses:Number(f.maximum_uses),starts_at:f.starts_at?new Date(String(f.starts_at)).toISOString():"",ends_at:f.ends_at?new Date(String(f.ends_at)).toISOString():""}),"สร้างคูปองแล้ว")}><input name="code" pattern="[A-Za-z0-9_-]{3,32}" required placeholder="CODE"/><select name="kind"><option value="fixed">ลดบาท</option><option value="percent">ลดเปอร์เซ็นต์</option></select><input name="value" type="number" min="1" required placeholder="มูลค่า"/><input name="minimum_order" type="number" min="0" defaultValue="0" placeholder="ขั้นต่ำ"/><input name="maximum_uses" type="number" min="0" defaultValue="0" placeholder="จำนวนสิทธิ์"/><input name="starts_at" type="datetime-local"/><input name="ends_at" type="datetime-local"/><button disabled={busy}>สร้างคูปอง</button></form><div className="coupon-grid">{data.coupons.map(x=><article key={x.id}><small>{x.kind}</small><h3>{x.code}</h3><strong>{x.kind==="percent"?`${x.value}%`:money(x.value)}</strong><p>ขั้นต่ำ {money(x.minimum_order)} · ใช้แล้ว {x.used_count}{x.maximum_uses?`/${x.maximum_uses}`:""}</p></article>)}</div></Panel>
  <Panel number="10" title="ใบเสร็จและภาษี"><div className="record-list">{data.receipts.length?data.receipts.map(receipt=>{const invoice=invoices.get(receipt.id);return <article key={receipt.id}><div><small>{receipt.receipt_number}</small><h3>{receipt.order_id}</h3><p>{money(receipt.total)} {invoice&&`· ${invoice.tax_invoice_number}`}</p></div><div className="actions"><button disabled={busy} onClick={()=>void printReceipt(receipt)}>พิมพ์</button>{!invoice&&<button disabled={busy} onClick={()=>setInvoiceReceipt(receipt)}>ออกใบกำกับภาษี</button>}</div></article>}):<Empty text="ยังไม่มีใบเสร็จ"/>}</div></Panel></div>
}

function InvoiceModal({receipt,busy,close,issue}:{receipt:Receipt;busy:boolean;close:()=>void;issue:(input:{buyer_name:string;buyer_tax_id:string;buyer_address:string})=>Promise<void>}){
  return <div className="modal-bg"><section className="invoice-modal" role="dialog" aria-modal="true" aria-labelledby="invoice-title"><button className="close" onClick={close}>×</button><p className="eyebrow">TAX INVOICE</p><h2 id="invoice-title">ข้อมูลผู้ซื้อ</h2><p>{receipt.receipt_number} · {money(receipt.total)}</p><form onSubmit={e=>{e.preventDefault();const f=values(e.currentTarget);void issue({buyer_name:String(f.buyer_name),buyer_tax_id:String(f.buyer_tax_id),buyer_address:String(f.buyer_address)})}}><label>ชื่อผู้ซื้อ<input name="buyer_name" required/></label><label>เลขผู้เสียภาษี<input name="buyer_tax_id" inputMode="numeric"/></label><label>ที่อยู่<textarea name="buyer_address"/></label><button disabled={busy}>ออกใบกำกับภาษี →</button></form></section></div>
}
createRoot(document.getElementById("root")!).render(<StrictMode><App/></StrictMode>);
