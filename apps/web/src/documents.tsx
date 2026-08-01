import { DragEvent, FormEvent, StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { MoopiewClient } from "@moopiew/sdk";
import type {
  DocumentRequirement,
  Provider,
  UploadedDocument,
} from "@moopiew/types";
import "./documents.css";

const api = new MoopiewClient({
  baseURL: import.meta.env.VITE_API_URL || window.location.origin,
});
const messageOf = (error: unknown) =>
  error instanceof Error ? error.message : "ดำเนินการไม่สำเร็จ";
const statusLabel: Record<string, string> = {
  pending: "รอตรวจสอบ",
  approved: "อนุมัติ",
  rejected: "ไม่ผ่าน",
  expired: "หมดอายุ",
};
const fileBase64 = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("ไม่สามารถอ่านไฟล์ได้"));
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.readAsDataURL(file);
  });

function OwnerGate({
  adminKey,
  setAdminKey,
  action,
  actionLabel,
  notice,
}: {
  adminKey: string;
  setAdminKey: (value: string) => void;
  action: () => void;
  actionLabel: string;
  notice: string;
}) {
  return (
    <section className="owner-gate">
      <label>
        Owner key
        <input
          type="password"
          autoComplete="current-password"
          value={adminKey}
          onChange={(event) => setAdminKey(event.target.value)}
          placeholder="ค่าจาก ADMIN_KEY"
        />
      </label>
      <button type="button" onClick={action}>{actionLabel} <span>→</span></button>
      <p role="status" aria-live="polite">{notice}</p>
      <small>คีย์อยู่ในหน่วยความจำของหน้านี้เท่านั้น และไม่ถูกบันทึกลง browser storage</small>
    </section>
  );
}

function UploadCard({
  requirement,
  adminKey,
  provider,
  subject,
  subjectId,
}: {
  requirement: DocumentRequirement;
  adminKey: string;
  provider: string;
  subject: "rider" | "merchant";
  subjectId: string;
}) {
  const [document, setDocument] = useState<UploadedDocument>();
  const [file, setFile] = useState<File>();
  const [preview, setPreview] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    if (!file || file.type === "application/pdf") {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function upload(next: File) {
    const allowed = requirement.allowed_mime_types.includes(next.type);
    if (!allowed || next.size > requirement.max_size_bytes) {
      setMessage("ชนิดไฟล์หรือขนาดไฟล์ไม่ผ่านข้อกำหนด");
      return;
    }
    setFile(next);
    setBusy(true);
    setMessage("กำลังเข้ารหัสและส่งเอกสาร…");
    try {
      const result = await api.documents.upload(adminKey, {
        provider,
        subject_type: subject,
        subject_id: subjectId,
        requirement_id: requirement.id,
        filename: next.name,
        mime_type: next.type,
        content_base64: await fileBase64(next),
      });
      setDocument(result.document);
      setFile(undefined);
      setMessage("ส่งเอกสารแล้ว รอเจ้าหน้าที่ตรวจสอบ");
    } catch (error) {
      setMessage(messageOf(error));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!document || !window.confirm("ลบเอกสารนี้ออกจากระบบ?")) return;
    setBusy(true);
    try {
      await api.documents.remove(adminKey, document.id);
      setDocument(undefined);
      setMessage("ลบเอกสารแล้ว");
    } catch (error) {
      setMessage(messageOf(error));
    } finally {
      setBusy(false);
    }
  }

  function drop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    setDragging(false);
    const [next] = Array.from(event.dataTransfer.files);
    if (next) void upload(next);
  }

  return (
    <article
      className={`upload-card ${dragging ? "dragging" : ""}`}
      onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={drop}
    >
      <header>
        <span className="card-number">{String(requirement.display_order + 1).padStart(2, "0")}</span>
        <span className={`status ${document?.status ?? "empty"}`}>
          {document ? statusLabel[document.status] ?? document.status : "ยังไม่ได้ส่ง"}
        </span>
      </header>
      <div>
        <h3>{requirement.metadata.label_th || requirement.document_name}</h3>
        <p>{requirement.is_required ? "เอกสารจำเป็น" : "เอกสารทางเลือก"} · สูงสุด {Math.ceil(requirement.max_size_bytes / 1024 / 1024)} MB</p>
      </div>
      {preview && <img className="preview" src={preview} alt={`ตัวอย่าง ${file?.name}`} />}
      {file?.type === "application/pdf" && <div className="pdf-preview">PDF</div>}
      {document && <div className="existing-file"><strong>{document.original_filename}</strong><small>{Math.ceil(document.size_bytes / 1024)} KB</small></div>}
      <label className={`dropzone ${busy ? "busy" : ""}`}>
        <input
          type="file"
          hidden
          disabled={busy}
          accept={requirement.allowed_mime_types.join(",")}
          onChange={(event) => {
            const next = event.target.files?.[0];
            if (next) void upload(next);
            event.target.value = "";
          }}
        />
        <span>{busy ? "กำลังอัปโหลด…" : document ? "เปลี่ยนไฟล์" : "เลือกหรือลากไฟล์มาวาง"}</span>
        <small>{requirement.allowed_mime_types.map((type) => type.split("/")[1]?.toUpperCase()).join(" · ")}</small>
      </label>
      {document && <button className="delete-button" type="button" disabled={busy} onClick={remove}>ลบเอกสาร</button>}
      <p className="card-message" role="status">{message}</p>
    </article>
  );
}

