import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/finance/[userId]/revenue-dashboard
 * Proxies to Django GET /api/v1/finance/platform/revenue-dashboard/
 * Subscription amounts are in KES (primary system currency). No USD conversion.
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
    const resp = await fetch(`${djangoUrl}/api/v1/finance/platform/revenue-dashboard/`, {
      method: 'GET',
      headers: authHeaders,
      credentials: 'include',
    });

    if (!resp.ok) {
      const err = await resp.text();
      console.error('Revenue dashboard API error:', resp.status, err);
      return NextResponse.json(
        {
          subscription_plans_bought: 0,
          student_outsourced: 0,
          revenue_breakdown: [],
          total_subscription_revenue_usd: 0,
          total_subscription_revenue_kes: 0,
          revenue_by_month_subscription: [],
          revenue_by_month_placement: [],
          distribution: [],
          total_placement_revenue_kes: 0,
          error: resp.status === 403 ? 'Forbidden' : 'Failed to load dashboard',
        },
        { status: 200 }
      );
    }

    const data = await resp.json();

    // Subscription revenue is in KES (read as KSh). Pass through; no USD conversion.
    const totalSubKes = Number(data.total_subscription_revenue_usd ?? data.total_subscription_revenue_kes ?? 0);
    const breakdown = (data.revenue_breakdown || []).map((b: Record<string, unknown>) => ({
      ...b,
      revenue_kes: Number(b.revenue_kes ?? b.revenue_usd ?? 0),
    }));

    return NextResponse.json({
      ...data,
      total_subscription_revenue_kes: totalSubKes,
      revenue_breakdown: breakdown,
    });
  } catch (error) {
    console.error('Revenue dashboard API error:', error);
    return NextResponse.json(
      {
        subscription_plans_bought: 0,
        student_outsourced: 0,
        revenue_breakdown: [],
        total_subscription_revenue_usd: 0,
        total_subscription_revenue_kes: 0,
        revenue_by_month_subscription: [],
        revenue_by_month_placement: [],
        distribution: [],
        total_placement_revenue_kes: 0,
        error: 'Failed to load dashboard',
      },
      { status: 200 }
    );
  }
}
