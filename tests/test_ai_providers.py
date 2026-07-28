import json
import os
import unittest
from unittest.mock import patch

import app


class AiProviderContractTests(unittest.TestCase):
    def setUp(self):
        app.AI_MODEL_CACHE.clear()
        app.AI_MODEL_CACHE.update(catalog={}, expires=0.0)

    def tearDown(self):
        app.AI_MODEL_CACHE.clear()
        app.AI_MODEL_CACHE.update(catalog={}, expires=0.0)

    def test_priority_provider_catalog_adapters(self):
        compatible = {
            "kimi": (app.kimi_models, app.KIMI_API_BASE),
            "scaleway": (app.scaleway_models, app.SCALEWAY_API_BASE),
            "together": (app.together_models, app.TOGETHER_API_BASE),
            "cerebras": (app.cerebras_models, app.CEREBRAS_API_BASE),
        }
        for provider, (loader, base) in compatible.items():
            with self.subTest(provider=provider), patch.object(
                app, "ai_http", return_value={"data": [{"id": "vendor/model"}]}
            ) as request:
                models = loader("secret")
                self.assertEqual(models[0]["id"], f"{provider}:vendor/model")
                request.assert_called_once_with(
                    f"{base}/models",
                    {"Authorization": "Bearer secret"},
                    allow_list=True,
                )

        with patch.object(
            app, "ai_http", return_value={"data": [{"id": "glm-4.5"}]}
        ) as request:
            self.assertEqual(app.zai_models("secret")[0]["id"], "zai:glm-4.5")
            request.assert_called_once_with(
                f"{app.ZAI_API_BASE}/models",
                {"Authorization": "Bearer secret"},
            )

        with patch.object(
            app,
            "ai_http",
            return_value=[{"id": "openai/gpt-4o-mini", "name": "GPT-4o mini"}],
        ) as request:
            models = app.github_models("secret")
            self.assertTrue(models[0]["free_tier"])
            request.assert_called_once_with(
                f"{app.GITHUB_MODELS_API_BASE}/catalog/models",
                {
                    "Authorization": "Bearer secret",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                allow_list=True,
            )

    def test_zero_price_catalogs_exclude_unproven_free_models(self):
        with patch.object(
            app,
            "ai_http",
            return_value={
                "data": [
                    {
                        "id": "vendor/free",
                        "pricing": {"prompt": "0", "completion": "0"},
                    },
                    {
                        "id": "vendor/paid",
                        "pricing": {"prompt": "0.001", "completion": "0"},
                    },
                    {"id": "vendor/unknown"},
                ]
            },
        ):
            self.assertEqual(
                [item["model"] for item in app.openrouter_models("secret")],
                ["vendor/free"],
            )

        with patch.object(
            app,
            "ai_http",
            return_value={
                "data": [
                    {"id": "alpha-free"},
                    {"id": "beta", "pricing": {"input": 0, "output": 0}},
                    {"id": "paid", "pricing": {"input": 1, "output": 0}},
                ]
            },
        ):
            self.assertEqual(
                [item["model"] for item in app.opencode_models("secret")],
                ["alpha-free", "beta"],
            )

    def test_catalog_preserves_priority_and_isolates_provider_failures(self):
        provider_keys = {
            name: f"{name}-secret"
            for name in (
                "zai",
                "kimi",
                "scaleway",
                "together",
                "github",
                "openrouter",
                "opencode",
                "groq",
                "cerebras",
            )
        }

        def model(provider, free=False):
            item = {
                "id": f"{provider}:{provider}-model",
                "provider": provider,
                "model": f"{provider}-model",
                "display_name": f"{provider}-model",
            }
            if free:
                item["free_tier"] = True
            return [item]

        loaders = {
            "zai_models": model("zai"),
            "kimi_models": model("kimi"),
            "scaleway_models": model("scaleway"),
            "together_models": model("together"),
            "github_models": model("github", True),
            "openrouter_models": ValueError("provider unavailable"),
            "opencode_models": model("opencode", True),
            "groq_models": model("groq", True),
            "cerebras_models": model("cerebras", True),
        }
        patches = [
            patch.object(
                app,
                name,
                side_effect=value if isinstance(value, Exception) else None,
                return_value=None if isinstance(value, Exception) else value,
            )
            for name, value in loaders.items()
        ]
        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER_KEYS_JSON": json.dumps(provider_keys),
                "LOCAL_AI_BASE_URL": "",
                "HF_ENABLED": "false",
                "ZEAZ_AI_GATEWAY_URL": "",
            },
            clear=False,
        ):
            for mocked in patches:
                mocked.start()
            try:
                catalog = app.ai_catalog()
            finally:
                for mocked in reversed(patches):
                    mocked.stop()

        self.assertEqual(
            [item["provider"] for item in catalog["models"]],
            [
                "zai",
                "kimi",
                "scaleway",
                "together",
                "github",
                "opencode",
                "groq",
                "cerebras",
            ],
        )
        self.assertFalse(catalog["providers"]["openrouter"]["enabled"])
        self.assertNotIn("secret", catalog["providers"]["openrouter"]["error"])

    def test_chat_dispatches_priority_provider_contracts(self):
        providers = (
            "local",
            "zai",
            "kimi",
            "scaleway",
            "together",
            "github",
            "openrouter",
            "opencode",
            "huggingface",
            "groq",
            "cerebras",
        )
        keys = {
            provider: f"{provider}-secret"
            for provider in providers
            if provider not in {"local", "huggingface"}
        }

        for provider in providers:
            with self.subTest(provider=provider):
                catalog = {
                    "models": [
                        {
                            "id": f"{provider}:model",
                            "provider": provider,
                            "model": "model",
                            "free_tier": True,
                        }
                    ],
                    "providers": {},
                }
                with patch.dict(
                    os.environ,
                    {
                        "AI_PROVIDER_KEYS_JSON": json.dumps(keys),
                        "LOCAL_AI_BASE_URL": "http://127.0.0.1:11434/v1",
                        "LOCAL_AI_API_KEY": "local-secret",
                    },
                    clear=False,
                ), patch.object(
                    app, "ai_catalog", return_value=catalog
                ), patch.object(
                    app, "zai_chat", return_value="ok"
                ) as zai_chat, patch.object(
                    app, "openai_compatible_chat", return_value="ok"
                ) as compatible_chat, patch.object(
                    app, "hf_chat", return_value={"content": "ok"}
                ) as hf_chat, patch.object(
                    app,
                    "ai_http",
                    return_value={
                        "choices": [{"message": {"content": "ok"}}]
                    },
                ) as http:
                    result = app.ai_chat(
                        f"{provider}:model",
                        "health check",
                        max_tokens=8,
                        temperature=0,
                    )

                self.assertEqual(result["provider"], provider)
                self.assertEqual(result["content"], "ok")
                if provider == "zai":
                    zai_chat.assert_called_once_with(
                        "zai-secret", "model", "health check", 8, 0
                    )
                elif provider == "local":
                    compatible_chat.assert_called_once_with(
                        "http://127.0.0.1:11434/v1",
                        "local-secret",
                        "model",
                        "health check",
                        8,
                        0,
                        "Local AI",
                    )
                elif provider == "huggingface":
                    hf_chat.assert_called_once_with(
                        "model", "health check", 8, 0
                    )
                elif provider == "github":
                    request = http.call_args
                    self.assertEqual(
                        request.args[0],
                        f"{app.GITHUB_MODELS_API_BASE}/inference/chat/completions",
                    )
                    self.assertEqual(
                        request.args[1]["Authorization"],
                        "Bearer github-secret",
                    )
                    self.assertEqual(request.args[2]["model"], "model")
                else:
                    compatible_chat.assert_called_once()
                    self.assertEqual(
                        compatible_chat.call_args.args[1],
                        f"{provider}-secret",
                    )
                    self.assertEqual(
                        compatible_chat.call_args.args[2:5],
                        ("model", "health check", 8),
                    )


if __name__ == "__main__":
    unittest.main()
