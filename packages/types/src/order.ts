export type OrderStatus = "pending" | "confirmed" | "preparing" | "ready" | "delivering" | "completed" | "cancelled";
export interface OrderItem { id: string; menuItemId: string; name: string; quantity: number; unitPrice: number; notes?: string; }
export interface Order { id: string; customerId?: string; restaurantId: string; items: OrderItem[]; status: OrderStatus; totalAmount: number; pickupAt?: string; createdAt: string; updatedAt: string; }
