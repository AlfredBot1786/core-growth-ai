"use client";

import { cn } from "@/lib/utils";

interface ScoreRingProps {
  score: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function ScoreRing({ score, size = "md", className }: ScoreRingProps) {
  const sizes = { sm: 40, md: 56, lg: 80 };
  const strokes = { sm: 3, md: 4, lg: 5 };
  const fonts = { sm: "text-xs", md: "text-sm", lg: "text-xl" };

  const s = sizes[size];
  const stroke = strokes[size];
  const radius = (s - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 70
      ? "stroke-red-500"
      : score >= 40
        ? "stroke-amber-500"
        : "stroke-zinc-500";

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={s} height={s} className="-rotate-90">
        <circle
          cx={s / 2}
          cy={s / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-zinc-800"
        />
        <circle
          cx={s / 2}
          cy={s / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={cn(color, "transition-all duration-700 ease-out")}
        />
      </svg>
      <span
        className={cn(
          "absolute font-bold text-zinc-100",
          fonts[size]
        )}
      >
        {score}
      </span>
    </div>
  );
}
