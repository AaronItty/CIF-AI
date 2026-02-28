import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import RemindersPopover from "./RemindersPopover";

const TopNav = () => {
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-card px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-medium text-muted-foreground">
          Good Morning, Admin
        </h2>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search..."
            className="h-9 w-56 rounded-lg bg-secondary pl-9 text-sm border-none focus-visible:ring-1 focus-visible:ring-primary"
          />
        </div>
        <RemindersPopover />
        <div className="flex items-center gap-2 rounded-lg bg-secondary px-3 py-1.5">
          <div className="h-7 w-7 rounded-full bg-primary flex items-center justify-center text-xs font-semibold text-primary-foreground">
            A
          </div>
          <span className="text-sm font-medium">Admin</span>
        </div>
      </div>
    </header>
  );
};

export default TopNav;
