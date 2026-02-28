import { Mail, MessageCircle, Globe, Phone, CheckCircle, XCircle, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useOrgId, useChannels } from "@/lib/useSupabase";

const typeToIcon: Record<string, typeof Mail> = {
  gmail: Mail,
  telegram: MessageCircle,
  webchat: Globe,
  whatsapp: Phone,
  phone: Phone,
};

const typeToLabel: Record<string, string> = {
  gmail: "Gmail",
  telegram: "Telegram",
  whatsapp: "WhatsApp",
  webchat: "Web Chat",
  phone: "Phone",
};

const ALL_CHANNEL_TYPES = ["gmail", "telegram", "whatsapp", "webchat", "phone"];

const Channels = () => {
  const { orgId, orgLoaded } = useOrgId();
  const { channels, loading } = useChannels(orgId, orgLoaded);

  // Build a set of connected types for easy lookup
  const connectedTypes = new Set(channels.map((ch) => ch.type));

  // Merge DB channels with the full static list
  const allChannels = ALL_CHANNEL_TYPES.map((type) => {
    const dbChannel = channels.find((ch) => ch.type === type);
    return {
      type,
      label: typeToLabel[type] ?? type,
      display_name: dbChannel?.display_name ?? null,
      status: dbChannel?.status ?? "not_connected",
      last_active_at: dbChannel?.last_active_at ?? null,
      id: dbChannel?.id ?? null,
    };
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Channels</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage multi-channel connections for case ingestion.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {allChannels.map((ch) => {
            const Icon = typeToIcon[ch.type] ?? Globe;
            const connected = ch.status === "active";
            const hasError = ch.status === "error";

            return (
              <div key={ch.type} className="flex items-center justify-between rounded-xl border bg-card p-5">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-lg ${connected ? "bg-accent" : "bg-secondary"
                      }`}
                  >
                    <Icon size={20} className={connected ? "text-accent-foreground" : "text-muted-foreground"} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">
                      {ch.display_name ?? ch.label}
                    </h3>
                    <div className="flex items-center gap-1 mt-0.5">
                      {connected ? (
                        <>
                          <CheckCircle size={12} className="text-success" />
                          <span className="text-xs text-success font-medium">Connected</span>
                          {ch.last_active_at && (
                            <span className="text-xs text-muted-foreground ml-1">
                              · Active {new Date(ch.last_active_at).toLocaleDateString()}
                            </span>
                          )}
                        </>
                      ) : hasError ? (
                        <>
                          <AlertCircle size={12} className="text-destructive" />
                          <span className="text-xs text-destructive font-medium">Error</span>
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
      )}

      {/* Webhook */}
      <div className="rounded-xl border bg-card p-5">
        <h3 className="text-sm font-semibold text-foreground mb-2">Webhook Endpoint</h3>
        <div className="flex items-center gap-2">
          <code className="flex-1 rounded-md bg-secondary px-3 py-2 text-xs font-mono text-muted-foreground break-all">
            {`${import.meta.env.VITE_SUPABASE_URL?.replace("/rest/v1", "") ?? "https://your-project.supabase.co"}/functions/v1/webhook-ingest`}
          </code>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const url = `${import.meta.env.VITE_SUPABASE_URL?.replace("/rest/v1", "") ?? ""}/functions/v1/webhook-ingest`;
              navigator.clipboard.writeText(url);
            }}
          >
            Copy
          </Button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Send POST requests to this endpoint to ingest cases from any external source.
        </p>
      </div>
    </div>
  );
};

export default Channels;
