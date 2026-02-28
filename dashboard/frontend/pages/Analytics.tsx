import { Loader2 } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from "recharts";
import { useOrgId, useUsageDaily } from "@/lib/useSupabase";

const Analytics = () => {
  const { orgId, orgLoaded } = useOrgId();
  const { usage, loading } = useUsageDaily(orgId, orgLoaded, 30);

  const conversationsTrend = usage.map((d) => ({
    date: new Date(d.usage_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    conversations: d.conversations_count,
    messages: d.messages_count,
  }));

  const escalationTrend = usage.map((d) => ({
    date: new Date(d.usage_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    rate:
      d.conversations_count > 0
        ? parseFloat(((d.escalations_count / d.conversations_count) * 100).toFixed(1))
        : 0,
  }));

  const toolUsage = usage.map((d) => ({
    date: new Date(d.usage_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    tool_calls: d.tool_calls_count,
    ai_messages: d.ai_message_count,
  }));

  const isEmpty = usage.length === 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">Track your platform's automation metrics — last 30 days.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-32">
          <Loader2 className="animate-spin text-muted-foreground" size={32} />
        </div>
      ) : isEmpty ? (
        <div className="rounded-xl border bg-card p-16 text-center">
          <p className="text-sm font-medium text-foreground">No usage data yet</p>
          <p className="text-sm text-muted-foreground mt-1">
            Analytics populate automatically as your AI agent handles conversations.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Conversations Over Time */}
          <div className="rounded-xl border bg-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Conversations Over Time</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={conversationsTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "hsl(220, 10%, 46%)" }} />
                <YAxis tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
                <Bar dataKey="conversations" name="Conversations" fill="hsl(24, 85%, 52%)" radius={[2, 2, 0, 0]} />
                <Bar dataKey="messages" name="Messages" fill="hsl(217, 91%, 60%)" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Escalation Rate Trend */}
          <div className="rounded-xl border bg-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Escalation Rate (%)</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={escalationTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "hsl(220, 10%, 46%)" }} />
                <YAxis tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} unit="%" />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
                <Line
                  type="monotone"
                  dataKey="rate"
                  name="Escalation %"
                  stroke="hsl(0, 72%, 51%)"
                  strokeWidth={2}
                  dot={{ fill: "hsl(0, 72%, 51%)", r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Tool Calls vs AI Messages */}
          <div className="rounded-xl border bg-card p-5 lg:col-span-2">
            <h3 className="text-sm font-semibold text-foreground mb-4">AI Activity — Tool Calls & AI Messages</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={toolUsage}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "hsl(220, 10%, 46%)" }} />
                <YAxis tick={{ fontSize: 12, fill: "hsl(220, 10%, 46%)" }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid hsl(220, 13%, 91%)", fontSize: 13 }} />
                <Bar dataKey="ai_messages" name="AI Messages" fill="hsl(38, 92%, 50%)" radius={[2, 2, 0, 0]} />
                <Bar dataKey="tool_calls" name="Tool Calls" fill="hsl(217, 91%, 60%)" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
