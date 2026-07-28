export interface Delivery { id: string; orderId: string; driverId?: string; status: "queued" | "assigned" | "picked_up" | "on_the_way" | "delivered" | "failed" | "cancelled"; etaMinutes?: number; }
