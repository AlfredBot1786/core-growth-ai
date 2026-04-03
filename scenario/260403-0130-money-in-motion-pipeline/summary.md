# Scenario Analysis Summary — Money in Motion Pipeline

## Overview

**Seed scenario:** Financial advisor lead generation pipeline detecting SEC filings, WARN Act layoffs, and LinkedIn job changes with Claude AI scoring
**Iterations:** 25 (bounded)
**Dimensions covered:** 12/12 (100%)
**Composite score:** 884

## Severity Breakdown

| Severity | Count | Scenarios |
|----------|-------|-----------|
| CRITICAL | 7 | #6 (filing burst), #7 (concurrent runs), #9 (mid-scoring crash), #11 (unauth webhook), #17 (Supabase failure), #21 (enrichment cascade), #24 (service role key) |
| HIGH | 11 | #2 (EDGAR down), #3 (Apollo exhausted), #10 (outreach lifecycle), #12 (API key exposure), #13 (Apify hangs), #14 (filing amendments), #15 (hallucinated data), #16 (earnings season), #19 (cross-detector correlation), #23 (prompt injection), #25 (retry storm) |
| MEDIUM | 5 | #4 (malformed XML), #5 (lookback overlap), #18 (SMTP compromise), #20 (EFTS caching), #22 (timezone mismatch) |
| LOW | 1 | #8 (unicode names) |

## Top 7 Critical Findings — Must Fix Before Production

### 1. Unauthenticated Webhook Endpoint (#11)
**Risk:** FastAPI /run endpoint exposed without auth — anyone can trigger runs, exhaust credits, and access PII in responses.
**Fix:** Add API key auth, rate limiting, IP whitelist. Strip PII from response JSON.

### 2. No Concurrent Run Protection (#7)
**Risk:** n8n retries or overlapping schedules cause double/triple runs — duplicate alerts, wasted API spend.
**Fix:** Add run lock (file lock, Redis, or DB flag). Return 409 if run in progress.

### 3. Pipeline Crash = Lost Work (#9, #17)
**Risk:** Mid-pipeline failure loses scored leads (Claude cost sunk), next run can't resume.
**Fix:** Per-lead error handling. Local JSON cache before Supabase write. Checkpoint/resume logic.

### 4. No Cost Circuit Breaker (#6, #16)
**Risk:** Earnings season or market events spike to 500+ filings — burns monthly API budgets in one run.
**Fix:** Daily/run budget caps. Max batch size. Tier-based throttling (score first 100, alert if more).

### 5. Supabase Service Role Key Exposure (#24)
**Risk:** Service role key bypasses RLS — leak exposes all PII (emails, phones, LinkedIn URLs).
**Fix:** Use anon key + RLS policies. Service role only for server-side operations with proper secrets management.

### 6. Enrichment Cascade = Silent Quality Drop (#21)
**Risk:** Both providers down → leads scored with minimal data → real T1s buried as T3 → never re-scored.
**Fix:** Track enrichment status per lead. Re-score enrichment-failed leads on next run. Alert when enrichment rate drops below threshold.

### 7. Prompt Injection via Filing Text (#23)
**Risk:** Malicious SEC filing text could manipulate Claude scoring.
**Fix:** Use structured data (not raw text) in prompts. Sanitize extracted text. System prompt hardening.

## Architectural Gaps Identified

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| No cross-detector correlation | Same person appears as 2 leads from 8-K + Form 4 | Add entity resolution layer (company + name matching) |
| No amendment handling | Form 4/A creates conflicting alerts | Link amendments to originals by CIK + filing date |
| No outreach status integration | Advisor re-alerted on contacted leads | Webhook from SBL.so/email agent → Supabase update |
| No monitoring/alerting on pipeline health | Silent failures go unnoticed | Add health check endpoint, Supabase error tracking, Slack alerts |
| No cost tracking | API spend invisible until bill arrives | Log per-run costs, daily aggregation, budget alerts |
| No lead re-scoring | Enrichment-failed leads permanently underscored | Queue for re-scoring when enrichment recovers |
| No idempotency on /run | Retries create duplicate work | Use run_id dedup, lookback window hashing |

## Dimension Coverage Matrix

| Dimension | Iterations | Findings |
|-----------|-----------|----------|
| Happy path | 1 | 1 baseline scenario |
| Error path | 1 | 1 (EDGAR unavailable) |
| Edge case | 3 | 3 (malformed XML, EFTS caching, amendments) |
| Integration | 3 | 3 (Apollo exhaustion, Apify hang, cross-detector) |
| Temporal | 3 | 3 (lookback overlap, earnings season, timezone) |
| Scale | 2 | 2 (filing burst, cascade failure) |
| Concurrent | 2 | 2 (dual runs, retry storm) |
| Data variation | 2 | 2 (unicode, unextractable 8-K) |
| Recovery | 2 | 2 (mid-scoring crash, Supabase down) |
| State transition | 1 | 1 (outreach lifecycle) |
| Abuse | 2 | 2 (unauth webhook, prompt injection) |
| Permission | 2 | 2 (API key exposure, service role key) |

## Recommendations Priority Order

1. **Before Day 1:** Add /run endpoint authentication + .gitignore verification
2. **Before Day 2:** Add per-lead error handling + run locking + local cache
3. **Before Day 3:** Add cost circuit breakers + enrichment failure alerting
4. **Before Day 5:** Add cross-detector entity resolution + amendment linking
5. **Before Day 6:** Switch to Supabase anon key + RLS, add prompt sanitization
6. **Ongoing:** Outreach integration, monitoring dashboard, re-scoring queue
