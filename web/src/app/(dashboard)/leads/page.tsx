"use client";

import { useState } from "react";
import { useLeads } from "@/lib/hooks/use-leads";
import { LeadFilters } from "@/components/lead-filters";
import { LeadCard } from "@/components/lead-card";
import type { Tier, EventType } from "@/lib/types";
import { Activity, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AllLeadsPage() {
  const [tierFilter, setTierFilter] = useState<Tier | "all">("all");
  const [eventFilter, setEventFilter] = useState<EventType | "all">("all");

  const { leads, loading } = useLeads({
    tier: tierFilter,
    eventType: eventFilter,
    limit: 200,
  });

  function exportCSV() {
    if (leads.length === 0) return;

    const headers = [
      "Tier",
      "Score",
      "Person",
      "Company",
      "Event Type",
      "Situation",
      "Talking Points",
      "Outreach Status",
      "Scored At",
    ];
    const rows = leads.map((l) => [
      l.tier,
      l.score,
      l.event?.person_name || "",
      l.event?.company_name || "",
      l.event?.event_type || "",
      `"${l.situation_brief.replace(/"/g, '""')}"`,
      `"${l.talking_points.join("; ").replace(/"/g, '""')}"`,
      l.outreach_status,
      l.scored_at,
    ]);

    const csv =
      headers.join(",") + "\n" + rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `leads-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">All Leads</h1>
          <p className="text-sm text-zinc-500 mt-1">
            {leads.length} lead{leads.length !== 1 ? "s" : ""} found
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={exportCSV}>
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
      </div>

      <LeadFilters
        activeTier={tierFilter}
        onTierChange={setTierFilter}
        activeEventType={eventFilter}
        onEventTypeChange={setEventFilter}
      />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-zinc-500">
            <Activity className="w-5 h-5 animate-pulse" />
            <span>Loading leads...</span>
          </div>
        </div>
      ) : leads.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-zinc-500">No leads match your filters.</p>
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
