"use client";

import { useState } from "react";
import { useLeads } from "@/lib/hooks/use-leads";
import { useStats } from "@/lib/hooks/use-stats";
import { StatsBar } from "@/components/stats-bar";
import { LeadFilters } from "@/components/lead-filters";
import { LeadCard } from "@/components/lead-card";
import type { Tier, EventType } from "@/lib/types";
import { Activity, RefreshCw } from "lucide-react";
import { formatDateTime } from "@/lib/utils";

export default function DashboardPage() {
  const [tierFilter, setTierFilter] = useState<Tier | "all">("all");
  const [eventFilter, setEventFilter] = useState<EventType | "all">("all");

  const { leads, loading, refetch } = useLeads({
    tier: tierFilter,
    eventType: eventFilter,
  });
  const { stats } = useStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Dashboard</h1>
          <p className="text-sm text-zinc-500 mt-1">
            {stats.lastRunAt ? (
              <>
                Last scan: {formatDateTime(stats.lastRunAt)}
              </>
            ) : (
              "Waiting for first pipeline run..."
            )}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <StatsBar
        total={stats.total}
        t1Count={stats.t1Count}
        t2Count={stats.t2Count}
        t3Count={stats.t3Count}
        lastRunAt={stats.lastRunAt}
      />

      {/* Filters */}
      <LeadFilters
        activeTier={tierFilter}
        onTierChange={setTierFilter}
        activeEventType={eventFilter}
        onEventTypeChange={setEventFilter}
      />

      {/* Lead list */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-zinc-500">
            <Activity className="w-5 h-5 animate-pulse" />
            <span>Loading leads...</span>
          </div>
        </div>
      ) : leads.length === 0 ? (
        <div className="text-center py-20">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zinc-800/50 mb-4">
            <Activity className="w-8 h-8 text-zinc-600" />
          </div>
          <h3 className="text-lg font-medium text-zinc-300">No leads yet</h3>
          <p className="text-sm text-zinc-500 mt-1">
            Leads will appear here once the pipeline detects money-in-motion events.
          </p>
        </div>
      ) : (
        <div className="space-y-3 stagger-list">
          {leads.map((lead) => (
            <LeadCard key={lead.lead_id} lead={lead} />
          ))}
        </div>
      )}
    </div>
  );
}
