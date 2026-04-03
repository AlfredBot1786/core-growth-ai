# Money in Motion — Opportunity Generator for Financial Advisors

## System Overview

A lead generation pipeline that detects "money in motion" events — moments when individuals experience financial transitions that create opportunities for financial advisory services. The system monitors public data sources, enriches contacts, scores leads with Claude AI, and routes actionable opportunities to advisors via email alerts and outreach sequences.

## Architecture

```
Detectors → Dedup → Enrichment Waterfall → Claude Scoring → Routing → Alerts/Outreach
    ↓                                            ↓                        ↓
  EDGAR API                                  Supabase                  Email/LinkedIn
  Apify (LinkedIn)                         (persistence)              (SBL.so, SMTP)
```

## Components

### 1. Detectors (4 sources)

#### SEC Form 4 Detector
- **Source:** Free EDGAR full-text search API (EFTS)
- **Signal:** Insider stock transactions (purchases, sales, option exercises)
- **Data extracted:** Transaction type, shares traded, price per share, total value, insider title, securities type
- **XML enrichment:** Parses Form 4 XML for detailed transaction data
- **Rate limit:** Max 10 requests/second to SEC (requires CONTACT_EMAIL in User-Agent header)
- **Lookback:** Default 24 hours

#### SEC 8-K Detector
- **Source:** Free EDGAR API
- **Signal types:**
  - Item 5.02: Executive departures/appointments
  - Item 2.05: Restructurings/layoffs
  - Items 1.01/2.01: M&A events
- **Data extracted:** Executive names, affected employee counts from filing HTML
- **Lookback:** Default 48 hours

#### WARN Act Detector
- **Source:** Two approaches:
  1. EDGAR 8-K filings searched for workforce reduction language
  2. State WARN database scraping with heuristic HTML parsing
- **Data extracted:** Affected employee counts via regex ("approximately 500 employees")
- **Configuration:** TARGET_STATES env var (e.g., CO,CA,NY,TX,FL)
- **Lookback:** Default 168 hours (7 days, filed less frequently)

#### LinkedIn Job Changes Detector
- **Source:** Apify actor runs against LinkedIn
- **Flow:** Start actor run → poll for completion → fetch dataset → parse for job change signals
- **Configuration:** TARGET_COMPANY_URLS env var with LinkedIn company URLs
- **Cost:** Apify free tier = 500 actor runs/month

### 2. Deduplication
- Events are deduped before enrichment/scoring
- Uses accession numbers (SEC) or unique identifiers per source

### 3. Enrichment Waterfall
- **Primary:** Apollo.io API (free plan: 10,000 credits/month)
  - Returns: emails, phone numbers, LinkedIn URLs, job titles
- **Fallback:** Prospeo.io ($39/mo for 1,000 credits)
- **Architecture:** BaseEnrichmentProvider interface, extensible to add Snov.io or others
- **Graceful degradation:** Pipeline continues if enrichment fails or keys not configured

### 4. Claude AI Lead Scoring
- **Model:** Claude Sonnet
- **Cost:** ~800 tokens per scoring call, ~$0.10-0.20 per 50 leads
- **Output per lead:**
  - Numeric score (0-100)
  - Tier assignment (T1: 70+, T2: 40-69, T3: <40)
  - Situation brief (narrative summary)
  - Talking points for the advisor
- **4 prompt templates** (one per event type):
  - Form 4: Equity compensation opportunities
  - 8-K: Executive transition / M&A planning
  - WARN Act: 401k rollovers, severance planning
  - LinkedIn: Career transition financial planning
- **Prompts separated from scorer logic** for independent iteration

### 5. Supabase Storage (3 tables)
- **events:** Raw detected filings/signals
- **scored_leads:** Scored entries with situation briefs, enrichment data, outreach_status
- **pipeline_runs:** Run records with counts (events_detected, events_new, t1/t2/t3_count, alerts_sent, errors)
- **Indexes and updated_at trigger** created via setup_supabase.sql

### 6. Routing & Alerts
- **T1 leads (score 70+):** HTML email alert with full situation brief, talking points, SEC filing link
- **T2 leads (score 40-69):** Queued for email sequences
- **T3 leads (score <40):** Stored but no action
- **SMTP config:** Gmail App Passwords supported
- **Outreach channels:**
  - SBL.so for LinkedIn connection requests + voice notes (T1)
  - Email agent for T2 sequences
  - outreach_status field tracks: sent/responded/meeting_booked

### 7. Entry Points
- **CLI:** `python -m src.main --run-once --lookback 24`
  - Flags: --dry-run, --detector (all/sec_form4/sec_8k/warn_act/linkedin), --lookback N
- **FastAPI webhook server:** `python -m src.server`
  - POST /run endpoint returns full run summary as JSON

### 8. Scheduling
- **Option A:** n8n Cloud — Schedule Trigger (every 4 hours) → HTTP POST to FastAPI server
- **Option B:** Cron job — `0 */4 * * *` running CLI directly

## Implementation Details

- **Language:** Python 3.11+
- **Size:** 38 files, ~3,800 lines
- **Test suite:** 20+ test cases (model validation, XML parsing, prompt generation, outreach routing, rate limiting)
- **Tests run without API keys** (mocked data)
- **Modular architecture:** Bug in WARN Act detector doesn't touch Form 4 pipeline

## Deployment Phases

1. **Foundation:** Repo setup, Supabase tables, env vars (Day 1)
2. **Validate Detector:** Test Form 4 in isolation, dry run full pipeline, run live (Day 1-2)
3. **Add Enrichment:** Apollo.io setup, optional Prospeo fallback (Day 2-3)
4. **Add Email Alerts:** SMTP config for T1 alerts (Day 3)
5. **Add More Detectors:** 8-K, WARN Act, LinkedIn (Day 4-5)
6. **Automate:** n8n Cloud or cron scheduling (Day 5-6)
7. **Monitor & Iterate:** Pipeline health checks, prompt tuning, outreach connection (Ongoing)

## Critical Path
Steps 1-6 first. Everything builds on detector → scorer → storage pipeline working.
Cheapest test: Steps 1-5 cost $0 (EDGAR free, Supabase free, dry run skips Claude). Step 6 adds ~$0.20 in Claude API.

## Known Dependencies
- SEC EDGAR EFTS API (free, public, rate-limited)
- Anthropic Claude API (paid)
- Supabase (free tier available)
- Apollo.io (free tier: 10k credits/mo)
- Prospeo.io (optional, $39/mo)
- Apify (optional, free tier: 500 runs/mo)
- SMTP provider (Gmail or similar)
- n8n Cloud or cron for scheduling
- SBL.so for LinkedIn outreach (optional)
