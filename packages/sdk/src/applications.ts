import type {
  MerchantApplication,
  MerchantApplicationInput,
  RiderApplication,
  RiderApplicationInput,
} from "@moopiew/types";
import type {MoopiewClient} from "./client.js";

export class ApplicationsService {
  constructor(private client: MoopiewClient) {}

  registerRider(input: RiderApplicationInput) {
    return this.client.request<{application: RiderApplication}>(
      "/api/riders/register",
      {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(input),
      },
    );
  }

  registerMerchant(input: MerchantApplicationInput) {
    return this.client.request<{application: MerchantApplication}>(
      "/api/merchants/register",
      {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(input),
      },
    );
  }
}
