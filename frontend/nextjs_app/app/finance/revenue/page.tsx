"use client";

import { Suspense, useState } from "react";
import { Card } from "@/components/ui/Card";
import { CardContent } from "@/components/ui/card-enhanced";
import { useAuth } from "@/hooks/useAuth";
import { FinanceDashboardSkeleton } from "../dashboard/components";
import { RouteGuard } from "@/components/auth/RouteGuard";
import { Download, Calendar, Package, UserCheck, Wallet, TrendingUp } from "lucide-react";
import useSWR from "swr";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Area,
  AreaChart,
} from "recharts";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

/** Set to true to show UI with hardcoded data; switch to false when wiring dynamic data. */
const USE_HARDCODED_DATA = true;

const BREAKDOWN_COLORS = ["#1e293b", "#22c55e", "#f97316"]; // dark, green, orange
const COUNTRY_NAMES: Record<string, string> = {
  KE: "Kenya", US: "United States", GB: "United Kingdom", NG: "Nigeria",
  ZA: "South Africa", AU: "Australia", IN: "India", XX: "Unknown",
};

// Hardcoded data for UI preview (all KES)
const HARDCODED = {
  plansBought: 1432,
  plansTrend: "+12.4% vs last month",
  studentOutsourced: 1835,
  studentStatus: "234 placements in progress",
  availableFunds: 234590,
  nextPayout: "Next payout in 3 days",
  revenueBreakdownTotal: 975993,
  breakdownPeriod: "Monthly" as "Monthly" | "Weekly",
  donutData: [
    { name: "Subscriptions", value: 567000, percent: 58, fill: "#1e293b" },
    { name: "Sponsor placement", value: 234000, percent: 24, fill: "#22c55e" },
    { name: "Cohort / Platform", value: 174993, percent: 18, fill: "#f97316" },
  ],
  trafficMonths: [
    { month: "Jan", revenueKes: 82000 },
    { month: "Feb", revenueKes: 95000 },
    { month: "Mar", revenueKes: 88000 },
    { month: "Apr", revenueKes: 102000 },
  ],
  revenuePerformanceTotal: 90984,
  revenuePerformanceTrend: "15.90%",
  lineData: [
    { month: "Jan", value: 45000 },
    { month: "Feb", value: 52000 },
    { month: "Mar", value: 48000 },
    { month: "Apr", value: 71000 },
    { month: "May", value: 65000 },
    { month: "Jun", value: 90984 },
  ],
  topMarkets: [
    { name: "Kenya", count: 2130, color: "#f97316" },
    { name: "United States", count: 1850, color: "#f97316" },
    { name: "United Kingdom", count: 1420, color: "#22c55e" },
    { name: "Nigeria", count: 980, color: "#22c55e" },
    { name: "South Africa", count: 750, color: "#22c55e" },
  ],
  distribution: [
    { country: "KE", count: 2130 },
    { country: "US", count: 1850 },
    { country: "GB", count: 1420 },
    { country: "NG", count: 980 },
    { country: "ZA", count: 750 },
  ],
};

