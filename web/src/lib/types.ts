export type EventType = "sec_form4" | "sec_8k" | "warn_act" | "linkedin";

export type Tier = "T1" | "T2" | "T3";

export type OutreachStatus =
  | "pending"
  | "contact_found"
  | "linkedin_sent"
  | "responded"
  | "meeting_booked"
  | "declined";

export interface Event {
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
}

export interface ScoredLead {
  lead_id: string;
  event_id: string;
  score: number;
  tier: Tier;
  situation_brief: string;
  talking_points: string[];
  outreach_status: OutreachStatus;
  scored_at: string;
  created_at: string;
  updated_at: string;
  // Joined from events table
  event?: Event;
}

export interface PipelineRun {
  run_id: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  events_detected: number;
  events_new: number;
  t1_count: number;
  t2_count: number;
  t3_count: number;
  alerts_sent: number;
  errors: string[];
  scoring_failures: number;
  api_cost_estimate: number;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  team_id: string | null;
  role: "admin" | "advisor";
  notification_prefs: {
    email_t1: boolean;
    email_t2: boolean;
    push_t1: boolean;
  };
  created_at: string;
}

export interface Team {
  team_id: string;
  name: string;
  created_at: string;
}

export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  sec_form4: "SEC Form 4",
  sec_8k: "SEC 8-K",
  warn_act: "WARN Act",
  linkedin: "LinkedIn",
};

export const TIER_CONFIG: Record<
  Tier,
  { label: string; color: string; bg: string; border: string }
> = {
  T1: {
    label: "Hot Lead",
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
  },
  T2: {
    label: "Warm Lead",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
  },
  T3: {
    label: "Stored",
    color: "text-zinc-400",
    bg: "bg-zinc-500/10",
    border: "border-zinc-500/20",
  },
};

export const OUTREACH_STATUS_LABELS: Record<OutreachStatus, string> = {
  pending: "Pending",
  contact_found: "Contact Found",
  linkedin_sent: "LinkedIn Sent",
  responded: "Responded",
  meeting_booked: "Meeting Booked",
  declined: "Declined",
};
