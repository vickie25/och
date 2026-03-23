"use client";

import { Suspense, useState, useMemo, useRef, useEffect } from "react";
import { Card } from "@/components/ui/Card";
import { CardContent } from "@/components/ui/card-enhanced";
import { useAuth } from "@/hooks/useAuth";
import { FinanceDashboardSkeleton } from "../dashboard/components";
import { RouteGuard } from "@/components/auth/RouteGuard";
import {
  Filter,
  Download,
  Search,
  MoreVertical,
  Target,
  Users,
  ShoppingBag,
} from "lucide-react";
import useSWR from "swr";
import { Button } from "@/components/ui/Button";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export type SubscriptionRow = {
  id: string;
  type: "plan" | "sponsor_placement_fee";
  planName: string;
  ownerName: string;
  invoiceCount: number;
  totalRevenueKes: number;
  startedAt: string | null;
  nextBillingDate: string | null;
  raw?: Record<string, unknown>;
};

function buildRows(
  users: Array<{
    id?: string;
    plan_name?: string;
    plan_display_name?: string;
    user_name?: string;
    user_email?: string;
    price_monthly?: number;
    billing_interval?: string;
    current_period_start?: string | null;
    current_period_end?: string | null;
  }>,
  invoices: Array<{
    id?: string;
    sponsor_name?: string;
    net_amount?: number;
    billing_month?: string;
    created_at?: string;
  }>
): SubscriptionRow[] {
  const planRows: SubscriptionRow[] = (users || []).map((sub) => ({
    id: `sub-${sub.id}`,
    type: "plan",
    planName:
      sub.plan_display_name ||
      (sub.plan_name ? sub.plan_name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "Plan"),
    ownerName: sub.user_name || sub.user_email || "—",
    invoiceCount: 1,
    totalRevenueKes: Number(sub.price_monthly ?? 0),
    startedAt: sub.current_period_start || null,
    nextBillingDate: sub.current_period_end || null,
    raw: sub,
  }));

  const nextMonth = (monthStr: string) => {
    try {
      const d = new Date(monthStr + "-01");
      d.setMonth(d.getMonth() + 1);
      return d.toISOString().slice(0, 10);
    } catch {
      return null;
    }
  };

  const invoiceRows: SubscriptionRow[] = (invoices || []).map((inv) => ({
    id: `inv-${inv.id}`,
    type: "sponsor_placement_fee",
    planName: "Sponsor placement fee",
    ownerName: inv.sponsor_name || "—",
    invoiceCount: 1,
    totalRevenueKes: Number(inv.net_amount ?? 0),
    startedAt: inv.billing_month ? `${inv.billing_month}-01` : inv.created_at || null,
    nextBillingDate: inv.billing_month ? nextMonth(inv.billing_month.slice(0, 7)) : null,
    raw: inv,
  }));

  return [...planRows, ...invoiceRows];
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    return `Date: ${d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}, Time: ${d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}`;
  } catch {
    return formatDate(dateStr);
  }
}

function RowActionsMenu({ row }: { row: SubscriptionRow }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("click", onOutside);
    return () => document.removeEventListener("click", onOutside);
  }, [open]);
  return (
    <div className="relative" ref={ref}>
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-slate-400 hover:text-white"
        onClick={() => setOpen((o) => !o)}
      >
        <MoreVertical className="w-4 h-4" />
      </Button>
      {open && (
        <div className="absolute right-0 top-full mt-1 z-20 w-40 rounded-lg border border-slate-700 bg-slate-800 py-1 shadow-xl">
          <button
            type="button"
            className="block w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-700"
            onClick={() => setOpen(false)}
          >
            View details
          </button>
          <button
            type="button"
            className="block w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-700"
            onClick={() => setOpen(false)}
          >
            Export row
          </button>
        </div>
      )}
    </div>
  );
}

