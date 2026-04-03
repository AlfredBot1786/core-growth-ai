"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface Stats {
  total: number;
  t1Count: number;
  t2Count: number;
  t3Count: number;
  lastRunAt: string | null;
}

export function useStats() {
  const [stats, setStats] = useState<Stats>({
    total: 0,
    t1Count: 0,
    t2Count: 0,
    t3Count: 0,
    lastRunAt: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      const supabase = createClient();

      const [totalRes, t1Res, t2Res, t3Res, runRes] = await Promise.all([
        supabase
          .from("scored_leads")
          .select("*", { count: "exact", head: true }),
        supabase
          .from("scored_leads")
          .select("*", { count: "exact", head: true })
          .eq("tier", "T1"),
        supabase
          .from("scored_leads")
          .select("*", { count: "exact", head: true })
          .eq("tier", "T2"),
        supabase
          .from("scored_leads")
          .select("*", { count: "exact", head: true })
          .eq("tier", "T3"),
        supabase
          .from("pipeline_runs")
          .select("completed_at")
          .eq("status", "completed")
          .order("completed_at", { ascending: false })
          .limit(1),
      ]);

      setStats({
        total: totalRes.count ?? 0,
        t1Count: t1Res.count ?? 0,
        t2Count: t2Res.count ?? 0,
        t3Count: t3Res.count ?? 0,
        lastRunAt: runRes.data?.[0]?.completed_at ?? null,
      });
      setLoading(false);
    }

    fetchStats();
  }, []);

  return { stats, loading };
}
