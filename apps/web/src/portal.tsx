import {StrictMode, useEffect, useState} from "react";
import {createRoot} from "react-dom/client";
import {MoopiewApiError, MoopiewClient} from "@moopiew/sdk";
import type {MenuResponse, MerchantApplicationInput, MonitorEndpoint, RiderApplicationInput} from "@moopiew/types";
import "./portal.css";

const api = new MoopiewClient({baseURL: import.meta.env.VITE_API_URL || window.location.origin});
const page = document.body.dataset.page;

function Shell({children}: {children: React.ReactNode}) {
  return <div className="portal"><header><a href="/"><b>M</b><span>MooPiew<small>PARTNER NETWORK</small></span></a><a href="/">กลับหน้าร้าน ↗</a></header>{children}<footer>MOOPIEW · CONNECTED COMMERCE</footer></div>;
}

function Registration({kind}: {kind: "rider" | "merchant"}) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(false); setMessage("");
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = kind === "rider"
        ? await api.applications.registerRider(values as unknown as RiderApplicationInput)
        : await api.applications.registerMerchant(values as unknown as MerchantApplicationInput);
      setMessage(`ส่งใบสมัครแล้ว เลขที่ ${result.application.id} · รอทีมงานตรวจสอบ`);
      event.currentTarget.reset();
    } catch (caught) {
      setError(true); setMessage(caught instanceof Error ? caught.message : "ส่งใบสมัครไม่สำเร็จ");
    } finally { setBusy(false); }
  }
  const rider = kind === "rider";
  return <Shell><main className="registration"><section><p className="eyebrow">{rider ? "RIDER PARTNER" : "MERCHANT PARTNER"}</p><h1>{rider ? "ส่งความอร่อย\nไปด้วยกัน" : "เติบโตไป\nด้วยกัน"}</h1><p>{rider ? "ร่วมทีมจัดส่งที่ใส่ใจทุกออเดอร์ สมัครง่าย ตรวจสอบสถานะโดยทีมร้าน" : "เชื่อมร้านของคุณกับเครือข่าย MooPiew และเริ่มต้นโอกาสทางธุรกิจใหม่"}</p><ol><li><b>01</b>กรอกข้อมูลให้ครบถ้วน</li><li><b>02</b>ทีมงานตรวจสอบใบสมัคร</li><li><b>03</b>รับการติดต่อเพื่อเปิดใช้งาน</li></ol></section><form onSubmit={submit}><div className="form-title"><span>APPLICATION</span><h2>{rider ? "สมัครเป็นไรเดอร์" : "สมัครร้านค้าพันธมิตร"}</h2></div>{rider ? <><label>ชื่อ–นามสกุล<input name="name" required minLength={2}/></label><label>เบอร์โทรศัพท์<input name="phone" inputMode="tel" required/></label><label>ยานพาหนะ<select name="vehicle_type" required><option value="motorcycle">มอเตอร์ไซค์</option><option value="bicycle">จักรยาน</option><option value="car">รถยนต์</option></select></label><label>ทะเบียนรถ (ถ้ามี)<input name="vehicle_plate"/></label></> : <><label>ชื่อร้าน<input name="business_name" required minLength={2}/></label><label>ชื่อเจ้าของร้าน<input name="owner_name" required minLength={2}/></label><div className="two"><label>เบอร์โทรศัพท์<input name="phone" inputMode="tel" required/></label><label>อีเมล (ถ้ามี)<input name="email" type="email"/></label></div><label>ประเภทร้าน/สินค้า<input name="category" required placeholder="เช่น อาหารปิ้งย่าง"/></label><label>ที่อยู่ร้าน<textarea name="address" required/></label></>}<label>หมายเหตุ<textarea name="note" placeholder={rider ? "เช่น ช่วงเวลาที่รับงานได้" : ""}/></label><button disabled={busy}>{busy ? "กำลังส่ง…" : "ส่งใบสมัคร →"}</button>{message&&<p className={error?"form-message error":"form-message"} role="status">{message}</p>}</form></main></Shell>;
}

