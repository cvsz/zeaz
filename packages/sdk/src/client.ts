import type { TokenStore } from "./auth.js";
import { AdminService } from "./admin.js";
import { AiService } from "./ai.js";
import { ApplicationsService } from "./applications.js";
import { DeliveryService } from "./delivery.js";
import { DocumentsService } from "./documents.js";
import { MoopiewApiError } from "./errors.js";
import { MenusService } from "./menus.js";
import { MonitoringService } from "./monitoring.js";
import { OperationsService } from "./operations.js";
import { OrdersService } from "./orders.js";
import { PaymentsService } from "./payments.js";

import { ZerpService } from "./zerp.js";

export interface ClientOptions {
  baseURL: string;
  token?: string;
  tokenStore?: TokenStore;
  fetch?: typeof fetch;
  retries?: number;
  requestId?: () => string;
  onTrace?: (trace: {
    method: string;
    path: string;
    status?: number;
    attempt: number;
  }) => void;
}

export class MoopiewClient {
  readonly baseURL: string;
  readonly orders: OrdersService;
  readonly menus: MenusService;
  readonly payments: PaymentsService;
  readonly delivery: DeliveryService;
  readonly ai: AiService;
  readonly applications: ApplicationsService;
  readonly monitoring: MonitoringService;
  readonly documents: DocumentsService;
  readonly admin: AdminService;
  readonly operations: OperationsService;
  readonly zerp: ZerpService;
  private readonly requestFetch: typeof fetch;
  private readonly retries: number;
  private token?: string;

  constructor(private options: ClientOptions) {
    this.baseURL = options.baseURL.replace(/\/$/, "");
    this.requestFetch = (options.fetch ?? globalThis.fetch).bind(globalThis);
    this.token = options.token;
    this.retries = options.retries ?? 2;
    this.orders = new OrdersService(this);
    this.menus = new MenusService(this);
    this.payments = new PaymentsService(this);
    this.delivery = new DeliveryService(this);
    this.ai = new AiService(this);
    this.applications = new ApplicationsService(this);
    this.monitoring = new MonitoringService(this);
    this.documents = new DocumentsService(this);
    this.admin = new AdminService(this);
    this.operations = new OperationsService(this);
    this.zerp = new ZerpService(this);
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const method = (init.method ?? "GET").toUpperCase();
    const retryable = ["GET", "HEAD", "OPTIONS"].includes(method);
    for (let attempt = 0; ; attempt += 1) {
      const headers = new Headers(init.headers);
      headers.set("Accept", "application/json");
      const token = this.options.tokenStore?.get() ?? this.token;
      if (token) headers.set("Authorization", `Bearer ${token}`);
      const requestId =
        this.options.requestId ??
        (() =>
          globalThis.crypto?.randomUUID?.() ??
          `req-${Date.now()}-${Math.random().toString(16).slice(2)}`);
      headers.set("X-Request-Id", requestId());
      try {
        const response = await this.requestFetch(`${this.baseURL}${path}`, {
          ...init,
          headers,
        });
        this.options.onTrace?.({ method, path, status: response.status, attempt });
        const text = await response.text();
        let body: unknown;
        try {
          body = text ? JSON.parse(text) : undefined;
        } catch {
          throw new MoopiewApiError("Server returned invalid JSON", response.status);
        }
        if (!response.ok) {
          throw new MoopiewApiError(
            (body as { error?: string } | undefined)?.error ?? response.statusText,
            response.status,
            (body as { code?: string } | undefined)?.code,
          );
        }
        return body as T;
      } catch (error) {
        if (
          !retryable ||
          attempt >= this.retries ||
          (error instanceof MoopiewApiError && error.status < 500)
        ) {
          throw error;
        }
        await new Promise((resolve) => setTimeout(resolve, 150 * (attempt + 1)));
      }
    }
  }

  async requestText(path: string, init: RequestInit = {}): Promise<string> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "text/html");
    const response = await this.requestFetch(`${this.baseURL}${path}`, {
      ...init,
      headers,
    });
    const text = await response.text();
    if (!response.ok) {
      throw new MoopiewApiError(
        `Request failed (${response.status})`,
        response.status,
      );
    }
    return text;
  }
}
