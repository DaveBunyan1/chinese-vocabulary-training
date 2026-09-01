import { NavLink, Outlet } from "react-router-dom";
import {
  BarChart3,
  BookOpen,
  Brain,
  FolderTree,
  Home,
  Languages,
  LayoutList,
  MessageCircle,
  GraduationCap,
  PanelLeftClose,
  PanelLeft,
  Sparkles,
  User,
} from "lucide-react";

import { ThemeToggle } from "../ui/ThemeToggle";
import PlaceholderTag from "../ui/PlaceholderTag";
import useSidebar from "../../hooks/useSidebar";
import { cn } from "../../lib/utils";
import { Button } from "../ui";

const NAV = [
  { to: "/", label: "Home", icon: Home },
  { to: "/import", label: "Build knowledge", icon: BookOpen },
  { to: "/vocabulary", label: "Vocabulary", icon: LayoutList },
  { to: "/characters", label: "Characters", icon: Languages },
  { to: "/categories", label: "Categories", icon: FolderTree },
  { to: "/review", label: "Smart review", icon: Sparkles },
  { to: "/practice", label: "Practice", icon: Brain },
  { to: "/progress", label: "Progress", icon: BarChart3 },
] as const;

const COMING_SOON = [
  { label: "Learn", icon: GraduationCap },
  { label: "Chat", icon: MessageCircle },
] as const;

export function AppShell() {
  const { collapsed, toggle } = useSidebar();

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside
        className={cn(
          "sticky top-0 flex h-screen flex-col border-r border-border bg-card transition-[width] duration-200",
          collapsed ? "w-16" : "w-56",
        )}
      >
        <div
          className={cn(
            "flex h-14 items-center border-b border-border px-3",
            collapsed ? "justify-center" : "justify-between gap-2",
          )}
        >
          {!collapsed && (
            <span className="truncate text-sm font-semibold tracking-tight">
              Chinese Learning
            </span>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={toggle}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand" : "Collapse"}
          >
            {collapsed ? (
              <PanelLeft className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </Button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              title={label}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                  collapsed && "justify-center px-2",
                  isActive
                    ? "bg-primary/10 text-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          ))}

          <div className="my-2 border-t border-border" />

          {COMING_SOON.map(({ label, icon: Icon }) => (
            <div
              key={label}
              title={`${label} (coming soon)`}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground/70",
                collapsed && "justify-center px-2",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && (
                <span className="flex min-w-0 flex-1 items-center gap-2 truncate">
                  {label}
                  <PlaceholderTag kind="coming_soon" />
                </span>
              )}
            </div>
          ))}
        </nav>

        {/* User / learner placeholder */}
        <div className="border-t border-border p-2">
          <div
            className={cn(
              "flex items-center gap-3 rounded-lg bg-muted/50 px-3 py-2",
              collapsed && "justify-center px-2",
            )}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
              <User className="h-4 w-4" />
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">Guest</p>
                <p className="truncate text-xs text-muted-foreground">
                  Chinese · profile soon
                </p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-end gap-2 border-b border-border bg-card px-4">
          <ThemeToggle />
        </header>
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
