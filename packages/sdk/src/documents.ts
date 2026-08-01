import type {
  DocumentRequirement,
  DocumentUploadInput,
  Provider,
  RequirementVersionInput,
  UploadedDocument,
} from "@moopiew/types";
import type { MoopiewClient } from "./client.js";
import { ownerHeaders } from "./owner-auth.js";

export class DocumentsService {
  constructor(private client: MoopiewClient) {}

  providers() {
    return this.client.request<{ providers: Provider[] }>("/api/providers");
  }

  requirements(
    provider: string,
    subject: "rider" | "merchant",
    signal?: AbortSignal,
  ) {
    return this.client.request<{ requirements: DocumentRequirement[] }>(
      `/api/providers/${encodeURIComponent(provider)}/requirements/${subject}`,
      { signal },
    );
  }

  upload(adminKey: string, input: DocumentUploadInput) {
    return this.client.request<{ document: UploadedDocument }>(
      "/api/documents/upload",
      {
        method: "POST",
        headers: {
          ...ownerHeaders(adminKey),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(input),
      },
    );
  }

  remove(adminKey: string, documentId: string) {
    return this.client.request<{ deleted: true; id: string }>(
      `/api/documents/${encodeURIComponent(documentId)}`,
      { method: "DELETE", headers: ownerHeaders(adminKey) },
    );
  }

  policies(adminKey: string) {
    return this.client.request<{ requirements: DocumentRequirement[] }>(
      "/api/admin/document-requirements",
      { headers: ownerHeaders(adminKey) },
    );
  }

  versionPolicy(
    adminKey: string,
    requirementId: string,
    input: RequirementVersionInput,
  ) {
    return this.client.request<{
      requirement_id: string;
      previous_id: string;
      effective_from: string;
    }>(`/api/admin/document-requirements/${encodeURIComponent(requirementId)}`, {
      method: "PATCH",
      headers: {
        ...ownerHeaders(adminKey),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    });
  }
}
