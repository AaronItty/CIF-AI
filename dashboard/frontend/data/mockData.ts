import { Case, Skill, Channel, KPI } from "../types/types";

export const kpiData: KPI[] = [
  { label: "Total Cases", value: "1,284", trend: "+12.5%", trendUp: true },
  { label: "Auto-Resolved", value: "78.3%", trend: "+3.2%", trendUp: true },
  { label: "Escalation Rate", value: "8.7%", trend: "-1.4%", trendUp: false },
  { label: "Avg Resolution Time", value: "2m 34s", trend: "-18s", trendUp: false },
];

export const intentDistribution = [
  { name: "Order Tracking", value: 420, fill: "hsl(24, 85%, 52%)" },
  { name: "Refund Requests", value: 280, fill: "hsl(38, 92%, 50%)" },
  { name: "Complaints", value: 190, fill: "hsl(0, 72%, 51%)" },
  { name: "Product Queries", value: 394, fill: "hsl(217, 91%, 60%)" },
];

export const cases: Case[] = [
  { id: "CSE-1024", customerId: "CUS-4421", customer: "Arjun Mehta", intent: "Refund Request", status: "Resolved", confidence: 92, escalated: false, createdAt: "2026-02-27T09:12:00Z", updatedAt: "2026-02-27T09:14:32Z" },
  { id: "CSE-1023", customerId: "CUS-3310", customer: "Priya Sharma", intent: "Order Tracking", status: "In Progress", confidence: 87, escalated: false, createdAt: "2026-02-27T08:45:00Z", updatedAt: "2026-02-27T08:47:11Z" },
  { id: "CSE-1022", customerId: "CUS-2208", customer: "Rohan Patel", intent: "Complaint", status: "Escalated", confidence: 54, escalated: true, createdAt: "2026-02-27T07:30:00Z", updatedAt: "2026-02-27T07:35:22Z" },
  { id: "CSE-1021", customerId: "CUS-1190", customer: "Sneha Iyer", intent: "Product Query", status: "Resolved", confidence: 95, escalated: false, createdAt: "2026-02-26T16:20:00Z", updatedAt: "2026-02-26T16:21:45Z" },
  { id: "CSE-1020", customerId: "CUS-5502", customer: "Vikram Singh", intent: "Refund Request", status: "Open", confidence: 79, escalated: false, createdAt: "2026-02-26T15:10:00Z", updatedAt: "2026-02-26T15:10:00Z" },
  { id: "CSE-1019", customerId: "CUS-6613", customer: "Ananya Desai", intent: "Order Tracking", status: "Resolved", confidence: 91, escalated: false, createdAt: "2026-02-26T14:00:00Z", updatedAt: "2026-02-26T14:03:12Z" },
  { id: "CSE-1018", customerId: "CUS-7724", customer: "Karan Joshi", intent: "Complaint", status: "In Progress", confidence: 63, escalated: false, createdAt: "2026-02-26T12:55:00Z", updatedAt: "2026-02-26T13:01:44Z" },
  { id: "CSE-1017", customerId: "CUS-8835", customer: "Meera Nair", intent: "Product Query", status: "Resolved", confidence: 88, escalated: false, createdAt: "2026-02-26T11:30:00Z", updatedAt: "2026-02-26T11:32:18Z" },
];

export const skills: Skill[] = [
  { name: "get_order_status", description: "Retrieves current order status from the fulfillment system using order ID.", inputSchema: '{ "order_id": "string" }', executions: 847 },
  { name: "create_refund", description: "Initiates a refund for a given order after policy validation.", inputSchema: '{ "order_id": "string", "reason": "string" }', executions: 312 },
  { name: "create_replacement", description: "Creates a replacement order for defective or missing items.", inputSchema: '{ "order_id": "string", "item_id": "string" }', executions: 156 },
  { name: "check_policy", description: "Checks applicable return/refund policy for a given product category.", inputSchema: '{ "category": "string" }', executions: 623 },
  { name: "escalate_to_human", description: "Transfers the case to a human agent when confidence is below threshold.", inputSchema: '{ "case_id": "string", "reason": "string" }', executions: 98 },
];

export const channels: Channel[] = [
  { name: "Gmail", status: "connected", icon: "Mail" },
  { name: "Telegram", status: "not_connected", icon: "MessageCircle" },
  { name: "Webhook", status: "connected", icon: "Globe" },
  { name: "WhatsApp", status: "not_connected", icon: "Phone" },
];

export const caseDetail = {
  id: "CSE-1024",
  customerId: "CUS-4421",
  customer: "Arjun Mehta",
  intent: "Refund Request",
  status: "Resolved" as const,
  confidence: 92,
  escalated: false,
  createdAt: "2026-02-27T09:12:00Z",
  updatedAt: "2026-02-27T09:14:32Z",
  conversation: [
    { role: "customer" as const, message: "Hi, I'd like a refund for order #ORD-8821. The product arrived damaged.", timestamp: "09:12:00" },
    { role: "agent" as const, message: "I'm sorry to hear that, Arjun. Let me look into order #ORD-8821 for you right away.", timestamp: "09:12:02" },
    { role: "agent" as const, message: "I've verified your order and confirmed the delivery. Based on our policy, damaged items are eligible for a full refund within 7 days. I've initiated the refund — it should reflect in 3-5 business days.", timestamp: "09:12:08" },
    { role: "customer" as const, message: "That was quick! Thank you.", timestamp: "09:13:15" },
    { role: "agent" as const, message: "You're welcome! Is there anything else I can help you with?", timestamp: "09:13:17" },
  ],
  executionLog: [
    { step: "Intent Classified", detail: "refund_request", confidence: 0.92 },
    { step: "Skill Executed", detail: "get_order_status", output: '{ "status": "delivered", "date": "2026-02-25" }' },
    { step: "Policy Retrieved", detail: "Refund allowed within 7 days for damaged items" },
    { step: "Skill Executed", detail: "create_refund", output: '{ "refund_id": "REF-4410", "amount": "₹1,299" }' },
    { step: "Case Resolved", detail: "Auto-resolved with confidence 0.92" },
  ],
};

export const analyticsData = {
  intentFrequency: [
    { month: "Jan", orderTracking: 120, refund: 80, complaint: 40, productQuery: 95 },
    { month: "Feb", orderTracking: 140, refund: 90, complaint: 55, productQuery: 110 },
    { month: "Mar", orderTracking: 100, refund: 70, complaint: 35, productQuery: 85 },
    { month: "Apr", orderTracking: 160, refund: 100, complaint: 60, productQuery: 120 },
    { month: "May", orderTracking: 130, refund: 85, complaint: 45, productQuery: 100 },
    { month: "Jun", orderTracking: 170, refund: 110, complaint: 50, productQuery: 130 },
  ],
  escalationTrend: [
    { month: "Jan", rate: 14 },
    { month: "Feb", rate: 12.5 },
    { month: "Mar", rate: 11 },
    { month: "Apr", rate: 10.2 },
    { month: "May", rate: 9.5 },
    { month: "Jun", rate: 8.7 },
  ],
  resolutionTime: [
    { range: "< 1m", count: 320 },
    { range: "1-3m", count: 480 },
    { range: "3-5m", count: 210 },
    { range: "5-10m", count: 85 },
    { range: "> 10m", count: 30 },
  ],
  skillUsage: [
    { name: "get_order_status", count: 847 },
    { name: "check_policy", count: 623 },
    { name: "create_refund", count: 312 },
    { name: "create_replacement", count: 156 },
    { name: "escalate_to_human", count: 98 },
  ],
};
