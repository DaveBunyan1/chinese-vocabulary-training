import { cn } from "../../lib/utils";

type PlaceholderKind = "placeholder" | "unwired" | "coming_soon";

const LABELS: Record<PlaceholderKind, string> = {
  placeholder: "Placeholder",
  unwired: "Unwired",
  coming_soon: "Coming soon",
};

const PlaceholderTag = ({
  kind = "placeholder",
  className,
}: {
  kind?: PlaceholderKind;
  className?: string;
}) => {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-dashed border-border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground",
        className,
      )}
    >
      {LABELS[kind]}
    </span>
  );
};

export default PlaceholderTag;
