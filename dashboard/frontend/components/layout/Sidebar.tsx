import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  FolderOpen,
  BarChart3,
  BookOpen,
  Zap,
  Radio,
  Settings,
  Bot,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";


const navSections = [
  {
    label: "Menu",
    items: [
      { to: "/dashboard", icon: LayoutDashboard, label: "Overview" },
      { to: "/cases", icon: FolderOpen, label: "Cases" },
      { to: "/analytics", icon: BarChart3, label: "Analytics" },
    ],
  },
  {
    label: "Platform",
    items: [
      { to: "/knowledge-base", icon: BookOpen, label: "Knowledge Base" },
      { to: "/skills", icon: Zap, label: "Skills" },
      { to: "/channels", icon: Radio, label: "Channels" },
    ],
  },
  {
    label: "System",
    items: [
      { to: "/settings", icon: Settings, label: "Settings" },
    ],
  },
];

const Sidebar = () => {
  const location = useLocation();
  const { signOut } = useAuth();

  const handleLogout = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-60 flex-col border-r border-sidebar-border bg-sidebar">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
          <Bot className="h-4.5 w-4.5 text-primary-foreground" size={18} />
        </div>
        <span className="text-lg font-semibold text-foreground tracking-tight">AgentOS</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-2">
        {navSections.map((section) => (
          <div key={section.label} className="mb-5">
            <p className="section-label mb-2 px-2">{section.label}</p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = location.pathname === item.to ||
                  (item.to !== "/dashboard" && location.pathname.startsWith(item.to));
                return (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive
                        ? "bg-accent text-accent-foreground"
                        : "text-sidebar-foreground hover:bg-secondary hover:text-foreground"
                        }`}
                    >
                      <item.icon size={18} strokeWidth={isActive ? 2 : 1.5} />
                      {item.label}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-sidebar-border px-4 py-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
        >
          <LogOut size={18} strokeWidth={1.5} />
          Sign Out
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
