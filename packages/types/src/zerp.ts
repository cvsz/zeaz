export interface ErpJournalLine {
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
}

export interface ErpJournalEntry {
  id: string;
  date: string;
  reference: string;
  journal: string;
  lines: ErpJournalLine[];
  state: "draft" | "posted" | "cancelled";
  source_type?: string;
  source_id?: string;
  total_debit?: number;
  total_credit?: number;
  balanced?: boolean;
}

export interface ErpStockMove {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  uom: string;
  source_location: string;
  destination_location: string;
  lot_number?: string;
  state: "draft" | "confirmed" | "done" | "cancelled";
  delta?: number;
  reason?: string;
  order_id?: string | null;
  note?: string;
  created_at?: string;
}

export interface ErpBomLine {
  product_id: string;
  product_name: string;
  quantity: number;
}

export interface ErpBom {
  id: string;
  product_id: string;
  product_name: string;
  routing: string;
  lines: ErpBomLine[];
}

export interface ErpOpportunity {
  id: string;
  name: string;
  partner_name: string;
  expected_revenue: number;
  stage: "new" | "qualified" | "proposition" | "won" | "lost";
}

export interface ErpEmployee {
  id: string;
  name: string;
  department: string;
  job_title: string;
  status: "active" | "on_leave" | "terminated";
}
