import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition",
  {
    variants: {
      variant: {
        default: "border-border bg-muted text-muted-foreground",
        primary: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-border bg-secondary text-secondary-foreground",
        success: "border-transparent bg-success text-success-foreground",
        warning: "border-transparent bg-warning text-warning-foreground",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground",
        outline: "border-border text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export type BadgeProps = HTMLAttributes<HTMLSpanElement> &
  VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

/** Knowledge status → semantic badge (new / learning / known). */
const STATUS_VARIANT: Record<string, BadgeProps["variant"]> = {
  new: "default",
  learning: "warning",
  known: "success",
};

export function StatusBadge({
  status,
  className,
  ...props
}: Omit<BadgeProps, "variant" | "children"> & { status: string }) {
  const variant = STATUS_VARIANT[status] ?? "default";
  return (
    <Badge variant={variant} className={className} {...props}>
      {status}
    </Badge>
  );
}
