export interface Delivery { id: string; orderId: string; driverId?: string; status: "assigned" | "picked_up" | "delivered" | "cancelled"; etaMinutes?: number; }
