import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { MoopiewClient } from "@moopiew/sdk";
import type { MenuItem } from "@moopiew/types";
import "./styles.css";

type Slot={time:string;remaining:number;available:boolean};
type MenuResponse={store_name:string;items:MenuItem[];slots:Slot[];date:string};
const api=new MoopiewClient({baseURL:import.meta.env.VITE_API_URL||window.location.origin});
const money=(value:number)=>new Intl.NumberFormat("th-TH",{style:"currency",currency:"THB",maximumFractionDigits:0}).format(value);

function App(){
  const [menu,setMenu]=useState<MenuResponse>(); const [error,setError]=useState("");
  useEffect(()=>{api.request<MenuResponse>("/api/menu").then(setMenu).catch(error=>setError(error.message));},[]);
  const available=menu?.slots.filter(slot=>slot.available).reduce((total,slot)=>total+slot.remaining,0)??0;
  return <><header className="topbar"><a className="wordmark" href="/"><img src="/assets/branding/logo/moopiew-logo-light.svg" alt="Moopiew"/></a><nav><a href="/">สั่งล่วงหน้า</a><a href="/dashboard.html">Operations</a><a className="nav-cta" href="#menu">ดูเมนู</a></nav></header><main>
    <section className="hero"><div className="hero-copy"><p className="eyebrow">THAI GRILL · ORDER AHEAD</p><h1>หอมถ่าน<br/><em>ปิ้ววว</em> ถึงใจ</h1><p>หมูปิ้งย่างสดทุกเช้า จองล่วงหน้าแล้วรับได้ตามเวลาที่คุณเลือก</p><div className="hero-actions"><a className="button" href="/">สั่งล่วงหน้า</a><a className="text-link" href="/dashboard.html">สำหรับทีมร้าน →</a></div><div className="trust"><span>✦ ย่างสดทุกวัน</span><span>✦ รับตามเวลา</span></div></div><div className="hero-visual"><img src="/images/moopiew-hero.png" alt="หมูปิ้งย่างบนเตาถ่าน"/></div></section>
    <section className="stats" aria-label="สถานะร้าน"><article><span>AVAILABLE TODAY</span><strong>{available}</strong><small>ไม้ที่ยังรับจองได้</small></article><article><span>PICKUP SLOTS</span><strong>{menu?.slots.length??"—"}</strong><small>รอบรับสินค้าวันนี้</small></article><article><span>LIVE MENU</span><strong>{menu?.items.length??"—"}</strong><small>เมนูพร้อมสั่ง</small></article></section>
    <section id="menu" className="menu-section"><div className="section-heading"><div><p className="eyebrow">CURATED MENU</p><h2>เลือกของอร่อย<br/>แล้วนัดเวลารับ</h2></div><a href="/" className="text-link">เปิดหน้าสั่งซื้อ →</a></div>{error?<p className="error" role="alert">{error}</p>:<div className="menu-grid">{menu?.items.map((item,index)=><article className={`menu-card menu-card-${index}`} key={item.id}><span className="card-index">0{index+1}</span><div><h3>{item.name}</h3><p>{item.description}</p></div><strong>{money(item.price)}</strong><a href="/" aria-label={`สั่ง ${item.name}`}>เพิ่มในออเดอร์ <b>→</b></a></article>)??<p className="loading">กำลังโหลดเมนูสดจากร้าน…</p>}</div>}</section>
    <section className="pickup"><div><p className="eyebrow">SIMPLE PICKUP</p><h2>จองง่าย<br/>รับไว ไม่ต้องรอ</h2></div><ol><li><b>01</b><span>เลือกเมนูและรอบรับที่สะดวก</span></li><li><b>02</b><span>ยืนยันการจองจากหน้า order</span></li><li><b>03</b><span>รับหมูปิ้งร้อน ๆ ที่หน้าร้าน</span></li></ol></section>
  </main><footer>MOOPIEW · ย่างด้วยใจทุกไม้ <a href="/api/menu">API status</a></footer></>;
}
createRoot(document.getElementById("root")!).render(<StrictMode><App/></StrictMode>);
