import { MoopiewClient } from "./client.js";
import type {
  ErpJournalEntry,
  ErpStockMove,
  ErpBom,
  ErpOpportunity,
  ErpEmployee,
} from "@moopiew/types";
import { ownerHeaders } from "./owner-auth.js";

export class ZerpService {
  constructor(private client: MoopiewClient) {}

  async listJournalEntries(adminKey: string): Promise<ErpJournalEntry[]> {
    const result = await this.client.request<{ entries: ErpJournalEntry[] }>("/api/admin/zerp/accounting/entries", { headers: ownerHeaders(adminKey) });
    return result.entries;
  }

  async listStockMoves(adminKey: string): Promise<ErpStockMove[]> {
    const result = await this.client.request<{ moves: ErpStockMove[] }>("/api/admin/zerp/inventory/moves", { headers: ownerHeaders(adminKey) });
    return result.moves;
  }

  async listBoms(): Promise<ErpBom[]> {
    return this.client.request<ErpBom[]>("/api/zerp/mrp/boms");
  }

  async listOpportunities(): Promise<ErpOpportunity[]> {
    return this.client.request<ErpOpportunity[]>("/api/zerp/crm/opportunities");
  }

  async listEmployees(): Promise<ErpEmployee[]> {
    return this.client.request<ErpEmployee[]>("/api/zerp/hrm/employees");
  }
}
