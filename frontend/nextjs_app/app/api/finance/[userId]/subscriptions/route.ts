import { NextRequest, NextResponse } from 'next/server';

/** Subscription plans are stored and displayed in KES (primary system currency). No USD conversion. */
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
    const resp = await fetch(`${djangoUrl}/api/v1/subscription/plans`, {
      method: 'GET',
      headers: authHeaders,
      credentials: 'include',
    });

    if (!resp.ok) {
      console.error('Subscriptions API error:', resp.status);
      return NextResponse.json({ plans: [] }, { status: 200 });
    }

    const rawPlans = await resp.json();
    const plansList = Array.isArray(rawPlans) ? rawPlans : [];
    // Backend amounts are read as KES (subscription currency). Pass through for display.
    const plans = plansList.map((p: { revenue?: number; price_monthly?: number; [k: string]: unknown }) => ({
      ...p,
      price_monthly: Number(p.price_monthly ?? 0),
      revenue: Number(p.revenue ?? 0),
      subscription_currency: 'KES',
    }));
    return NextResponse.json({ plans });
  } catch (error) {
    console.error('Subscriptions API error:', error);
    return NextResponse.json({ plans: [] }, { status: 200 });
  }
}
