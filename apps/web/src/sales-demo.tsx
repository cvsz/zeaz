import {useMemo, useState, type FormEvent} from "react";
import {createRoot} from "react-dom/client";
import "./sales-demo.css";

type DemoView = "overview" | "inbox" | "knowledge" | "orders";
type Channel = "Facebook Messenger" | "Shopee";
type MessageRole = "customer" | "bot" | "human";

type DemoMessage = {
  id: string;
  role: MessageRole;
  content: string;
  time: string;
};

type Conversation = {
  id: string;
  channel: Channel;
  customer: string;
  initials: string;
  preview: string;
  intent: string;
  wait: string;
  needsHuman: boolean;
  messages: DemoMessage[];
};

type DemoOrder = {
  id: string;
  customer: string;
  channel: Channel;
  items: string;
  total: number;
  status: string;
  time: string;
};

const PROMO_PRICE = 990;
const PROMO_LABEL = "2 แถม 1";
const money = new Intl.NumberFormat("th-TH", {
  style: "currency",
  currency: "THB",
  maximumFractionDigits: 0,
});

const initialConversations: Conversation[] = [
  {
    id: "fb-may",
    channel: "Facebook Messenger",
    customer: "คุณเมย์",
    initials: "ม",
    preview: "ช่วยเรื่องขาลายกับรอยคล้ำไหมคะ?",
    intent: "รอยคล้ำ / ขาลาย",
    wait: "ตอบเมื่อ 12 วินาทีก่อน",
    needsHuman: false,
    messages: [
      {
        id: "may-1",
        role: "customer",
        content: "ตัวนี้ช่วยเรื่องขาลายกับรอยแผลเป็นไหมคะ โดนแดดแล้วผิวหมองมาก?",
        time: "10:42",
      },
      {
        id: "may-2",
        role: "bot",
        content:
          "เข้าใจปัญหาผิวหมองและรอยคล้ำเลยค่ะคุณพี่ 😊 สูตรนี้มี Niacinamide, Ascorbic Acid และ Licorice Extract ที่ช่วยดูแลสีผิวให้ดูสม่ำเสมอขึ้น พร้อมดูแลผิวที่โดนแดดค่ะ\n\nตอนนี้มีโปร 2 แถม 1 ราคา 990 บาท ส่งฟรี มีเก็บเงินปลายทาง รับเป็นชุดนี้เลยไหมคะ?",
        time: "10:42",
      },
    ],
  },
  {
    id: "shopee-nok",
    channel: "Shopee",
    customer: "คุณนก",
    initials: "น",
    preview: "ผิวแพ้ง่าย ใช้แล้วจะแสบไหมคะ",
    intent: "ผิวบอบบาง / แสบแดด",
    wait: "ตอบเมื่อ 2 นาทีที่แล้ว",
    needsHuman: false,
    messages: [
      {
        id: "nok-1",
        role: "customer",
        content: "ผิวแพ้ง่ายมาก เพิ่งไปทะเลมาผิวลอกแสบ ใช้ได้ไหมคะ",
        time: "10:38",
      },
      {
        id: "nok-2",
        role: "bot",
        content:
          "ถ้าผิวยังแสบหรือลอกมาก แนะนำพักการใช้ผลิตภัณฑ์ใหม่และทดสอบการแพ้บริเวณเล็ก ๆ ก่อนนะคะ สูตรนี้มี Chamomile Extract กับ Panthenol ที่ช่วยดูแลผิวให้รู้สึกสบายขึ้น และ Sodium Hyaluronate ช่วยเติมความชุ่มชื้นค่ะ\n\nหากมีอาการรุนแรงควรปรึกษาผู้เชี่ยวชาญด้านผิวหนังนะคะ สนใจรับโปร 2 แถม 1 ราคา 990 บาทไหมคะ?",
        time: "10:39",
      },
    ],
  },
  {
    id: "fb-aom",
    channel: "Facebook Messenger",
    customer: "คุณอ้อม",
    initials: "อ",
    preview: "ขอคุยกับแอดมินคนได้ไหมคะ",
    intent: "ขอคุยกับคน",
    wait: "รอแอดมิน 4 นาที",
    needsHuman: true,
    messages: [
      {
        id: "aom-1",
        role: "customer",
        content: "ขอคุยกับแอดมินคนได้ไหมคะ มีเรื่องออเดอร์อยากสอบถาม",
        time: "10:36",
      },
      {
        id: "aom-2",
        role: "human",
        content: "รับเรื่องแล้วค่ะ เดี๋ยวแอดมินเข้ามาดูแลต่อให้ทันทีนะคะ 🙏",
        time: "10:37",
      },
    ],
  },
];

