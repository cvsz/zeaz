import {StrictMode, useEffect, useMemo, useState} from "react";
import {createRoot} from "react-dom/client";
import {MoopiewClient} from "@moopiew/sdk";
import type {AiCatalog, AiChatInput, AiChatResponse, AiConfig, AiModel} from "@moopiew/types";
import "./ai.css";

const api = new MoopiewClient({baseURL: import.meta.env.VITE_API_URL || window.location.origin});

const DEFAULT_TEMPERATURE = 0.25;
const DEFAULT_MAX_TOKENS = 1024;
const CONTEXT_LIMIT = 12_000;
const SYSTEM_PROMPT = [
  "You are Qwen on qwen.zeaz.dev.",
  "Be direct, practical, and concise.",
  "If the user asks for code or steps, answer with actionable detail.",
  "Do not mention hidden policies or internal routes.",
].join("\n");

type Mode = "public" | "owner";
type Role = "user" | "assistant";

type Message = {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
  model?: string;
  fallback?: boolean;
  error?: boolean;
  pending?: boolean;
};

const safeText = (error: unknown) =>
  error instanceof Error ? error.message : "โหลดข้อมูลไม่สำเร็จ";

const shortModelName = (model: AiModel) =>
  model.display_name && model.display_name !== model.model
    ? model.display_name
    : model.model;

const providerLabel = (model: AiModel) =>
  model.provider === "huggingface"
    ? "HF"
    : model.provider === "github"
      ? "GitHub"
      : model.provider;

function buildPrompt(messages: Message[]) {
  const transcript = messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) =>
      `${message.role === "user" ? "User" : "Assistant"}: ${message.content.trim()}`,
    );
  const promptLines = [
    SYSTEM_PROMPT,
    "",
    "Conversation:",
    ...transcript,
    "Assistant:",
  ];
  let prompt = promptLines.join("\n");
  while (prompt.length > CONTEXT_LIMIT && transcript.length > 2) {
    transcript.shift();
    prompt = [SYSTEM_PROMPT, "", "Conversation:", ...transcript, "Assistant:"].join("\n");
  }
  return prompt.length > CONTEXT_LIMIT ? prompt.slice(prompt.length - CONTEXT_LIMIT) : prompt;
}

