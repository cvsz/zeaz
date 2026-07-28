const $ = (selector) => document.querySelector(selector);
const STATUS_CLASSES = new Set(["pass", "fail", "unknown", "not_applicable", "invalid"]);
const label = (value) => value === true
  ? "PASS"
  : value === false
    ? "MISSING"
    : String(value).toUpperCase();

function clear(node) {
  node.replaceChildren();
  return node;
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

function renderScores(scores) {
  const container = clear($("#scores"));
  for (const [name, rawValue] of Object.entries(scores)) {
    const value = Math.max(0, Math.min(100, Number(rawValue) || 0));
    const card = element("article", undefined, "score");
    card.append(element("span", name.replace(/[A-Z]/g, (char) => ` ${char}`)));
    card.append(element("strong", `${value}%`));
    const meter = element("meter", `${value}%`);
    meter.min = 0;
    meter.max = 100;
    meter.value = value;
    card.append(meter);
    container.append(card);
  }
}

function renderChecks(checks) {
  const container = clear($("#checks"));
  for (const [name, value] of Object.entries(checks)) {
    const item = element("li");
    item.append(element("span", undefined, `dot ${value ? "pass" : "missing"}`));
    item.append(element("strong", name));
    item.append(element("small", label(value)));
    container.append(item);
  }
}

function renderReports(reports) {
  const container = clear($("#reports"));
  for (const [name, report] of Object.entries(reports)) {
    const status = STATUS_CLASSES.has(report.status) ? report.status : "invalid";
    const card = element("article");
    const header = element("header");
    header.append(element("strong", name));
    header.append(element("span", label(status), `pill ${status}`));
    card.append(header);
    card.append(element("p", report.summary || report.reason || "Machine-readable evidence available."));
    container.append(card);
  }
}

function renderCommits(commits) {
  const container = clear($("#commits"));
  if (!commits.length) {
    container.append(element("li", "No Git history available."));
    return;
  }
  for (const commit of commits) {
    const item = element("li");
    item.append(element("code", commit.sha));
    item.append(element("span", commit.subject));
    const date = element("time", new Date(commit.date).toLocaleDateString());
    date.dateTime = commit.date;
    item.append(date);
    container.append(item);
  }
}

function render(data) {
  $("#updated").textContent = new Date(data.generatedAt).toLocaleTimeString();
  $("#branch").textContent = `${data.repository.branch} @ ${data.repository.revision}`;
  $("#working-tree").textContent = data.repository.dirty
    ? `${data.repository.changedFiles} local changes`
    : "Clean working tree";
  renderScores(data.scores);
  renderChecks(data.checks);
  renderReports(data.reports);
  renderCommits(data.commits);
}

async function load() {
  const response = await fetch("/api/health");
  if (!response.ok) throw new Error(`Health API returned ${response.status}`);
  render(await response.json());
}

load().catch((error) => { $("#connection").textContent = error.message; });
const events = new EventSource("/api/events");
events.addEventListener("health", (event) => {
  $("#connection").textContent = "LIVE";
  render(JSON.parse(event.data));
});
events.onerror = () => { $("#connection").textContent = "RECONNECTING"; };