function DocumentsPage() {
  const [adminKey, setAdminKey] = useState("");
  const [providers, setProviders] = useState<Provider[]>([]);
  const [provider, setProvider] = useState("");
  const [subject, setSubject] = useState<"rider" | "merchant">("rider");
  const [subjectId, setSubjectId] = useState("");
  const [requirements, setRequirements] = useState<DocumentRequirement[]>([]);
  const [notice, setNotice] = useState("เลือกข้อมูลผู้สมัครเพื่อโหลดรายการเอกสาร");

  useEffect(() => {
    api.documents.providers()
      .then(({ providers: rows }) => {
        setProviders(rows);
        setProvider(rows[0]?.slug ?? "");
      })
      .catch((error) => setNotice(messageOf(error)));
  }, []);

  async function load() {
    if (!adminKey || !provider || !/^[A-Za-z0-9_-]{2,100}$/.test(subjectId)) {
      setNotice("กรุณากรอก Owner key และรหัสผู้สมัครให้ถูกต้อง");
      return;
    }
    try {
      const result = await api.documents.requirements(provider, subject);
      setRequirements(result.requirements);
      setNotice(`พบ ${result.requirements.length} requirements จากฐานข้อมูล provider`);
    } catch (error) {
      setNotice(messageOf(error));
    }
  }

  return (
    <Shell eyebrow="SECURE DOCUMENT INTAKE" title={<>เอกสารสมัครงาน<br /><em>ครบ จบ ปลอดภัย</em></>} description="รายการเอกสารถูกโหลดจากนโยบาย provider ในฐานข้อมูล ไฟล์ถูกตรวจชนิดและจัดเก็บแบบเข้ารหัสนอก public web root">
      <OwnerGate adminKey={adminKey} setAdminKey={setAdminKey} action={load} actionLabel="โหลด requirements" notice={notice} />
      <section className="filters">
        <label>Provider<select value={provider} onChange={(event) => setProvider(event.target.value)}>{providers.map((item) => <option key={item.id} value={item.slug}>{item.name}</option>)}</select></label>
        <label>ประเภท<select value={subject} onChange={(event) => setSubject(event.target.value as "rider" | "merchant")}><option value="rider">Rider</option><option value="merchant">Merchant</option></select></label>
        <label>รหัสผู้สมัคร<input value={subjectId} pattern="[A-Za-z0-9_-]{2,100}" onChange={(event) => setSubjectId(event.target.value)} placeholder="RDR-... / MAP-..." /></label>
      </section>
      <section className="upload-grid" aria-live="polite">
        {requirements.map((requirement) => <UploadCard key={requirement.id} requirement={requirement} adminKey={adminKey} provider={provider} subject={subject} subjectId={subjectId} />)}
      </section>
    </Shell>
  );
}

