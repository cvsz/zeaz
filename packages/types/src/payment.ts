export type PaymentStatus = "pending" | "paid" | "refunded";
export interface Payment { id: string; orderId: string; amount: number; currency: "THB"; method: "cash" | "transfer" | "scb_qr"; status: PaymentStatus; }
