import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

const SettingsPage = () => {
  const [companyName, setCompanyName] = useState("Acme MSME Corp");
  const [domain, setDomain] = useState("msme");
  const [confidenceThreshold, setConfidenceThreshold] = useState([70]);
  const [escalationThreshold, setEscalationThreshold] = useState([50]);

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Configure your platform's domain and automation thresholds.</p>
      </div>

      <div className="rounded-xl border bg-card p-6 space-y-6">
        {/* Company Name */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Company Name</Label>
          <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="max-w-sm" />
        </div>

        {/* Domain Config */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Domain Configuration</Label>
          <Select value={domain} onValueChange={setDomain}>
            <SelectTrigger className="max-w-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="msme">MSME E-Commerce</SelectItem>
              <SelectItem value="healthcare">Healthcare Demo</SelectItem>
              <SelectItem value="fintech">Fintech</SelectItem>
              <SelectItem value="custom">Custom Domain</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">This controls intent classification models and policy retrieval logic.</p>
        </div>

        {/* Confidence Threshold */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Confidence Threshold</Label>
            <span className="text-sm font-mono text-foreground">{confidenceThreshold[0]}%</span>
          </div>
          <Slider value={confidenceThreshold} onValueChange={setConfidenceThreshold} max={100} min={0} step={5} className="max-w-sm" />
          <p className="text-xs text-muted-foreground">Cases below this confidence will be flagged for review.</p>
        </div>

        {/* Escalation Threshold */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Escalation Threshold</Label>
            <span className="text-sm font-mono text-foreground">{escalationThreshold[0]}%</span>
          </div>
          <Slider value={escalationThreshold} onValueChange={setEscalationThreshold} max={100} min={0} step={5} className="max-w-sm" />
          <p className="text-xs text-muted-foreground">Cases below this threshold are automatically escalated to a human agent.</p>
        </div>

        <div className="pt-2">
          <Button>Save Settings</Button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