const hubs=[["OWNER","จัดการร้าน","ยอดจอง เมนู การชำระเงิน และ audit log","/admin.html"],["OPERATIONS","ศูนย์ปฏิบัติการ","ไรเดอร์ สต็อก คูปอง เอกสาร และจัดส่ง","/ops.html"],["KITCHEN","คิวครัว","ดูคิวที่ยืนยันแล้วและทำรายการให้พร้อมรับ","/ops.html?role=kitchen"],["AI","MooPiew Intelligence","วางแผน วิเคราะห์ และสร้างงานด้วย live models","/ai.html"]];
function Dashboard(){return <Shell><main className="hub"><p className="eyebrow">MOO PIW PIW / OPERATIONS</p><h1>เลือกศูนย์งาน</h1><p>เข้าสู่ workspace ตามหน้าที่ แต่ละส่วนใช้สิทธิ์และ API boundary ที่กำหนดไว้</p><section>{hubs.map(([tag,title,copy,href],index)=><a key={tag} href={href} className={index===0?"featured":""}><span>{tag}</span><b>0{index+1}</b><h2>{title}</h2><p>{copy}</p><i>เปิด workspace →</i></a>)}</section></main></Shell>}

const money=(value:number)=>new Intl.NumberFormat("th-TH",{style:"currency",currency:"THB",maximumFractionDigits:0}).format(value);

function MenuPreview(){
  const [menu,setMenu]=useState<MenuResponse>(); const [error,setError]=useState("");
  useEffect(()=>{api.menus.get().then(setMenu).catch(caught=>setError(caught instanceof Error?caught.message:"โหลดเมนูไม่สำเร็จ"));},[]);
  if(error)return <Shell><main className="preview"><p className="form-message error" role="alert">{error}</p></main></Shell>;
  return <Shell><main className="preview" style={menu?{"--preview-primary":menu.theme.primary,"--preview-secondary":menu.theme.secondary} as React.CSSProperties:undefined}><header><p>LIVE STOREFRONT SKIN</p><h1>{menu?.store.name||"กำลังโหลด MooPiew"}</h1><span>{menu?`อัปเดต ${new Date(menu.generated_at).toLocaleString("th-TH")}`:"กำลังเชื่อมต่อ API…"}</span></header><section className="preview-stats"><div><b>PRIMARY</b><code>{menu?.theme.primary||"—"}</code></div><div><b>SECONDARY</b><code>{menu?.theme.secondary||"—"}</code></div><div><b>AVAILABLE</b><strong>{menu?.pickup.remaining_total??"—"}</strong></div></section><section className="preview-menu"><div className="preview-heading"><div><p>LIVE MENU</p><h2>เมนูพร้อมสั่ง</h2></div><a href={menu?.links.order||"/"}>สั่งล่วงหน้า →</a></div><div>{menu?.items.map(item=><article key={item.id}><div><h3>{item.name}</h3><p>{item.description}</p></div><strong>{money(item.price)}</strong></article>)||<p>กำลังโหลดเมนู…</p>}</div></section><section className="preview-slots"><p>PICKUP SLOTS</p><h2>{menu?.pickup.date||"—"}</h2><div>{menu?.pickup.slots.map(slot=><span className={slot.available?"":"off"} key={slot.time}><i/>{slot.time} · เหลือ {slot.remaining}</span>)}</div></section></main></Shell>;
}

