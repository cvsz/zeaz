import type {
  HealthResponse,
  MonitorEndpoint,
  ReadyResponse,
  StatusResponse,
} from "@moopiew/types";
import type {MoopiewClient} from "./client.js";
import {ownerHeaders} from "./owner-auth.js";

export class MonitoringService {
  constructor(private client: MoopiewClient) {}

  health() {
    return this.client.request<HealthResponse>("/api/health", {cache: "no-store"});
  }

  ready() {
    return this.client.request<ReadyResponse>("/api/ready", {cache: "no-store"});
  }

  status() {
    return this.client.request<StatusResponse>("/api/status", {cache: "no-store"});
  }

  probe(endpoint: MonitorEndpoint, adminKey = "") {
    return this.client.request<Record<string, unknown>>(endpoint, {
      cache: "no-store",
      headers: adminKey ? ownerHeaders(adminKey) : undefined,
    });
  }
}
