# Edge Cases & Failure Modes — Money in Motion Pipeline

## CRITICAL Failures

### 1. Filing Burst Overwhelm (Scale)
- **Trigger:** Earnings season generates 500+ filings per run
- **Impact:** Exhausts Apollo credits (10k/mo), Claude API budget blown, 50+ T1 emails cause alert fatigue
- **Missing:** Batch size limits, cost caps, intra-tier priority ranking

### 2. Concurrent Run Race Condition
- **Trigger:** n8n retry or overlapping schedule fires while run in progress
- **Impact:** Double scoring, duplicate alerts, inconsistent pipeline_runs records, 2x API cost
- **Missing:** Run lock mechanism, idempotency key, 409 response for in-progress runs

### 3. Mid-Pipeline Crash (Partial State)
- **Trigger:** Claude API error on lead #27 of 50
- **Impact:** 26 leads scored and written, 24 lost, events table shows all 50 "detected," no resume capability
- **Missing:** Per-lead try/except, checkpoint/resume, local cache before DB write

### 4. Unauthenticated /run Endpoint
- **Trigger:** Attacker discovers exposed FastAPI server
- **Impact:** Unlimited pipeline triggers, PII in JSON response, API credit drain
- **Missing:** Authentication, rate limiting, PII scrubbing from responses

### 5. Supabase Down After Scoring
- **Trigger:** Supabase maintenance or quota exceeded
- **Impact:** Sunk Claude API costs (~$0.20+ per run), no persistence, next run re-scores everything
- **Missing:** Local fallback storage, retry queue, Supabase health monitoring

### 6. Enrichment Waterfall Total Failure
- **Trigger:** Apollo AND Prospeo both return 500
- **Impact:** All leads scored with minimal data, T1 leads misclassified as T3, never re-scored
- **Missing:** Enrichment failure tracking per lead, re-score queue, enrichment rate monitoring

### 7. Service Role Key Leak
- **Trigger:** .env committed to git, or server compromise
- **Impact:** Full read/write access to all tables, PII exposure, data manipulation
- **Missing:** RLS policies, anon key usage, secrets scanning in CI

## HIGH-Impact Edge Cases

### 8. SEC EDGAR Unreachable
- No retry logic with backoff → single network blip kills entire run
- EDGAR returning HTML error page instead of JSON → unhandled parse exception
- No pipeline_run record created → silent failure

### 9. Apollo Credits Exhausted Mid-Month
- Free tier (10k/mo) depleted → silent fallback to "no enrichment"
- No alerting on credit status → discovered only when checking API dashboard
- Scoring quality degrades without anyone noticing

### 10. Filing Amendment Conflict
- Form 4/A has different accession number → treated as new lead
- Original: "50,000 shares sold @ $142" vs Amendment: "5,000 shares sold @ $142"
- Advisor gets two conflicting alerts, no amendment linking logic

### 11. Apify Actor Run Hangs
- No timeout on polling loop → pipeline blocks indefinitely
- Blocks all other detectors if run sequentially
- Hung processes accumulate if cron fires again

### 12. Claude Hallucinates From Insufficient Data
- 8-K with no extractable text → Claude infers details from company name
- Generated talking points based on fabricated executive details
- Advisor credibility destroyed by acting on hallucinated information

### 13. Cross-Detector Duplicate Leads
- CEO departure: 8-K (Item 5.02) + Form 4 (stock sale) = same person, two leads
- No entity resolution → advisor gets separate alerts for each
- Combined signal (departure + cashout) is stronger than either alone, but system can't see it

### 14. Prompt Injection via SEC Filing Text
- 8-K/WARN Act extract freeform text from filings
- Crafted filing remarks could manipulate Claude scoring
- Large injection surface area across all text-extracting detectors

### 15. n8n Retry Storm
- Pipeline returns 500 → n8n retries 4x with backoff
- Multiple retries succeed after transient failure → concurrent runs
- 3x API costs, triplicate email alerts

## MEDIUM-Impact Edge Cases

### 16. Malformed Form 4 XML
- Missing `<transactionAmounts>` element or unexpected namespace
- If not caught per-filing, one bad XML kills entire batch
- Partial data extraction (shares but no price) → misleading total_value

### 17. Lookback Window Overlap Waste
- 24h lookback with 4h runs = 20h overlap per run
- events_detected count inflated (47 "detected" but 5 new)
- Wasted compute on re-processing already-seen filings

### 18. Timezone Boundary Misses
- Server UTC, SEC filings ET, cron uses server time
- Filing at 23:59 ET Friday, pipeline at 00:01 UTC Saturday → calendar day mismatch
- Weekend filing accumulation creates Monday spike

### 19. EFTS Indexing Lag
- Filing submitted at 15:00 but EFTS hasn't indexed it yet
- If lookback = exactly run interval, filing can be missed permanently
- 24h lookback with 4h runs is safe (20h overlap) but not explicitly designed for this

### 20. SMTP Credential Compromise
- Using personal Gmail password instead of app password
- No email delivery monitoring → silent alert failure
- No rate limiting on burst sends → flagged as spam

## LOW-Impact Edge Cases

### 21. Unicode/Special Characters in Insider Names
- "José García-López" through XML parser → Apollo lookup → email HTML
- Encoding mismatches possible at each boundary
- Generally handled by modern Python 3.11+ but worth testing
