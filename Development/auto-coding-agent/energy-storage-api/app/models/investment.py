"""
Pydantic models for Energy Storage Investment calculations
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
from enum import Enum


class ScenarioType(str, Enum):
    """Investment scenario types"""
    OPTIMISTIC = "optimistic"
    BASE = "base"
    CONSERVATIVE = "conservative"


class ElectricityRate(BaseModel):
    """Electricity rate structure for a city"""
    city_name: str = Field(..., description="City name")
    province_code: str = Field(..., description="Province code (e.g., 'GD' for Guangdong)")
    peak_price: float = Field(..., gt=0, description="Peak hour price (CNY/kWh)")
    valley_price: float = Field(..., gt=0, description="Valley hour price (CNY/kWh)")
    flat_price: float = Field(..., gt=0, description="Flat price (CNY/kWh)")
    peak_hours: str = Field(..., description="Peak hours (e.g., '08:00-12:00,14:00-17:00')")
    valley_hours: str = Field(..., description="Valley hours (e.g., '23:00-07:00')")
    subsidy_amount: float = Field(0, ge=0, description="Subsidy amount (CNY/kWh)")
    effective_date: date = Field(..., description="Policy effective date")

    @validator('peak_price', 'valley_price', 'flat_price')
    def validate_prices(cls, v):
        """Validate price ranges"""
        if not 0.1 <= v <= 5.0:
            raise ValueError('Price must be between 0.1 and 5.0 CNY/kWh')
        return v


class StorageSystem(BaseModel):
    """Energy storage system specifications"""
    capacity_mwh: float = Field(..., gt=0, description="Storage capacity (MWh)")
    power_mw: float = Field(..., gt=0, description="Power rating (MW)")
    discharge_efficiency: float = Field(0.92, ge=0.5, le=1.0, description="Round-trip efficiency")
    cycle_life: int = Field(6000, ge=1000, description="Battery cycle life (cycles)")
    daily_cycles: float = Field(1.5, ge=0.1, le=3.0, description="Daily charge/discharge cycles")

    @validator('capacity_mwh', 'power_mw')
    def validate_system_size(cls, v):
        """Validate system size is reasonable"""
        if not 0.1 <= v <= 1000:
            raise ValueError('System size must be between 0.1 and 1000 MW/MWh')
        return v


class InvestmentParameters(BaseModel):
    """Investment financial parameters"""
    # System costs (CNY)
    equipment_cost_per_mwh: float = Field(..., gt=0, description="Equipment cost (CNY/MWh)")
    installation_cost_per_mwh: float = Field(..., gt=0, description="Installation cost (CNY/MWh)")
    grid_connection_cost: float = Field(0, ge=0, description="Grid connection cost (CNY)")

    # Operating costs
    annual_maintenance_cost_percent: float = Field(2.0, ge=0, le=10, description="Annual maintenance as % of CAPEX")
    insurance_cost_percent: float = Field(0.5, ge=0, le=5, description="Annual insurance as % of CAPEX")

    # Financial parameters
    project_lifetime_years: int = Field(15, ge=5, le=30, description="Project lifetime (years)")
    discount_rate: float = Field(0.08, ge=0, le=0.3, description="Discount rate (e.g., 0.08 for 8%)")
    inflation_rate: float = Field(0.03, ge=0, le=0.1, description="Inflation rate (e.g., 0.03 for 3%)")

    # Revenue assumptions
    peak_shaving_hours_per_day: float = Field(4, ge=0, le=24, description="Peak shaving hours per day")
    peak_shaving_days_per_year: int = Field(300, ge=0, le=365, description="Peak shaving days per year")
    arbitrage_cycles_per_day: float = Field(1.5, ge=0, le=3, description="Arbitrage cycles per day")


class InvestmentRequest(BaseModel):
    """Request model for investment calculation"""
    # Location
    city_name: str = Field(..., description="Target city (e.g., '深圳', '广州')")
    province_code: str = Field(..., description="Province code (e.g., 'GD', 'ZJ')")

    # System specification
    storage_system: StorageSystem

    # Financial parameters
    investment_params: InvestmentParameters

    # Scenario
    scenario: ScenarioType = Field(ScenarioType.BASE, description="Calculation scenario")

    # Optional overrides
    electricity_rate: Optional[ElectricityRate] = Field(None, description="Override city rate from database")


class CashFlowProjection(BaseModel):
    """Single year cash flow"""
    year: int
    # Revenue
    arbitrage_revenue: float
    peak_shaving_revenue: float
    subsidy_revenue: float
    total_revenue: float

    # Costs
    maintenance_cost: float
    insurance_cost: float
    electricity_cost: float
    total_costs: float

    # Net
    net_cash_flow: float
    cumulative_cash_flow: float


class InvestmentMetrics(BaseModel):
    """Key investment performance metrics"""
    # Return metrics
    irr_percent: float = Field(..., description="Internal Rate of Return (%)")
    npv: float = Field(..., description="Net Present Value (CNY)")
    payback_period_years: float = Field(..., description="Payback period (years)")

    # Revenue metrics (annual averages)
    annual_arbitrage_revenue: float = Field(..., description="Average annual arbitrage revenue (CNY)")
    annual_peak_shaving_revenue: float = Field(..., description="Average annual peak shaving revenue (CNY)")
    annual_subsidy_revenue: float = Field(..., description="Average annual subsidy revenue (CNY)")
    annual_total_revenue: float = Field(..., description="Average annual total revenue (CNY)")

    # Cost metrics
    annual_operating_cost: float = Field(..., description="Average annual operating cost (CNY)")
    annual_net_cash_flow: float = Field(..., description="Average annual net cash flow (CNY)")

    # Total investment
    total_capex: float = Field(..., description="Total capital expenditure (CNY)")
    total_opex_over_lifetime: float = Field(..., description="Total operating expense over lifetime (CNY)")

    # Profitability
    total_profit: float = Field(..., description="Total profit over lifetime (CNY)")
    roi_percent: float = Field(..., description="Return on Investment (%)")


class InvestmentAnalysis(BaseModel):
    """Complete investment analysis result"""
    # Request metadata
    city_name: str
    province_code: str
    scenario: ScenarioType
    calculation_date: date

    # System specification
    storage_system: StorageSystem

    # Electricity rates used
    electricity_rate: ElectricityRate

    # Investment metrics
    metrics: InvestmentMetrics

    # Cash flow projections
    cash_flows: List[CashFlowProjection]

    # Recommendation
    is_recommendable: bool = Field(..., description="Whether investment is recommended")
    recommendation_reason: str = Field(..., description="Reason for recommendation")


class ReportRequest(BaseModel):
    """Request to generate PDF report"""
    analysis: InvestmentAnalysis
    include_charts: bool = Field(True, description="Include charts in report")
    language: str = Field("zh", description="Report language ('zh' or 'en')")


class ReportResponse(BaseModel):
    """Response for PDF report generation"""
    report_url: str = Field(..., description="URL to download PDF report")
    report_filename: str = Field(..., description="Report filename")
    generated_at: str = Field(..., description="Report generation timestamp")
