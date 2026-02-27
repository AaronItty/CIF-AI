import { TrendingUp, TrendingDown } from "lucide-react";
import { kpiData, intentDistribution, cases } from "@/data/mockData";
import { useNavigate } from "react-router-dom";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";

const statusClass: Record<string, string> = {
  Open: "status-open",
  "In Progress": "status-in-progress",
  Resolved: "status-resolved",
  Escalated: "status-escalated",
};

const Dashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Overview</h1>
        <p className="text-sm text-muted-foreground mt-1">Monitor your AI agent performance at a glance.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpiData.map((kpi) => (
          <div key={kpi.label} className="kpi-card">
            <p className="text-sm text-muted-foreground">{kpi.label}</p>
            <p className="mt-1 text-3xl font-bold text-foreground">{kpi.value}</p>
            <div className="mt-2 flex items-center gap-1 text-xs">
              {kpi.trendUp ? (
                <TrendingUp size={14} className="text-success" />
              ) : (
                <TrendingDown size={14} className="text-success" />
              )}
              <span className="text-success font-medium">{kpi.trend}</span>
              <span className="text-muted-foreground">vs last week</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Intent Distribution */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Intent Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={intentDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
              >
                {intentDistribution.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex flex-wrap gap-4 justify-center">
            {intentDistribution.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: item.fill }} />
                {item.name}
              </div>
            ))}
          </div>
        </div>

        {/* Skill Usage Preview */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Skill Executions (This Month)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={[
              { name: "get_order", count: 847 },
              { name: "check_policy", count: 623 },
              { name: "create_refund", count: 312 },
              { name: "replacement", count: 156 },
              { name: "escalate", count: 98 },
            ]} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(220, 13%, 91%)" />
              <XAxis type="number" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} width={100} />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
              <Bar dataKey="count" fill="hsl(24, 85%, 52%)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
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
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Intent</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Confidence</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Updated</th>
              </tr>
            </thead>
            <tbody>
              {cases.slice(0, 5).map((c) => (
                <tr
                  key={c.id}
                  className="cursor-pointer border-b last:border-0 transition-colors hover:bg-secondary/30"
                  onClick={() => navigate(`/cases/${c.id}`)}
                >
                  <td className="px-5 py-3 font-mono text-xs font-medium">{c.id}</td>
                  <td className="px-5 py-3">{c.customer}</td>
                  <td className="px-5 py-3 text-muted-foreground">{c.intent}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusClass[c.status]}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 rounded-full bg-secondary">
                        <div
                          className="h-1.5 rounded-full bg-primary"
                          style={{ width: `${c.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">{c.confidence}%</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-xs text-muted-foreground">
                    {new Date(c.updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
