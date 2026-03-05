import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Filter, Loader2 } from "lucide-react";
import { useOrgId, useConversations } from "@/hooks/useSupabase";
import { useSearch } from "@/context/SearchContext";

const statusClass: Record<string, string> = {
  active: "status-open",
  escalated: "status-escalated",
  resolved: "status-resolved",
  closed: "status-resolved",
};

const DB_STATUSES = ["All", "active", "escalated", "resolved", "closed"];

const SAMPLE_CASES = [
  {
    id: "a1b2c3d4-0000-0000-0000-000000000001",
    users: { full_name: "Sarah Mitchell", email: "sarah.mitchell@example.com" },
    channels: { type: "web", display_name: "Web Chat" },
    status: "active",
    ai_confidence_score: 0.87,
    message_count: 6,
    created_at: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 4 * 60 * 1000).toISOString(),
  },
  {
    id: "b2c3d4e5-0000-0000-0000-000000000002",
    users: { full_name: "James Okonkwo", email: "james.okonkwo@example.com" },
    channels: { type: "email", display_name: "Email" },
    status: "escalated",
    ai_confidence_score: 0.54,
    message_count: 11,
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 22 * 60 * 1000).toISOString(),
  },
];

const Cases = () => {
  const navigate = useNavigate();
  const { orgId, orgLoaded } = useOrgId();
  const { conversations, loading } = useConversations(orgId, orgLoaded);
  const { searchQuery } = useSearch();

  const [statusFilter, setStatusFilter] = useState("All");

  // Use sample cases when no real data is available yet
  const effectiveConversations = conversations;

  const filtered = useMemo(() => {
    return effectiveConversations.filter((c) => {
      if (statusFilter !== "All" && c.status !== statusFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const nameMatch = c.users?.full_name?.toLowerCase().includes(q);
        const emailMatch = c.users?.email?.toLowerCase().includes(q);
        const idMatch = c.id.toLowerCase().includes(q);
        if (!nameMatch && !emailMatch && !idMatch) return false;
      }
      return true;
    });
  }, [effectiveConversations, statusFilter, searchQuery]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Cases</h1>
        <p className="text-sm text-muted-foreground mt-1">View and manage all active and historical cases.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5">
          <Filter size={14} className="text-muted-foreground" />
          {DB_STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors ${statusFilter === s
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-muted-foreground hover:text-foreground"
                }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-secondary/50">
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Case ID</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Customer</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Channel</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Confidence</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Messages</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center">
                    <Loader2 className="animate-spin mx-auto text-muted-foreground" />
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-sm text-muted-foreground italic">
                    No cases match your filters.
                  </td>
                </tr>
              ) : (
                filtered.map((c) => (
                  <tr
                    key={c.id}
                    className="cursor-pointer border-b last:border-0 transition-colors hover:bg-secondary/30"
                    onClick={() => navigate(`/cases/${c.id}`)}
                  >
                    <td className="px-5 py-3 font-mono text-xs font-medium">{c.id.slice(0, 8)}…</td>
                    <td className="px-5 py-3">
                      <div className="flex flex-col">
                        <span className="font-medium">{c.users?.full_name ?? c.users?.email ?? "Anonymous"}</span>
                        {c.summary && <span className="text-[10px] text-muted-foreground truncate max-w-[200px]">{c.summary}</span>}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-muted-foreground capitalize">
                      {c.channels?.display_name ?? c.channels?.type ?? "—"}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${statusClass[c.status] ?? ""}`}>
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
                    <td className="px-5 py-3 text-xs text-muted-foreground">{c.message_count}</td>
                    <td className="px-5 py-3 text-xs text-muted-foreground">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Cases;
