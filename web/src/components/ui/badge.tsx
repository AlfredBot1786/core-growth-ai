import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "t1" | "t2" | "t3" | "outline";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg px-2.5 py-0.5 text-xs font-semibold tracking-wide uppercase",
        {
          "bg-zinc-800 text-zinc-300": variant === "default",
          "bg-red-500/10 text-red-400 border border-red-500/20":
            variant === "t1",
          "bg-amber-500/10 text-amber-400 border border-amber-500/20":
            variant === "t2",
          "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20":
            variant === "t3",
          "border border-zinc-700 text-zinc-400": variant === "outline",
        },
        className
      )}
    >
      {children}
    </span>
  );
}
