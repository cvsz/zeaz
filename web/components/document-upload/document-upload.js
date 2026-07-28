/* Database-driven document upload components. No provider checklist is kept here. */
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export class UploadButton {
  constructor(card) { this.card = card; }
  click() { this.card.input.click(); }
}

export class DocumentPreview {
  static render(file) {
    if (!file) return '';
    const url = URL.createObjectURL(file);
    const body = file.type === 'application/pdf' ? `<span class="document-pdf">PDF</span>` : `<img src="${url}" alt="ตัวอย่างเอกสาร">`;
    return `<div class="document-preview">${body}<small>${esc(file.name)} · ${Math.ceil(file.size / 1024)} KB</small></div>`;
  }
}

export class DocumentStatus {
  static label(status) { return ({pending:'รอตรวจสอบ',approved:'อนุมัติ',rejected:'ไม่ผ่าน',expired:'หมดอายุ',deleted:'ลบแล้ว'})[status] || status || 'ยังไม่ได้ส่ง'; }
}

export class UploadCard {
  constructor(requirement, options) {
    this.requirement = requirement; this.options = options; this.file = null; this.document = null;
    this.element = document.createElement('article'); this.element.className = 'document-upload-card'; this.render();
  }
  render(message = '') {
    const r = this.requirement, status = this.document?.status || '';
    this.element.innerHTML = `<header><div><h3>${esc(r.document_name)}</h3><p>${r.is_required ? '<strong>จำเป็น</strong>' : 'เลือกส่งได้'}${r.metadata?.note ? ` · ${esc(r.metadata.note)}` : ''}</p></div><span class="document-status status-${esc(status || 'empty')}">${esc(DocumentStatus.label(status))}</span></header>
      ${this.file ? DocumentPreview.render(this.file) : this.document ? `<p class="document-existing">ส่งแล้ว: ${esc(this.document.original_filename)}</p>` : '<p class="document-hint">ถ่ายรูป อัปโหลดจากคลัง ลากไฟล์ หรือเลือก PDF</p>'}
      <div class="document-progress" aria-live="polite"></div><p class="document-error" role="alert">${esc(message)}</p>
      <input class="document-input" type="file" accept="${esc((r.allowed_mime_types || []).join(','))}" capture="environment" hidden>
      <div class="document-actions"><button type="button" class="button choose">${this.file || this.document ? 'เปลี่ยนไฟล์' : 'อัปโหลดเอกสาร'}</button>${this.document ? '<button type="button" class="text-button remove">ลบ</button>' : ''}</div>`;
    this.input = this.element.querySelector('.document-input');
    this.element.querySelector('.choose').onclick = () => this.input.click();
    this.input.onchange = () => { const [file] = this.input.files; if (file) { this.file = file; this.render(); this.upload(); } };
    this.element.querySelector('.remove')?.addEventListener('click', () => this.remove());
  }
  async upload() {
    const file = this.file, max = Number(this.requirement.max_size_bytes || 10485760);
    if (!file || !this.requirement.allowed_mime_types.includes(file.type) || file.size > max) { this.render('ชนิดไฟล์หรือขนาดไฟล์ไม่ผ่านการตรวจสอบ'); return; }
    const reader = new FileReader(); reader.onprogress = event => { if (event.lengthComputable) this.element.querySelector('.document-progress').textContent = `กำลังเตรียมไฟล์ ${Math.round(event.loaded / event.total * 100)}%`; };
    reader.onload = async () => {
      try {
        const response = await fetch('/api/documents/upload', {method:'POST', headers:{'Content-Type':'application/json','X-Admin-Key':this.options.adminKey()}, body:JSON.stringify({provider:this.options.provider(), subject_type:this.options.subjectType(), subject_id:this.options.subjectId(), requirement_id:this.requirement.id, filename:file.name, mime_type:file.type, content_base64:String(reader.result).split(',')[1]})});
        const data = await response.json(); if (!response.ok) throw new Error(data.error || 'อัปโหลดไม่สำเร็จ');
        this.document = data.document; this.file = null; this.render('ส่งเอกสารแล้ว รอเจ้าหน้าที่ตรวจสอบ');
      } catch (error) { this.render(error.message || 'อัปโหลดไม่สำเร็จ'); }
    }; reader.readAsDataURL(file);
  }
  async remove() { if (!this.document) return; try { const response=await fetch(`/api/documents/${encodeURIComponent(this.document.id)}`,{method:'DELETE',headers:{'X-Admin-Key':this.options.adminKey()}}); if(!response.ok) throw new Error('ลบเอกสารไม่สำเร็จ'); this.document=null; this.render(); } catch(error) { this.render(error.message); } }
}

export class UploadGrid {
  constructor(container, options) { this.container=container; this.options=options; this.cards=[]; }
  render(requirements) { this.container.innerHTML=''; this.cards=requirements.map(requirement=>new UploadCard(requirement,this.options)); this.cards.forEach(card=>this.container.append(card.element)); }
}

export class UploadSection { constructor(container, options) { this.grid=new UploadGrid(container,options); } render(requirements) { this.grid.render(requirements); } }
export class DocumentViewer { static render(document) { return `<a href="#" data-document-id="${esc(document.id)}">${esc(document.original_filename)}</a>`; } }
window.DocumentUpload = {UploadButton,DocumentPreview,DocumentStatus,UploadCard,UploadGrid,UploadSection,DocumentViewer};
