import type { BusinessProfile, Coupon, DeliveryPricing, DeliveryStatus, DeliveryZone, OperationsInventoryItem, MerchantApplication, MenuRecipe, OperationsDashboard, Receipt, Rider, RiderApplication, TaxInvoice } from "@moopiew/types";
import type { MoopiewClient } from "./client.js";
import { ownerHeaders } from "./owner-auth.js";

const headers = (adminKey: string) => ({...ownerHeaders(adminKey), "Content-Type": "application/json"});
export class OperationsService {
  constructor(private client: MoopiewClient) {}
  private write<T>(adminKey: string, path: string, method: "POST" | "PATCH", input: unknown) {
    return this.client.request<T>(path, {method, headers: headers(adminKey), body: JSON.stringify(input)});
  }
  dashboard(adminKey: string) { return this.client.request<OperationsDashboard>("/api/admin/operations", {headers: ownerHeaders(adminKey)}); }
  updateBusinessProfile(adminKey: string, input: Omit<BusinessProfile, "vat_rate">) { return this.write<{business_profile: BusinessProfile}>(adminKey, "/api/admin/business-profile", "POST", input); }
  updateDeliveryPricing(adminKey: string, input: DeliveryPricing) { return this.write<{delivery_pricing: DeliveryPricing}>(adminKey, "/api/admin/delivery-pricing", "POST", input); }
  createZone(adminKey: string, input: {name: string; fee: number; minimum_order: number}) { return this.write<{zone: DeliveryZone}>(adminKey, "/api/admin/delivery-zones", "POST", input); }
  createRider(adminKey: string, input: {name: string; phone: string}) { return this.write<{rider: Rider}>(adminKey, "/api/admin/riders", "POST", input); }
  updateRider(adminKey: string, id: string, input: {active?: boolean; available?: boolean}) { return this.write<{rider: Rider}>(adminKey, `/api/admin/riders/${encodeURIComponent(id)}`, "PATCH", input); }
  reviewRiderApplication(adminKey: string, id: string, status: "approved" | "rejected") { return this.write<{application: RiderApplication}>(adminKey, `/api/admin/rider-applications/${encodeURIComponent(id)}`, "PATCH", {status}); }
  reviewMerchantApplication(adminKey: string, id: string, status: "approved" | "rejected") { return this.write<{application: MerchantApplication}>(adminKey, `/api/admin/merchant-applications/${encodeURIComponent(id)}`, "PATCH", {status}); }
  updateDelivery(adminKey: string, id: string, input: {rider_id?: string; status?: DeliveryStatus}) { return this.write<{order: unknown}>(adminKey, `/api/admin/deliveries/${encodeURIComponent(id)}`, "PATCH", input); }
  createInventory(adminKey: string, input: {name: string; unit: string; on_hand: number; reorder_level: number}) { return this.write<{item: OperationsInventoryItem}>(adminKey, "/api/admin/inventory", "POST", input); }
  adjustInventory(adminKey: string, input: {inventory_item_id: string; delta: number; reason: string; note?: string}) { return this.write<{item: OperationsInventoryItem}>(adminKey, "/api/admin/inventory/adjust", "POST", input); }
  setRecipe(adminKey: string, input: {menu_item_id: string; inventory_item_id: string; quantity: number}) { return this.write<{recipe: MenuRecipe}>(adminKey, "/api/admin/inventory/recipes", "POST", input); }
  createCoupon(adminKey: string, input: Omit<Coupon, "id" | "used_count" | "active">) { return this.write<{coupon: Coupon}>(adminKey, "/api/admin/coupons", "POST", input); }
  issueReceipt(adminKey: string, orderId: string) { return this.write<{receipt: Receipt}>(adminKey, `/api/admin/orders/${encodeURIComponent(orderId)}/receipt`, "POST", {}); }
  issueTaxInvoice(adminKey: string, receiptId: string, input: {buyer_name: string; buyer_tax_id: string; buyer_address: string}) { return this.write<{tax_invoice: TaxInvoice}>(adminKey, `/api/admin/receipts/${encodeURIComponent(receiptId)}/tax-invoice`, "POST", input); }
  printReceipt(adminKey: string, receiptId: string) { return this.client.requestText(`/api/admin/receipts/${encodeURIComponent(receiptId)}/print`, {headers: ownerHeaders(adminKey)}); }
}
