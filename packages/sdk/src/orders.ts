import type {
  CreateOrderInput,
  OrderLookupResponse,
  PublicOrder,
  ScbPayment,
} from "@moopiew/types";
import type { MoopiewClient } from "./client.js";

export class OrdersService {
  constructor(private client: MoopiewClient) {}

  create(input: CreateOrderInput) {
    return this.client.request<{ order: PublicOrder }>("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  }

  lookup(orderId: string, phone: string) {
    return this.client.request<OrderLookupResponse>("/api/order-lookup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId, phone }),
    });
  }

  cancel(orderId: string, phone: string) {
    return this.client.request<{ order: PublicOrder }>(
      `/api/orders/${encodeURIComponent(orderId)}/cancel`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone }),
      },
    );
  }

  createScbQr(orderId: string, phone: string) {
    return this.client.request<{ payment: ScbPayment }>(
      `/api/orders/${encodeURIComponent(orderId)}/payments/scb/qr`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone }),
      },
    );
  }
}