const initialOrders: DemoOrder[] = [
  {id: "ZT-1048", customer: "คุณเมย์", channel: "Facebook Messenger", items: PROMO_LABEL, total: PROMO_PRICE, status: "รอยืนยัน COD", time: "10:42"},
  {id: "SH-8831", customer: "คุณนก", channel: "Shopee", items: "1 ขวด", total: 390, status: "ชำระเงินแล้ว", time: "10:31"},
  {id: "ZT-1044", customer: "คุณพลอย", channel: "Facebook Messenger", items: PROMO_LABEL, total: PROMO_PRICE, status: "กำลังแพ็กสินค้า", time: "09:58"},
  {id: "SH-8828", customer: "คุณฝน", channel: "Shopee", items: "1 ขวด", total: 390, status: "จัดส่งแล้ว", time: "09:22"},
];

const extracts = [
  {name: "Niacinamide", thai: "วิตามินบี 3", tone: "#d9f76a", problem: "ผิวหมอง รอยคล้ำ ขาลาย", detail: "ช่วยดูแลสีผิวให้ดูสม่ำเสมอขึ้นและเสริมเกราะปกป้องผิว"},
  {name: "Ascorbic Acid", thai: "วิตามินซี", tone: "#ffc46b", problem: "ผิวดูเหนื่อยล้าจากแดด", detail: "สารต้านอนุมูลอิสระสำหรับผิวที่ต้องการการดูแลหลังออกแดด"},
  {name: "Tocopherol", thai: "วิตามินอี", tone: "#ff8c67", problem: "ผิวแห้งกร้าน ลอกเป็นขุย", detail: "ช่วยล็อกความชุ่มชื้นและดูแลผิวที่แห้งตึง"},
  {name: "Panthenol", thai: "วิตามินบี 5", tone: "#b6a4ff", problem: "ผิวระคายเคืองง่าย", detail: "ช่วยปลอบประโลมและเติมความชุ่มชื้นให้ผิวรู้สึกสบาย"},
  {name: "Sodium Hyaluronate", thai: "ไฮยาลูรอน", tone: "#78d9ff", problem: "ข้อศอก หัวเข่าแห้ง", detail: "ช่วยเติมน้ำให้ผิวดูอิ่มและนุ่มขึ้น"},
  {name: "Witch Hazel", thai: "วิชฮาเซล", tone: "#d2a2ff", problem: "ผิวมันและไม่เรียบเนียน", detail: "ช่วยดูแลความสมดุลและความรู้สึกสะอาดของผิว"},
  {name: "Chamomile Extract", thai: "คาโมมายล์", tone: "#f7e58b", problem: "ผิวบอบบาง แดงง่าย", detail: "ช่วยปลอบประโลมผิวที่รู้สึกไม่สบายจากสภาพแวดล้อม"},
  {name: "Licorice Extract", thai: "รากชะเอมเทศ", tone: "#e7b68c", problem: "จุดด่างดำ รอยคล้ำสะสม", detail: "ช่วยดูแลผิวให้ดูสม่ำเสมอและเรียบเนียนขึ้น"},
];

const scenarioPrompts = [
  "ช่วยเรื่องขาลายกับรอยคล้ำไหมคะ",
  "ผิวแห้งลอก ใช้ตัวนี้ได้ไหม",
  "ผิวแพ้ง่ายและแสบแดดค่ะ",
  "สั่ง 2 แถม 1 เก็บเงินปลายทางค่ะ",
  "ขอคุยกับแอดมินคนได้ไหมคะ",
];

function isHandoffRequest(message: string) {
  return ["คุยกับคน", "แอดมิน", "คนตอบ", "ร้องเรียน", "โกง", "ออเดอร์มีปัญหา"].some((word) => message.includes(word));
}

