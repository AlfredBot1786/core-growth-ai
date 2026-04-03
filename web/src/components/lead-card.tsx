"use client";

import Link from "next/link";
import type { ScoredLead, EventType } from "@/lib/types";
import {
  EVENT_TYPE_LABELS,
  TIER_CONFIG,
  OUTREACH_STATUS_LABELS,
} from "@/lib/types";
import { timeAgo } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ScoreRing } from "@/components/ui/score-ring";
import { Card } from "@/components/ui/card";
import {
  FileText,
  AlertTriangle,
  Briefcase,
  Link2,
  ExternalLink,
} from "lucide-react";

const EVENT_ICONS: Record<EventType, typeof FileText> = {
  sec_form4: FileText,
  sec_8k: AlertTriangle,
  warn_act: Briefcase,
  linkedin: Link2,
};

interface LeadCardProps {
  lead: ScoredLead;
}

export function LeadCard({ lead }: LeadCardProps) {
  const tier = TIER_CONFIG[lead.tier];
  const EventIcon = lead.event
    ? EVENT_ICONS[lead.event.event_type]
    : FileText;

  return (
    <Link href={`/leads/${lead.lead_id}`}>
      <Card hover className="group">
        <div className="flex items-start gap-4">
          {/* Score */}
          <ScoreRing score={lead.score} size="md" />

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-sm font-semibold text-zinc-100 truncate">
                {lead.event?.person_name || "Unknown"}
              </h3>
              <Badge variant={lead.tier.toLowerCase() as "t1" | "t2" | "t3"}>
                {tier.label}
              </Badge>
            </div>

            <p className="text-xs text-zinc-400 mb-2 truncate">
              {lead.event?.company_name || "Unknown Company"}
            </p>

            <p className="text-sm text-zinc-300 line-clamp-2 mb-3">
              {lead.situation_brief}
            </p>

            {/* Footer */}
            <div className="flex items-center gap-3 text-xs text-zinc-500">
              <span className="inline-flex items-center gap-1">
                <EventIcon className="w-3 h-3" />
                {lead.event
                  ? EVENT_TYPE_LABELS[lead.event.event_type]
                  : "Unknown"}
              </span>
              <span>{timeAgo(lead.scored_at)}</span>
              <Badge variant="outline" className="text-[10px]">
                {OUTREACH_STATUS_LABELS[lead.outreach_status]}
              </Badge>
              {lead.event?.url && (
                <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </div>
          </div>
        </div>
      </Card>
    </Link>
  );
}
