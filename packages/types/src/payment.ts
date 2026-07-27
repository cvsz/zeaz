export type PaymentStatus = "pending" | "authorized" | "paid" | "refunded" | "failed";
export interface Payment { id: string; orderId: string; amount: number; currency: "THB"; method: "cash" | "transfer" | "card" | "wallet"; status: PaymentStatus; }