function salesReply(message: string) {
  const normalized = message.toLowerCase();
  if (isHandoffRequest(normalized)) {
    return {
      content: "รับทราบค่ะคุณพี่ เดี๋ยวส่งต่อให้แอดมินดูแลต่อทันทีนะคะ 😊 ระหว่างนี้ระบบจะหยุดตอบอัตโนมัติเพื่อไม่ให้ข้อมูลซ้ำค่ะ",
      needsHuman: true,
    };
  }
  if (normalized.includes("2 แถม 1") || normalized.includes("990") || normalized.includes("cod") || normalized.includes("เก็บเงิน")) {
    return {
      content: `ได้เลยค่ะคุณพี่ จัดเป็นชุดโปร ${PROMO_LABEL} รวม 3 ขวด ราคา ${money.format(PROMO_PRICE)} ส่งฟรีและเก็บเงินปลายทางได้ค่ะ\n\nรบกวนแจ้งชื่อ ที่อยู่ และเบอร์โทรไว้ได้เลยนะคะ เดี๋ยวสรุปออเดอร์ให้ตรวจสอบก่อนส่งค่ะ 🛒`,
      needsHuman: false,
    };
  }
  if (["แพ้", "แสบ", "ลอก", "ทะเล", "บอบบาง", "แดง"].some((word) => normalized.includes(word))) {
    return {
      content: `ถ้าผิวยังแสบหรือลอกมาก แนะนำทดสอบการแพ้บริเวณเล็ก ๆ ก่อนนะคะ สูตรนี้มี Chamomile Extract, Panthenol และ Sodium Hyaluronate ที่ช่วยดูแลผิวให้รู้สึกสบายและชุ่มชื้นขึ้นค่ะ หากมีอาการรุนแรงควรปรึกษาผู้เชี่ยวชาญด้านผิวหนังค่ะ\n\nรับโปร ${PROMO_LABEL} ราคา ${money.format(PROMO_PRICE)} ไว้ลองไหมคะ?`,
      needsHuman: false,
    };
  }
  if (["แห้ง", "ลอก", "ข้อศอก", "หัวเข่า", "ขุย"].some((word) => normalized.includes(word))) {
    return {
      content: `เข้าใจเรื่องผิวแห้งตึงเลยค่ะคุณพี่ สูตรนี้มี Tocopherol, Panthenol และ Sodium Hyaluronate ที่ช่วยดูแลความชุ่มชื้นและผิวบริเวณข้อศอกหรือหัวเข่าให้รู้สึกนุ่มขึ้นค่ะ\n\nสนใจรับโปร ${PROMO_LABEL} ราคา ${money.format(PROMO_PRICE)} ส่งฟรี มี COD ไหมคะ?`,
      needsHuman: false,
    };
  }
  if (["ขาลาย", "รอย", "คล้ำ", "ด่าง", "หมอง", "แดด", "แผลเป็น"].some((word) => normalized.includes(word))) {
    return {
      content: `เข้าใจปัญหารอยคล้ำและผิวหมองเลยค่ะคุณพี่ สูตรนี้มี Niacinamide, Ascorbic Acid และ Licorice Extract ที่ช่วยดูแลสีผิวให้ดูสม่ำเสมอและเรียบเนียนขึ้นค่ะ\n\nตอนนี้มีโปร ${PROMO_LABEL} ราคา ${money.format(PROMO_PRICE)} ส่งฟรี มีเก็บเงินปลายทาง รับเป็นชุดนี้เลยไหมคะ? ✨`,
      needsHuman: false,
    };
  }
  return {
    content: `เซรั่มผิวกาย Complete Care มีสารสกัด 8 ชนิด ช่วยดูแลทั้งความชุ่มชื้นและผิวที่ดูหมองค่ะ คุณพี่กังวลเรื่องผิวแห้ง รอยคล้ำ หรือผิวบอบบางเป็นพิเศษคะ?\n\nถ้าต้องการลองแบบคุ้ม แนะนำโปร ${PROMO_LABEL} ราคา ${money.format(PROMO_PRICE)} ส่งฟรี มี COD ค่ะ`,
    needsHuman: false,
  };
}

function ChannelMark({channel}: {channel: Channel}) {
  return <span className={`channel-mark ${channel === "Shopee" ? "shopee" : "facebook"}`} aria-hidden="true">{channel === "Shopee" ? "S" : "f"}</span>;
}

