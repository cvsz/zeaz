const $ = selector => document.querySelector(selector);
const money = n => `฿${Number(n).toLocaleString('th-TH')}`;
let dashboard;
function message(text, error=false) { const node=$('#notice'); node.textContent=text; node.className=`notice ${error?'error':''}`; }
async function api(url, options={}) {
  const response=await fetch(url,{...options,headers:{'Content-Type':'application/json','X-Admin-Key':$('#key').value,...(options.headers||{})}});
  const raw=await response.text(); let data={}; try { data=raw?JSON.parse(raw):{}; } catch { throw new Error('เซิร์ฟเวอร์ส่งข้อมูลไม่สมบูรณ์ กรุณาลองใหม่'); }
  if(!response.ok) throw new Error(data.error||`เกิดข้อผิดพลาด (${response.status})`); return data;
}
const orderCard=order=>`<article class="menu-item"><div><h4>${order.id} · ${order.customer.name}</h4><p>${order.customer.phone} · ${order.pickup.date} ${order.pickup.slot}</p><p>${order.items.map(item=>`${item.name} × ${item.quantity}`).join(', ')} · ชำระ: ${order.payment.status}</p><p class="price">${money(order.total)}</p></div><div class="order-actions"><select data-order="${order.id}" data-field="status">${['new','confirmed','ready','completed','cancelled'].map(value=>`<option value="${value}" ${value===order.status?'selected':''}>${value}</option>`).join('')}</select><select data-order="${order.id}" data-field="payment_status">${['pending','paid','refunded'].map(value=>`<option value="${value}" ${value===order.payment.status?'selected':''}>${value}</option>`).join('')}</div></article>`;
function render() {
  const {summary,orders,settings,audit=[]}=dashboard; $('#dashboard').hidden=false;
  $('#summary').innerHTML=`<div><strong>${summary.orders}</strong><span>ออเดอร์ทั้งหมด</span></div><div><strong>${summary.active_orders}</strong><span>กำลังดำเนินการ</span></div><div><strong>${money(summary.revenue)}</strong><span>ยอดจอง</span></div><div><strong>${summary.ready}</strong><span>พร้อมรับ</span></div>`;
  $('#slot-capacity').value=settings.slot_capacity; $('#advance-days').value=settings.advance_days;
  $('#menu-list').innerHTML=settings.menu.map(item=>`<article class="menu-item"><div><h4>${item.name} ${item.available?'':'(ปิดขาย)'}</h4><p>${item.description}</p><p class="price">${money(item.price)}</p></div><button class="text-button" data-menu="${item.id}" data-available="${!item.available}">${item.available?'ปิดขาย':'เปิดขาย'}</button></article>`).join('');
  $('#orders').innerHTML=orders.length?orders.map(orderCard).join(''):'<p>ยังไม่มีออเดอร์</p>';
  $('#audit').innerHTML=audit.length?audit.map(item=>`<p><b>${item.actor_role}</b> · ${item.action} ${item.entity_type} <code>${item.entity_id}</code><small>${new Date(item.at).toLocaleString('th-TH')}</small></p>`).join(''):'<p>ยังไม่มีกิจกรรม</p>';
}
async function load(){try{dashboard=await api('/api/admin/dashboard');render();message('อัปเดตข้อมูลแล้ว');}catch(error){message(error.message,true);}}
$('#load').onclick=load;
$('#settings-form').onsubmit=async event=>{event.preventDefault();try{await api('/api/admin/settings',{method:'PATCH',body:JSON.stringify(Object.fromEntries(new FormData(event.currentTarget)))});await load();}catch(error){message(error.message,true);}};
$('#menu-form').onsubmit=async event=>{event.preventDefault();try{await api('/api/admin/menu',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(event.currentTarget)))});event.currentTarget.reset();await load();}catch(error){message(error.message,true);}};
$('#menu-list').onclick=async event=>{const button=event.target.closest('[data-menu]');if(!button)return;try{await api(`/api/admin/menu/${button.dataset.menu}`,{method:'PATCH',body:JSON.stringify({available:button.dataset.available==='true'})});await load();}catch(error){message(error.message,true);}};
$('#orders').onchange=async event=>{const select=event.target;if(!select.dataset.order)return;try{await api(`/api/admin/orders/${select.dataset.order}`,{method:'PATCH',body:JSON.stringify({[select.dataset.field]:select.value})});await load();}catch(error){message(error.message,true);}};
