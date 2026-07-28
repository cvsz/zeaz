import os
import unittest
from unittest.mock import patch

import app


class AiFallbackTests(unittest.TestCase):
    def test_fallback_uses_free_catalog_model_after_failure(self):
        catalog = {
            "models": [
                {"id": "groq:first", "provider": "groq", "model": "first", "free_tier": True},
                {"id": "cerebras:backup", "provider": "cerebras", "model": "backup", "free_tier": True},
            ],
            "providers": {},
        }

        def chat(base, token, model, prompt, max_tokens, temperature, provider):
            if model == "first":
                raise ValueError("rate limited")
            return "backup response"

        with patch.dict(os.environ, {"AI_PROVIDER_KEYS_JSON": '{"groq":"g","cerebras":"c"}'}, clear=False), \
             patch.object(app, "ai_catalog", return_value=catalog), \
             patch.object(app, "openai_compatible_chat", side_effect=chat):
            result = app.ai_chat("groq:first", "hello")

        self.assertEqual(result["id"], "cerebras:backup")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["requested_id"], "groq:first")

    def test_local_http_endpoint_is_loopback_only(self):
        with patch.dict(os.environ, {"LOCAL_AI_BASE_URL": "http://127.0.0.1:11434/v1"}, clear=False):
            self.assertEqual(app.local_ai_base(), "http://127.0.0.1:11434/v1")
        with patch.dict(os.environ, {"LOCAL_AI_BASE_URL": "http://10.0.0.8:11434/v1"}, clear=False):
            with self.assertRaises(ValueError):
                app.local_ai_base()

    def test_boolean_form_values_are_not_truthy_strings(self):
        self.assertFalse(app.parse_bool("false", True))
        self.assertTrue(app.parse_bool("true", False))
        with self.assertRaises(ValueError):
            app.parse_bool("sometimes")


if __name__ == "__main__":
    unittest.main()
