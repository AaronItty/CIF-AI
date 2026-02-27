import { analyticsData } from "@/data/mockData";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell,
} from "recharts";

const colors = ["hsl(24, 85%, 52%)", "hsl(38, 92%, 50%)", "hsl(0, 72%, 51%)", "hsl(217, 91%, 60%)"];

const Analytics = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">Track your platform's automation metrics.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Intent Frequency */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Intent Frequency Over Time</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={analyticsData.intentFrequency}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
              <YAxis tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
              <Bar dataKey="orderTracking" name="Order Tracking" fill={colors[0]} radius={[2, 2, 0, 0]} />
              <Bar dataKey="refund" name="Refund" fill={colors[1]} radius={[2, 2, 0, 0]} />
              <Bar dataKey="complaint" name="Complaint" fill={colors[2]} radius={[2, 2, 0, 0]} />
              <Bar dataKey="productQuery" name="Product Query" fill={colors[3]} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Escalation Trend */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Escalation Rate Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={analyticsData.escalationTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
              <YAxis tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} unit="%" />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
              <Line type="monotone" dataKey="rate" stroke="hsl(24, 85%, 52%)" strokeWidth={2} dot={{ fill: "hsl(24, 85%, 52%)", r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Resolution Time */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Resolution Time Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={analyticsData.resolutionTime}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
              <XAxis dataKey="range" tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
              <YAxis tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
              <Bar dataKey="count" fill="hsl(24, 85%, 52%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Skill Usage */}
        <div className="rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Skill Usage Frequency</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={analyticsData.skillUsage} cx="50%" cy="50%" outerRadius={100} innerRadius={55} dataKey="count" paddingAngle={3}>
                {analyticsData.skillUsage.map((_, i) => (
                  <Cell key={i} fill={colors[i % colors.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex flex-wrap gap-3 justify-center">
            {analyticsData.skillUsage.map((s, i) => (
              <div key={s.name} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="h-2 w-2 rounded-full" style={{ background: colors[i % colors.length] }} />
                {s.name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
