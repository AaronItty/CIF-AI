import { Zap, Code, Info } from "lucide-react";
import { skills } from "@/data/mockData";

const Skills = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Skills</h1>
        <p className="text-sm text-muted-foreground mt-1">Registered skills that extend AI agent capabilities.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {skills.map((skill) => (
          <div key={skill.name} className="rounded-xl border bg-card p-5 transition-shadow hover:shadow-md">
            <div className="flex items-start justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent">
                <Zap size={16} className="text-accent-foreground" />
              </div>
              <span className="text-xs text-muted-foreground">{skill.executions} runs</span>
            </div>
            <h3 className="mt-3 font-mono text-sm font-semibold text-foreground">{skill.name}</h3>
            <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">{skill.description}</p>
            <div className="mt-3">
              <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1">Input Schema</p>
              <pre className="rounded-md bg-secondary p-2 text-[11px] font-mono text-muted-foreground overflow-x-auto">
                {skill.inputSchema}
              </pre>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-start gap-2 rounded-xl border bg-accent/50 p-4">
        <Info size={16} className="mt-0.5 shrink-0 text-accent-foreground" />
        <p className="text-xs text-accent-foreground">
          Custom skills can be developed for deeper backend integration. Contact the platform team to register new skills.
        </p>
      </div>
    </div>
  );
};

export default Skills;
