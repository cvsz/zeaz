import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { MoopiewClient } from "@moopiew/sdk";
import type { MenuItem } from "@moopiew/types";
import "./styles.css";
type MenuResponse={store_name:string;items:MenuItem[];date:string};
const api=new MoopiewClient({baseURL:import.meta.env.VITE_API_URL||window.location.origin});
function App(){const [menu,setMenu]=useState<MenuResponse>();const [error,setError]=useState("");useEffect(()=>{api.request<MenuResponse>("/api/menu").then(setMenu).catch(error=>setError(error.message));},[]);return <main><p className="eyebrow">MOOPIEW / PLATFORM WEB</p><h1>{menu?.store_name??"หมูปิ้ววว"}</h1><p>React web shell เชื่อมกับ API production เดียวกัน</p><nav><a href="/">สั่งล่วงหน้า</a><a href="/dashboard.html">Operations</a></nav>{error?<p role="alert">{error}</p>:<section>{menu?.items.map(item=><article key={item.id}><h2>{item.name}</h2><p>{item.description}</p><strong>฿{item.price}</strong></article>)??<p>กำลังโหลดเมนู…</p>}</section>}</main>}
createRoot(document.getElementById("root")!).render(<StrictMode><App/></StrictMode>);
