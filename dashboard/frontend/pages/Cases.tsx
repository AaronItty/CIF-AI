import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cases } from "@/data/mockData";

const statusClass: Record<string, string> = {
  Open: "status-open",
  "In Progress": "status-in-progress",
  Resolved: "status-resolved",
  Escalated: "status-escalated",
};

const statuses = ["All", "Open", "In Progress", "Resolved", "Escalated"];
const intents = ["All", "Order Tracking", "Refund Request", "Complaint", "Product Query"];

const Cases = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("All");
  const [intentFilter, setIntentFilter] = useState("All");
  const [search, setSearch] = useState("");

  const filtered = cases.filter((c) => {
    if (statusFilter !== "All" && c.status !== statusFilter) return false;
    if (intentFilter !== "All" && c.intent !== intentFilter) return false;
    if (search && !c.id.toLowerCase().includes(search.toLowerCase()) && !c.customer.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Cases</h1>
        <p className="text-sm text-muted-foreground mt-1">View and manage all active and historical cases.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search cases..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 pl-9 bg-card border text-sm"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter size={14} className="text-muted-foreground" />
          {statuses.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === s
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-muted-foreground hover:text-foreground"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <select
          value={intentFilter}
          onChange={(e) => setIntentFilter(e.target.value)}
          className="h-9 rounded-lg border bg-card px-3 text-sm text-foreground"
        >
          {intents.map((i) => (
            <option key={i} value={i}>{i === "All" ? "All Intents" : i}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-secondary/50">
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Case ID</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Customer</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Intent</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Confidence</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Escalated</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
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
                        <div className="h-1.5 rounded-full bg-primary" style={{ width: `${c.confidence}%` }} />
                      </div>
                      <span className="text-xs text-muted-foreground">{c.confidence}%</span>
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    {c.escalated && <span className="text-xs font-medium text-destructive">⚠ Yes</span>}
                    {!c.escalated && <span className="text-xs text-muted-foreground">No</span>}
                  </td>
                  <td className="px-5 py-3 text-xs text-muted-foreground">
                    {new Date(c.createdAt).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="py-12 text-center text-sm text-muted-foreground">No cases match your filters.</div>
        )}
      </div>
    </div>
  );
};

export default Cases;