function App() {
  const [activeView, setActiveView] = useState<DemoView>("overview");
  const [conversations, setConversations] = useState(initialConversations);
  const [selectedConversationId, setSelectedConversationId] = useState(initialConversations[0].id);
  const [draft, setDraft] = useState("");
  const [orders, setOrders] = useState(initialOrders);
  const [stockCount, setStockCount] = useState(387);
  const [lastSync, setLastSync] = useState("เมื่อสักครู่");
  const [toast, setToast] = useState("");
  const [showAllExtracts, setShowAllExtracts] = useState(false);

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId) ?? conversations[0],
    [conversations, selectedConversationId],
  );
  const handoffCount = conversations.filter((conversation) => conversation.needsHuman).length;

  function showToast(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  }

  function selectView(view: DemoView) {
    setActiveView(view);
  }

  function sendMessage(message = draft) {
    const content = message.trim();
    if (!content || !selectedConversation) return;
    const answer = salesReply(content);
    const now = new Date().toLocaleTimeString("th-TH", {hour: "2-digit", minute: "2-digit"});
    setConversations((current) => current.map((conversation) => {
      if (conversation.id !== selectedConversation.id) return conversation;
      return {
        ...conversation,
        preview: content,
        wait: answer.needsHuman ? "รอแอดมินดูแล" : "ตอบเมื่อสักครู่",
        needsHuman: answer.needsHuman,
        messages: [
          ...conversation.messages,
          {id: `${conversation.id}-${Date.now()}-user`, role: "customer", content, time: now},
          {id: `${conversation.id}-${Date.now()}-bot`, role: answer.needsHuman ? "human" : "bot", content: answer.content, time: now},
        ],
      };
    }));
    setDraft("");
    if (answer.needsHuman) showToast("ส่งต่อแอดมินแล้ว · AI หยุดตอบอัตโนมัติ");
  }

  function submitMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    sendMessage();
  }

  function createDemoOrder() {
    if (stockCount < 3) {
      showToast("สต็อกจำลองไม่พอสำหรับชุดโปร");
      return;
    }
    setStockCount((current) => current - 3);
    setOrders((current) => [
      {
        id: `ZT-${1050 + current.length}`,
        customer: selectedConversation.customer,
        channel: selectedConversation.channel,
        items: PROMO_LABEL,
        total: PROMO_PRICE,
        status: "รอยืนยัน COD",
        time: "ตอนนี้",
      },
      ...current,
    ]);
    showToast("สร้างออเดอร์ Demo แล้ว · ตัดสต็อก 3 ขวดแบบจำลอง");
    setActiveView("orders");
  }

  function syncChannels() {
    setLastSync("เพิ่งซิงก์");
    showToast("ซิงก์สถานะ Shopee + Facebook สำเร็จ (Demo)");
  }

  return (
    <div className="sales-demo-app">
      <aside className="demo-sidebar">
        <a className="demo-brand" href="/" aria-label="กลับหน้าหลัก zTT Shop">
          <span className="brand-symbol">Z</span>
          <span><strong>zTT Shop</strong><small>commerce OS</small></span>
        </a>
        <div className="sidebar-label">DEMO WORKSPACE</div>
        <nav className="demo-nav" aria-label="Demo navigation">
          <button className={activeView === "overview" ? "active" : ""} onClick={() => selectView("overview")}><span>◈</span> Command center</button>
          <button className={activeView === "inbox" ? "active" : ""} onClick={() => selectView("inbox")}><span>◌</span> AI sales inbox <em>{conversations.length}</em></button>
          <button className={activeView === "knowledge" ? "active" : ""} onClick={() => selectView("knowledge")}><span>✦</span> Product knowledge</button>
          <button className={activeView === "orders" ? "active" : ""} onClick={() => selectView("orders")}><span>▤</span> Orders & stock</button>
        </nav>
        <div className="sidebar-footnote">
          <span className="status-dot" />
          <div><strong>Demo mode online</strong><small>ข้อมูลจำลอง ไม่เชื่อมบัญชีจริง</small></div>
        </div>
      </aside>

      <main className="demo-main">
        <header className="demo-topbar">
          <div className="mobile-brand"><span className="brand-symbol">Z</span><strong>zTT Shop</strong></div>
          <div className="topbar-context"><span>Customer presentation</span><b>/</b><strong>{activeView === "overview" ? "Command center" : activeView === "inbox" ? "AI sales inbox" : activeView === "knowledge" ? "Product knowledge" : "Orders & stock"}</strong></div>
          <div className="topbar-actions"><span className="demo-badge"><i /> DEMO DATA</span><button className="sync-button" onClick={syncChannels}>↻ <span>Sync channels</span></button></div>
        </header>

        <div className="demo-content">
          {activeView === "overview" && <OverviewView stockCount={stockCount} handoffCount={handoffCount} orders={orders} conversations={conversations} lastSync={lastSync} selectView={selectView} setSelectedConversationId={setSelectedConversationId} />}
          {activeView === "inbox" && <InboxView conversations={conversations} selectedConversation={selectedConversation} selectedConversationId={selectedConversationId} setSelectedConversationId={setSelectedConversationId} draft={draft} setDraft={setDraft} submitMessage={submitMessage} sendMessage={sendMessage} createDemoOrder={createDemoOrder} />}
          {activeView === "knowledge" && <KnowledgeView showAllExtracts={showAllExtracts} setShowAllExtracts={setShowAllExtracts} selectView={selectView} />}
          {activeView === "orders" && <OrdersView orders={orders} stockCount={stockCount} selectView={selectView} />}
        </div>
      </main>
      {toast && <div className="demo-toast" role="status"><span>✓</span>{toast}</div>}
    </div>
  );
}

