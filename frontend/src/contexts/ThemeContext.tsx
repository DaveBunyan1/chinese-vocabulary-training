import { createContext } from "react";

import type { Theme } from "../lib/theme";

export type ThemeContextValue = {
  /** User preference: light | dark | system */
  theme: Theme;
  /** Effective theme currently painted on the document */
  resolvedTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
  /** Cycle light → dark → system → light */
  cycleTheme: () => void;
};

export const ThemeContext = createContext<ThemeContextValue | null>(null);
