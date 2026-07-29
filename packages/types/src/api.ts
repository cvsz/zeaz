/** Contracts for the currently deployed MooPiew HTTP API. */
export interface StorefrontMenuItem { id: string; name: string; description: string; price: number; available: boolean; }
export interface PickupSlot { time: string; remaining: number; available: boolean; }
export interface DeliveryZone { id: string; name: string; fee: number; minimum_order: number; }
export interface MenuResponse {
  api_version: string;
  generated_at: string;
  store: { name: string; locale: "th-TH"; currency: "THB" };
  store_name: string;
  theme: { name: string; primary: string; primary_light: string; secondary: string; surface: string; text: string };
  items: StorefrontMenuItem[];
  pickup: { date: string; slots: PickupSlot[]; capacity_per_slot: number; remaining_total: number };
  slots: PickupSlot[];
  date: string;
  advance_days: number;
  delivery_zones: DeliveryZone[];
  delivery_pricing: { mode: string; base_fee: number; per_km_fee: number; maximum_km: number; configured: boolean };
  links: { order: string; dashboard: string; platform: string; preview: string; health: string };
}
export interface OrderLineInput { id: string; quantity: number; }
export interface CreateOrderInput { name: string; phone: string; pickup_date?: string; pickup_slot?: string; fulfillment_type?: "pickup" | "delivery"; payment_method?: "cash" | "transfer" | "scb_qr"; items: OrderLineInput[]; coupon_code?: string; points_to_redeem?: number; notes?: string; delivery_zone_id?: string; recipient_name?: string; recipient_phone?: string; delivery_address?: string; delivery_landmark?: string; delivery_latitude?: number; delivery_longitude?: number; }
export interface PublicOrder {
  id: string;
  created_at: string;
  status: "new" | "confirmed" | "ready" | "completed" | "cancelled";
  total: number;
  notes: string;
  pickup: { date: string; slot: string };
  payment: {
    method: "cash" | "transfer" | "scb_qr";
    status: "pending" | "paid" | "refunded";
  };
  items: Array<{ id: string; name: string; quantity: number; unit_price: number }>;
  financial: {
    subtotal: number;
    delivery_fee: number;
    discount: number;
    total: number;
    coupon_code: string;
    points_earned: number;
    points_redeemed: number;
  };
  fulfillment:
    | { type: "pickup" }
    | {
        type: "delivery";
        delivery: {
          tracking_code: string;
          status: DeliveryStatus;
          zone_name: string;
          rider_name: string | null;
        };
      };
}
export interface OrderLookupResponse {
  order: PublicOrder;
  can_cancel: boolean;
  loyalty: { points_balance: number; point_value_thb: number };
}
export interface DeliveryQuoteInput { zone_id: string; subtotal: number; latitude?: number; longitude?: number; }
export interface DeliveryQuote { distance_km: number; delivery_fee: number; subtotal: number; total: number; zone: { id: string; name: string; minimum_order: number }; }
export type DeliveryStatus = "queued" | "assigned" | "picked_up" | "on_the_way" | "delivered" | "failed" | "cancelled";
export interface TrackingSnapshot { tracking: { tracking_code: string; status: DeliveryStatus; updated_at: string; zone_name: string; rider_name: string | null } }
export interface ScbPaymentConfig { enabled: boolean; provider: "scb_maemanee"; method: "scb_qr"; payment_types: string[]; environment: string; }
export interface ScbPayment { id: string; provider: string; amount: number; status: string; qr_image: string; qr_type: string; expires_at: string; }
export interface AiProviderStatus { enabled: boolean; models: number; error?: string; }
export interface AiConfig {
  enabled: boolean;
  providers: Record<string, boolean>;
  catalog: "live";
  chat_only: true;
  fallback: boolean;
}
export interface AiModel {
  id: string;
  provider: string;
  model: string;
  display_name: string;
  free?: boolean;
  free_tier?: boolean;
}
export interface AiCatalog {
  models: AiModel[];
  providers: Record<string, AiProviderStatus>;
  catalog: "live-provider";
  cached_seconds: number;
}
export interface AiChatInput {
  model: string;
  prompt: string;
  max_tokens?: number;
  temperature?: number;
}
export interface AiUsage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}
export interface AiChatResponse {
  id: string;
  requested_id: string;
  provider: string;
  model: string;
  content: string;
  fallback: boolean;
  usage?: AiUsage;
}
export interface RiderApplicationInput {
  name: string;
  phone: string;
  vehicle_type: "motorcycle" | "bicycle" | "car";
  vehicle_plate?: string;
  note?: string;
}
export interface RiderApplication {
  id: string;
  name: string;
  phone: string;
  vehicle_type: string;
  vehicle_plate: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}
export interface MerchantApplicationInput {
  business_name: string;
  owner_name: string;
  phone: string;
  email?: string;
  category: string;
  address: string;
  note?: string;
}
export interface MerchantApplication {
  id: string;
  business_name: string;
  owner_name: string;
  phone: string;
  email: string;
  category: string;
  address: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}