function OverviewView({stockCount, handoffCount, orders, conversations, lastSync, selectView, setSelectedConversationId}: {stockCount: number; handoffCount: number; orders: DemoOrder[]; conversations: Conversation[]; lastSync: string; selectView: (view: DemoView) => void; setSelectedConversationId: (id: string) => void}) {
  const totalSales = orders.reduce((sum, order) => sum + order.total, 0) + 44520;
  return <>
    <section className="demo-hero">
      <div className="hero-copy">
        <p className="overline"><span /> AI SALES COMMAND CENTER</p>
        <h1>แชตเดียว<br /><em>ปิดการขายได้</em></h1>
        <p className="hero-lead">รวมแชตจาก Facebook และ Shopee ให้ AI เข้าใจปัญหาผิว ตอบอย่างเป็นธรรมชาติ และส่งต่อคนได้ในจังหวะที่ควรส่งต่อ</p>
        <div className="hero-actions"><button className="primary-button" onClick={() => selectView("inbox")}>ดู AI ปิดการขาย <span>↗</span></button><span className="hero-note">Hybrid RAG · Sales framework · Human handoff</span></div>
      </div>
      <div className="hero-script-card"><div className="script-orbit"><span>8</span><small>EXTRACTS</small></div><p className="overline">LIVE SALES SCRIPT</p><h2>ถาม → เข้าใจ<br /><em>→ เสนอ → ปิด</em></h2><div className="script-line"><span>01</span><b>เรียนรู้ pain point</b><small>10:42:08</small></div><div className="script-line"><span>02</span><b>เลือกสารสกัดที่ตรง</b><small>10:42:09</small></div><div className="script-line"><span>03</span><b>เสนอโปร {PROMO_LABEL}</b><small>10:42:10</small></div></div>
    </section>
    <section className="metric-grid" aria-label="Demo metrics">
      <Metric label="ยอดขายรวมวันนี้" value={money.format(totalSales)} detail="+24.8% จากเมื่อวาน" tone="lime" />
      <Metric label="ออเดอร์จากแชต" value="126" detail="38% ปิดโดย AI" tone="coral" />
      <Metric label="สต็อกพร้อมขาย" value={`${stockCount} ขวด`} detail="ตัดทันทีเมื่อสร้างออเดอร์" tone="blue" />
      <Metric label="ส่งต่อแอดมิน" value={String(handoffCount).padStart(2, "0")} detail="AI หยุดตอบทุกเคส" tone="violet" />
    </section>
    <section className="overview-grid">
      <div className="panel channel-panel"><PanelHeading eyebrow="CHANNEL PULSE" title="ทุกช่องทาง อยู่ในจอเดียว" action={<button className="text-button" onClick={() => selectView("inbox")}>เปิด inbox ↗</button>} /><div className="channel-list"><ChannelRow channel="Facebook Messenger" state="Connected" detail="48 conversations · 12 active" icon="facebook" /><ChannelRow channel="Shopee" state="Connected" detail="78 orders · 4 pending" icon="shopee" /><ChannelRow channel="AI Sales Agent" state="Ready" detail="ตอบตาม knowledge base" icon="ai" /></div><div className="sync-foot"><span><i className="status-dot" /> All systems nominal</span><small>Last sync {lastSync}</small></div></div>
      <div className="panel stock-panel"><PanelHeading eyebrow="INVENTORY GUARDRAIL" title="สต็อกไม่หลุดมือ" action={<button className="text-button" onClick={() => selectView("orders")}>ดูสต็อก ↗</button>} /><div className="stock-feature"><div className="bottle-art"><div className="bottle-cap" /><div className="bottle-body"><small>BODY</small><strong>8</strong><span>serum</span></div></div><div><span className="stock-tag">BEST SELLER · BODY-SERUM-01</span><h3>Complete Care<br />8 สารสกัด</h3><p>พร้อมส่ง <strong>{stockCount} ขวด</strong></p></div></div><div className="stock-meter"><div><span>Stock level</span><b>{Math.round((stockCount / 500) * 100)}%</b></div><div className="meter-track"><i style={{width: `${Math.max(8, (stockCount / 500) * 100)}%`}} /></div><small>จุดสั่งซื้อเพิ่ม 100 ขวด · ไม่มี oversell</small></div></div>
      <div className="panel inbox-preview"><PanelHeading eyebrow="AI SALES INBOX" title="บทสนทนาที่กำลังปิดการขาย" action={<button className="text-button" onClick={() => selectView("inbox")}>ดูทั้งหมด ↗</button>} /><div className="preview-list">{conversations.map((conversation) => <button className="preview-row" key={conversation.id} onClick={() => {setSelectedConversationId(conversation.id); selectView("inbox");}}><span className="avatar">{conversation.initials}</span><span className="preview-copy"><strong>{conversation.customer}</strong><small>{conversation.preview}</small></span><span className="preview-meta"><i className={`channel-mini ${conversation.channel === "Shopee" ? "shopee" : "facebook"}`} />{conversation.needsHuman ? <em className="handoff-label">HANDOFF</em> : <em>{conversation.wait}</em>}</span></button>)}</div></div>
      <div className="panel close-rate"><div className="rate-copy"><p className="overline">WHY AI DOESN'T FEEL LIKE A BOT</p><h2>“ตอบตรงจุด<br /><em>ก่อนชวนซื้อ”</em></h2><p>เริ่มจากความเข้าใจ ไม่ใช่ยิงโปรทันที ระบบใช้ข้อมูลสินค้าเป็นแหล่งอ้างอิงเดียวและหยุดทันทีเมื่อควรให้คนดูแล</p></div><div className="rate-ring"><strong>38<span>%</span></strong><small>AI close rate</small></div></div>
    </section>
  </>;
}

