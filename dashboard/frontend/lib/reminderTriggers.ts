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
    // Fetch conversations from backend to calculate summary
    const res = await fetch(`${API_BASE}/conversations/${orgId}`);
    if (!res.ok) return;
    const conversations = await res.json();

    if (!conversations) return;

    const active = conversations.filter((c: any) => c.status === "active").length;
    const escalated = conversations.filter((c: any) => c.status === "escalated").length;

    if (active === 0 && escalated === 0) return;

    await fetch(`${API_BASE}/reminders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            organization_id: orgId,
            type: "daily_summary",
            title: "Daily Morning Brief",
            description: `You have ${active} active cases and ${escalated} pending escalations waiting for you.`,
            link: "/cases",
        })
    });
};
