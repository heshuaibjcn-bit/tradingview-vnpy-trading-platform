"""
Investment calculator service using numpy-financial for IRR calculations
"""
import numpy as np
import numpy_financial as npf
from typing import List, Tuple
from datetime import date

from app.models.investment import (
    InvestmentRequest,
    InvestmentAnalysis,
    InvestmentMetrics,
    CashFlowProjection,
    ElectricityRate,
    ScenarioType,
)


class InvestmentCalculator:
    """
    Calculate investment returns for energy storage projects

    Uses numpy-financial for professional IRR and NPV calculations
    """

    def __init__(self):
        """Initialize calculator"""
        pass

    def calculate(self, request: InvestmentRequest) -> InvestmentAnalysis:
        """
        Perform complete investment analysis

        Args:
            request: Investment calculation request

        Returns:
            InvestmentAnalysis with metrics and cash flows
        """
        # Get electricity rates (from database or override)
        electricity_rate = request.electricity_rate or self._get_default_rate(
            request.city_name, request.province_code
        )

        # Apply scenario adjustments
        electricity_rate = self._apply_scenario(
            electricity_rate, request.scenario
        )

        # Calculate CAPEX
        total_capex = self._calculate_capex(
            request.storage_system,
            request.investment_params
        )

        # Calculate annual cash flows
        cash_flows = self._calculate_cash_flows(
            request.storage_system,
            request.investment_params,
            electricity_rate,
            total_capex
        )

        # Extract cash flow arrays for numpy-financial
        initial_investment = -total_capex
        annual_cash_flows = [cf.net_cash_flow for cf in cash_flows]
        all_cash_flows = [initial_investment] + annual_cash_flows

        # Calculate IRR using numpy-financial
        irr_decimal = npf.irr(all_cash_flows)
        irr_percent = irr_decimal * 100 if not np.isnan(irr_decimal) else 0.0

        # Calculate NPV using numpy-financial
        discount_rate = request.investment_params.discount_rate
        npv_value = npf.npv(discount_rate, all_cash_flows)

        # Calculate payback period
        payback_period = self._calculate_payback_period(annual_cash_flows, total_capex)

        # Calculate ROI
        total_profit = sum(annual_cash_flows)
        roi_percent = (total_profit / total_capex) * 100 if total_capex > 0 else 0.0

        # Calculate metrics
        metrics = InvestmentMetrics(
            irr_percent=irr_percent,
            npv=npv_value,
            payback_period_years=payback_period,
            annual_arbitrage_revenue=sum(cf.arbitrage_revenue for cf in cash_flows) / len(cash_flows),
            annual_peak_shaving_revenue=sum(cf.peak_shaving_revenue for cf in cash_flows) / len(cash_flows),
            annual_subsidy_revenue=sum(cf.subsidy_revenue for cf in cash_flows) / len(cash_flows),
            annual_total_revenue=sum(cf.total_revenue for cf in cash_flows) / len(cash_flows),
            annual_operating_cost=sum(cf.total_costs for cf in cash_flows) / len(cash_flows),
            annual_net_cash_flow=sum(cf.net_cash_flow for cf in cash_flows) / len(cash_flows),
            total_capex=total_capex,
            total_opex_over_lifetime=sum(cf.total_costs for cf in cash_flows),
            total_profit=total_profit,
            roi_percent=roi_percent,
        )

        # Generate recommendation
        is_recommendable, recommendation_reason = self._generate_recommendation(
            irr_percent, payback_period, npv_value
        )

        return InvestmentAnalysis(
            city_name=request.city_name,
            province_code=request.province_code,
            scenario=request.scenario,
            calculation_date=date.today(),
            storage_system=request.storage_system,
            electricity_rate=electricity_rate,
            metrics=metrics,
            cash_flows=cash_flows,
            is_recommendable=is_recommendable,
            recommendation_reason=recommendation_reason,
        )

    def _get_default_rate(self, city_name: str, province_code: str) -> ElectricityRate:
        """
        Get default electricity rate for a city

        In production, this would query from Supabase database
        For now, returns reasonable defaults
        """
        # Default rates (CNY/kWh) - these would come from database
        default_rates = {
            "深圳": {
                "peak": 1.2,
                "valley": 0.35,
                "flat": 0.75,
            },
            "广州": {
                "peak": 1.15,
                "valley": 0.38,
                "flat": 0.72,
            },
            "佛山": {
                "peak": 1.15,
                "valley": 0.38,
                "flat": 0.72,
            },
            "东莞": {
                "peak": 1.15,
                "valley": 0.38,
                "flat": 0.72,
            },
            "杭州": {
                "peak": 1.1,
                "valley": 0.4,
                "flat": 0.7,
            },
        }

        rates = default_rates.get(city_name, {
            "peak": 1.0,
            "valley": 0.4,
            "flat": 0.68,
        })

        return ElectricityRate(
            city_name=city_name,
            province_code=province_code,
            peak_price=rates["peak"],
            valley_price=rates["valley"],
            flat_price=rates["flat"],
            peak_hours="08:00-12:00,14:00-17:00",
            valley_hours="23:00-07:00",
            subsidy_amount=0.0,
            effective_date=date.today(),
        )

    def _apply_scenario(
        self,
        rate: ElectricityRate,
        scenario: ScenarioType
    ) -> ElectricityRate:
        """Apply scenario adjustments to electricity rates"""
        if scenario == ScenarioType.BASE:
            return rate

        # Create a mutable copy
        rate_dict = rate.model_dump()

        if scenario == ScenarioType.OPTIMISTIC:
            # Optimistic: higher prices, more subsidy
            rate_dict["peak_price"] *= 1.1  # 10% higher
            rate_dict["valley_price"] *= 0.9  # 10% lower
            rate_dict["subsidy_amount"] += 0.1  # Additional 0.1 CNY/kWh
        elif scenario == ScenarioType.CONSERVATIVE:
            # Conservative: lower prices, less subsidy
            rate_dict["peak_price"] *= 0.9  # 10% lower
            rate_dict["valley_price"] *= 1.1  # 10% higher
            rate_dict["subsidy_amount"] = max(0, rate_dict["subsidy_amount"] - 0.05)

        return ElectricityRate(**rate_dict)

    def _calculate_capex(
        self,
        system,
        params
    ) -> float:
        """Calculate total capital expenditure"""
        equipment_cost = (
            params.equipment_cost_per_mwh * system.capacity_mwh
        )
        installation_cost = (
            params.installation_cost_per_mwh * system.capacity_mwh
        )

        return equipment_cost + installation_cost + params.grid_connection_cost

    def _calculate_cash_flows(
        self,
        system,
        params,
        rate: ElectricityRate,
        total_capex: float
    ) -> List[CashFlowProjection]:
        """Calculate annual cash flows over project lifetime"""

        cash_flows = []
        cumulative_cf = -total_capex

        for year in range(1, params.project_lifetime_years + 1):
            # Revenue calculations
            arbitrage_revenue = self._calculate_arbitrage_revenue(
                system, params, rate
            )
            peak_shaving_revenue = self._calculate_peak_shaving_revenue(
                system, params, rate
            )
            subsidy_revenue = self._calculate_subsidy_revenue(
                system, params, rate
            )

            total_revenue = (
                arbitrage_revenue +
                peak_shaving_revenue +
                subsidy_revenue
            )

            # Cost calculations
            maintenance_cost = (
                total_capex *
                (params.annual_maintenance_cost_percent / 100)
            )
            insurance_cost = (
                total_capex *
                (params.insurance_cost_percent / 100)
            )
            electricity_cost = self._calculate_electricity_cost(
                system, params, rate
            )

            total_costs = (
                maintenance_cost + insurance_cost + electricity_cost
            )

            # Net cash flow
            net_cf = total_revenue - total_costs
            cumulative_cf += net_cf

            cash_flows.append(CashFlowProjection(
                year=year,
                arbitrage_revenue=arbitrage_revenue,
                peak_shaving_revenue=peak_shaving_revenue,
                subsidy_revenue=subsidy_revenue,
                total_revenue=total_revenue,
                maintenance_cost=maintenance_cost,
                insurance_cost=insurance_cost,
                electricity_cost=electricity_cost,
                total_costs=total_costs,
                net_cash_flow=net_cf,
                cumulative_cash_flow=cumulative_cf,
            ))

        return cash_flows

    def _calculate_arbitrage_revenue(
        self,
        system,
        params,
        rate: ElectricityRate
    ) -> float:
        """
        Calculate arbitrage revenue (buy low, sell high)

        Strategy: Charge during valley hours, discharge during peak hours
        """
        # Price spread (peak - valley)
        price_spread = rate.peak_price - rate.valley_price

        # Daily energy arbitrage (MWh)
        daily_energy = (
            system.capacity_mwh *
            params.investment_params.arbitrage_cycles_per_day *
            system.discharge_efficiency
        )

        # Annual revenue
        days_per_year = params.investment_params.peak_shaving_days_per_year
        annual_revenue = daily_energy * price_spread * days_per_year * 1000  # CNY

        return annual_revenue

    def _calculate_peak_shaving_revenue(
        self,
        system,
        params,
        rate: ElectricityRate
    ) -> float:
        """
        Calculate peak shaving revenue

        Strategy: Reduce peak demand charges by discharging during peak hours
        """
        # Assume peak shaving reduces demand charge
        # Typically charged as CNY/kW/month

        # For simplicity, assume peak shaving value of 100 CNY/kW/year
        peak_shaving_value_per_kw_year = 100

        # Annual revenue
        annual_revenue = (
            system.power_mw * 1000 *  # Convert MW to kW
            peak_shaving_value_per_kw_year
        )

        return annual_revenue

    def _calculate_subsidy_revenue(
        self,
        system,
        params,
        rate: ElectricityRate
    ) -> float:
        """Calculate subsidy revenue"""
        if rate.subsidy_amount <= 0:
            return 0.0

        # Subsidy per kWh discharged
        daily_energy = (
            system.capacity_mwh *
            params.investment_params.daily_cycles *
            system.discharge_efficiency
        )

        # Annual subsidy revenue
        days_per_year = params.investment_params.peak_shaving_days_per_year
        annual_revenue = (
            daily_energy *
            rate.subsidy_amount *
            days_per_year * 1000  # CNY
        )

        return annual_revenue

    def _calculate_electricity_cost(
        self,
        system,
        params,
        rate: ElectricityRate
    ) -> float:
        """
        Calculate electricity cost for charging

        Assume charging during valley hours (lowest cost)
        """
        # Energy needed to charge (accounting for efficiency)
        charging_energy = (
            system.capacity_mwh *
            params.investment_params.arbitrage_cycles_per_day /
            system.discharge_efficiency
        )

        # Annual cost
        days_per_year = params.investment_params.peak_shaving_days_per_year
        annual_cost = (
            charging_energy *
            rate.valley_price *
            days_per_year * 1000  # CNY
        )

        return annual_cost

    def _calculate_payback_period(
        self,
        annual_cash_flows: List[float],
        initial_investment: float
    ) -> float:
        """
        Calculate payback period in years

        Returns fractional year if payback occurs mid-year
        """
        cumulative = -initial_investment

        for year, cf in enumerate(annual_cash_flows, 1):
            cumulative += cf

            if cumulative >= 0:
                # Payback occurred this year
                # Calculate fraction of year
                prev_cumulative = cumulative - cf
                fraction = abs(prev_cumulative) / cf if cf != 0 else 0
                return year - 1 + fraction

        # Payback not achieved within project lifetime
        return float('inf')

    def _generate_recommendation(
        self,
        irr: float,
        payback: float,
        npv: float
    ) -> Tuple[bool, str]:
        """
        Generate investment recommendation

        Criteria:
        - IRR > 12% and payback < 8 years: RECOMMEND
        - IRR > 8% and payback < 10 years: CONSIDER
        - Otherwise: NOT RECOMMENDED
        """
        if irr > 12 and payback < 8 and npv > 0:
            return True, (
                f"强烈推荐。内部收益率 {irr:.1f}% 超过12%阈值，"
                f"投资回收期 {payback:.1f} 年低于8年，"
                f"净现值 {npv:,.0f} 元为正。"
            )
        elif irr > 8 and payback < 10 and npv > 0:
            return True, (
                f"可以投资。内部收益率 {irr:.1f}% 达到8%阈值，"
                f"投资回收期 {payback:.1f} 年在10年内，"
                f"净现值 {npv:,.0f} 元为正。建议进一步调研。"
            )
        else:
            return False, (
                f"不推荐投资。内部收益率 {irr:.1f}% 低于8%阈值，"
                f"或投资回收期 {payback:.1f} 年超过10年，"
                f"或净现值 {npv:,.0f} 元为负。建议重新评估项目参数。"
            )