function Metric({label, value, detail, tone}: {label: string; value: string; detail: string; tone: string}) {
  return <article className={`metric-card ${tone}`}><span className="metric-label">{label}</span><strong>{value}</strong><small><i />{detail}</small></article>;
}

function PanelHeading({eyebrow, title, action}: {eyebrow: string; title: string; action?: React.ReactNode}) {
  return <div className="panel-heading"><div><p className="overline">{eyebrow}</p><h2>{title}</h2></div>{action}</div>;
}

function ChannelRow({channel, state, detail, icon}: {channel: string; state: string; detail: string; icon: string}) {
  return <div className="channel-row"><span className={`channel-icon ${icon}`}>{icon === "facebook" ? "f" : icon === "shopee" ? "S" : "✦"}</span><span><strong>{channel}</strong><small>{detail}</small></span><b><i />{state}</b></div>;
}

function InboxView({conversations, selectedConversation, selectedConversationId, setSelectedConversationId, draft, setDraft, submitMessage, sendMessage, createDemoOrder}: {conversations: Conversation[]; selectedConversation: Conversation; selectedConversationId: string; setSelectedConversationId: (id: string) => void; draft: string; setDraft: (value: string) => void; submitMessage: (event: FormEvent<HTMLFormElement>) => void; sendMessage: (message?: string) => void; createDemoOrder: () => void}) {
  return <section className="inbox-page"><div className="page-heading"><div><p className="overline"><span /> UNIFIED CUSTOMER INBOX</p><h1>คุยกับลูกค้า<br /><em>แบบที่คนขายคุย</em></h1></div><div className="page-heading-note"><strong>AI is on</strong><span>กดสถานการณ์ด้านล่างเพื่อสาธิต</span></div></div><div className="inbox-layout"><aside className="conversation-panel"><div className="conversation-toolbar"><strong>Conversations <span>{conversations.length}</span></strong><button aria-label="ค้นหาบทสนทนา">⌕</button></div><div className="inbox-filters"><button className="active">ทั้งหมด</button><button>รอแอดมิน <span>{conversations.filter((conversation) => conversation.needsHuman).length}</span></button></div><div className="conversation-list">{conversations.map((conversation) => <button key={conversation.id} className={`conversation-row ${conversation.id === selectedConversationId ? "selected" : ""}`} onClick={() => setSelectedConversationId(conversation.id)}><span className="avatar">{conversation.initials}</span><span className="conversation-copy"><strong>{conversation.customer}</strong><small>{conversation.preview}</small><em>{conversation.intent}</em></span><span className="conversation-side"><i className={`channel-mini ${conversation.channel === "Shopee" ? "shopee" : "facebook"}`} /><small>{conversation.wait}</small></span></button>)}</div></aside><section className="chat-panel"><div className="chat-head"><div className="customer-heading"><span className="avatar large">{selectedConversation.initials}</span><div><strong>{selectedConversation.customer}</strong><span><ChannelMark channel={selectedConversation.channel} /> {selectedConversation.channel} · {selectedConversation.needsHuman ? "Human handoff" : "AI active"}</span></div></div><button className={selectedConversation.needsHuman ? "handoff-active" : "handoff-button"}>{selectedConversation.needsHuman ? "● แอดมินรับช่วงแล้ว" : "AI auto-reply"}</button></div><div className="chat-thread">{selectedConversation.messages.map((message) => <div className={`chat-message ${message.role}`} key={message.id}><span className="message-author">{message.role === "customer" ? selectedConversation.customer : message.role === "human" ? "Admin team" : "AI Sales Bot"}</span><p>{message.content}</p><small>{message.time}</small></div>)}</div><div className="quick-prompts"><span>ลองเดโม</span>{scenarioPrompts.map((prompt) => <button key={prompt} onClick={() => sendMessage(prompt)}>{prompt}</button>)}</div><form className="chat-composer" onSubmit={submitMessage}><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="พิมพ์คำถามลูกค้าเพื่อทดสอบ AI…" rows={2} /><button type="submit" aria-label="ส่งข้อความ">↗</button></form><div className="composer-hint"><span>AI uses Product Knowledge only</span><button onClick={createDemoOrder}>＋ สร้างออเดอร์ Demo</button></div></section><aside className="conversation-context"><p className="overline">CONVERSATION CONTEXT</p><h2>ลูกค้ากำลังสนใจ</h2><div className="context-intent"><span>Detected intent</span><strong>{selectedConversation.intent}</strong><small>ความมั่นใจ 94% · จากข้อความล่าสุด</small></div><div className="context-section"><span>Suggested knowledge</span><div className="knowledge-chip"><b>✦</b><span><strong>{selectedConversation.intent.includes("แห้ง") ? "Panthenol + Hyaluronate" : selectedConversation.intent.includes("ผิวบอบบาง") ? "Chamomile + Panthenol" : "Niacinamide + Licorice"}</strong><small>ข้อมูลจาก Product Knowledge</small></span></div></div><div className="context-section"><span>Recommended close</span><p>เสนอชุด <strong>{PROMO_LABEL}</strong><br />ราคา <strong>{money.format(PROMO_PRICE)}</strong> · ส่งฟรี · COD</p><button className="context-cta" onClick={createDemoOrder}>สร้างออเดอร์จากแชต <span>↗</span></button></div><div className="guardrail-note"><span>✓</span><p><strong>Guardrail active</strong><small>ไม่ตอบนอกข้อมูล · ส่งต่อเมื่อขอคน</small></p></div></aside></div></section>;
}

