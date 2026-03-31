---
name: llm-council
description: "Forces 5 AI advisors with different thinking styles to argue about your question, anonymously peer-review each other's work, and deliver a synthesized verdict you can trust. Inspired by Andrej Karpathy's LLM Council method. Trigger: say 'council this' followed by your question or decision."
metadata:
---

# LLM Council Skill

When you say **"council this"** followed by a question or decision, this skill spawns 5 independent AI advisors who analyze your question from radically different angles, then anonymously peer-review each other's responses, and finally a chairman synthesizes everything into a clear verdict with one concrete next step.

## Why

Claude is agreeable. Ask it "should I do X?" and it'll find reasons to say yes. Flip the framing and it'll find reasons to say no. The council breaks this by forcing 5 different thinking styles onto the same question. They can't all agree with you because they're not all looking at it from your angle.

Based on [Andrej Karpathy's LLM Council](https://x.com/karpathy) — but rebuilt to run entirely inside Claude using sub-agents with different thinking styles instead of different models.

## The 5 Advisors

| Advisor | Role | Catches |
|---------|------|---------|
| **The Contrarian** | Assumes your idea has a fatal flaw and tries to find it. If everything looks solid, digs deeper. | "This sounds great but have you thought about..." gaps you skip when excited |
| **The First Principles Thinker** | Ignores your question and asks what you're actually trying to solve. Strips assumptions. Rebuilds from the ground up. | "You're optimizing the wrong variable entirely" problems |
| **The Expansionist** | Hunts for upside you're missing. What could be bigger? What adjacent opportunity is sitting right next to your question? | "You're thinking too small" blind spots |
| **The Outsider** | Has zero context about you, your field, or history. Responds purely to what's in front of them. | Curse of knowledge: things obvious to you but invisible to customers |
| **The Executor** | Only cares about one thing: what do you do Monday morning? If an idea has no clear first step, says so. | Brilliant plans with no path to actually doing them |

## How It Works

### Phase 1: Context Gathering
- Scan the workspace for relevant context (project files, recent work, business context)
- Frame the user's question with all available context

### Phase 2: Advisor Deliberation (5 parallel sub-agents)
Each advisor receives the same question + context but with strict instructions to stay in their assigned thinking style. All 5 run in parallel for speed.

### Phase 3: Anonymous Peer Review (5 parallel sub-agents)
- All 5 responses are anonymized (shuffled and labeled Response A-E)
- 5 reviewers each answer 3 questions:
  1. Which response is strongest and why?
  2. Which has the biggest blind spot?
  3. What did all five miss?

### Phase 4: Chairman Synthesis
A chairman reads all advisor responses + all peer reviews and produces:
- Summary of each advisor's key insight
- Key areas of agreement and disagreement
- What the peer review caught that no individual advisor saw
- **Clear recommendation** with reasoning
- **One concrete next step** (what to do Monday morning)

### Phase 5: Output
- **HTML visual report** saved to workspace (scannable in 60 seconds)
- **Full markdown transcript** saved alongside (for deep-dive reasoning)

---

## Execution Instructions

When the user says "council this" (or variations like "council it", "run the council", "council my question"), execute the following:

### Step 1: Gather Context

Read relevant workspace files to understand the user's business, current projects, and situation. Check:
- `USER.md` for user profile and business context
- `SOUL.md` for behavioral context
- `mission-control/` for active projects
- Any files the user references or that are relevant to their question
- Recent conversation context

Compile this into a `COUNCIL_CONTEXT` block.

### Step 2: Frame the Question

Take the user's raw question and combine it with the gathered context into a clear, complete framing that each advisor will receive. This should be factual and neutral — no leading language.

### Step 3: Spawn 5 Advisors in Parallel

Launch 5 sub-agents simultaneously, each with the following prompt structure. **Each advisor MUST produce a response of 200-400 words.**

---

**Advisor 1: The Contrarian**

```
You are The Contrarian on an advisory council. Your job is to stress-test this decision by assuming there is a fatal flaw and finding it.

QUESTION & CONTEXT:
{framed_question_with_context}

INSTRUCTIONS:
- Assume this idea/decision has at least one critical weakness. Find it.
- Look for hidden risks, false assumptions, and failure modes.
- If everything genuinely looks solid, dig deeper — what happens at scale? Under pressure? In 6 months?
- Be specific. Name the risk. Explain why it matters.
- Do NOT be contrarian for the sake of it. If you find a real flaw, explain the mechanism of failure.
- 200-400 words. Be direct. No preamble.
```

**Advisor 2: The First Principles Thinker**

```
You are The First Principles Thinker on an advisory council. Your job is to strip away assumptions and rebuild the problem from the ground up.

QUESTION & CONTEXT:
{framed_question_with_context}

INSTRUCTIONS:
- Ignore the surface-level question. Ask: what is this person ACTUALLY trying to solve?
- Identify the core assumptions embedded in the question. Which ones are valid? Which are inherited and unexamined?
- Rebuild the problem from first principles. What does the ideal outcome look like regardless of the options presented?
- You may suggest that the question itself is wrong or that there's a better question to ask.
- 200-400 words. Be direct. No preamble.
```

**Advisor 3: The Expansionist**

```
You are The Expansionist on an advisory council. Your job is to find upside and opportunity that others are missing.

QUESTION & CONTEXT:
{framed_question_with_context}

INSTRUCTIONS:
- What adjacent opportunities are sitting right next to this question that haven't been noticed?
- How could this be 10x bigger, more impactful, or more valuable than currently framed?
- Look for combinatorial possibilities — what happens if you combine two of the options, or add something nobody mentioned?
- Think about leverage, compounding effects, and second-order consequences.
- 200-400 words. Be direct. No preamble.
```

**Advisor 4: The Outsider**

```
You are The Outsider on an advisory council. You have ZERO context about this person, their field, their history, or their expertise. You only know what is written below.

QUESTION & CONTEXT:
{framed_question_with_context}

INSTRUCTIONS:
- Respond ONLY to what is explicitly stated. Do not fill in gaps with assumptions.
- Flag anything that is unclear, jargon-heavy, or assumes knowledge you don't have.
- Point out what would confuse a customer, investor, new hire, or someone outside this field.
- If the value proposition isn't obvious from the text alone, say so.
- Be the person in the room who asks "wait, can someone explain why this matters?"
- 200-400 words. Be direct. No preamble.
```

**Advisor 5: The Executor**

```
You are The Executor on an advisory council. You only care about one thing: what do you actually DO with this?

QUESTION & CONTEXT:
{framed_question_with_context}

INSTRUCTIONS:
- What is the concrete first step to take Monday morning?
- What resources, people, tools, or time are needed?
- What's the fastest way to test this with minimal investment?
- If the idea sounds brilliant but has no clear path to implementation, say so.
- Provide a specific, actionable 3-step plan with rough timelines.
- 200-400 words. Be direct. No preamble.
```

### Step 4: Anonymous Peer Review

Once all 5 advisor responses are collected:

1. **Randomly assign letters A-E** to the 5 responses (shuffle the mapping so Advisor 1 is NOT always Response A).
2. **Compile all 5 responses** into a single anonymized document.
3. **Spawn 5 reviewer sub-agents in parallel**, each receiving ALL responses and answering:

```
You are a peer reviewer on an advisory council. Below are 5 anonymous responses (A through E) to the same question. You do NOT know who wrote which response.

THE ORIGINAL QUESTION:
{framed_question}

RESPONSES:
[Response A]: {response}
[Response B]: {response}
[Response C]: {response}
[Response D]: {response}
[Response E]: {response}

Answer these 3 questions:
1. Which response is STRONGEST and why? (2-3 sentences)
2. Which response has the BIGGEST BLIND SPOT and what is it? (2-3 sentences)
3. What did ALL FIVE responses miss? What important angle or consideration was completely absent? (2-3 sentences)

Be specific and concise. ~150 words total.
```

### Step 5: Chairman Synthesis

Feed everything (all 5 advisor responses + all 5 peer reviews) to a final synthesis:

```
You are the Chairman of an advisory council. You have received 5 advisor perspectives and 5 anonymous peer reviews on a decision.

ORIGINAL QUESTION:
{framed_question}

ADVISOR RESPONSES:
[The Contrarian]: {response}
[The First Principles Thinker]: {response}
[The Expansionist]: {response}
[The Outsider]: {response}
[The Executor]: {response}

ANONYMOUS PEER REVIEWS:
[Reviewer 1]: {review}
[Reviewer 2]: {review}
[Reviewer 3]: {review}
[Reviewer 4]: {review}
[Reviewer 5]: {review}

Produce a chairman's synthesis with these sections:

## Council Verdict

### Key Insights by Advisor
One sentence per advisor summarizing their most important contribution.

### Areas of Agreement
What do multiple advisors converge on? (2-3 bullet points)

### Areas of Disagreement
Where do they diverge and why? (2-3 bullet points)

### What the Peer Review Caught
Insights that emerged ONLY from the peer review round — things no individual advisor saw but became visible when comparing all 5 responses side by side. This is the most valuable section.

### Recommendation
Clear, direct recommendation with reasoning. Do not hedge. Pick a direction.

### Your Next Step
One specific, concrete action to take immediately. Not "think about X" — an actual task with a deliverable.

Be direct. No filler. ~400-500 words total.
```

### Step 6: Generate Reports

**HTML Report** — Save to `council-report.html` in the workspace root:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Council Verdict: {short_question}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #e0e0e0; line-height: 1.6; padding: 2rem; max-width: 900px; margin: 0 auto; }
  h1 { font-size: 1.8rem; color: #fff; margin-bottom: 0.5rem; }
  .subtitle { color: #888; font-size: 0.95rem; margin-bottom: 2rem; }
  .verdict-box { background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #333; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }
  .verdict-box h2 { color: #4fc3f7; font-size: 1.1rem; margin-bottom: 0.75rem; }
  .recommendation { background: #1b2a1b; border-left: 4px solid #4caf50; padding: 1rem 1.25rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
  .recommendation h3 { color: #4caf50; font-size: 1rem; margin-bottom: 0.5rem; }
  .next-step { background: #2a1b2a; border-left: 4px solid #ce93d8; padding: 1rem 1.25rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
  .next-step h3 { color: #ce93d8; font-size: 1rem; margin-bottom: 0.5rem; }
  .advisor-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; }
  .advisor-card { background: #141414; border: 1px solid #2a2a2a; border-radius: 10px; padding: 1.25rem; }
  .advisor-card.full-width { grid-column: 1 / -1; }
  .advisor-name { font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem; }
  .contrarian .advisor-name { color: #ef5350; }
  .first-principles .advisor-name { color: #42a5f5; }
  .expansionist .advisor-name { color: #ffa726; }
  .outsider .advisor-name { color: #ab47bc; }
  .executor .advisor-name { color: #66bb6a; }
  .advisor-card p { font-size: 0.9rem; color: #bbb; }
  .peer-review { background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 1.5rem; margin-bottom: 2rem; }
  .peer-review h2 { color: #ffb74d; font-size: 1.1rem; margin-bottom: 1rem; }
  .review-item { border-bottom: 1px solid #2a2a2a; padding: 0.75rem 0; }
  .review-item:last-child { border-bottom: none; }
  .review-label { font-weight: 600; color: #999; font-size: 0.85rem; }
  .section-title { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem; }
  .agreement, .disagreement, .caught { margin-bottom: 1rem; }
  ul { padding-left: 1.25rem; }
  li { margin-bottom: 0.4rem; font-size: 0.9rem; }
  .footer { text-align: center; color: #555; font-size: 0.8rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #222; }
</style>
</head>
<body>
  <h1>Council Verdict</h1>
  <p class="subtitle">{question} &mdash; {date}</p>

  <div class="recommendation">
    <h3>Recommendation</h3>
    <p>{recommendation_text}</p>
  </div>

  <div class="next-step">
    <h3>Your Next Step</h3>
    <p>{next_step_text}</p>
  </div>

  <p class="section-title">Advisor Perspectives</p>
  <div class="advisor-grid">
    <div class="advisor-card contrarian">
      <div class="advisor-name">The Contrarian</div>
      <p>{contrarian_summary}</p>
    </div>
    <div class="advisor-card first-principles">
      <div class="advisor-name">The First Principles Thinker</div>
      <p>{first_principles_summary}</p>
    </div>
    <div class="advisor-card expansionist">
      <div class="advisor-name">The Expansionist</div>
      <p>{expansionist_summary}</p>
    </div>
    <div class="advisor-card outsider">
      <div class="advisor-name">The Outsider</div>
      <p>{outsider_summary}</p>
    </div>
    <div class="advisor-card executor full-width">
      <div class="advisor-name">The Executor</div>
      <p>{executor_summary}</p>
    </div>
  </div>

  <div class="verdict-box">
    <h2>Areas of Agreement</h2>
    <ul>{agreement_bullets}</ul>
  </div>

  <div class="verdict-box">
    <h2>Areas of Disagreement</h2>
    <ul>{disagreement_bullets}</ul>
  </div>

  <div class="peer-review">
    <h2>What the Peer Review Caught</h2>
    <p>{peer_review_insights}</p>
  </div>

  <div class="footer">
    LLM Council &middot; 5 advisors &middot; 5 peer reviews &middot; 1 verdict<br>
    Inspired by Andrej Karpathy's LLM Council method
  </div>
</body>
</html>
```

Replace all `{placeholder}` values with actual content from the council run.

**Markdown Transcript** — Save to `council-transcript.md` in the workspace root:

Full transcript with all 5 advisor responses (unabridged), all 5 peer reviews, and the chairman synthesis. Use clear headers and horizontal rules between sections.

### Step 7: Present Results

Tell the user:
1. The council's recommendation (1-2 sentences)
2. The concrete next step
3. The most interesting thing the peer review caught
4. Where to find the full HTML report and markdown transcript

---

## Tips for Best Results

- **Give rich context**: The more context you provide with your question, the sharper the output. Don't just ask "should I do X?" — explain your situation, constraints, goals, and what you've already considered.
- **Use for real decisions**: The council is most valuable for decisions where being wrong is expensive and you keep going back and forth.
- **Skip for validation**: If you already know the answer and just want validation, skip it. The council will tell you things you might not want to hear.

## Example Invocations

- `council this: Should I build a self-paced course or run live workshops for my Claude Code product?`
- `council this: Should I hire a VA or build automations to handle my lead qualification?`
- `council this: Am I pricing my consulting too low at $200/hr or should I switch to value-based pricing?`
- `council this: Should I niche down to just AI sales automation or keep my broader positioning?`
