import { supabase } from "./supabase";

/**
 * Triggers a reminder in the database.
 * In a real production environment, this would ideally be done via 
 * Database Triggers (PL/pgSQL) or Edge Functions.
 * For this implementation, we provide helper functions that can be called 
 * when important events occur in the application.
 */

export const triggerEscalationReminder = async (orgId: string, conversationId: string, customerName: string) => {
    await supabase.from("reminders").insert({
        organization_id: orgId,
        type: "escalation",
        title: "New Escalation Required",
        description: `Customer ${customerName} is waiting for human intervention.`,
        link: `/cases/${conversationId}`,
    });
};

export const triggerPriorityReminder = async (orgId: string, conversationId: string, score: number) => {
    if (score < 0.3) { // High uncertainty
        await supabase.from("reminders").insert({
            organization_id: orgId,
            type: "priority_case",
            title: "High Uncertainty Case",
            description: `AI confidence is very low (${(score * 100).toFixed(0)}%). Please review.`,
            link: `/cases/${conversationId}`,
        });
    }
};

/**
 * Generates a "Daily Summary" reminder.
 * This can be called upon administrator login or via a scheduled job.
 */
export const generateDailySummary = async (orgId: string) => {
    // Fetch some stats for the summary
    const { data: conversations } = await supabase
        .from("conversations")
        .select("status")
        .eq("organization_id", orgId);

    if (!conversations) return;

    const active = conversations.filter(c => c.status === "active").length;
    const escalated = conversations.filter(c => c.status === "escalated").length;

    if (active === 0 && escalated === 0) return;

    await supabase.from("reminders").insert({
        organization_id: orgId,
        type: "daily_summary",
        title: "Daily Morning Brief",
        description: `You have ${active} active cases and ${escalated} pending escalations waiting for you.`,
        link: "/cases",
    });
};