export interface HealthResponse { status: "ok"; service: string; time: string; }
export interface ReadyResponse { status: "ready"; database: "ok"; }
export interface StatusResponse {
  status: "operational";
  service: string;
  time: string;
  database: "ok";
  api_version: string;
  endpoints: Record<string, string>;
}
export type MonitorEndpoint =
  | "/api/health"
  | "/api/ready"
  | "/api/status"
  | "/api/menu"
  | "/api/payments/scb/config"
  | "/api/admin/menu"
  | "/api/admin/scb/auth/status"
  | "/api/admin/ai/config"
  | "/api/admin/ai/models";

export interface Provider {
  id: string;
  slug: string;
  name: string;
  status: string;
  metadata: Record<string, unknown>;
}
export interface DocumentRequirement {
  id: string;
  provider_slug: string;
  provider_name: string;
  subject_type: "rider" | "merchant";
  document_slug: string;
  document_name: string;
  merchant_type_slug: string | null;
  vehicle_type_slug: string | null;
  allowed_mime_types: string[];
  max_size_bytes: number;
  is_required: boolean;
  is_optional: boolean;
  display_order: number;
  effective_from: string;
  effective_to: string;
  is_current?: boolean;
  status: "active" | "inactive";
  metadata: { label_th?: string; label_en?: string; note?: string; [key: string]: unknown };
}
export type DocumentStatus = "pending" | "approved" | "rejected" | "expired" | "deleted";
export interface UploadedDocument {
  id: string;
  provider_id: string;
  subject_type: "rider" | "merchant";
  subject_id: string;
  requirement_id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  status: DocumentStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
export interface DocumentUploadInput {
  provider: string;
  subject_type: "rider" | "merchant";
  subject_id: string;
  requirement_id: string;
  filename: string;
  mime_type: string;
  content_base64: string;
}
export interface RequirementVersionInput {
  display_order: number;
  is_required: boolean;
  is_optional: boolean;
  status?: "active" | "inactive";
  metadata: { label_th: string; label_en: string };
}
export interface AdminOrder extends PublicOrder {
  customer: { name: string; phone: string };
}
export interface AdminSummary {
  orders: number;
  active_orders: number;
  revenue: number;
  ready: number;
  new: number;
  completed: number;
}
export interface StoreSettings {
  store_name: string;
  slot_capacity: number;
  advance_days: number;
  pickup_slots: string[];
  menu: StorefrontMenuItem[];
  [key: string]: unknown;
}
export interface PaymentAttempt extends ScbPayment {
  provider_reference: string;
  provider_order_id: string;
  created_at: string;
  confirmed_at: string;
}
export interface AuditEvent {
  id: number;
  at: string;
  actor_role: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: string;
}
export interface AdminDashboard {
  summary: AdminSummary;
  orders: AdminOrder[];
  settings: StoreSettings;
  payments: PaymentAttempt[];
  audit: AuditEvent[];
}
export interface ScbAuthorizationStatus {
  connected: boolean;
  access_valid: boolean;
  refresh_valid: boolean;
  access_expires_at: string;
  refresh_expires_at: string;
  updated_at: string;
}
export interface BusinessProfile { legal_name: string; tax_id: string; address: string; branch: string; vat_registered: boolean; vat_rate: number; }
export interface DeliveryPricing { mode: "distance" | "zone"; base_fee: number; per_km_fee: number; maximum_km: number; store_latitude: number | null; store_longitude: number | null; }
export interface Rider { id: string; name: string; phone: string; active: boolean; available: boolean; created_at: string; updated_at: string; }
export interface OperationsDelivery { order_id: string; recipient_name: string; address: string; zone_name: string; status: DeliveryStatus; rider_name: string | null; total: number; }
export interface OperationsInventoryItem { id: string; name: string; unit: string; on_hand: number; reorder_level: number; active: boolean; }
export interface MenuRecipe { menu_item_id: string; inventory_item_id: string; quantity: number; menu_name: string; inventory_name: string; unit: string; }
export interface Coupon { id: string; code: string; kind: "fixed" | "percent"; value: number; minimum_order: number; maximum_uses: number; used_count: number; starts_at: string; ends_at: string; active: boolean; }
export interface Receipt { id: string; order_id: string; receipt_number: string; subtotal: number; discount: number; delivery_fee: number; total: number; issued_at: string; }
export interface TaxInvoice { receipt_id: string; tax_invoice_number: string; buyer_name: string; total: number; issued_at: string; }
export interface OperationsDashboard {
  delivery_zones: DeliveryZone[];
  delivery_pricing: DeliveryPricing;
  deliveries: OperationsDelivery[];
  riders: Rider[];
  rider_applications: RiderApplication[];
  merchant_applications: MerchantApplication[];
  inventory: OperationsInventoryItem[];
  menu: StorefrontMenuItem[];
  recipes: MenuRecipe[];
  coupons: Coupon[];
  receipts: Receipt[];
  tax_invoices: TaxInvoice[];
  business_profile: BusinessProfile;
}
