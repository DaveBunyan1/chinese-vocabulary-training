import { Monitor, Moon, Sun } from "lucide-react";

import { useTheme } from "../../hooks/useTheme";
import type { Theme } from "../../lib/theme";

const ICONS: Record<Theme, React.ReactNode> = {
  light: <Sun className="h-4 w-4" />,
  dark: <Moon className="h-4 w-4" />,
  system: <Monitor className="h-4 w-4" />,
};

const LABELS: Record<Theme, string> = {
  light: "Light",
  dark: "Dark",
  system: "System",
};

/**
 * Compact control: click cycles light → dark → system.
 * Title/aria reflect the current preference.
 */
export function ThemeToggle() {
  const { theme, cycleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={cycleTheme}
      title={`Theme: ${LABELS[theme]} (click to cycle)`}
      aria-label={`Current theme: ${LABELS[theme]}. Click to change.`}
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-foreground transition hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {ICONS[theme]}
    </button>
  );
}
