/**
 * Shared API data hooks for the dashboard.
 * All pages import from here — never query the database directly in pages.
 * Fully Refactored to Phase 3: Pure API Consumer based on HTTP Fetch.
 */
import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000/api/dashboard";

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
    role: "user" | "customer" | "assistant" | "system";
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
        fetch(`${API_BASE}/org`)
            .then((res) => res.json())
            .then((data) => {
                if (data && data.id) setOrgId(data.id);
            })
            .catch((err) => console.error("Error fetching orgId", err))
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

export function useDashboardStats(orgId: string | null, orgLoaded: boolean) {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgLoaded) return;
        if (!orgId) { setLoading(false); return; }

        const fetchStats = async () => {
            setLoading(true);
            try {
                const res = await fetch(`${API_BASE}/stats/${orgId}`);
                if (res.ok) {
                    const data = await res.json();
                    setStats(data);
                }
            } catch (err) {
                console.error("Error fetching dashboard stats", err);
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
                const res = await fetch(`${API_BASE}/conversations/${orgId}`);
                if (res.ok) {
                    const data = await res.json();
                    setConversations(data || []);
                }
            } catch (err) {
                console.error("Error fetching conversations", err);
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

        const fetchUsage = async () => {
            setLoading(true);
            try {
                const res = await fetch(`${API_BASE}/usage/${orgId}?days_back=${daysBack}`);
                if (res.ok) {
                    const data = await res.json();
                    setUsage(data || []);
                }
            } catch (err) {
                console.error("Error fetching usage daily", err);
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
                const res = await fetch(`${API_BASE}/channels/${orgId}`);
                if (res.ok) {
                    const data = await res.json();
                    setChannels(data || []);
                }
            } catch (err) {
                console.error("Error fetching channels", err);
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
            const res = await fetch(`${API_BASE}/reminders/${orgId}`);
            if (res.ok) {
                const data = await res.json();
                setReminders(data || []);
            }
        } catch (err) {
            console.error("Error fetching reminders", err);
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

        // Polling approach (replacing realtime Supabase subscription)
        const intervalId = setInterval(() => {
            fetchReminders();
        }, 10000); // Poll every 10 seconds

        return () => {
            clearInterval(intervalId);
        };
    }, [orgId, orgLoaded]);

    const markAsRead = async (id: string) => {
        try {
            await fetch(`${API_BASE}/reminders/${id}/read`, { method: "PUT" });
            setReminders((prev) =>
                prev.map((r) => (r.id === id ? { ...r, is_read: true } : r))
            );
        } catch (err) {
            console.error("Error marking reminder read", err);
        }
    };

    const markAllAsRead = async () => {
        if (!orgId) return;
        try {
            await fetch(`${API_BASE}/reminders/org/${orgId}/read-all`, { method: "PUT" });
            setReminders((prev) => prev.map((r) => ({ ...r, is_read: true })));
        } catch (err) {
            console.error("Error marking all reminders read", err);
        }
    };

    const clearAll = async () => {
        if (!orgId) return;
        try {
            await fetch(`${API_BASE}/reminders/org/${orgId}`, { method: "DELETE" });
            setReminders([]);
        } catch (err) {
            console.error("Error clearing reminders", err);
        }
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
                const res = await fetch(`${API_BASE}/cases/${caseId}`);
                if (res.ok) {
                    const data = await res.json();
                    setConversation(data);
                } else {
                    setConversation(null);
                }
            } catch (err) {
                console.error("Error fetching case detail", err);
                setConversation(null);
            } finally {
                setLoading(false);
            }
        };

        fetchDetail();
    }, [caseId]);

    return { conversation, loading };
}