function App() {
  const [mode, setMode] = useState<Mode>("public");
  const [ownerKey, setOwnerKey] = useState("");
  const [ownerConfig, setOwnerConfig] = useState<AiConfig>();
  const [catalog, setCatalog] = useState<AiCatalog>();
  const [selectedModelId, setSelectedModelId] = useState("");
  const [search, setSearch] = useState("");
  const [provider, setProvider] = useState("all");
  const [temperature, setTemperature] = useState(DEFAULT_TEMPERATURE);
  const [maxTokens, setMaxTokens] = useState(DEFAULT_MAX_TOKENS);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "เลือกโมเดลด้านซ้ายแล้วเริ่มคุยได้ทันที หากมี owner key จะปลดล็อก catalog เต็มและเส้นทาง admin ได้",
      createdAt: new Date().toISOString(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("กำลังเชื่อมต่อ live catalog");
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const models = catalog?.models ?? [];
  const providers = useMemo(
    () =>
      Object.entries(catalog?.providers ?? {})
        .map(([name, info]) => ({name, info}))
        .sort((left, right) => left.name.localeCompare(right.name)),
    [catalog],
  );
  const filteredModels = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return models.filter((model) => {
      if (provider !== "all" && model.provider !== provider) return false;
      if (!needle) return true;
      return [model.id, model.model, model.display_name, model.provider]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    });
  }, [models, provider, search]);
  const selectedModel = useMemo(
    () =>
      filteredModels.find((model) => model.id === selectedModelId) ??
      filteredModels[0] ??
      models.find((model) => model.id === selectedModelId) ??
      models[0],
    [filteredModels, models, selectedModelId],
  );

  useEffect(() => {
    if (selectedModel && selectedModel.id !== selectedModelId) {
      setSelectedModelId(selectedModel.id);
    }
  }, [selectedModel, selectedModelId]);

  async function loadCatalog(nextMode: Mode = mode) {
    setLoading(true);
    setError("");
    try {
      const key = ownerKey.trim();
      const nextCatalog =
        nextMode === "owner"
          ? await api.ai.models(key)
          : await api.ai.publicModels();
      setCatalog(nextCatalog);
      if (nextMode === "owner") {
        setOwnerConfig(await api.ai.config(key));
      } else {
        setOwnerConfig(undefined);
      }
      setStatus(
        nextMode === "owner"
          ? "Owner catalog เชื่อมต่อกับ live providers แล้ว"
          : "Public free-model catalog พร้อมใช้งาน",
      );
      setLastUpdated(new Date().toLocaleString("th-TH"));
      if (!selectedModelId || !nextCatalog.models.some((model) => model.id === selectedModelId)) {
        setSelectedModelId(nextCatalog.models[0]?.id ?? "");
      }
      setMode(nextMode);
    } catch (caught) {
      setError(safeText(caught));
      setStatus("เชื่อมต่อ catalog ไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCatalog("public");
    // Load once on startup; owner mode is explicit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function unlockOwner() {
    if (!ownerKey.trim()) {
      setError("กรุณากรอก owner key");
      return;
    }
    await loadCatalog("owner");
  }

  function resetChat() {
    setMessages([
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "เริ่มคุยใหม่ได้เลย",
        createdAt: new Date().toISOString(),
      },
    ]);
  }

  async function sendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || !selectedModel) return;
    setDraft("");
    setError("");

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    };
    const pendingMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      createdAt: new Date().toISOString(),
      pending: true,
    };
    const nextMessages = [...messages, userMessage, pendingMessage];
    setMessages(nextMessages);
    setLoading(true);

    try {
      const input: AiChatInput = {
        model: selectedModel.id,
        prompt: buildPrompt([...messages, userMessage]),
        max_tokens: Number.isFinite(maxTokens) ? maxTokens : DEFAULT_MAX_TOKENS,
        temperature: Number.isFinite(temperature) ? temperature : DEFAULT_TEMPERATURE,
      };
      const result: AiChatResponse =
        mode === "owner"
          ? await api.ai.chat(ownerKey, input)
          : await api.ai.publicChat(input);
      setMessages([
        ...messages,
        userMessage,
        {
          id: result.id,
          role: "assistant",
          content: result.content,
          createdAt: new Date().toISOString(),
          model: result.model,
          fallback: result.fallback,
        },
      ]);
      setStatus(result.fallback ? "ตอบกลับจาก fallback free model" : "ตอบกลับสำเร็จ");
      setLastUpdated(new Date().toLocaleString("th-TH"));
    } catch (caught) {
      const message = safeText(caught);
      setError(message);
      setMessages([
        ...messages,
        userMessage,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: message,
          createdAt: new Date().toISOString(),
          error: true,
        },
      ]);
      setStatus("ส่งข้อความไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  function handleComposerKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      const form = event.currentTarget.form;
      if (form) void form.requestSubmit();
    }
  }

  return (
    <div className="ai-app">
      <header className="ai-topbar">
        <div className="brand">
          <a href="/" className="brand-mark" aria-label="กลับหน้าหลัก">
            <span>Q</span>
          </a>
          <div>
            <strong>Qwen Live Chat</strong>
            <small>qwen.zeaz.dev · nextchat/open-webui style</small>
          </div>
        </div>
        <div className="topbar-actions">
          <a href="#composer">Composer</a>
          <button type="button" onClick={() => void loadCatalog(mode)} disabled={loading}>
            {loading ? "Refreshing…" : "Refresh"}
          </button>
          <button type="button" onClick={resetChat}>New chat</button>
        </div>
      </header>

      <main className="ai-shell">
        <aside className="ai-sidebar">
          <section className="mode-card">
            <p className="eyebrow">ACCESS</p>
            <h1>Public chat first</h1>
            <p>
              `qwen.zeaz.dev` เปิดได้โดยตรง และถ้าจะใช้ catalog เต็มก็ปลดล็อกด้วย owner key
            </p>
            <div className="mode-switch" role="radiogroup" aria-label="Chat mode">
              <button
                type="button"
                role="radio"
                aria-checked={mode === "public"}
                className={mode === "public" ? "selected" : ""}
                onClick={() => void loadCatalog("public")}
              >
                Public
              </button>
              <button
                type="button"
                role="radio"
                aria-checked={mode === "owner"}
                className={mode === "owner" ? "selected" : ""}
                onClick={() => setMode("owner")}
              >
                Owner
              </button>
            </div>
            {mode === "owner" ? (
              <form
                className="owner-unlock"
                onSubmit={(event) => {
                  event.preventDefault();
                  void unlockOwner();
                }}
              >
                <label>
                  Owner key
                  <input
                    type="password"
                    value={ownerKey}
                    autoComplete="current-password"
                    onChange={(event) => setOwnerKey(event.target.value)}
                    placeholder="ไม่ถูกบันทึก"
                  />
                </label>
                <button type="submit" disabled={loading || !ownerKey.trim()}>
                  Unlock owner catalog
                </button>
              </form>
            ) : (
              <button type="button" className="owner-unlock-button" onClick={() => setMode("owner")}>
                เปิด owner catalog →
              </button>
            )}
          </section>

          <section className="catalog-card">
            <div className="section-head">
              <div>
                <p className="eyebrow">MODELS</p>
                <h2>{filteredModels.length} live models</h2>
              </div>
              <small>{lastUpdated || "not loaded yet"}</small>
            </div>
            <label className="search-field">
              <span>Search</span>
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="model / provider / display name"
              />
            </label>
            <div className="provider-row" role="radiogroup" aria-label="Provider filters">
              <button
                type="button"
                role="radio"
                aria-checked={provider === "all"}
                className={provider === "all" ? "selected" : ""}
                onClick={() => setProvider("all")}
              >
                All
              </button>
              {providers.map(({name, info}) => (
                <button
                  key={name}
                  type="button"
                  role="radio"
                  aria-checked={provider === name}
                  className={provider === name ? "selected" : ""}
                  onClick={() => setProvider(name)}
                >
                  {name} · {info.models}
                </button>
              ))}
            </div>
            <div className="model-list" aria-busy={loading}>
              {filteredModels.length ? (
                filteredModels.map((model) => (
                  <button
                    key={model.id}
                    type="button"
                    className={model.id === selectedModel?.id ? "model-card selected" : "model-card"}
                    onClick={() => setSelectedModelId(model.id)}
                  >
                    <span>{providerLabel(model)}</span>
                    <strong>{shortModelName(model)}</strong>
                    <small>{model.id}</small>
                    <em>{model.free ? "free" : model.free_tier ? "free tier" : "public"}</em>
                  </button>
                ))
              ) : (
                <p className="empty-state">No models match the current filter.</p>
              )}
            </div>
          </section>

          <section className="health-card">
            <div className="section-head">
              <div>
                <p className="eyebrow">STATUS</p>
                <h2>{mode === "owner" && ownerConfig ? "Owner catalog" : "Public catalog"}</h2>
              </div>
              <small>{mode === "owner" ? "admin routes enabled" : "no access gate"}</small>
            </div>
            <p role="status" aria-live="polite" className="status-line">
              {error || status}
            </p>
            <ul>
              {providers.length ? (
                providers.map(({name, info}) => (
                  <li key={name} className={info.enabled ? "ok" : "warn"}>
                    <b>{name}</b>
                    <small>
                      {info.models} models{info.error ? ` · ${info.error}` : ""}
                    </small>
                  </li>
                ))
              ) : (
                <li className="warn">
                  <b>No catalog</b>
                  <small>Load public or owner catalog to begin.</small>
                </li>
              )}
            </ul>
            {ownerConfig && (
              <div className="owner-flags">
                <span>{ownerConfig.enabled ? "enabled" : "disabled"}</span>
                <span>{ownerConfig.fallback ? "fallback on" : "fallback off"}</span>
                <span>{Object.values(ownerConfig.providers).filter(Boolean).length} providers</span>
              </div>
            )}
          </section>
        </aside>

        <section className="chat-panel">
          <header className="chat-header">
            <div>
              <p className="eyebrow">CONVERSATION</p>
              <h2>{selectedModel ? shortModelName(selectedModel) : "Select a model"}</h2>
              <p>
                {selectedModel
                  ? `${selectedModel.provider} · ${selectedModel.id}`
                  : "Choose a model from the sidebar to start chatting"}
              </p>
            </div>
            <div className="chat-meta">
              <span>{messages.filter((message) => message.role === "user").length} turns</span>
              <span>{mode === "owner" ? "Owner mode" : "Public mode"}</span>
            </div>
          </header>

          <div className="chat-stream" aria-live="polite">
            {messages.map((message) => (
              <article key={message.id} className={`message ${message.role} ${message.pending ? "pending" : ""} ${message.error ? "error" : ""}`}>
                <div className="message-head">
                  <strong>{message.role === "user" ? "You" : "Qwen"}</strong>
                  <span>{new Date(message.createdAt).toLocaleTimeString("th-TH", {hour: "2-digit", minute: "2-digit"})}</span>
                </div>
                <div className="message-body">
                  {message.content || (message.pending ? "Thinking…" : "")}
                </div>
                {message.model && (
                  <footer>
                    <span>{message.model}</span>
                    {message.fallback && <span>fallback</span>}
                  </footer>
                )}
              </article>
            ))}
          </div>

          <form id="composer" className="composer" onSubmit={sendMessage}>
            <div className="composer-head">
              <div>
                <p className="eyebrow">PROMPT</p>
                <strong>Compose a message</strong>
              </div>
              <small>{draft.length}/{CONTEXT_LIMIT}</small>
            </div>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleComposerKeyDown}
              placeholder="Ask Qwen anything. Enter to send, Shift+Enter for a new line."
              maxLength={12000}
            />
            <div className="composer-footer">
              <label>
                Temperature
                <input
                  type="range"
                  min="0"
                  max="1.5"
                  step="0.05"
                  value={temperature}
                  onChange={(event) => setTemperature(Number(event.target.value))}
                />
                <span>{temperature.toFixed(2)}</span>
              </label>
              <label>
                Max tokens
                <input
                  type="number"
                  min="64"
                  max="2048"
                  step="32"
                  value={maxTokens}
                  onChange={(event) => setMaxTokens(Number(event.target.value))}
                />
              </label>
              <button
                type="submit"
                disabled={!selectedModel || !draft.trim() || loading || (mode === "owner" && !ownerKey.trim())}
              >
                {mode === "owner" && !ownerKey.trim() ? "Unlock owner first" : loading ? "Sending…" : "Send →"}
              </button>
            </div>
          </form>
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
