# Energy Storage Investment Decision API

FastAPI service for calculating energy storage investment returns with numpy-financial and generating PDF reports with reportlab.

## Features

- **IRR Calculation**: Professional Internal Rate of Return calculations using numpy-financial
- **NPV Analysis**: Net Present Value with configurable discount rates
- **Cash Flow Projections**: Multi-year cash flow forecasts
- **PDF Reports**: Professional investment analysis reports in Chinese
- **Scenario Analysis**: Optimistic, base, and conservative scenarios
- **City-Level Granularity**: Uses city-specific electricity pricing data

## Installation

```bash
cd energy-storage-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# - Supabase credentials (for city policy data)
# - API parameters
# - Calculation defaults
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Investment Calculation

**POST** `/api/v1/investment/calculate`

Calculate investment returns for an energy storage project.

Request body:
```json
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

Response:
```json
{
  "city_name": "深圳",
  "province_code": "GD",
  "scenario": "base",
  "calculation_date": "2026-03-26",
  "metrics": {
    "irr_percent": 14.5,
    "npv": 5200000,
    "payback_period_years": 6.8,
    "roi_percent": 145.2,
    ...
  },
  "is_recommendable": true,
  "recommendation_reason": "强烈推荐。内部收益率 14.5% 超过12%阈值..."
}
```

### Generate PDF Report

**POST** `/api/v1/investment/report/generate`

Generate a professional PDF investment report.

Request body:
```json
{
  "analysis": { ... InvestmentAnalysis object ... },
  "include_charts": true,
  "language": "zh"
}
```

Response:
```json
{
  "report_url": "/api/v1/investment/report/download/investment_report_深圳_20260326_143000.pdf",
  "report_filename": "investment_report_深圳_20260326_143000.pdf",
  "generated_at": "2026-03-26T14:30:00"
}
```

### Download Report

**GET** `/api/v1/investment/report/download/{filename}`

Download generated PDF report.

### Get Scenarios

**GET** `/api/v1/investment/scenarios`

Get available calculation scenarios.

## Calculation Logic

### Revenue Streams

1. **Arbitrage Revenue**: Buy electricity at valley prices, sell at peak prices
   ```
   Daily Revenue = Capacity × Cycles × Efficiency × Price Spread × Days
   ```

2. **Peak Shaving Revenue**: Reduce demand charges during peak hours
   ```
   Annual Revenue = Power (kW) × Peak Shaving Value (CNY/kW/year)
   ```

3. **Subsidy Revenue**: Government subsidies per kWh discharged
   ```
   Annual Revenue = Daily Energy × Subsidy × Days
   ```

### Cost Components

1. **CAPEX**: Equipment + Installation + Grid Connection
2. **OPEX**: Maintenance + Insurance + Electricity (charging cost)

### Financial Metrics

- **IRR**: Calculated using `numpy_financial.irr()`
- **NPV**: Calculated using `numpy_financial.npv()`
- **Payback Period**: Years until cumulative cash flow turns positive
- **ROI**: Total profit / Total investment × 100%

### Recommendation Criteria

- **Strong Buy**: IRR > 12%, Payback < 8 years, NPV > 0
- **Buy**: IRR > 8%, Payback < 10 years, NPV > 0
- **Don't Buy**: Otherwise

## PDF Report Sections

1. **Title Page**: Project name, location, key parameters
2. **Executive Summary**: IRR, NPV, payback period, key metrics
3. **System Specifications**: Technical parameters, electricity rates
4. **Financial Metrics**: Detailed financial analysis
5. **Cash Flow Projections**: Year-by-year cash flows (15+ years)
6. **Investment Recommendation**: Buy/Don't Buy with reasoning
7. **Risk Factors**: Policy, technology, market, operational risks

## City-Level Data

The system uses city-specific electricity pricing data from the Supabase database:

- **深圳** (Shenzhen, Guangdong)
- **广州** (Guangzhou, Guangdong)
- **佛山** (Foshan, Guangdong)
- **东莞** (Dongguan, Guangdong)
- **杭州** (Hangzhou, Zhejiang)

Each city has different peak/valley prices and hours.

## Example Usage with Python

```python
import httpx

async def calculate_investment():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/investment/calculate",
            json={
                "city_name": "深圳",
                "province_code": "GD",
                "storage_system": {
                    "capacity_mwh": 10.0,
                    "power_mw": 5.0,
                },
                "investment_params": {
                    "equipment_cost_per_mwh": 1500000,
                    "installation_cost_per_mwh": 300000,
                },
            }
        )
        return response.json()

# Run
result = await calculate_investment()
print(f"IRR: {result['metrics']['irr_percent']:.1f}%")
print(f"Recommendation: {result['recommendation_reason']}")
```

## Example Usage with curl

```bash
curl -X POST "http://localhost:8000/api/v1/investment/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "city_name": "深圳",
    "province_code": "GD",
    "storage_system": {
      "capacity_mwh": 10.0,
      "power_mw": 5.0
    },
    "investment_params": {
      "equipment_cost_per_mwh": 1500000,
      "installation_cost_per_mwh": 300000
    }
  }'
```

## Architecture

```
energy-storage-api/
├── app/
│   ├── api/
│   │   └── investment.py       # API endpoints
│   ├── core/
│   │   └── config.py           # Configuration
│   ├── models/
│   │   └── investment.py       # Pydantic models
│   ├── services/
│   │   ├── investment_calculator.py  # IRR calculations
│   │   └── report_generator.py       # PDF generation
│   └── main.py                # FastAPI app
├── reports/                    # Generated PDFs
├── requirements.txt
├── .env.example
└── README.md
```

## Dependencies

- **FastAPI**: Web framework
- **numpy-financial**: Financial calculations (IRR, NPV)
- **reportlab**: PDF generation
- **Pydantic**: Data validation
- **Supabase**: Database (city policy data)

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Format code
black app/
isort app/

# Type checking
mypy app/
```

## Integration with Next.js

The Next.js frontend calls this API:

```typescript
// src/app/api/investment/calculate/route.ts
export async function POST(request: NextRequest) {
  const body = await request.json();

  // Call Python FastAPI service
  const response = await fetch(
    `${process.env.PYTHON_API_URL}/api/v1/investment/calculate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }
  );

  const analysis = await response.json();
  return NextResponse.json(analysis);
}
```

## Troubleshooting

### Port already in use
```bash
lsof -i :8000
kill -9 <PID>
```

### Import errors
```bash
pip install -r requirements.txt --upgrade
```

### ReportLab font issues
ReportLab uses built-in fonts. For Chinese characters, ensure your system has appropriate fonts or modify the font configuration in `report_generator.py`.

## License

MIT

## Support

For issues or questions, please check the API documentation at `/docs` when the server is running.