function RevenueContent() {
  const { user } = useAuth();
  const userId = user?.id || "finance-user";
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [revenueRange, setRevenueRange] = useState<"Day" | "Week" | "Month" | "Year">("Month");
  const [breakdownPeriod, setBreakdownPeriod] = useState<"Monthly" | "Weekly">(HARDCODED.breakdownPeriod);

  const { data: dashboard, isLoading } = useSWR(
    USE_HARDCODED_DATA ? null : `/api/finance/${userId}/revenue-dashboard`,
    fetcher,
    { refreshInterval: 60000 }
  );

  const { data: revenueData } = useSWR(
    USE_HARDCODED_DATA ? null : (startDate && endDate ? `/api/finance/${userId}/revenue?start=${startDate}&end=${endDate}` : `/api/finance/${userId}/revenue`),
    fetcher,
    { refreshInterval: 30000 }
  );

  const handleDownloadReport = async () => {
    const dateRange = startDate && endDate ? `${startDate}_to_${endDate}` : "all_time";
    try {
      const response = await fetch(`/api/finance/${userId}/export/csv?start=${startDate}&end=${endDate}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `revenue_report_${dateRange}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Failed to download report");
    }
  };

  const plansBought = USE_HARDCODED_DATA ? HARDCODED.plansBought : Number(dashboard?.subscription_plans_bought ?? 0);
  const studentOutsourced = USE_HARDCODED_DATA ? HARDCODED.studentOutsourced : Number(dashboard?.student_outsourced ?? 0);
  const totalSubscriptionKes = USE_HARDCODED_DATA ? HARDCODED.revenueBreakdownTotal : Number(dashboard?.total_subscription_revenue_kes ?? 0);
  const totalPlacementKes = USE_HARDCODED_DATA ? 0 : Number(dashboard?.total_placement_revenue_kes ?? 0);
  const availableFunds = USE_HARDCODED_DATA ? HARDCODED.availableFunds : totalSubscriptionKes + totalPlacementKes;
  const breakdown = USE_HARDCODED_DATA ? HARDCODED.donutData : (Array.isArray(dashboard?.revenue_breakdown) ? dashboard.revenue_breakdown : []);
  const donutData = USE_HARDCODED_DATA
    ? HARDCODED.donutData
    : breakdown
        .filter((b: { revenue_kes?: number }) => (b.revenue_kes ?? 0) > 0)
        .map((b: { name?: string; revenue_kes?: number; percent?: number }, i: number) => ({
          name: b.name || "Plan",
          value: Number(b.revenue_kes ?? 0),
          percent: Number(b.percent ?? 0),
          fill: BREAKDOWN_COLORS[i % BREAKDOWN_COLORS.length],
        }));
  const lastMonths = USE_HARDCODED_DATA ? HARDCODED.trafficMonths : (Array.isArray(dashboard?.revenue_by_month_subscription) ? dashboard.revenue_by_month_subscription.slice(-6) : []).map((m: { month?: string; total_usd?: number }) => ({
    month: (m.month || "").slice(5),
    revenueKes: Number(m.total_usd ?? 0) * 130,
  }));
  const lineData = USE_HARDCODED_DATA ? HARDCODED.lineData : (() => {
    const subByMonth = Array.isArray(dashboard?.revenue_by_month_subscription) ? dashboard.revenue_by_month_subscription : [];
    const placementByMonth = Array.isArray(dashboard?.revenue_by_month_placement) ? dashboard.revenue_by_month_placement : [];
    const USD_TO_KES = 130;
    const monthMap = new Map<string, { month: string; subscription: number; placement: number }>();
    subByMonth.forEach((m: { month?: string; total_usd?: number }) => {
      const key = (m.month || "").slice(0, 7);
      if (!key) return;
      monthMap.set(key, { month: key, subscription: Number(m.total_usd ?? 0) * USD_TO_KES, placement: monthMap.get(key)?.placement ?? 0 });
    });
    placementByMonth.forEach((m: { month?: string; total_kes?: number }) => {
      const key = (m.month || "").slice(0, 7);
      if (!key) return;
      const existing = monthMap.get(key);
      monthMap.set(key, { month: key, subscription: existing?.subscription ?? 0, placement: Number(m.total_kes ?? 0) });
    });
    return Array.from(monthMap.values()).sort((a, b) => a.month.localeCompare(b.month)).map((x) => ({ month: x.month.slice(5), value: x.subscription + x.placement }));
  })();
  const topMarkets = USE_HARDCODED_DATA ? HARDCODED.topMarkets : (Array.isArray(dashboard?.distribution) ? dashboard.distribution : []).slice(0, 5).map((d: { country?: string; count?: number }, i: number) => ({
    name: COUNTRY_NAMES[(d.country || "XX").toUpperCase()] || (d.country || "XX"),
    count: Number(d.count ?? 0),
    color: i < 2 ? "#f97316" : "#22c55e",
  }));
  const distribution = USE_HARDCODED_DATA ? HARDCODED.distribution : (Array.isArray(dashboard?.distribution) ? dashboard.distribution : []);
  const maxMarketCount = Math.max(1, ...topMarkets.map((m) => m.count));

  if (!USE_HARDCODED_DATA && isLoading) {
    return (
      <div className="w-full max-w-7xl py-4 px-4 sm:px-6 lg:px-8 mx-auto">
        <FinanceDashboardSkeleton />
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl py-4 px-4 sm:px-6 lg:px-8 mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-white">Finance Revenue</h1>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-slate-400" />
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="bg-slate-800 text-white px-2 py-1.5 rounded border border-slate-700 focus:border-cyan-500 focus:outline-none text-sm w-36" />
          <span className="text-slate-400 text-sm">to</span>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="bg-slate-800 text-white px-2 py-1.5 rounded border border-slate-700 focus:border-cyan-500 focus:outline-none text-sm w-36" />
          <button onClick={handleDownloadReport} className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-500 hover:bg-cyan-600 text-white rounded text-sm">
            <Download className="w-4 h-4" /> Download Report
          </button>
        </div>
      </div>

      {/* Top row: compact cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-slate-400">Subscription plans bought</p>
              <Package className="w-4 h-4 text-orange-500" />
            </div>
            <p className="text-xl font-bold text-white">{plansBought.toLocaleString()}</p>
            <p className="text-xs text-emerald-500 mt-0.5 flex items-center gap-1">
              {USE_HARDCODED_DATA ? HARDCODED.plansTrend : "Active paid subscriptions"}
              {USE_HARDCODED_DATA && <TrendingUp className="w-3 h-3" />}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-slate-400">Student outsourced</p>
              <UserCheck className="w-4 h-4 text-emerald-500" />
            </div>
            <p className="text-xl font-bold text-white">{studentOutsourced.toLocaleString()}</p>
            <p className="text-xs text-slate-400 mt-0.5">{USE_HARDCODED_DATA ? HARDCODED.studentStatus : "Total hires from placements"}</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-slate-400">Available funds</p>
              <Wallet className="w-4 h-4 text-cyan-500" />
            </div>
            <p className="text-xl font-bold text-white">Ksh {availableFunds.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
            <p className="text-xs text-cyan-500 mt-0.5">{USE_HARDCODED_DATA ? HARDCODED.nextPayout : "Subscriptions + placement"}</p>
          </CardContent>
        </Card>
      </div>

      {/* Two-column: left (Revenue breakdown + Performance), right (Funds + Distribution + Markets) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        {/* Left column: 2/3 */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-white">Revenue breakdown</h3>
                <select value={breakdownPeriod} onChange={(e) => setBreakdownPeriod(e.target.value as "Monthly" | "Weekly")} className="bg-slate-700 text-white text-xs px-2 py-1 rounded border border-slate-600">
                  <option value="Monthly">Monthly</option>
                  <option value="Weekly">Weekly</option>
                </select>
              </div>
              <p className="text-lg font-bold text-white mb-2">Ksh {(USE_HARDCODED_DATA ? HARDCODED.revenueBreakdownTotal : totalSubscriptionKes).toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              {donutData.length === 0 ? (
                <p className="text-xs text-slate-400">No revenue data yet.</p>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-32 h-28 flex-shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={donutData} cx="50%" cy="50%" innerRadius={28} outerRadius={44} paddingAngle={2} dataKey="value" nameKey="name">
                          {donutData.map((entry, index) => (
                            <Cell key={index} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(v: number) => [`Ksh ${v.toLocaleString()}`, "Revenue"]} contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", fontSize: 11 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-1 text-xs">
                    {donutData.map((d, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.fill }} />
                        <span className="text-slate-300">{d.name}</span>
                        <span className="text-slate-400">{d.percent}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-white">Revenue performance</h3>
                  <span className="text-xs text-emerald-500 flex items-center gap-0.5">
                    {USE_HARDCODED_DATA ? HARDCODED.revenuePerformanceTrend : ""} <TrendingUp className="w-3 h-3" />
                  </span>
                </div>
                <div className="flex gap-1">
                  {(["Day", "Week", "Month", "Year"] as const).map((r) => (
                    <button key={r} onClick={() => setRevenueRange(r)} className={`px-2 py-1 rounded text-xs font-medium ${revenueRange === r ? "bg-slate-600 text-white" : "bg-slate-700/50 text-slate-400 hover:bg-slate-700"}`}>{r}</button>
                  ))}
                </div>
              </div>
              <p className="text-lg font-bold text-white mb-2">Ksh {(USE_HARDCODED_DATA ? HARDCODED.revenuePerformanceTotal : availableFunds).toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              {lineData.length === 0 ? (
                <p className="text-xs text-slate-400">No time-series data yet.</p>
              ) : (
                <div className="h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={lineData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                      <defs><linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#f97316" stopOpacity={0.4} /><stop offset="100%" stopColor="#f97316" stopOpacity={0} /></linearGradient></defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="month" stroke="#94a3b8" fontSize={10} />
                      <YAxis stroke="#94a3b8" fontSize={10} tickFormatter={(v) => `Ksh ${(v / 1000).toFixed(0)}k`} />
                      <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", fontSize: 11 }} formatter={(v: number) => [`Ksh ${Number(v).toLocaleString()}`, "Revenue"]} />
                      <Area type="monotone" dataKey="value" stroke="#f97316" strokeWidth={2} fill="url(#revGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column: 1/3 */}
        <div className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold text-white mb-2">Available funds</h3>
              <p className="text-lg font-bold text-white">Ksh {availableFunds.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              <p className="text-xs text-slate-400 mt-1">{USE_HARDCODED_DATA ? HARDCODED.nextPayout : "Subscriptions + placement"}</p>
              <div className="mt-3">
                <p className="text-xs text-slate-400 mb-1">Payout method</p>
                <div className="flex items-center gap-2 bg-slate-700/50 rounded px-2 py-1.5 text-sm text-slate-300">Card **** 9076</div>
              </div>
              <button className="mt-3 w-full py-2 rounded bg-slate-600 hover:bg-slate-500 text-white text-sm font-medium">Withdraw balance</button>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold text-white mb-2">Global revenue distribution</h3>
              {distribution.length === 0 ? (
                <p className="text-xs text-slate-400">No data yet.</p>
              ) : (
                <div className="space-y-1.5 max-h-36 overflow-y-auto">
                  {distribution.slice(0, 6).map((d: { country?: string; count?: number }) => (
                    <div key={d.country} className="flex justify-between text-xs py-1 border-b border-slate-700/50">
                      <span className="text-slate-300">{COUNTRY_NAMES[(d.country || "XX").toUpperCase()] || d.country}</span>
                      <span className="text-cyan-400 font-medium">{Number(d.count ?? 0).toLocaleString()} sales</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold text-white mb-2">Top performing markets</h3>
              {topMarkets.length === 0 ? (
                <p className="text-xs text-slate-400">No data yet.</p>
              ) : (
                <div className="space-y-2">
                  {topMarkets.map((m) => (
                    <div key={m.name} className="space-y-0.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-300">{m.name}</span>
                        <span className="text-slate-400">{m.count.toLocaleString()}</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full" style={{ width: `${(m.count / maxMarketCount) * 100}%`, backgroundColor: (m as { color?: string }).color || "#0ea5e9" }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Traffic-style bar (subscription revenue by month) - compact */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-4">
          <h3 className="text-sm font-semibold text-white mb-2">Traffic insights (Ksh)</h3>
          {lastMonths.length === 0 ? (
            <p className="text-xs text-slate-400">No data yet.</p>
          ) : (
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={lastMonths} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={10} />
                  <YAxis stroke="#94a3b8" fontSize={10} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", fontSize: 11 }} formatter={(v: number) => [`Ksh ${Number(v).toLocaleString()}`, "Revenue"]} />
                  <Bar dataKey="revenueKes" fill="#f97316" radius={[2, 2, 0, 0]} name="Revenue" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function RevenuePage() {
  return (
    <RouteGuard requiredRoles={["finance"]}>
      <RevenueContent />
    </RouteGuard>
  );
}
