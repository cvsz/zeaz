"""Safe deterministic project generation with an optional provider seam."""

from __future__ import annotations

import html
import json
import re
import urllib.request
from typing import Any, Callable


SUPPORTED_CATEGORIES = {"internal", "customer", "marketing", "mobile"}
CATEGORY_LABELS = {
    "internal": "Internal workspace",
    "customer": "Customer portal",
    "marketing": "Marketing site",
    "mobile": "Mobile-ready workflow",
}


class OpenAICompatibleGenerator:
    """Small provider adapter whose output is still validated by this module."""

    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def __call__(self, prompt: str, category: str) -> dict[str, Any]:
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Return one JSON object with string name, string summary, and a files object. "
                            "Files must be a safe static app containing index.html, styles.css, and app.js. "
                            "Do not return server code, external scripts, secrets, or path traversal."
                        ),
                    },
                    {"role": "user", "content": f"Category: {category}\nBrief: {prompt}"},
                ],
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=body, headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError("AI provider request failed")
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("AI provider content is invalid")
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
        return json.loads(fenced.group(1) if fenced else content)


def _project_name(prompt: str, category: str) -> str:
    lowered = prompt.lower()
    if "crm" in lowered or "sales" in lowered or "deal" in lowered:
        return "Sales CRM"
    if "inventory" in lowered or "warehouse" in lowered or "stock" in lowered:
        return "Inventory Tracker"
    if "portal" in lowered or category == "customer":
        return "Client Portal"
    if "marketing" in lowered or "website" in lowered or category == "marketing":
        return "Growth Site"
    if "field" in lowered or "mobile" in lowered or category == "mobile":
        return "Field Companion"
    return CATEGORY_LABELS[category]


def _summary(category: str) -> str:
    return {
        "internal": "A focused workspace for your team, metrics, and daily operations.",
        "customer": "A clear customer-facing portal for updates, documents, and next steps.",
        "marketing": "A conversion-ready website with a simple, structured content system.",
        "mobile": "A responsive workflow for teams working from phones and the field.",
    }[category]


def _safe_prompt(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise ValueError("prompt must be text")
    clean = " ".join(prompt.split())
    if not 3 <= len(clean) <= 2_000:
        raise ValueError("prompt must be between 3 and 2000 characters")
    return clean


def _local_project(prompt: str, category: str) -> dict[str, Any]:
    title = _project_name(prompt, category)
    escaped_title = html.escape(title)
    escaped_prompt = html.escape(prompt)
    category_label = html.escape(CATEGORY_LABELS[category])
    html_file = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{html.escape(_summary(category))}">
    <title>{escaped_title} — Arin app</title>
    <link rel="stylesheet" href="styles.css">
  </head>
  <body>
    <main class="app-shell">
      <p class="eyebrow">{category_label}</p>
      <h1>{escaped_title}</h1>
      <p class="lead">{html.escape(_summary(category))}</p>
      <section class="brief" aria-labelledby="brief-title">
        <h2 id="brief-title">Built from your brief</h2>
        <p>{escaped_prompt}</p>
      </section>
      <button id="primary-action" type="button">Mark first step complete</button>
      <p id="action-status" role="status" aria-live="polite">Ready for your team.</p>
    </main>
    <script src="app.js"></script>
  </body>
</html>
'''
    css_file = '''
:root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #15163a; background: #f7f7f6; }
* { box-sizing: border-box; }
body { min-height: 100vh; margin: 0; padding: 6vw; background: radial-gradient(circle at top right, #e8ebff, #f7f7f6 48%); }
.app-shell { max-width: 760px; margin: 0 auto; padding: clamp(24px, 6vw, 72px); border: 1px solid #dedff0; border-radius: 28px; background: rgba(255, 255, 255, .88); box-shadow: 0 24px 80px rgba(40, 39, 92, .13); }
.eyebrow { color: #4855f5; font-size: .78rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
h1 { margin: 12px 0; font-size: clamp(2.7rem, 8vw, 5.6rem); line-height: .94; letter-spacing: -.07em; }
.lead { max-width: 48ch; color: #5f617c; font-size: 1.12rem; line-height: 1.7; }
.brief { margin: 36px 0; padding: 20px; border-radius: 18px; background: #f0f1ff; }
.brief h2 { margin: 0 0 8px; font-size: 1rem; }
.brief p { margin: 0; color: #55577a; line-height: 1.6; }
button { border: 0; border-radius: 999px; padding: 14px 20px; color: #fff; background: #4855f5; font: inherit; font-weight: 800; cursor: pointer; }
button:focus-visible { outline: 3px solid #f3b33d; outline-offset: 3px; }
#action-status { min-height: 1.5em; color: #5f617c; }
'''
    js_file = '''
const action = document.querySelector('#primary-action');
const status = document.querySelector('#action-status');
if (action && status) {
  action.addEventListener('click', () => {
    action.disabled = true;
    action.textContent = 'Completed';
    status.textContent = 'Your first step is complete.';
  });
}
'''
    return {
        "name": title,
        "summary": _summary(category),
        "category": category,
        "source": "local",
        "files": {"index.html": html_file, "styles.css": css_file, "app.js": js_file},
    }


def generate_project(
    prompt: str,
    category: str,
    ai_client: Callable[[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate a validated static project, falling back to local templates."""

    clean_prompt = _safe_prompt(prompt)
    if category not in SUPPORTED_CATEGORIES:
        raise ValueError("category is unsupported")
    if ai_client is not None:
        try:
            candidate = ai_client(clean_prompt, category)
            if isinstance(candidate, dict) and _valid_candidate(candidate):
                return candidate | {"source": "provider"}
        except Exception:
            pass
    return _local_project(clean_prompt, category)


def _valid_candidate(candidate: dict[str, Any]) -> bool:
    files = candidate.get("files")
    if not isinstance(files, dict) or not files:
        return False
    if not all(isinstance(path, str) and isinstance(content, str) for path, content in files.items()):
        return False
    if not {"index.html", "styles.css", "app.js"}.issubset(files):
        return False
    if any(
        not path or path.startswith("/") or ".." in path.split("/") or len(path) > 180
        for path in files
    ):
        return False
    if any(len(content.encode("utf-8")) > 256 * 1024 for content in files.values()):
        return False
    return bool(candidate.get("name")) and bool(candidate.get("summary"))
