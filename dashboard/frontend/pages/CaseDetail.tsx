import { useNavigate } from "react-router-dom";
import { ArrowLeft, CheckCircle2, AlertTriangle, Cpu, FileText, Target } from "lucide-react";
import { caseDetail } from "@/data/mockData";

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

const CaseDetail = () => {
  const navigate = useNavigate();
  const c = caseDetail;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/cases")}
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
          <p className="text-sm text-muted-foreground">{c.customer} · {c.intent} · Confidence {c.confidence}%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Conversation Timeline */}
        <div className="lg:col-span-3 rounded-xl border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Conversation Timeline</h3>
          <div className="space-y-4">
            {c.conversation.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "customer" ? "justify-start" : "justify-end"}`}
              >
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${
                    msg.role === "customer"
                      ? "bg-secondary text-foreground rounded-bl-sm"
                      : "bg-primary text-primary-foreground rounded-br-sm"
                  }`}
                >
                  <p>{msg.message}</p>
                  <p className={`mt-1 text-[10px] ${msg.role === "customer" ? "text-muted-foreground" : "text-primary-foreground/70"}`}>
                    {msg.timestamp}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Execution Log */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border bg-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Execution Log</h3>
            <div className="space-y-3">
              {c.executionLog.map((step, i) => {
                const Icon = stepIcons[step.step] || Cpu;
                return (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent">
                        <Icon size={14} className="text-accent-foreground" />
                      </div>
                      {i < c.executionLog.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
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
                ["Customer ID", c.customerId],
                ["Intent", c.intent],
                ["Escalated", c.escalated ? "Yes" : "No"],
                ["Created", new Date(c.createdAt).toLocaleString()],
                ["Resolved", new Date(c.updatedAt).toLocaleString()],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between">
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
