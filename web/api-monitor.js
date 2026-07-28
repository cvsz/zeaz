const publicEndpoints=[
  ['Service health','/api/health'],['Database readiness','/api/ready'],
  ['Platform status','/api/status'],['Live storefront menu','/api/menu'],
  ['SCB public configuration','/api/payments/scb/config'],
];
const protectedEndpoints=[
  ['Admin menu configuration','/api/admin/menu'],['SCB authorization status','/api/admin/scb/auth/status'],
  ['AI catalog configuration','/api/admin/ai/config'],['Live AI model catalog','/api/admin/ai/models'],
];
const $=(selector)=>document.querySelector(selector);
let refreshing=false;

async function check(name,url,adminKey=''){
  const started=performance.now();
  try{
    // HTTP headers are ISO-8859-1 on the wire; use the same UTF-8-safe
    // base64 credential transport as the admin console to avoid browser
    // "String contains non ISO-8859-1 code point" failures.
    const encoded=adminKey?btoa(Array.from(new TextEncoder().encode(adminKey),byte=>String.fromCharCode(byte)).join('')):'';
    const response=await fetch(url,{cache:'no-store',headers:encoded?{'X-Admin-Key-B64':encoded}:{}});
    let data={};try{data=await response.json();}catch{}
    const protectedRoute=response.status===401&&Boolean(adminKey)===false;
    const aiCount=Array.isArray(data.models)?`${data.models.length} โมเดล` : '';
    const detail=data.status||data.service||data.store_name||data.error||aiCount||(protectedRoute?'ต้องใช้ Admin key':'ok');
    return{name,url,ok:response.ok,protected:protectedRoute,status:response.status,ms:Math.round(performance.now()-started),detail};
  }catch(error){return{name,url,ok:false,protected:false,status:0,ms:Math.round(performance.now()-started),detail:'เชื่อมต่อไม่ได้'};}
}
function row(result){
  const article=document.createElement('article');article.className='check';
  const dot=document.createElement('i');dot.className=`dot ${result.ok?'ok':result.protected?'warn':'bad'}`;
  const info=document.createElement('div');const title=document.createElement('b');title.textContent=result.name;
  const detail=document.createElement('small');detail.textContent=`${result.url} · ${result.detail}`;info.append(title,detail);
  const status=document.createElement('strong');status.textContent=result.protected?'LOCKED':result.ok?`${result.status} · ${result.ms} ms`:`${result.status||'FAIL'} · ${result.ms} ms`;
  article.append(dot,info,status);return article;
}
function renderRows(target,results){const root=$(target);root.replaceChildren(...results.map(row));}
async function render(includeAdmin=false){
  if(refreshing)return;
  refreshing=true;
  const refreshButton=$('#refresh'),adminButton=$('#check-admin');refreshButton.disabled=true;
  if(includeAdmin){adminButton.disabled=true;adminButton.textContent='กำลังตรวจ…';}
  try{
  const overall=$('#overall');overall.className='overall';overall.querySelector('b').textContent='กำลังตรวจสอบ';
  const publicResults=await Promise.all(publicEndpoints.map(([name,url])=>check(name,url)));renderRows('#checks',publicResults);
  const allOk=publicResults.every(result=>result.ok);overall.classList.add(allOk?'ok':'bad');overall.querySelector('b').textContent=allOk?'Public API ทำงานปกติ':'พบ Public API ที่ต้องตรวจสอบ';
  overall.querySelector('small').textContent=allOk?`${publicResults.length} endpoint ตอบกลับสำเร็จ`:'ดูรายการด้านล่างเพื่อวินิจฉัย';$('#public-count').textContent=`${publicResults.filter(r=>r.ok).length}/${publicResults.length} ผ่าน`;
  const key=$('#admin-key').value.trim();
  if(includeAdmin&&key){const results=await Promise.all(protectedEndpoints.map(([name,url])=>check(name,url,key)));renderRows('#protected-checks',results);$('#admin-note').textContent=results.every(r=>r.ok)?'ตรวจ endpoint ผู้ดูแลสำเร็จ':'ไม่สามารถยืนยัน Admin key หรือ provider ได้';}
  else {renderRows('#protected-checks',protectedEndpoints.map(([name,url])=>({name,url,ok:false,protected:true,status:401,ms:0,detail:'กรอก Admin key เพื่อทดสอบ'})));$('#admin-note').textContent=includeAdmin?'กรุณากรอก Admin key ก่อนตรวจสอบ':'เว้นว่างไว้ได้ — ระบบจะตรวจเฉพาะ public API';}
  $('#updated').textContent=`อัปเดต ${new Date().toLocaleString('th-TH')} · รีเฟรชอัตโนมัติทุก 30 วินาที`;
  }finally{refreshing=false;refreshButton.disabled=false;adminButton.disabled=false;adminButton.textContent='ตรวจส่วนผู้ดูแล';}
}
$('#refresh').onclick=()=>render();$('#check-admin').onclick=()=>render(true);render();setInterval(()=>render(),30000);