function SubscriptionsContent() {
  const { user } = useAuth();
  const userId = user?.id || "finance-user";

  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [filterPlanId, setFilterPlanId] = useState<string>("all");
  const [filterOpen, setFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!filterOpen) return;
    const onOutside = (e: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) setFilterOpen(false);
    };
    document.addEventListener("click", onOutside);
    return () => document.removeEventListener("click", onOutside);
  }, [filterOpen]);

  const { data: subscriptionsData } = useSWR(`/api/finance/${userId}/subscriptions`, fetcher);
  const { data: usersData } = useSWR(`/api/finance/${userId}/subscription-users`, fetcher);
  const { data: invoicesData } = useSWR(`/api/finance/${userId}/invoices`, fetcher);

  const plans = subscriptionsData?.plans || [];
  const users = Array.isArray(usersData) ? usersData : [];
  const invoices = Array.isArray(invoicesData?.invoices) ? invoicesData.invoices : [];

  const allRows = useMemo(() => buildRows(users, invoices), [users, invoices]);

  const filteredRows = useMemo(() => {
    let list = allRows;
    const q = searchQuery.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (r) =>
          r.planName.toLowerCase().includes(q) ||
          r.ownerName.toLowerCase().includes(q)
      );
    }
    if (filterType === "plan") {
      list = list.filter((r) => r.type === "plan");
    } else if (filterType === "sponsor_placement_fee") {
      list = list.filter((r) => r.type === "sponsor_placement_fee");
    }
    if (filterPlanId !== "all") {
      list = list.filter((r) => r.type === "plan" && (r.raw as any)?.plan_id === filterPlanId);
    }
    return list;
  }, [allRows, searchQuery, filterType, filterPlanId]);

  const totalSubscriptionCount = users.length;
  const totalInvoiceCount = invoices.length;
  const totalEntries = totalSubscriptionCount + totalInvoiceCount;

  const totalRevenueKes = useMemo(() => {
    return allRows.reduce((sum, r) => sum + r.totalRevenueKes, 0);
  }, [allRows]);

  const planBreakdown = useMemo(() => {
    const byPlan: Record<string, number> = {};
    plans.forEach((p: { name?: string; users?: number }) => {
      const name = p.name || "Other";
      byPlan[name] = Number(p.users ?? 0);
    });
    if (invoices.length > 0) {
      byPlan["Sponsor placement fee"] = invoices.length;
    }
    return byPlan;
  }, [plans, invoices.length]);

  const handleExport = () => {
    const headers = [
      "Plan / Source",
      "Owner Name",
      "Invoice Count",
      "Total Revenue (KES)",
      "Started At",
      "Next Billing Date",
    ];
    const rows = filteredRows.map((r) => [
      r.planName,
      r.ownerName,
      r.invoiceCount,
      r.totalRevenueKes.toFixed(2),
      r.startedAt ? formatDate(r.startedAt) : "—",
      r.nextBillingDate ? formatDate(r.nextBillingDate) : "—",
    ]);
    const csv = [headers.join(","), ...rows.map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `subscriptions_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-7xl py-4 px-4 sm:px-6 lg:px-8 mx-auto">
      <div className="mb-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-white">Subscriptions</h1>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by plan or owner..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-800 text-white pl-9 pr-4 py-2 rounded-lg border border-slate-700 focus:border-cyan-500 focus:outline-none text-sm w-56 sm:w-64"
            />
          </div>
          <div className="relative" ref={filterRef}>
            <Button
              variant="outline"
              size="sm"
              className="bg-slate-800 border-slate-700 text-white hover:bg-slate-700"
              onClick={() => setFilterOpen((o) => !o)}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </Button>
            {filterOpen && (
              <div className="absolute right-0 top-full mt-1 z-20 w-56 rounded-lg border border-slate-700 bg-slate-800 p-3 shadow-xl">
                <p className="text-xs text-slate-400 mb-2">Type</p>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full bg-slate-900 text-white text-sm rounded border border-slate-600 px-2 py-1.5 mb-3"
                >
                  <option value="all">All</option>
                  <option value="plan">Plan only</option>
                  <option value="sponsor_placement_fee">Sponsor placement fee only</option>
                </select>
                <p className="text-xs text-slate-400 mb-2">Plan</p>
                <select
                  value={filterPlanId}
                  onChange={(e) => setFilterPlanId(e.target.value)}
                  className="w-full bg-slate-900 text-white text-sm rounded border border-slate-600 px-2 py-1.5"
                >
                  <option value="all">All plans</option>
                  {plans.map((p: { id: string; name: string; catalog?: { display_name?: string } }) => (
                    <option key={p.id} value={p.id}>
                      {p.catalog?.display_name || p.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <Button
            size="sm"
            className="bg-cyan-500 hover:bg-cyan-600 text-white"
            onClick={handleExport}
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
        </div>
        <p className="text-sm text-slate-400 mt-2 max-w-3xl">
          Lists active and trial OCH student subscriptions from the same billing records as the student subscription page.
          Plan names show catalog labels when available; monthly amounts are in KES.
        </p>
      </div>

      <Suspense fallback={<FinanceDashboardSkeleton />}>
        {/* Three metric cards - compact */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1.5 rounded bg-orange-500/20">
                  <Target className="w-4 h-4 text-orange-500" />
                </div>
                <p className="text-xs text-slate-400">Total Subscriptions</p>
              </div>
              <p className="text-xl font-bold text-white">{totalEntries}</p>
              <div className="mt-1.5 h-5 flex items-end gap-0.5">
                {[2, 4, 3, 5, 4, 6].map((h, i) => (
                  <div key={i} className="w-1 bg-orange-500/50 rounded-t" style={{ height: `${h * 3}px` }} />
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1.5 rounded bg-orange-500/20">
                  <Users className="w-4 h-4 text-orange-500" />
                </div>
                <p className="text-xs text-slate-400">By plan / source</p>
              </div>
              <p className="text-xl font-bold text-white">{totalEntries}</p>
              <div className="mt-1.5 space-y-0.5 text-xs text-slate-300">
                {Object.entries(planBreakdown).map(([name, count]) => (
                  <div key={name}>{name}: {count}</div>
                ))}
                {Object.keys(planBreakdown).length === 0 && <span className="text-slate-500">No data</span>}
              </div>
              <div className="mt-1.5 h-5 flex items-end gap-0.5">
                {[3, 5, 2, 4].map((h, i) => (
                  <div key={i} className="w-1 bg-orange-500/50 rounded-t" style={{ height: `${h * 3}px` }} />
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <div className="p-1.5 rounded bg-orange-500/20">
                  <ShoppingBag className="w-4 h-4 text-orange-500" />
                </div>
                <p className="text-xs text-slate-400">Total Revenue</p>
              </div>
              <p className="text-xl font-bold text-white">
                KES {totalRevenueKes.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <div className="mt-1.5 h-5 flex items-end gap-0.5">
                {[4, 3, 5, 4, 6, 5].map((h, i) => (
                  <div key={i} className="w-1 bg-orange-500/50 rounded-t" style={{ height: `${h * 3}px` }} />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Table - compact */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left text-xs font-medium text-slate-400 py-3 px-3">Plan / Source</th>
                    <th className="text-left text-xs font-medium text-slate-400 py-3 px-3">Owner Name</th>
                    <th className="text-left text-xs font-medium text-slate-400 py-3 px-3">Invoice Count</th>
                    <th className="text-left text-xs font-medium text-slate-400 py-3 px-3">Total Revenue</th>
                    <th className="text-left text-xs font-medium text-slate-400 py-3 px-3">Started At</th>
                    <th className="text-left text-xs font-medium text-slate-400 py-3 px-3">Next Billing Date</th>
                    <th className="w-10 py-3 px-2" />
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400 text-sm">
                        No subscriptions match your filters.
                      </td>
                    </tr>
                  ) : (
                    filteredRows.map((row) => (
                      <tr key={row.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                        <td className="py-2 px-3 text-white font-medium text-sm">{row.planName}</td>
                        <td className="py-2 px-3 text-slate-300 text-sm">{row.ownerName}</td>
                        <td className="py-2 px-3 text-slate-300 text-sm">{row.invoiceCount}</td>
                        <td className="py-2 px-3 text-white font-medium text-sm">
                          KES {row.totalRevenueKes.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2 px-3 text-slate-400 text-xs">{formatDateTime(row.startedAt)}</td>
                        <td className="py-2 px-3 text-slate-400 text-xs">{formatDateTime(row.nextBillingDate)}</td>
                        <td className="py-2 px-2">
                          <RowActionsMenu row={row} />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </Suspense>
    </div>
  );
}

export default function SubscriptionsPage() {
  return (
    <RouteGuard requiredRoles={["finance"]}>
      <SubscriptionsContent />
    </RouteGuard>
  );
}
