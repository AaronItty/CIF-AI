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

    useEffect(() => {
        supabase
            .from("organizations")
            .select("id")
            .limit(1)
            .single()
            .then(({ data }) => {
                if (data) setOrgId(data.id);
            });
    }, []);

    return orgId;
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

export function useDashboardStats(orgId: string | null) {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgId) return;

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

export function useConversations(orgId: string | null) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgId) return;

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

export function useUsageDaily(orgId: string | null, daysBack = 30) {
    const [usage, setUsage] = useState<UsageDay[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgId) return;

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

export function useChannels(orgId: string | null) {
    const [channels, setChannels] = useState<ChannelRow[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgId) return;

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
