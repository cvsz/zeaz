/** Contracts for the currently deployed MooPiew HTTP API. */
export interface StorefrontMenuItem { id: string; name: string; description: string; price: number; available: boolean; }
export interface PickupSlot { time: string; remaining: number; available: boolean; }
export interface MenuResponse { api_version: string; generated_at: string; store: { name: string; locale: "th-TH"; currency: "THB" }; items: StorefrontMenuItem[]; pickup: { date: string; slots: PickupSlot[]; capacity_per_slot: number; remaining_total: number }; }
export interface OrderLineInput { id: string; quantity: number; }
export interface CreateOrderInput { name: string; phone: string; pickup_date?: string; pickup_slot?: string; fulfillment_type?: "pickup" | "delivery"; payment_method?: "cash" | "transfer" | "scb_qr"; items: OrderLineInput[]; coupon_code?: string; points_to_redeem?: number; notes?: string; delivery_zone_id?: string; recipient_name?: string; recipient_phone?: string; delivery_address?: string; delivery_landmark?: string; delivery_latitude?: number; delivery_longitude?: number; }
export interface PublicOrder { id: string; created_at: string; status: "new" | "confirmed" | "ready" | "completed" | "cancelled"; total: number; customer: { name: string; phone: string }; pickup: { date: string; slot: string }; payment: { method: "cash" | "transfer" | "scb_qr"; status: "pending" | "paid" | "refunded" }; items: Array<{ id: string; name: string; quantity: number; unit_price: number }>; }
export interface DeliveryQuoteInput { zone_id: string; subtotal: number; latitude?: number; longitude?: number; }
export interface DeliveryQuote { distance_km: number; delivery_fee: number; subtotal: number; total: number; zone: { id: string; name: string; minimum_order: number }; }
export type DeliveryStatus = "queued" | "assigned" | "picked_up" | "on_the_way" | "delivered" | "failed" | "cancelled";
export interface TrackingSnapshot { tracking: { tracking_code: string; status: DeliveryStatus; updated_at: string; zone_name: string; rider_name: string | null } }
export interface ScbPaymentConfig { enabled: boolean; provider: "scb_maemanee"; method: "scb_qr"; payment_types: string[]; environment: string; }
export interface ScbPayment { id: string; provider: string; amount: number; status: string; qr_image: string; qr_type: string; expires_at: string; }
