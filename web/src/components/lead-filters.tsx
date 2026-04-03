"use client";

import { cn } from "@/lib/utils";
import type { Tier, EventType } from "@/lib/types";
import { EVENT_TYPE_LABELS } from "@/lib/types";

interface LeadFiltersProps {
  activeTier: Tier | "all";
  onTierChange: (tier: Tier | "all") => void;
  activeEventType: EventType | "all";
  onEventTypeChange: (type: EventType | "all") => void;
}

const TIER_OPTIONS: { value: Tier | "all"; label: string }[] = [
  { value: "all", label: "All Tiers" },
  { value: "T1", label: "Hot" },
  { value: "T2", label: "Warm" },
  { value: "T3", label: "Stored" },
];

const EVENT_OPTIONS: { value: EventType | "all"; label: string }[] = [
  { value: "all", label: "All Sources" },
  ...Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => ({
    value: value as EventType,
    label,
  })),
];

export function LeadFilters({
  activeTier,
  onTierChange,
  activeEventType,
  onEventTypeChange,
}: LeadFiltersProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {/* Tier filter pills */}
      <div className="flex gap-1 bg-zinc-900 rounded-xl p-1 border border-zinc-800">
        {TIER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onTierChange(opt.value)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer",
              activeTier === opt.value
                ? "bg-zinc-700 text-zinc-100 shadow-sm"
                : "text-zinc-500 hover:text-zinc-300"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Event type filter pills */}
      <div className="flex gap-1 bg-zinc-900 rounded-xl p-1 border border-zinc-800">
        {EVENT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onEventTypeChange(opt.value)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer",
              activeEventType === opt.value
                ? "bg-zinc-700 text-zinc-100 shadow-sm"
                : "text-zinc-500 hover:text-zinc-300"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
