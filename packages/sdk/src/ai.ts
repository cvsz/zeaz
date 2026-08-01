import type {
  AiCatalog,
  AiChatInput,
  AiChatResponse,
  AiConfig,
} from "@moopiew/types";
import type { MoopiewClient } from "./client.js";
import {ownerHeaders} from "./owner-auth.js";

export class AiService {
  constructor(private client: MoopiewClient) {}

  publicModels(signal?: AbortSignal): Promise<AiCatalog> {
    return this.client.request<AiCatalog>("/api/ai/models", {
      signal,
    });
  }

  publicChat(
    input: AiChatInput,
    signal?: AbortSignal,
  ): Promise<AiChatResponse> {
    return this.client.request<AiChatResponse>("/api/ai/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
      signal,
    });
  }

  config(adminKey: string, signal?: AbortSignal): Promise<AiConfig> {
    return this.client.request<AiConfig>("/api/admin/ai/config", {
      headers: ownerHeaders(adminKey),
      signal,
    });
  }

  models(adminKey: string, signal?: AbortSignal): Promise<AiCatalog> {
    return this.client.request<AiCatalog>("/api/admin/ai/models", {
      headers: ownerHeaders(adminKey),
      signal,
    });
  }

  chat(
    adminKey: string,
    input: AiChatInput,
    signal?: AbortSignal,
  ): Promise<AiChatResponse> {
    return this.client.request<AiChatResponse>("/api/admin/ai/chat", {
      method: "POST",
      headers: {
        ...ownerHeaders(adminKey),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
      signal,
    });
  }
}
