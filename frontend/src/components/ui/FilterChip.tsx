import { cn } from "../../lib/utils";

const FilterChip: React.FC<{
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}> = ({ label, count, active, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "rounded-full border px-3 py-1.5 text-sm transition",
      active
        ? "border-primary bg-primary text-primary-foreground"
        : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground",
    )}
  >
    {label}{" "}
    <span className={active ? "opacity-90" : "text-muted-foreground"}>
      ({count})
    </span>
  </button>
);

export default FilterChip;
