"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import type { ScoredLead, Tier, EventType } from "@/lib/types";

interface UseLeadsOptions {
  tier?: Tier | "all";
  eventType?: EventType | "all";
  limit?: number;
}

interface LeadRow {
  lead_id: string;
  event_id: string;
  score: number;
  tier: Tier;
  situation_brief: string;
  talking_points: string[];
  outreach_status: ScoredLead["outreach_status"];
  scored_at: string;
  created_at: string;
  updated_at: string;
  events: {
    event_id: string;
    event_type: EventType;
    source_id: string;
    person_name: string;
    company_name: string;
    filed_at: string | null;
    detected_at: string;
    url: string;
    raw_data: Record<string, unknown>;
    created_at: string;
  };
}

export function useLeads({ tier = "all", eventType = "all", limit = 50 }: UseLeadsOptions = {}) {
  const [leads, setLeads] = useState<ScoredLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLeads = useCallback(async () => {
    const supabase = createClient();

    let query = supabase
      .from("scored_leads")
      .select(
        `
        *,
        events!inner (
          event_id, event_type, source_id, person_name,
          company_name, filed_at, detected_at, url, raw_data, created_at
        )
      `
      )
      .order("score", { ascending: false })
      .limit(limit);

    if (tier !== "all") {
      query = query.eq("tier", tier);
    }
    if (eventType !== "all") {
      query = query.eq("events.event_type", eventType);
    }

    const { data, error: fetchError } = await query;

    if (fetchError) {
      setError(fetchError.message);
      setLoading(false);
      return;
    }

    const mapped: ScoredLead[] = (data as unknown as LeadRow[]).map((row) => ({
      lead_id: row.lead_id,
      event_id: row.event_id,
      score: row.score,
      tier: row.tier,
      situation_brief: row.situation_brief,
      talking_points: row.talking_points || [],
      outreach_status: row.outreach_status,
      scored_at: row.scored_at,
      created_at: row.created_at,
      updated_at: row.updated_at,
      event: row.events,
    }));

    setLeads(mapped);
    setLoading(false);
  }, [tier, eventType, limit]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  // Realtime subscription for new leads
  useEffect(() => {
    const supabase = createClient();
    const channel = supabase
      .channel("leads-realtime")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "scored_leads" },
        () => {
          fetchLeads();
        }
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "scored_leads" },
        () => {
          fetchLeads();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [fetchLeads]);

  return { leads, loading, error, refetch: fetchLeads };
}
