import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, AlertTriangle, Cpu, FileText, Target, Loader2, Mail, MessageSquare, Globe } from "lucide-react";
import { useCaseDetail } from "@/hooks/useSupabase";
import { format } from "date-fns";

const statusClass: Record<string, string> = {
  Resolved: "status-resolved",
  Escalated: "status-escalated",
  "In Progress": "status-in-progress",
  Open: "status-open",
};

const stepIcons: Record<string, typeof Target> = {
  "Intent Classified": Target,
  "Skill Executed": Cpu,
  "Policy Retrieved": FileText,
  "Case Resolved": CheckCircle2,
};

const channelIcons: Record<string, typeof Mail> = {
  email: Mail,
  gmail: Mail,
  web: Globe,
  telegram: MessageSquare,
};

const CaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { conversation: c, loading } = useCaseDetail(id);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!c) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-8 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-destructive mb-2" />
        <h3 className="text-lg font-semibold text-foreground">Case Not Found</h3>
        <p className="text-sm text-muted-foreground mt-1">
          The case ID could not be found or you don't have access.
        </p>
        <button
          onClick={() => navigate("/cases")}
          className="mt-4 text-sm font-medium text-primary hover:underline"
        >
          Return to Cases
        </button>
      </div>
    );
  }

  // Fallback for execution log if not present in metadata
  const executionLog = (c.metadata as any)?.execution_log || [
    { step: "Intent Classified", detail: "Customer query categorized successfully", confidence: c.ai_confidence_score || 0.95 },
    { step: "Case Logged", detail: "Interaction saved to database", timestamp: c.created_at }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/cases")}
          title="Back to Cases"
          className="flex h-8 w-8 items-center justify-center rounded-lg border bg-card transition-colors hover:bg-secondary"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-foreground">{c.id}</h1>
            <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusClass[c.status]}`}>
              {c.status}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            {c.users?.full_name ?? "Anonymous Customer"} · {c.channels?.display_name ?? c.channels?.type ?? "Web Chat"} · Confidence {c.ai_confidence_score != null ? `${(c.ai_confidence_score * 100).toFixed(0)}%` : "N/A"}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Conversation Timeline */}
        <div className="lg:col-span-3 rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Conversation Timeline</h3>
          <div className="space-y-4">
            {c.messages && c.messages.length > 0 ? (
              c.messages.map((msg, i) => (
                <div
                  key={msg.id || i}
                  className={`flex ${msg.role === "user" ? "justify-start" : "justify-end"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${msg.role === "user"
                      ? "bg-secondary text-foreground rounded-bl-sm"
                      : "bg-primary text-primary-foreground rounded-br-sm"
                      }`}
                  >
                    <p>{msg.content}</p>
                    <p className={`mt-1 text-[10px] ${msg.role === "user" ? "text-muted-foreground" : "text-primary-foreground/70"}`}>
                      {format(new Date(msg.created_at), "MMM d, h:mm a")}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-sm text-muted-foreground italic">
                No messages found for this case.
              </div>
            )}
          </div>
        </div>

        {/* Execution Log */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border bg-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Execution Log</h3>
            <div className="space-y-3">
              {executionLog.map((step: any, i: number) => {
                const Icon = stepIcons[step.step] || Cpu;
                return (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent">
                        <Icon size={14} className="text-accent-foreground" />
                      </div>
                      {i < executionLog.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
                    </div>
                    <div className="pb-3">
                      <p className="text-xs font-semibold text-foreground">{step.step}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{step.detail}</p>
                      {step.output && (
                        <pre className="mt-1.5 rounded-md bg-secondary p-2 text-[11px] font-mono text-muted-foreground overflow-x-auto">
                          {step.output}
                        </pre>
                      )}
                      {step.confidence !== undefined && (
                        <p className="mt-1 text-[11px] text-muted-foreground">Confidence: {step.confidence}</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Metadata */}
          <div className="rounded-xl border bg-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-3">Case Metadata</h3>
            <dl className="space-y-2 text-sm">
              {[
                ["Customer", c.users?.full_name ?? c.users?.email ?? "Anonymous"],
                ["Channel", (
                  <span className="flex items-center gap-2">
                    {(() => {
                      const Icon = channelIcons[c.channels?.type?.toLowerCase() || "web"] || Globe;
                      return <Icon size={14} className="text-muted-foreground" />;
                    })()}
                    <span className="capitalize">{c.channels?.display_name || c.channels?.type || "Web"}</span>
                  </span>
                )],
                ["Escalated", c.status === "escalated" ? "Yes" : "No"],
                ["Created", format(new Date(c.created_at), "MMM d, h:mm a")],
                ["Last Activity", format(new Date(c.updated_at), "MMM d, h:mm a")],
              ].map(([k, v]) => (
                <div key={k as string} className="flex justify-between items-center">
                  <dt className="text-muted-foreground">{k}</dt>
                  <dd className="font-medium text-foreground">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CaseDetail;
