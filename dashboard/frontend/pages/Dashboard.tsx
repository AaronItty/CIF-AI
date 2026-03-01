import { TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { useOrgId, useDashboardStats } from "@/hooks/useSupabase";
import { useEffect } from "react";
import { generateDailySummary } from "@/lib/reminderTriggers";

const statusClass: Record<string, string> = {
  active: "status-open",
  escalated: "status-escalated",
  resolved: "status-resolved",
  closed: "status-resolved",
};

const SAMPLE_CASES = [
  {
    id: "a1b2c3d4-0000-0000-0000-000000000001",
    users: { full_name: "Sarah Mitchell", email: "sarah.mitchell@example.com" },
    channels: { type: "web" },
    status: "active",
    ai_confidence_score: 0.87,
    updated_at: new Date(Date.now() - 4 * 60 * 1000).toISOString(),
  },
  {
    id: "b2c3d4e5-0000-0000-0000-000000000002",
    users: { full_name: "James Okonkwo", email: "james.okonkwo@example.com" },
    channels: { type: "email" },
    status: "escalated",
    ai_confidence_score: 0.54,
    updated_at: new Date(Date.now() - 22 * 60 * 1000).toISOString(),
  },
] as const;

const SAMPLE_STATS = {
  totalConversations: 2,
  autoResolvedPct: "50%",
  escalationRatePct: "50%",
  activeCount: 1,
  resolvedCount: 0,
  escalatedCount: 1,
  intentDistribution: [
    { name: "Billing", value: 1, fill: "hsl(24, 85%, 52%)" },
    { name: "Support", value: 1, fill: "hsl(262, 80%, 58%)" },
  ],
  recentConversations: SAMPLE_CASES as unknown as typeof SAMPLE_CASES[number][],
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { orgId, orgLoaded } = useOrgId();
  const { stats, loading } = useDashboardStats(orgId, orgLoaded);

  useEffect(() => {
    if (orgId && orgLoaded) {
      generateDailySummary(orgId);
    }
  }, [orgId, orgLoaded]);

  const effectiveStats = (stats && stats.totalConversations > 0) ? stats : (!loading ? SAMPLE_STATS : null);

  const kpiCards = effectiveStats
    ? [
      { label: "Total Cases", value: effectiveStats.totalConversations.toLocaleString(), trend: "", trendUp: true },
      { label: "Auto-Resolved", value: effectiveStats.autoResolvedPct, trend: "", trendUp: true },
      { label: "Escalation Rate", value: effectiveStats.escalationRatePct, trend: "", trendUp: false },
      { label: "Active Now", value: effectiveStats.activeCount.toLocaleString(), trend: "", trendUp: true },
    ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Overview</h1>
        <p className="text-sm text-muted-foreground mt-1">Monitor your AI agent performance at a glance.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="kpi-card animate-pulse">
              <div className="h-4 w-24 rounded bg-secondary mb-2" />
              <div className="h-8 w-16 rounded bg-secondary" />
            </div>
          ))
          : kpiCards.map((kpi) => (
            <div key={kpi.label} className="kpi-card">
              <p className="text-sm text-muted-foreground">{kpi.label}</p>
              <p className="mt-1 text-3xl font-bold text-foreground">{kpi.value}</p>
              <div className="mt-2 flex items-center gap-1 text-xs">
                {kpi.trendUp ? (
                  <TrendingUp size={14} className="text-success" />
                ) : (
                  <TrendingDown size={14} className="text-destructive" />
                )}
                <span className="text-muted-foreground">Live data</span>
              </div>
            </div>
          ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Intent Distribution */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Tag Distribution</h3>
          {loading ? (
            <div className="flex items-center justify-center h-60">
              <Loader2 className="animate-spin text-muted-foreground" />
            </div>
          ) : effectiveStats && effectiveStats.intentDistribution.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={effectiveStats.intentDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {effectiveStats.intentDistribution.map((entry, index) => (
                      <Cell key={index} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-2 flex flex-wrap gap-4 justify-center">
                {effectiveStats.intentDistribution.map((item) => (
                  <div key={item.name} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="h-2.5 w-2.5 rounded-full bg-dynamic" style={{ "--bg-color": item.fill } as React.CSSProperties} />
                    {item.name}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-60 text-sm text-muted-foreground italic">
              No tag data yet. Start conversations and tag them.
            </div>
          )}
        </div>

        {/* Conversation Status Breakdown */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Conversation Status Breakdown</h3>
          {loading ? (
            <div className="flex items-center justify-center h-60">
              <Loader2 className="animate-spin text-muted-foreground" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={[
                  { name: "Active", count: effectiveStats?.activeCount ?? 0 },
                  { name: "Resolved", count: effectiveStats?.resolvedCount ?? 0 },
                  { name: "Escalated", count: effectiveStats?.escalatedCount ?? 0 },
                ]}
                layout="vertical"
                margin={{ left: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(220, 13%, 91%)" />
                <XAxis type="number" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} width={80} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
                <Bar dataKey="count" fill="hsl(24, 85%, 52%)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent Cases */}
      <div className="rounded-xl border bg-card">
        <div className="flex items-center justify-between border-b p-5">
          <h3 className="text-sm font-semibold text-foreground">Recent Cases</h3>
          <button
            onClick={() => navigate("/cases")}
            className="text-xs font-medium text-primary hover:underline"
          >
            View All →
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-secondary/50">
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Case ID</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Customer</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Channel</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Confidence</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Updated</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-sm text-muted-foreground">
                    <Loader2 className="animate-spin mx-auto" />
                  </td>
                </tr>
              ) : effectiveStats && effectiveStats.recentConversations.length > 0 ? (
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (effectiveStats.recentConversations as any[]).map((c: any) => (
                  <tr
                    key={c.id}
                    className="cursor-pointer border-b last:border-0 transition-colors hover:bg-secondary/30"
                    onClick={() => navigate(`/cases/${c.id}`)}
                  >
                    <td className="px-5 py-3 font-mono text-xs font-medium">{c.id.slice(0, 8)}…</td>
                    <td className="px-5 py-3">{c.users?.full_name ?? c.users?.email ?? "—"}</td>
                    <td className="px-5 py-3 text-muted-foreground capitalize">{c.channels?.type ?? "—"}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusClass[c.status] ?? ""}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {c.ai_confidence_score != null ? (
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-16 rounded-full bg-secondary">
                            <div
                              className="h-1.5 rounded-full bg-primary w-dynamic"
                              style={{ "--width": `${(c.ai_confidence_score * 100).toFixed(0)}%` } as React.CSSProperties}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {(c.ai_confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-xs text-muted-foreground">
                      {new Date(c.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-sm text-muted-foreground italic">
                    No conversations yet. Your AI agent cases will appear here.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
