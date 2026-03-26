"""
FastAPI application for Energy Storage Investment Decision System
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from typing import Dict, Any
import os
from datetime import datetime

from app.models.investment import (
    InvestmentRequest,
    InvestmentAnalysis,
    ReportRequest,
    ReportResponse,
    ScenarioType,
)
from app.services.investment_calculator import InvestmentCalculator
from app.services.report_generator import ReportGenerator
from app.core.config import get_settings

router = APIRouter(prefix="/investment", tags=["investment"])

# Initialize services
calculator = InvestmentCalculator()
report_generator = ReportGenerator()

settings = get_settings()


@router.post("/calculate", response_model=InvestmentAnalysis, status_code=status.HTTP_200_OK)
async def calculate_investment(request: InvestmentRequest) -> InvestmentAnalysis:
    """
    Calculate investment returns for energy storage project

    Performs comprehensive financial analysis including:
    - IRR (Internal Rate of Return)
    - NPV (Net Present Value)
    - Payback period
    - Cash flow projections
    - ROI metrics

    Args:
        request: Investment calculation parameters

    Returns:
        InvestmentAnalysis with complete financial metrics and recommendations

    Example:
        ```python
        {
          "city_name": "深圳",
          "province_code": "GD",
          "storage_system": {
            "capacity_mwh": 10.0,
            "power_mw": 5.0,
            "discharge_efficiency": 0.92,
            "cycle_life": 6000,
            "daily_cycles": 1.5
          },
          "investment_params": {
            "equipment_cost_per_mwh": 1500000,
            "installation_cost_per_mwh": 300000,
            "grid_connection_cost": 500000,
            "annual_maintenance_cost_percent": 2.0,
            "insurance_cost_percent": 0.5,
            "project_lifetime_years": 15,
            "discount_rate": 0.08,
            "inflation_rate": 0.03
          },
          "scenario": "base"
        }
        ```
    """
    try:
        # Validate request
        if not request.city_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="city_name is required"
            )

        if not request.province_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="province_code is required"
            )

        # Perform calculation
        analysis = calculator.calculate(request)

        return analysis

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation error: {str(e)}"
        )


@router.post("/report/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """
    Generate PDF investment report

    Creates a professional PDF report with:
    - Executive summary
    - System specifications
    - Financial metrics
    - Cash flow projections
    - Investment recommendation

    Args:
        request: Report generation request with investment analysis

    Returns:
        ReportResponse with download URL and metadata

    Example:
        ```python
        {
          "analysis": { ... InvestmentAnalysis object ... },
          "include_charts": true,
          "language": "zh"
        }
        ```
    """
    try:
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"investment_report_{request.analysis.city_name}_{timestamp}.pdf"

        filepath = report_generator.generate_report(
            analysis=request.analysis,
            filename=filename,
            language=request.language
        )

        # Generate download URL
        # In production, this would be a proper CDN or storage URL
        report_url = f"/api/v1/investment/report/download/{filename}"

        return ReportResponse(
            report_url=report_url,
            report_filename=filename,
            generated_at=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(e)}"
        )


@router.get("/report/download/{filename}", status_code=status.HTTP_200_OK)
async def download_report(filename: str):
    """
    Download generated PDF report

    Args:
        filename: Name of the report file to download

    Returns:
        PDF file as attachment
    """
    try:
        filepath = os.path.join(report_generator.output_dir, filename)

        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {filename}"
            )

        return FileResponse(
            filepath,
            media_type="application/pdf",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download error: {str(e)}"
        )


@router.get("/scenarios", status_code=status.HTTP_200_OK)
async def get_scenarios() -> Dict[str, Any]:
    """
    Get available calculation scenarios

    Returns:
        List of available scenarios and their descriptions
    """
    return {
        "scenarios": [
            {
                "value": ScenarioType.OPTIMISTIC,
                "name": "乐观情景",
                "description": "假设峰谷价差扩大，补贴增加",
            },
            {
                "value": ScenarioType.BASE,
                "name": "基准情景",
                "description": "基于当前电价政策的基准情景",
            },
            {
                "value": ScenarioType.CONSERVATIVE,
                "name": "保守情景",
                "description": "假设峰谷价差缩小，补贴减少",
            },
        ]
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint

    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "Energy Storage Investment API",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }
