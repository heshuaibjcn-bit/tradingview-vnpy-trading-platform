/**
 * Investment Calculator Types
 * Matches FastAPI service models
 */

export type ScenarioType = 'optimistic' | 'base' | 'conservative';

export interface ElectricityRate {
  city_name: string;
  province_code: string;
  peak_price: number;
  valley_price: number;
  flat_price: number;
  peak_hours: string;
  valley_hours: string;
  subsidy_amount: number;
  effective_date: string;
}

export interface StorageSystem {
  capacity_mwh: number;
  power_mw: number;
  discharge_efficiency?: number;
  cycle_life?: number;
  daily_cycles?: number;
}

export interface InvestmentParameters {
  equipment_cost_per_mwh: number;
  installation_cost_per_mwh: number;
  grid_connection_cost?: number;
  annual_maintenance_cost_percent?: number;
  insurance_cost_percent?: number;
  project_lifetime_years?: number;
  discount_rate?: number;
  inflation_rate?: number;
  peak_shaving_hours_per_day?: number;
  peak_shaving_days_per_year?: number;
  arbitrage_cycles_per_day?: number;
}

export interface InvestmentRequest {
  city_name: string;
  province_code: string;
  storage_system: StorageSystem;
  investment_params: InvestmentParameters;
  scenario?: ScenarioType;
  electricity_rate?: ElectricityRate;
}

export interface CashFlowProjection {
  year: number;
  arbitrage_revenue: number;
  peak_shaving_revenue: number;
  subsidy_revenue: number;
  total_revenue: number;
  maintenance_cost: number;
  insurance_cost: number;
  electricity_cost: number;
  total_costs: number;
  net_cash_flow: number;
  cumulative_cash_flow: number;
}

export interface InvestmentMetrics {
  irr_percent: number;
  npv: number;
  payback_period_years: number;
  annual_arbitrage_revenue: number;
  annual_peak_shaving_revenue: number;
  annual_subsidy_revenue: number;
  annual_total_revenue: number;
  annual_operating_cost: number;
  annual_net_cash_flow: number;
  total_capex: number;
  total_opex_over_lifetime: number;
  total_profit: number;
  roi_percent: number;
}

export interface InvestmentAnalysis {
  city_name: string;
  province_code: string;
  scenario: ScenarioType;
  calculation_date: string;
  storage_system: StorageSystem;
  electricity_rate: ElectricityRate;
  metrics: InvestmentMetrics;
  cash_flows: CashFlowProjection[];
  is_recommendable: boolean;
  recommendation_reason: string;
}

export interface ReportRequest {
  analysis: InvestmentAnalysis;
  include_charts?: boolean;
  language?: string;
}

export interface ReportResponse {
  report_url: string;
  report_filename: string;
  generated_at: string;
}
