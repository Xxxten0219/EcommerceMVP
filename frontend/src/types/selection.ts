export type SelectionAnalysis = {
  site: string;
  platform: string;
  start_date: string;
  end_date: string;
  product_names: string[];
  sales: {
    units_sold: number;
    revenue: number;
    gross_margin_rate: number;
    refund_rate: number;
  };
  trend: {
    direction: "growing" | "stable" | "declining";
    overall_growth_rate: number;
    latest_mom_rate: number;
  } | null;
  inventory: {
    items: Array<{
      sku: string;
      product_name: string;
      snapshot_date: string;
      available: number;
      inbound: number;
    }>;
  };
  pressure: {
    coverage_days: number | null;
    pressure: string;
    rationale: string;
  };
  restock: {
    should_restock: boolean;
    recommended_quantity: number;
    rationale: string;
    requires_human_confirmation: boolean;
  };
  risks: string[];
  evidence: string[];
  human_confirmation_notice: string;
};
