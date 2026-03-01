import { Bell, Check, Trash2, ExternalLink, Calendar, AlertCircle, Info, Sparkles } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useOrgId, useReminders, Reminder } from "@/hooks/useSupabase";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";

const RemindersPopover = () => {
    const { orgId, orgLoaded } = useOrgId();
    const { reminders, loading, markAsRead, markAllAsRead, clearAll } = useReminders(orgId, orgLoaded);

    const unreadCount = reminders.filter((r) => !r.is_read).length;

    const typeIcons = {
        escalation: <AlertCircle className="h-4 w-4 text-destructive" />,
        system: <Info className="h-4 w-4 text-info" />,
        daily_summary: <Calendar className="h-4 w-4 text-primary" />,
        priority_case: <Sparkles className="h-4 w-4 text-warning" />,
    };

    const typeLabels = {
        escalation: "Escalation",
        system: "System",
        daily_summary: "Daily Summary",
        priority_case: "Priority Case",
    };

    return (
        <Popover>
            <PopoverTrigger asChild>
                <button
                    className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    title="Notifications"
                >
                    <Bell size={18} />
                    {unreadCount > 0 && (
                        <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground shadow-sm">
                            {unreadCount > 9 ? "9+" : unreadCount}
                        </span>
                    )}
                </button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-0" align="end">
                <div className="flex items-center justify-between border-b p-4 pb-3">
                    <h4 className="text-sm font-semibold">Reminders</h4>
                    <div className="flex gap-2">
                        {unreadCount > 0 && (
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7"
                                onClick={() => markAllAsRead()}
                                title="Mark all as read"
                            >
                                <Check className="h-4 w-4" />
                            </Button>
                        )}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-muted-foreground hover:text-destructive"
                            onClick={() => clearAll()}
                            title="Clear all"
                        >
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                <ScrollArea className="h-[400px]">
                    {loading ? (
                        <div className="flex items-center justify-center py-10 text-xs text-muted-foreground">
                            Loading reminders...
                        </div>
                    ) : reminders.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary/50">
                                <Bell className="h-5 w-5 text-muted-foreground" />
                            </div>
                            <p className="mt-3 text-xs font-medium text-muted-foreground">No reminders yet</p>
                            <p className="px-6 mt-1 text-[10px] text-muted-foreground/60">
                                Critical events and daily summaries will appear here.
                            </p>
                        </div>
                    ) : (
                        <div className="grid divide-y divide-border">
                            {reminders.map((reminder) => (
                                <div
                                    key={reminder.id}
                                    className={`relative flex flex-col gap-1 p-4 transition-colors hover:bg-secondary/30 ${!reminder.is_read ? 'bg-primary/5' : ''
                                        }`}
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex items-center gap-2">
                                            {typeIcons[reminder.type]}
                                            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                                                {typeLabels[reminder.type]}
                                            </span>
                                        </div>
                                        {!reminder.is_read && (
                                            <button
                                                onClick={() => markAsRead(reminder.id)}
                                                className="h-2 w-2 rounded-full bg-primary"
                                                title="Mark as read"
                                            />
                                        )}
                                    </div>

                                    <p className="mt-1 text-xs font-semibold leading-tight text-foreground">
                                        {reminder.title}
                                    </p>

                                    {reminder.description && (
                                        <p className="text-[11px] text-muted-foreground line-clamp-2">
                                            {reminder.description}
                                        </p>
                                    )}

                                    <div className="mt-2 flex items-center justify-between">
                                        <span className="text-[10px] text-muted-foreground">
                                            {new Date(reminder.created_at).toLocaleDateString() === new Date().toLocaleDateString()
                                                ? new Date(reminder.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                                : new Date(reminder.created_at).toLocaleDateString()}
                                        </span>

                                        {reminder.link && (
                                            <Link
                                                to={reminder.link}
                                                className="flex items-center gap-1 text-[10px] font-medium text-primary hover:underline"
                                                onClick={() => !reminder.is_read && markAsRead(reminder.id)}
                                            >
                                                View Details
                                                <ExternalLink className="h-2.5 w-2.5" />
                                            </Link>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </ScrollArea>

                {reminders.length > 0 && (
                    <div className="border-t p-2">
                        <Button variant="ghost" size="sm" className="w-full text-xs font-normal h-8" asChild>
                            <Link to="/analytics">View Full History</Link>
                        </Button>
                    </div>
                )}
            </PopoverContent>
        </Popover>
    );
};

export default RemindersPopover;
