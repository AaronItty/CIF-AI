/**
 * Shared Supabase data hooks for the dashboard.
 * All pages import from here — never query Supabase directly in pages.
 */
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface Conversation {
    id: string;
    status: string;
    ai_confidence_score: number | null;
    tags: string[] | null;
    created_at: string;
    updated_at: string;
    escalated_at: string | null;
    resolved_at: string | null;
    message_count: number;
    users?: { full_name: string | null; email: string | null };
    channels?: { type: string; display_name: string | null };
    messages?: Message[];
    metadata: any;
}

export interface Message {
    id: string;
    role: "customer" | "assistant" | "system";
    content: string;
    created_at: string;
}

export interface ChannelRow {
    id: string;
    type: string;
    display_name: string | null;
    status: string;
    last_active_at: string | null;
}

export interface UsageDay {
    usage_date: string;
    conversations_count: number;
    escalations_count: number;
    messages_count: number;
    tool_calls_count: number;
    ai_message_count: number;
}

// ─── useOrgId ────────────────────────────────────────────────────────────────
// Fetches the first org ID from the DB (or returns null while loading)

export function useOrgId() {
    const [orgId, setOrgId] = useState<string | null>(null);
    const [orgLoaded, setOrgLoaded] = useState(false);

    useEffect(() => {
        supabase
            .from("organizations")
            .select("id")
            .limit(1)
            .maybeSingle()
            .then(({ data }) => {
                if (data) setOrgId(data.id);
            })
            .finally(() => setOrgLoaded(true));
    }, []);

    return { orgId, orgLoaded };
}

// ─── useDashboardStats ───────────────────────────────────────────────────────

export interface DashboardStats {
    totalConversations: number;
    resolvedCount: number;
    escalatedCount: number;
    activeCount: number;
    autoResolvedPct: string;
    escalationRatePct: string;
    recentConversations: Conversation[];
    intentDistribution: { name: string; value: number; fill: string }[];
}

const COLORS = [
    "hsl(24, 85%, 52%)",
    "hsl(38, 92%, 50%)",
    "hsl(0, 72%, 51%)",
    "hsl(217, 91%, 60%)",
];

export function useDashboardStats(orgId: string | null, orgLoaded: boolean) {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgLoaded) return;
        if (!orgId) { setLoading(false); return; }

        const fetchStats = async () => {
            setLoading(true);
            try {
                // Recent conversations for the table
                const { data: recent } = await supabase
                    .from("conversations")
                    .select("*, users(full_name, email), channels(type, display_name)")
                    .eq("organization_id", orgId)
                    .order("created_at", { ascending: false })
                    .limit(5);

                // All conversations for counts
                const { data: all } = await supabase
                    .from("conversations")
                    .select("status, tags, ai_confidence_score")
                    .eq("organization_id", orgId);

                const total = all?.length ?? 0;
                const resolved = all?.filter((c) => c.status === "resolved").length ?? 0;
                const escalated = all?.filter((c) => c.status === "escalated").length ?? 0;
                const active = all?.filter((c) => c.status === "active").length ?? 0;

                // Build intent distribution from tags
                const tagCounts: Record<string, number> = {};
                all?.forEach((c) => {
                    (c.tags ?? []).forEach((tag: string) => {
                        tagCounts[tag] = (tagCounts[tag] ?? 0) + 1;
                    });
                });
                const intentDistribution = Object.entries(tagCounts)
                    .slice(0, 6)
                    .map(([name, value], i) => ({
                        name,
                        value,
                        fill: COLORS[i % COLORS.length],
                    }));

                setStats({
                    totalConversations: total,
                    resolvedCount: resolved,
                    escalatedCount: escalated,
                    activeCount: active,
                    autoResolvedPct: total > 0 ? ((resolved / total) * 100).toFixed(1) + "%" : "0%",
                    escalationRatePct: total > 0 ? ((escalated / total) * 100).toFixed(1) + "%" : "0%",
                    recentConversations: (recent ?? []) as Conversation[],
                    intentDistribution,
                });
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, [orgId]);

    return { stats, loading };
}

// ─── useConversations ────────────────────────────────────────────────────────

export function useConversations(orgId: string | null, orgLoaded = false) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgLoaded) return;
        if (!orgId) { setLoading(false); return; }

        const fetchAll = async () => {
            setLoading(true);
            try {
                const { data } = await supabase
                    .from("conversations")
                    .select("*, users(full_name, email), channels(type, display_name)")
                    .eq("organization_id", orgId)
                    .order("created_at", { ascending: false });

                setConversations((data ?? []) as Conversation[]);
            } finally {
                setLoading(false);
            }
        };

        fetchAll();
    }, [orgId]);

    return { conversations, loading };
}

