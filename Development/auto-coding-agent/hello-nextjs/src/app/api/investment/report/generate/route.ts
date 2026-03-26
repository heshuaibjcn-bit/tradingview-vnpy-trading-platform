/**
 * Investment Report Generation API Route
 * Proxies report generation requests to the FastAPI service
 */

import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Call FastAPI service
    const response = await fetch(
      `${FASTAPI_URL}/api/v1/investment/report/generate`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: 'Unknown error from FastAPI service',
      }));
      return NextResponse.json(
        { error: error.detail || 'Report generation failed' },
        { status: response.status }
      );
    }

    const reportData = await response.json();

    return NextResponse.json(reportData);
  } catch (error) {
    console.error('Report generation error:', error);
    return NextResponse.json(
      {
        error: 'Failed to generate report',
        detail: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
