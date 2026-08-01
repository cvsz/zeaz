import type {
  AdminDashboard,
  AdminOrder,
  PaymentAttempt,
  ScbAuthorizationStatus,
  StorefrontMenuItem,
} from "@moopiew/types";
import type { MoopiewClient } from "./client.js";
import { ownerHeaders } from "./owner-auth.js";

const jsonHeaders = (adminKey: string) => ({
  ...ownerHeaders(adminKey),
  "Content-Type": "application/json",
});

export class AdminService {
  constructor(private client: MoopiewClient) {}

  dashboard(adminKey: string) {
    return this.client.request<AdminDashboard>("/api/admin/dashboard", {
      headers: ownerHeaders(adminKey),
    });
  }

  updateSettings(
    adminKey: string,
    input: { slot_capacity?: number; advance_days?: number },
  ) {
    return this.client.request<{ settings: Record<string, unknown> }>(
      "/api/admin/settings",
      {
        method: "PATCH",
        headers: jsonHeaders(adminKey),
        body: JSON.stringify(input),
      },
    );
  }

  createMenu(
    adminKey: string,
    input: { name: string; description: string; price: number },
  ) {
    return this.client.request<{ item: StorefrontMenuItem }>("/api/admin/menu", {
      method: "POST",
      headers: jsonHeaders(adminKey),
      body: JSON.stringify(input),
    });
  }

  updateMenu(
    adminKey: string,
    menuId: string,
    input: Partial<Pick<StorefrontMenuItem, "name" | "description" | "price" | "available">>,
  ) {
    return this.client.request<{ item: StorefrontMenuItem }>(
      `/api/admin/menu/${encodeURIComponent(menuId)}`,
      {
        method: "PATCH",
        headers: jsonHeaders(adminKey),
        body: JSON.stringify(input),
      },
    );
  }

  updateOrder(
    adminKey: string,
    orderId: string,
    input: { status?: AdminOrder["status"]; payment_status?: AdminOrder["payment"]["status"] },
  ) {
    return this.client.request<{ order: AdminOrder }>(
      `/api/admin/orders/${encodeURIComponent(orderId)}`,
      {
        method: "PATCH",
        headers: jsonHeaders(adminKey),
        body: JSON.stringify(input),
      },
    );
  }

  inquirePayment(adminKey: string, paymentId: string) {
    return this.client.request<{ payment: PaymentAttempt; inquiry: "paid" | "pending" | "already_paid" }>(
      `/api/admin/payments/scb/${encodeURIComponent(paymentId)}/inquire`,
      {
        method: "POST",
        headers: jsonHeaders(adminKey),
        body: "{}",
      },
    );
  }

  startScbAuthorization(adminKey: string) {
    return this.client.request<{ authorization_url: string }>(
      "/api/admin/scb/auth/start",
      { headers: ownerHeaders(adminKey) },
    );
  }

  scbAuthorizationStatus(adminKey: string) {
    return this.client.request<ScbAuthorizationStatus>(
      "/api/admin/scb/auth/status",
      { headers: ownerHeaders(adminKey) },
    );
  }
}
