import type {
  DeliveryQuote,
  DeliveryQuoteInput,
  TrackingSnapshot,
} from "@moopiew/types";
import type { MoopiewClient } from "./client.js";

export class DeliveryService {
  constructor(private client: MoopiewClient) {}

  quote(input: DeliveryQuoteInput) {
    return this.client.request<DeliveryQuote>("/api/delivery/quote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  }

  tracking(code: string) {
    return this.client.request<TrackingSnapshot>(
      `/api/tracking/${encodeURIComponent(code)}`,
    );
  }

  subscribe(
    code: string,
    onTracking: (snapshot: TrackingSnapshot) => void,
    onError?: () => void,
  ) {
    const source = new EventSource(
      `${this.client.baseURL}/api/tracking/${encodeURIComponent(code)}/events`,
    );
    source.addEventListener("tracking", (event) => {
      onTracking(JSON.parse((event as MessageEvent<string>).data));
    });
    if (onError) source.addEventListener("error", onError);
    return () => source.close();
  }
}