type Probe={name:string;endpoint:MonitorEndpoint;protected?:boolean};
type ProbeResult=Probe&{ok:boolean;status:number;ms:number;detail:string};
const probes:Probe[]=[{name:"Service health",endpoint:"/api/health"},{name:"Database readiness",endpoint:"/api/ready"},{name:"Platform status",endpoint:"/api/status"},{name:"Live storefront menu",endpoint:"/api/menu"},{name:"SCB public configuration",endpoint:"/api/payments/scb/config"},{name:"Admin menu configuration",endpoint:"/api/admin/menu",protected:true},{name:"SCB authorization status",endpoint:"/api/admin/scb/auth/status",protected:true},{name:"AI catalog configuration",endpoint:"/api/admin/ai/config",protected:true},{name:"Live AI model catalog",endpoint:"/api/admin/ai/models",protected:true}];
async function runProbe(probe:Probe,key=""):Promise<ProbeResult>{const started=performance.now();try{const data=await api.monitoring.probe(probe.endpoint,key);const models=Array.isArray(data.models)?`${data.models.length} โมเดล`:"";return{...probe,ok:true,status:200,ms:Math.round(performance.now()-started),detail:String(data.status||data.service||data.store_name||models||"ok")};}catch(caught){const status=caught instanceof MoopiewApiError?caught.status:0;return{...probe,ok:false,status,ms:Math.round(performance.now()-started),detail:caught instanceof Error?caught.message:"เชื่อมต่อไม่ได้"};}}
function ApiMonitor(){
  const [adminKey,setAdminKey]=useState(""); const [results,setResults]=useState<ProbeResult[]>([]); const [busy,setBusy]=useState(false); const [updated,setUpdated]=useState("");
  async function refresh(includeAdmin=false){if(busy)return;setBusy(true);const selected=probes.filter(probe=>!probe.protected||(includeAdmin&&adminKey));const next=await Promise.all(selected.map(probe=>runProbe(probe,probe.protected?adminKey:"")));setResults([...next,...probes.filter(probe=>probe.protected&&!selected.includes(probe)).map(probe=>({...probe,ok:false,status:401,ms:0,detail:"กรอก Admin key เพื่อทดสอบ"}))]);setUpdated(new Date().toLocaleString("th-TH"));setBusy(false);}
  useEffect(()=>{void refresh();const timer=window.setInterval(()=>void refresh(),30000);return()=>window.clearInterval(timer);},[]);
  const publicResults=results.filter(result=>!result.protected);const allPublicOk=publicResults.length>0&&publicResults.every(result=>result.ok);
  return <Shell><main className="monitor"><header><div><p>MOOPIEW / API MONITOR</p><h1>สถานะระบบแบบ Live</h1></div><button onClick={()=>void refresh()} disabled={busy}>{busy?"กำลังตรวจ…":"รีเฟรช"}</button></header><section className={`overall ${allPublicOk?"ok":publicResults.length?"bad":""}`}><i/><div><b>{allPublicOk?"Public API ทำงานปกติ":busy?"กำลังตรวจสอบ":"พบ endpoint ที่ต้องตรวจสอบ"}</b><small>{publicResults.filter(result=>result.ok).length}/{publicResults.length||5} endpoint ตอบกลับสำเร็จ</small></div></section><section className="monitor-admin"><label>Admin key <span>(ไม่บันทึกในเบราว์เซอร์)</span></label><div><input type="password" value={adminKey} onChange={event=>setAdminKey(event.target.value)} autoComplete="off" placeholder="ใส่เพื่อตรวจ protected API"/><button onClick={()=>void refresh(true)} disabled={busy||!adminKey}>ตรวจส่วนผู้ดูแล</button></div></section>{[false,true].map(protectedGroup=><section className="probe-group" key={String(protectedGroup)}><div><h2>{protectedGroup?"Protected API":"Public API"}</h2><span>{protectedGroup?"ต้องใช้ Admin key":`${publicResults.filter(result=>result.ok).length}/${publicResults.length||5} ผ่าน`}</span></div><div>{results.filter(result=>Boolean(result.protected)===protectedGroup).map(result=><article key={result.endpoint}><i className={result.ok?"ok":result.status===401?"warn":"bad"}/><div><b>{result.name}</b><small>{result.endpoint} · {result.detail}</small></div><strong>{result.status===401?"LOCKED":`${result.status||"FAIL"} · ${result.ms} ms`}</strong></article>)}</div></section>)}<footer>อัปเดต {updated||"—"} · รีเฟรชอัตโนมัติทุก 30 วินาที</footer></main></Shell>;
}

const app=page==="rider"?<Registration kind="rider"/>:page==="merchant"?<Registration kind="merchant"/>:page==="preview"?<MenuPreview/>:page==="monitor"?<ApiMonitor/>:<Dashboard/>;
createRoot(document.getElementById("root")!).render(<StrictMode>{app}</StrictMode>);
