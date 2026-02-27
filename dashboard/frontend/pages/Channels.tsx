import { Mail, MessageCircle, Globe, Phone, CheckCircle, XCircle } from "lucide-react";
import { channels } from "@/data/mockData";
import { Button } from "@/components/ui/button";

const iconMap: Record<string, typeof Mail> = {
  Mail,
  MessageCircle,
  Globe,
  Phone,
};

const Channels = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Channels</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage multi-channel connections for case ingestion.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {channels.map((ch) => {
          const Icon = iconMap[ch.icon] || Globe;
          const connected = ch.status === "connected";
          return (
            <div key={ch.name} className="flex items-center justify-between rounded-xl border bg-card p-5">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${connected ? "bg-accent" : "bg-secondary"}`}>
                  <Icon size={20} className={connected ? "text-accent-foreground" : "text-muted-foreground"} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">{ch.name}</h3>
                  <div className="flex items-center gap-1 mt-0.5">
                    {connected ? (
                      <>
                        <CheckCircle size={12} className="text-success" />
                        <span className="text-xs text-success font-medium">Connected</span>
                      </>
                    ) : (
                      <>
                        <XCircle size={12} className="text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Not Connected</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <Button variant={connected ? "outline" : "default"} size="sm">
                {connected ? "Configure" : "Connect"}
              </Button>
            </div>
          );
        })}
      </div>

      {/* Webhook */}
      <div className="rounded-xl border bg-card p-5">
        <h3 className="text-sm font-semibold text-foreground mb-2">Webhook Endpoint</h3>
        <div className="flex items-center gap-2">
          <code className="flex-1 rounded-md bg-secondary px-3 py-2 text-xs font-mono text-muted-foreground">
            https://api.agentos.io/webhook/ingest/your-company-id
          </code>
          <Button variant="outline" size="sm">Copy</Button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">Send POST requests to this endpoint to ingest cases from any external source.</p>
      </div>
    </div>
  );
};

export default Channels;
