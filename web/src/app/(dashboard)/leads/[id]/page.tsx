"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import type { ScoredLead, EventType } from "@/lib/types";
import {
  EVENT_TYPE_LABELS,
  TIER_CONFIG,
  OUTREACH_STATUS_LABELS,
} from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScoreRing } from "@/components/ui/score-ring";
import {
  ArrowLeft,
  ExternalLink,
  MessageSquare,
  Copy,
  CheckCircle2,
  Clock,
  Zap,
  Send,
  UserCheck,
  Calendar,
  XCircle,
} from "lucide-react";

const TIMELINE_ICONS: Record<string, typeof Clock> = {
  pending: Clock,
  contact_found: UserCheck,
  linkedin_sent: Send,
  responded: MessageSquare,
  meeting_booked: Calendar,
  declined: XCircle,
};

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [lead, setLead] = useState<ScoredLead | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function fetchLead() {
      const supabase = createClient();
      const { data } = await supabase
        .from("scored_leads")
        .select(
          `
          *,
          events (
            event_id, event_type, source_id, person_name,
            company_name, filed_at, detected_at, url, raw_data, created_at
          )
        `
        )
        .eq("lead_id", params.id)
        .single();

      if (data) {
        const row = data as Record<string, unknown>;
        const events = row.events as Record<string, unknown>;
        setLead({
          lead_id: row.lead_id as string,
          event_id: row.event_id as string,
          score: row.score as number,
          tier: row.tier as ScoredLead["tier"],
          situation_brief: row.situation_brief as string,
          talking_points: (row.talking_points as string[]) || [],
          outreach_status: row.outreach_status as ScoredLead["outreach_status"],
          scored_at: row.scored_at as string,
          created_at: row.created_at as string,
          updated_at: row.updated_at as string,
          event: {
            event_id: events.event_id as string,
            event_type: events.event_type as EventType,
            source_id: events.source_id as string,
            person_name: events.person_name as string,
            company_name: events.company_name as string,
            filed_at: events.filed_at as string | null,
            detected_at: events.detected_at as string,
            url: events.url as string,
            raw_data: events.raw_data as Record<string, unknown>,
            created_at: events.created_at as string,
          },
        });
      }
      setLoading(false);
    }

    fetchLead();
  }, [params.id]);

  function copyTalkingPoints() {
    if (!lead) return;
    const text = lead.talking_points.map((tp) => `- ${tp}`).join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-zinc-500">
        Loading...
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="text-center py-20">
        <h2 className="text-lg font-medium text-zinc-300">Lead not found</h2>
        <Button variant="secondary" onClick={() => router.back()} className="mt-4">
          Go back
        </Button>
      </div>
    );
  }

  const tier = TIER_CONFIG[lead.tier];
  const StatusIcon = TIMELINE_ICONS[lead.outreach_status] || Clock;

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Back button */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      {/* Header card */}
      <Card className="relative overflow-hidden">
        {/* Glow accent for T1 */}
        {lead.tier === "T1" && (
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 via-orange-500 to-red-500" />
        )}
        {lead.tier === "T2" && (
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-yellow-500 to-amber-500" />
        )}

        <div className="flex items-start gap-5 pt-2">
          <ScoreRing score={lead.score} size="lg" />
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-xl font-bold text-zinc-100">
                {lead.event?.person_name || "Unknown"}
              </h1>
              <Badge variant={lead.tier.toLowerCase() as "t1" | "t2" | "t3"}>
                {tier.label}
              </Badge>
            </div>
            <p className="text-sm text-zinc-400 mb-3">
              {lead.event?.company_name || "Unknown Company"}
            </p>
            <p className="text-sm text-zinc-300 leading-relaxed">
              {lead.situation_brief}
            </p>
          </div>
        </div>
      </Card>

      {/* Info grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="p-3 text-center">
          <p className="text-xs text-zinc-500 mb-1">Event Type</p>
          <p className="text-sm font-medium text-zinc-200">
            {lead.event ? EVENT_TYPE_LABELS[lead.event.event_type] : "—"}
          </p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xs text-zinc-500 mb-1">Filed</p>
          <p className="text-sm font-medium text-zinc-200">
            {formatDateTime(lead.event?.filed_at ?? null)}
          </p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xs text-zinc-500 mb-1">Detected</p>
          <p className="text-sm font-medium text-zinc-200">
            {formatDateTime(lead.event?.detected_at ?? null)}
          </p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xs text-zinc-500 mb-1">Outreach</p>
          <div className="flex items-center justify-center gap-1.5">
            <StatusIcon className="w-3.5 h-3.5 text-zinc-400" />
            <p className="text-sm font-medium text-zinc-200">
              {OUTREACH_STATUS_LABELS[lead.outreach_status]}
            </p>
          </div>
        </Card>
      </div>

      {/* Talking points */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-zinc-100">
              Talking Points
            </h2>
          </div>
          <button
            onClick={copyTalkingPoints}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            {copied ? (
              <>
                <CheckCircle2 className="w-3 h-3 text-green-400" />
                Copied
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                Copy all
              </>
            )}
          </button>
        </div>
        <ul className="space-y-3">
          {lead.talking_points.map((point, i) => (
            <li key={i} className="flex items-start gap-3">
              <Zap className="w-3.5 h-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-zinc-300 leading-relaxed">
                {point}
              </span>
            </li>
          ))}
        </ul>
      </Card>

      {/* SEC filing link */}
      {lead.event?.url && (
        <a
          href={lead.event.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          View original filing
        </a>
      )}

      {/* Timeline */}
      <Card>
        <h2 className="text-sm font-semibold text-zinc-100 mb-4">Timeline</h2>
        <div className="space-y-4">
          <TimelineItem
            icon={<Zap className="w-3.5 h-3.5" />}
            label="Event detected"
            time={lead.event?.detected_at ?? ""}
            active
          />
          <TimelineItem
            icon={<CheckCircle2 className="w-3.5 h-3.5" />}
            label={`Scored ${lead.score}/100 — ${tier.label}`}
            time={lead.scored_at}
            active
          />
          {lead.outreach_status !== "pending" && (
            <TimelineItem
              icon={<StatusIcon className="w-3.5 h-3.5" />}
              label={OUTREACH_STATUS_LABELS[lead.outreach_status]}
              time={lead.updated_at}
              active
            />
          )}
        </div>
      </Card>
    </div>
  );
}

function TimelineItem({
  icon,
  label,
  time,
  active,
}: {
  icon: React.ReactNode;
  label: string;
  time: string;
  active?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex items-center justify-center w-7 h-7 rounded-full ${
          active
            ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
            : "bg-zinc-800 text-zinc-500"
        }`}
      >
        {icon}
      </div>
      <div className="flex-1">
        <p className="text-sm text-zinc-200">{label}</p>
        <p className="text-xs text-zinc-500">{formatDateTime(time)}</p>
      </div>
    </div>
  );
}
