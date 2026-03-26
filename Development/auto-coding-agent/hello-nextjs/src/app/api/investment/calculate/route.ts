/**
 * Investment Calculation API Route
 * Proxies requests to the FastAPI investment calculation service
 */

import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Call FastAPI service
    const response = await fetch(
      `${FASTAPI_URL}/api/v1/investment/calculate`,
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
        { error: error.detail || 'Calculation failed' },
        { status: response.status }
      );
    }

    const analysis = await response.json();

    return NextResponse.json(analysis);
  } catch (error) {
    console.error('Investment calculation error:', error);
    return NextResponse.json(
      {
        error: 'Failed to calculate investment returns',
        detail: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