function KnowledgeView({showAllExtracts, setShowAllExtracts, selectView}: {showAllExtracts: boolean; setShowAllExtracts: (value: boolean) => void; selectView: (view: DemoView) => void}) {
  const visibleExtracts = showAllExtracts ? extracts : extracts.slice(0, 4);
  return <section className="knowledge-page"><div className="page-heading knowledge-heading"><div><p className="overline"><span /> PRODUCT KNOWLEDGE ENGINE</p><h1>สมองของ<br /><em>นักปิดการขาย</em></h1><p>ข้อมูลที่ AI ใช้ตอบต้องมาจาก catalog นี้เท่านั้น ลดการมโน และทำให้ทุกช่องทางพูดด้วยข้อมูลชุดเดียวกัน</p></div><div className="knowledge-stat"><strong>8</strong><span>active extracts</span><small>1 product · 3 pain point clusters</small></div></div><div className="product-knowledge-card"><div className="product-visual"><div className="bottle-art big"><div className="bottle-cap" /><div className="bottle-body"><small>COMPLETE</small><strong>8</strong><span>BODY SERUM</span></div></div><span className="orbit-label top">8 ACTIVE<br />EXTRACTS</span><span className="orbit-label bottom">BODY-SERUM-01</span></div><div className="product-copy"><div className="product-topline"><span className="stock-tag">VERIFIED CATALOG</span><span>Updated just now</span></div><h2>เซรั่มผิวกาย<br />Complete Care</h2><p>สูตรดูแลผิวกายด้วยสารสกัด 8 ชนิด สำหรับลูกค้าที่กังวลเรื่องผิวหมอง รอยคล้ำ ความแห้งกร้าน และความรู้สึกไม่สบายผิวจากแดด</p><div className="product-price"><strong>{money.format(390)}</strong><span>/ ขวด</span><b>โปร {PROMO_LABEL} · {money.format(PROMO_PRICE)}</b></div><div className="product-safety"><span>✓</span><p><strong>Safe sales guidance</strong><small>แนะนำทดสอบการแพ้ก่อนใช้ และไม่วินิจฉัยโรคผิวหนัง</small></p></div><button className="primary-button" onClick={() => selectView("inbox")}>ทดลองให้ AI ตอบจากชุดข้อมูลนี้ <span>↗</span></button></div></div><div className="extract-section-heading"><div><p className="overline">PAIN POINT MAPPING</p><h2>ถามเรื่องไหน<br /><em>ดึงตัวไหนขึ้นมา</em></h2></div><span>ใช้เป็น evidence ไม่ใช่คำโฆษณาลอย ๆ</span></div><div className="extract-grid">{visibleExtracts.map((extract, index) => <article className="extract-card" key={extract.name} style={{"--extract-tone": extract.tone} as React.CSSProperties}><div className="extract-index">0{index + 1}</div><div className="extract-dot" /><span>{extract.thai}</span><h3>{extract.name}</h3><strong>{extract.problem}</strong><p>{extract.detail}</p></article>)}</div><button className="load-more" onClick={() => setShowAllExtracts(!showAllExtracts)}>{showAllExtracts ? "แสดงน้อยลง ↑" : "ดูสารสกัดทั้ง 8 ชนิด ↓"}</button></section>;
}

