import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AIConsoleTests(unittest.TestCase):
    def setUp(self):
        self.redirect = (ROOT / "web" / "ai.html").read_text(encoding="utf-8")
        self.entry = (ROOT / "apps" / "web" / "ai.html").read_text(encoding="utf-8")
        self.component = (
            ROOT / "apps" / "web" / "src" / "ai.tsx"
        ).read_text(encoding="utf-8")
        self.service = (
            ROOT / "packages" / "sdk" / "src" / "ai.ts"
        ).read_text(encoding="utf-8")
        self.owner_auth = (
            ROOT / "packages" / "sdk" / "src" / "owner-auth.ts"
        ).read_text(encoding="utf-8")
        self.contracts = (
            ROOT / "packages" / "types" / "src" / "api.ts"
        ).read_text(encoding="utf-8")

    def test_legacy_entry_routes_to_published_react_shell(self):
        self.assertIn('url=/platform/ai.html', self.redirect)
        self.assertIn('src="/src/ai.tsx"', self.entry)
        self.assertIn('id="root"', self.entry)

    def test_owner_key_and_conversation_are_not_persisted(self):
        source = self.component + self.service
        self.assertNotIn("localStorage", source)
        self.assertNotIn("sessionStorage", source)
        self.assertNotIn("indexedDB", source)
        self.assertNotIn("?key=", source)
        self.assertIn("ownerHeaders(adminKey)", self.service)
        self.assertIn('"X-Admin-Key-B64"', self.owner_auth)

    def test_console_uses_typed_sdk_for_production_ai_routes(self):
        self.assertIn("api.ai.publicModels()", self.component)
        self.assertIn("api.ai.publicChat(", self.component)
        self.assertIn("api.ai.config(key)", self.component)
        self.assertIn("api.ai.models(key)", self.component)
        self.assertIn("api.ai.chat(ownerKey,", self.component)
        self.assertNotIn("fetch(", self.component)
        for route in (
            "/api/ai/models",
            "/api/ai/chat",
            "/api/admin/ai/config",
            "/api/admin/ai/models",
            "/api/admin/ai/chat",
        ):
            self.assertIn(route, self.service)
        for contract in (
            "AiConfig",
            "AiCatalog",
            "AiChatInput",
            "AiChatResponse",
        ):
            self.assertIn(f"interface {contract}", self.contracts)

    def test_accessible_workflow_and_bounded_prompt_are_present(self):
        for marker in (
            'role="status"',
            'aria-live="polite"',
            'role="radiogroup"',
            "maxLength={12000}",
            'href="#composer"',
        ):
            self.assertIn(marker, self.component)


if __name__ == "__main__":
    unittest.main()
