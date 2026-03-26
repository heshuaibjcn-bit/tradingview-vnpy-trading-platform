/**
 * Investment Report Download API Route
 * Proxies PDF download requests to the FastAPI service
 */

import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ filename: string }> }
) {
  try {
    const { filename } = await params;

    // Call FastAPI service
    const response = await fetch(
      `${FASTAPI_URL}/api/v1/investment/report/download/${filename}`,
      {
        method: 'GET',
      }
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Report not found or download failed' },
        { status: response.status }
      );
    }

    // Get the PDF file
    const pdfBuffer = await response.arrayBuffer();

    // Return the PDF file
    return new NextResponse(pdfBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${filename}"`,
      },
    });
  } catch (error) {
    console.error('Report download error:', error);
    return NextResponse.json(
      {
        error: 'Failed to download report',
        detail: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
