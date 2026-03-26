"""
PDF report generator using reportlab
"""
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.platypus.flowables import Image, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY
from datetime import datetime
from typing import Optional
import os

from app.models.investment import InvestmentAnalysis, CashFlowProjection


class ReportGenerator:
    """Generate professional PDF investment reports"""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator

        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Page setup
        self.page_size = A4
        self.width, self.height = self.page_size
        self.margin = 0.75 * inch

    def generate_report(
        self,
        analysis: InvestmentAnalysis,
        filename: Optional[str] = None,
        language: str = "zh"
    ) -> str:
        """
        Generate PDF report for investment analysis

        Args:
            analysis: Investment analysis results
            filename: Optional custom filename
            language: Report language ('zh' or 'en')

        Returns:
            Path to generated PDF file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"investment_report_{analysis.city_name}_{timestamp}.pdf"

        filepath = os.path.join(self.output_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # Build story (content elements)
        story = []

        # Title page
        story.extend(self._create_title_page(analysis))

        # Page break
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(analysis))

        # Page break
        story.append(PageBreak())

        # System specification
        story.extend(self._create_system_section(analysis))

        # Page break
        story.append(PageBreak())

        # Financial metrics
        story.extend(self._create_financial_section(analysis))

        # Page break
        story.append(PageBreak())

        # Cash flow projections
        story.extend(self._create_cash_flow_section(analysis))

        # Page break
        story.append(PageBreak())

        # Recommendation
        story.extend(self._create_recommendation_section(analysis))

        # Build PDF
        doc.build(story)

        return filepath

    def _create_title_page(self, analysis: InvestmentAnalysis):
        """Create title page elements"""
        story = []

        # Custom styles
        styles = getSampleStyleSheet()

        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=30,
        )

        # Subtitle style
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceAfter=20,
        )

        # Title
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("储能项目投资分析报告", title_style))
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(
            f"{analysis.city_name} • {analysis.storage_system.capacity_mwh}MWh",
            subtitle_style
        ))
        story.append(Spacer(1, 0.5 * inch))

        # Metadata table
        metadata_data = [
            ["城市", analysis.city_name],
            ["省份代码", analysis.province_code],
            ["计算日期", analysis.calculation_date.strftime("%Y-%m-%d")],
            ["场景", analysis.scenario.value],
            ["系统容量", f"{analysis.storage_system.capacity_mwh} MWh"],
            ["功率", f"{analysis.storage_system.power_mw} MW"],
        ]

        metadata_table = Table(metadata_data, colWidths=[2 * inch, 3 * inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (0, -1), colors.lightgrey),
        ]))

        # Center the table
        table_wrapper = KeepTogether(metadata_table)
        story.append(table_wrapper)

        # Disclaimer
        story.append(Spacer(1, 1.5 * inch))
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_CENTER,
        )
        story.append(Paragraph(
            "本报告仅供参考，不构成投资建议。实际投资决策需结合更多市场调研和风险评估。",
            disclaimer_style
        ))

        return story

    def _create_executive_summary(self, analysis: InvestmentAnalysis):
        """Create executive summary section"""
        story = []
        styles = getSampleStyleSheet()

        # Section header
        story.append(Paragraph("执行摘要", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))

        # Summary metrics
        metrics = analysis.metrics

        summary_data = [
            ["指标", "数值"],
            ["内部收益率 (IRR)", f"{metrics.irr_percent:.2f}%"],
            ["净现值 (NPV)", f"{metrics.npv:,.0f} 元"],
            ["投资回收期", f"{metrics.payback_period_years:.1f} 年"],
            ["总投资回报率 (ROI)", f"{metrics.roi_percent:.2f}%"],
            ["总投资额 (CAPEX)", f"{metrics.total_capex:,.0f} 元"],
            ["年平均净现金流", f"{metrics.annual_net_cash_flow:,.0f} 元"],
        ]

        summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), colors.white),
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Key revenue breakdown
        revenue_style = ParagraphStyle(
            'Revenue',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
        )

        story.append(Paragraph("年平均收入构成:", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))

        revenue_text = f"""
        <b>套利收入:</b> {metrics.annual_arbitrage_revenue:,.0f} 元/年<br/>
        <b>峰谷价差收益:</b> {metrics.annual_peak_shaving_revenue:,.0f} 元/年<br/>
        <b>补贴收入:</b> {metrics.annual_subsidy_revenue:,.0f} 元/年<br/>
        <b>总计:</b> {metrics.annual_total_revenue:,.0f} 元/年
        """

        story.append(Paragraph(revenue_text, revenue_style))
        story.append(Spacer(1, 0.2 * inch))

        # Operating costs
        story.append(Paragraph("年平均运营成本:", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))

        cost_text = f"""
        年运营成本: <b>{metrics.annual_operating_cost:,.0f} 元/年</b><br/>
        年净利润: <b>{metrics.annual_net_cash_flow:,.0f} 元/年</b>
        """

        story.append(Paragraph(cost_text, revenue_style))

        return story

    def _create_system_section(self, analysis: InvestmentAnalysis):
        """Create system specification section"""
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("系统规格", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))

        system = analysis.storage_system
        rate = analysis.electricity_rate

        # System specifications
        system_data = [
            ["参数", "规格"],
            ["装机容量 (MWh)", f"{system.capacity_mwh:.2f}"],
            ["额定功率 (MW)", f"{system.power_mw:.2f}"],
            ["充放电效率", f"{system.discharge_efficiency * 100:.1f}%"],
            ["循环寿命", f"{system.cycle_life:,} 次"],
            ["每日充放电次数", f"{system.daily_cycles:.1f}"],
        ]

        system_table = Table(system_data, colWidths=[2.5 * inch, 2.5 * inch])
        system_table.setStyle(self._get_table_style())
        story.append(system_table)
        story.append(Spacer(1, 0.3 * inch))

        # Electricity rates
        story.append(Paragraph("电价政策", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))

        rate_data = [
            ["电价类型", "价格 (元/kWh)", "时段"],
            ["峰时电价", f"{rate.peak_price:.3f}", rate.peak_hours],
            ["谷时电价", f"{rate.valley_price:.3f}", rate.valley_hours],
            ["平电价", f"{rate.flat_price:.3f}", "-"],
            ["补贴", f"{rate.subsidy_amount:.3f}", "-"],
        ]

        rate_table = Table(rate_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
        rate_table.setStyle(self._get_table_style())
        story.append(rate_table)

        return story

    def _create_financial_section(self, analysis: InvestmentAnalysis):
        """Create financial metrics section"""
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("财务指标", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))

        metrics = analysis.metrics

        # Detailed metrics
        financial_data = [
            ["财务指标", "数值", "说明"],
            ["内部收益率", f"{metrics.irr_percent:.2f}%", "项目实际收益率"],
            ["净现值", f"{metrics.npv:,.0f} 元", "折现后的净收益"],
            ["投资回收期", f"{metrics.payback_period_years:.1f} 年", "收回投资所需时间"],
            ["投资回报率", f"{metrics.roi_percent:.2f}%", "总投资回报百分比"],
            ["总投资额", f"{metrics.total_capex:,.0f} 元", "初始投资成本"],
            ["总运营成本", f"{metrics.total_opex_over_lifetime:,.0f} 元", f"{analysis.storage_system.project_lifetime_years}年累计"],
            ["总利润", f"{metrics.total_profit:,.0f} 元", "项目生命周期内"],
        ]

        financial_table = Table(financial_data, colWidths=[2 * inch, 2 * inch, 1 * inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(financial_table)

        return story

    def _create_cash_flow_section(self, analysis: InvestmentAnalysis):
        """Create cash flow projections section"""
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("现金流预测", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))

        # Prepare cash flow data (show first 10 years if more)
        cash_flows = analysis.cash_flows[:10]

        cf_data = [["年份", "收入", "成本", "净现金流", "累计现金流"]]

        for cf in cash_flows:
            cf_data.append([
                f"第{cf.year}年",
                f"{cf.total_revenue:,.0f}",
                f"{cf.total_costs:,.0f}",
                f"{cf.net_cash_flow:,.0f}",
                f"{cf.cumulative_cash_flow:,.0f}",
            ])

        cf_table = Table(cf_data, colWidths=[1 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        cf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(cf_table)

        # Note if showing partial data
        if len(analysis.cash_flows) > 10:
            story.append(Spacer(1, 0.2 * inch))
            note_style = ParagraphStyle(
                'Note',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.gray,
            )
            story.append(Paragraph(
                f"注: 仅显示前10年，完整周期为{len(analysis.cash_flows)}年",
                note_style
            ))

        return story

    def _create_recommendation_section(self, analysis: InvestmentAnalysis):
        """Create recommendation section"""
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("投资建议", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))

        # Recommendation box
        recommendation_text = analysis.recommendation_reason

        rec_color = colors.green if analysis.is_recommendable else colors.red

        rec_style = ParagraphStyle(
            'Recommendation',
            parent=styles['Normal'],
            fontSize=14,
            textColor=rec_color,
            alignment=TA_CENTER,
            spaceAfter=20,
        )

        story.append(Paragraph("投资结论", styles['Heading2']))
        story.append(Paragraph(
            "✓ 推荐" if analysis.is_recommendable else "✗ 不推荐",
            rec_style
        ))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(recommendation_text, styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # Risk factors
        story.append(Paragraph("风险提示", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))

        risk_style = ParagraphStyle(
            'Risk',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=10,
        )

        risk_factors = [
            "1. 电价政策变化风险: 政府可能调整峰谷电价差或补贴政策",
            "2. 技术进步风险: 电池成本可能下降，影响投资回报",
            "3. 运营风险: 设备故障、性能衰减可能影响实际收益",
            "4. 市场风险: 电力需求变化可能影响峰谷价差",
            "5. 政策风险: 补贴政策可能调整或取消",
        ]

        for risk in risk_factors:
            story.append(Paragraph(risk, risk_style))

        # Disclaimer
        story.append(Spacer(1, 0.3 * inch))
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_JUSTIFY,
        )

        disclaimer_text = """
        <b>免责声明:</b> 本报告基于当前可获得的电价政策和技术参数进行计算，
        仅供投资参考之用。实际投资决策需综合考虑更多因素，包括但不限于：
        市场环境变化、政策调整、技术进步、运营管理等。
        本报告不构成任何投资建议，投资者需自行承担投资风险。
        """

        story.append(Paragraph(disclaimer_text, disclaimer_style))

        return story

    def _get_table_style(self):
        """Get standard table style"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