// ─── useUsageDaily ───────────────────────────────────────────────────────────

export function useUsageDaily(orgId: string | null, orgLoaded = false, daysBack = 30) {
    const [usage, setUsage] = useState<UsageDay[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgLoaded) return;
        if (!orgId) { setLoading(false); return; }

        const sinceDate = new Date();
        sinceDate.setDate(sinceDate.getDate() - daysBack);
        const since = sinceDate.toISOString().split("T")[0];

        const fetchUsage = async () => {
            setLoading(true);
            try {
                const { data } = await supabase
                    .from("organization_usage_daily")
                    .select(
                        "usage_date,conversations_count,escalations_count,messages_count,tool_calls_count,ai_message_count"
                    )
                    .eq("organization_id", orgId)
                    .gte("usage_date", since)
                    .order("usage_date");

                setUsage((data ?? []) as UsageDay[]);
            } finally {
                setLoading(false);
            }
        };

        fetchUsage();
    }, [orgId, daysBack]);

    return { usage, loading };
}

// ─── useChannels ─────────────────────────────────────────────────────────────

export function useChannels(orgId: string | null, orgLoaded = false) {
    const [channels, setChannels] = useState<ChannelRow[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgLoaded) return;
        if (!orgId) { setLoading(false); return; }

        const fetchChannels = async () => {
            setLoading(true);
            try {
                const { data } = await supabase
                    .from("channels")
                    .select("id,type,display_name,status,last_active_at")
                    .eq("organization_id", orgId)
                    .order("type");

                setChannels((data ?? []) as ChannelRow[]);
            } finally {
                setLoading(false);
            }
        };

        fetchChannels();
    }, [orgId]);

    return { channels, loading };
}

// ─── useReminders ────────────────────────────────────────────────────────────

export interface Reminder {
    id: string;
    type: "escalation" | "system" | "daily_summary" | "priority_case";
    title: string;
    description: string | null;
    link: string | null;
    is_read: boolean;
    created_at: string;
}

export function useReminders(orgId: string | null, orgLoaded = false) {
    const [reminders, setReminders] = useState<Reminder[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchReminders = async () => {
        if (!orgId) return;
        setLoading(true);
        try {
            const { data } = await supabase
                .from("reminders")
                .select("*")
                .eq("organization_id", orgId)
                .order("created_at", { ascending: false });

            setReminders((data ?? []) as Reminder[]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!orgLoaded || !orgId) {
            if (orgLoaded) setLoading(false);
            return;
        }

        fetchReminders();

        // Real-time subscription
        const channel = supabase
            .channel("reminders_changes")
            .on(
                "postgres_changes",
                {
                    event: "*",
                    schema: "public",
                    table: "reminders",
                    filter: `organization_id=eq.${orgId}`,
                },
                () => {
                    fetchReminders();
                }
            )
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, [orgId, orgLoaded]);

    const markAsRead = async (id: string) => {
        await supabase.from("reminders").update({ is_read: true }).eq("id", id);
        setReminders((prev) =>
            prev.map((r) => (r.id === id ? { ...r, is_read: true } : r))
        );
    };

    const markAllAsRead = async () => {
        if (!orgId) return;
        await supabase
            .from("reminders")
            .update({ is_read: true })
            .eq("organization_id", orgId)
            .eq("is_read", false);
        setReminders((prev) => prev.map((r) => ({ ...r, is_read: true })));
    };

    const clearAll = async () => {
        if (!orgId) return;
        await supabase.from("reminders").delete().eq("organization_id", orgId);
        setReminders([]);
    };

    return { reminders, loading, markAsRead, markAllAsRead, clearAll };
}

// ─── useCaseDetail ───────────────────────────────────────────────────────────

export function useCaseDetail(caseId: string | undefined) {
    const [conversation, setConversation] = useState<Conversation | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!caseId) {
            setLoading(false);
            return;
        }

        const fetchDetail = async () => {
            setLoading(true);
            try {
                // Fetch conversation with messages. 
                // Note: database uses 'session_id' as the FK for messages.
                const { data, error } = await supabase
                    .from("conversations")
                    .select("*, users(full_name, email), channels(type, display_name), messages!session_id(*)")
                    .eq("id", caseId)
                    .single();

                if (error) {
                    console.error("Error fetching case detail:", error);
                    setConversation(null);
                } else {
                    // Sort messages by creation date
                    if (data.messages) {
                        data.messages.sort((a: Message, b: Message) =>
                            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                        );
                    }
                    setConversation(data as Conversation);
                }
            } finally {
                setLoading(false);
            }
        };

        fetchDetail();
    }, [caseId]);

    return { conversation, loading };
}