function OrdersView({orders, stockCount, selectView}: {orders: DemoOrder[]; stockCount: number; selectView: (view: DemoView) => void}) {
  return <section className="orders-page"><div className="page-heading"><div><p className="overline"><span /> CENTRAL ERP · DEMO LEDGER</p><h1>ออเดอร์และสต็อก<br /><em>ไม่ต้องเปิดหลายจอ</em></h1></div><button className="primary-button" onClick={() => selectView("inbox")}>กลับไปปิดการขาย <span>↗</span></button></div><div className="orders-summary"><div className="summary-card"><span>ORDERS TODAY</span><strong>{orders.length + 122}</strong><small>จาก Facebook + Shopee</small></div><div className="summary-card"><span>PAYMENT PENDING</span><strong>{orders.filter((order) => order.status.includes("รอ")).length}</strong><small>ต้องติดตามต่อ</small></div><div className="summary-card"><span>LIVE STOCK</span><strong>{stockCount}</strong><small>ขวดพร้อมขาย</small></div></div><div className="orders-table-panel"><div className="panel-heading"><div><p className="overline">RECENT ORDERS</p><h2>ออเดอร์ล่าสุด</h2></div><span className="table-note">Demo ledger · no real charge</span></div><div className="order-table"><div className="order-table-head"><span>Order</span><span>Customer</span><span>Channel</span><span>Items</span><span>Total</span><span>Status</span></div>{orders.map((order) => <div className="order-row" key={order.id}><strong>{order.id}<small>{order.time}</small></strong><span>{order.customer}</span><span><ChannelMark channel={order.channel} />{order.channel}</span><span>{order.items}</span><b>{money.format(order.total)}</b><em className={order.status.includes("รอ") ? "pending" : order.status.includes("แล้ว") ? "paid" : "packing"}>{order.status}</em></div>)}</div></div><div className="orders-bottom"><div className="panel mini-sync"><p className="overline">MULTI-CHANNEL SYNC</p><h2>สต็อกตัวเดียว<br /><em>ทุกช่องทางใช้ร่วมกัน</em></h2><p>เมื่อ Facebook ปิดการขาย ชุดโปรจะหัก 3 ขวดจาก stock กลาง ก่อนส่งสถานะไป Shopee ต่อ</p><div className="sync-chain"><span>Facebook</span><i>→</i><strong>Central stock</strong><i>→</i><span>Shopee</span></div></div><div className="panel mini-promo"><p className="overline">PROMOTION RULE</p><div><strong>{PROMO_LABEL}</strong><span>{money.format(PROMO_PRICE)}</span></div><p>ส่งฟรี · COD available · รวม 3 ขวด</p><button onClick={() => selectView("knowledge")}>ดู product knowledge ↗</button></div></div></section>;
}

createRoot(document.getElementById("root")!).render(<App />);
