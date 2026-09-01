import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "sidebar-collapsed";

const useSidebar = () => {
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch {
      // ignore
    }
  }, [collapsed]);

  const toggle = useCallback(() => setCollapsed((c) => !c), []);

  return { collapsed, setCollapsed, toggle };
};

export default useSidebar;