function PolicyCard({
  requirement,
  adminKey,
  reload,
}: {
  requirement: DocumentRequirement;
  adminKey: string;
  reload: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    try {
      await api.documents.versionPolicy(adminKey, requirement.id, {
        display_order: Number(form.get("display_order")),
        is_required: form.get("is_required") === "on",
        is_optional: form.get("is_optional") === "on",
        metadata: {
          label_th: String(form.get("label_th") ?? ""),
          label_en: String(form.get("label_en") ?? ""),
        },
      });
      await reload();
    } catch (error) {
      setMessage(messageOf(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className={`policy-card ${requirement.is_current ? "" : "historical"}`}>
      <header><div><small>{requirement.provider_name} · {requirement.subject_type}</small><h3>{requirement.document_name}</h3></div><span className="status">{requirement.is_current ? "CURRENT" : "HISTORY"}</span></header>
      <p>{requirement.merchant_type_slug || requirement.vehicle_type_slug || "ทุกประเภท"} · เริ่มใช้ {requirement.effective_from}</p>
      {requirement.is_current ? <form onSubmit={submit}>
        <div className="field-row"><label>ลำดับ<input name="display_order" type="number" min="0" defaultValue={requirement.display_order} /></label><label>ชื่อไทย<input name="label_th" defaultValue={requirement.metadata.label_th ?? ""} /></label><label>ชื่ออังกฤษ<input name="label_en" defaultValue={requirement.metadata.label_en ?? ""} /></label></div>
        <div className="check-row"><label><input name="is_required" type="checkbox" defaultChecked={requirement.is_required} /> จำเป็น</label><label><input name="is_optional" type="checkbox" defaultChecked={requirement.is_optional} /> เลือกได้</label></div>
        <button disabled={busy}>{busy ? "กำลังสร้างเวอร์ชัน…" : "สร้าง policy version ใหม่ →"}</button>
        {message && <p className="error" role="alert">{message}</p>}
      </form> : <small>สิ้นสุด {requirement.effective_to} · เวอร์ชันประวัติอ่านอย่างเดียว</small>}
    </article>
  );
}

function PolicyPage() {
  const [adminKey, setAdminKey] = useState("");
  const [requirements, setRequirements] = useState<DocumentRequirement[]>([]);
  const [notice, setNotice] = useState("กรอก Owner key เพื่อโหลด policy versions");
  async function load() {
    if (!adminKey) return setNotice("กรุณากรอก Owner key");
    try {
      const result = await api.documents.policies(adminKey);
      setRequirements(result.requirements);
      setNotice(`โหลดแล้ว ${result.requirements.length} policy versions`);
    } catch (error) {
      setNotice(messageOf(error));
    }
  }
  return (
    <Shell eyebrow="PROVIDER POLICY CONTROL" title={<>นโยบายเอกสาร<br /><em>มีเวอร์ชัน ตรวจสอบได้</em></>} description="แก้ไข policy ด้วย additive versioning ประวัติเดิมไม่ถูกเขียนทับ และทุก mutation ผ่าน owner authentication">
      <OwnerGate adminKey={adminKey} setAdminKey={setAdminKey} action={() => void load()} actionLabel="โหลดนโยบาย" notice={notice} />
      <section className="policy-list">
        {requirements.map((requirement) => <PolicyCard key={requirement.id} requirement={requirement} adminKey={adminKey} reload={load} />)}
      </section>
    </Shell>
  );
}

function Shell({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: React.ReactNode;
  description: string;
  children: React.ReactNode;
}) {
  return <><header className="document-nav"><a href="/">MOOPIEW®</a><nav><a href="/platform/documents.html">Upload</a><a href="/platform/document-admin.html">Policy</a><a href="/platform/dashboard.html">Dashboard</a></nav></header><main><section className="document-hero"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></section>{children}</main><footer>MOOPIEW · PRIVATE DOCUMENT WORKSPACE <a href="/platform/api-monitor.html">System status</a></footer></>;
}

const page = document.body.dataset.page;
createRoot(document.getElementById("root")!).render(
  <StrictMode>{page === "document-admin" ? <PolicyPage /> : <DocumentsPage />}</StrictMode>,
);
