export interface MetricPoint { at: string; value: number; }
export interface SalesAnalytics { revenue: MetricPoint[]; orderCount: MetricPoint[]; currency: "THB"; }
