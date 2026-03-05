/**
 * Triggers a reminder in the database via the backend API.
 */

const API_BASE = "http://localhost:8000/api/dashboard";

export const triggerEscalationReminder = async (orgId: string, conversationId: string, customerName: string) => {
    await fetch(`${API_BASE}/reminders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            organization_id: orgId,
            type: "escalation",
            title: "New Escalation Required",
            description: `Customer ${customerName} is waiting for human intervention.`,
            link: `/cases/${conversationId}`,
        })
    });
};

export const triggerPriorityReminder = async (orgId: string, conversationId: string, score: number) => {
    if (score < 0.3) { // High uncertainty
        await fetch(`${API_BASE}/reminders`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                organization_id: orgId,
                type: "priority_case",
                title: "High Uncertainty Case",
                description: `AI confidence is very low (${(score * 100).toFixed(0)}%). Please review.`,
                link: `/cases/${conversationId}`,
            })
        });
    }
};

/**
 * Generates a "Daily Summary" reminder.
 */
export const generateDailySummary = async (orgId: string) => {
    // 1. Check if we already created a summary today to avoid duplicates
    const remindersRes = await fetch(`${API_BASE}/reminders/${orgId}`);
    if (remindersRes.ok) {
        const existingReminders = await remindersRes.json();
        const today = new Date().toISOString().split('T')[0];
        const hasTodaySummary = existingReminders.some((r: any) =>
            r.type === "daily_summary" && r.created_at.startsWith(today)
        );
        if (hasTodaySummary) return;
    }

    // 2. Fetch conversations to calculate summary
    const res = await fetch(`${API_BASE}/conversations/${orgId}`);
    if (!res.ok) return;
    const conversations = await res.json();

    if (!conversations || conversations.length === 0) return;

    const active = conversations.filter((c: any) => c.status === "active").length;
    const escalated = conversations.filter((c: any) => c.status === "escalated").length;

    if (active === 0 && escalated === 0) return;

    const hour = new Date().getHours();
    let title = "Daily Morning Brief";
    if (hour >= 12 && hour < 17) title = "Afternoon Update";
    if (hour >= 17) title = "Evening Review";

    await fetch(`${API_BASE}/reminders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            organization_id: orgId,
            type: "daily_summary",
            title,
            description: `You have ${active} active cases and ${escalated} pending escalations waiting for you.`,
            link: "/cases",
        })
    });
};

/**
 * Checks for cases that haven't been updated in over 24 hours.
 */
export const checkStaleCases = async (orgId: string) => {
    const res = await fetch(`${API_BASE}/conversations/${orgId}`);
    if (!res.ok) return;
    const conversations = await res.json();

    if (!conversations) return;

    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const staleCases = conversations.filter((c: any) =>
        c.status === "active" && new Date(c.updated_at) < oneDayAgo
    );

    if (staleCases.length > 0) {
        // Only trigger if no stale case reminder exists from today
        const remindersRes = await fetch(`${API_BASE}/reminders/${orgId}`);
        if (remindersRes.ok) {
            const existingReminders = await remindersRes.json();
            const today = new Date().toISOString().split('T')[0];
            const hasStaleReminder = existingReminders.some((r: any) =>
                r.type === "system" && r.title.includes("Stale Cases") && r.created_at.startsWith(today)
            );
            if (hasStaleReminder) return;
        }

        await fetch(`${API_BASE}/reminders`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                organization_id: orgId,
                type: "system",
                title: "Action Required: Stale Cases",
                description: `${staleCases.length} cases have not been updated for over 24 hours.`,
                link: "/cases",
            })
        });
    }
};
