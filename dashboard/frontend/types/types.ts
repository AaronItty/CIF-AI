export interface KPI {
  label: string;
  value: string;
  trend: string;
  trendUp: boolean;
}

export interface Case {
  id: string;
  customerId: string;
  customer: string;
  intent: string;
  status: "Open" | "In Progress" | "Resolved" | "Escalated";
  confidence: number;
  escalated: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Skill {
  name: string;
  description: string;
  inputSchema: string;
  executions: number;
}

export interface Channel {
  name: string;
  status: "connected" | "not_connected";
  icon: string;
}

export interface ConversationMessage {
  role: "customer" | "agent";
  message: string;
  timestamp: string;
}

export interface ExecutionStep {
  step: string;
  detail: string;
  confidence?: number;
  output?: string;
}
