import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/finance/[userId]/export/pdf
 * Proxies to Django ReportLab-generated finance ROI report PDF.
 * Returns a clean PDF attachment (no HTML). All data from backend DB.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const djangoUrl =
    process.env.DJANGO_API_URL ||
    process.env.NEXT_PUBLIC_DJANGO_API_URL;

  const cookie = request.headers.get('cookie') ?? '';
  const accessToken = request.cookies.get('access_token')?.value ?? '';
  const authHeaders: Record<string, string> = { Cookie: cookie };
  if (accessToken) authHeaders['Authorization'] = `Bearer ${accessToken}`;

  try {
    const resp = await fetch(`${djangoUrl}/api/v1/finance/platform/roi-report/pdf/`, {
      method: 'GET',
      headers: authHeaders,
      credentials: 'include',
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error('Finance PDF export error:', resp.status, text);
      if (resp.status === 403) {
        return NextResponse.json(
          { error: 'You do not have permission to export this report' },
          { status: 403 }
        );
      }
      if (resp.status === 503) {
        return NextResponse.json(
          { error: 'PDF generation is unavailable (ReportLab required)' },
          { status: 503 }
        );
      }
      return NextResponse.json(
        { error: 'Failed to generate PDF report' },
        { status: 500 }
      );
    }

    const contentType = resp.headers.get('content-type') || 'application/pdf';
    const contentDisposition = resp.headers.get('content-disposition') || `attachment; filename="och-finance-roi-report-${new Date().toISOString().split('T')[0]}.pdf"`;
    const blob = await resp.arrayBuffer();

    return new NextResponse(blob, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': contentDisposition,
      },
    });
  } catch (error) {
    console.error('Finance PDF export error:', error);
    return NextResponse.json(
      { error: 'Failed to generate PDF report' },
      { status: 500 }
    );
  }
}
