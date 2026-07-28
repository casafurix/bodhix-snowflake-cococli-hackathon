# Snowflake CoCo CLI Hackathon 2026 — Details & Winning Strategy

## Event Metadata

| | |
|---|---|
| **Prize pool** | $10,000 total |
| **Team size** | 1–4 members (individual allowed) |
| **Eligibility** | Age 18+; Software/Data Engineers, Data Scientists, AI/ML & backend devs |
| **Regions** | APJ — ASEAN, Japan, Korea, ANZ (India via separate registration) |
| **Cost** | Free |
| **Format** | Online; Grand Finale is a Demo Day |
| **Platform** | Snowflake CoCo (Cortex Code) CLI — mandatory |
| **Organizer** | Hack2skill · support+cococlihack@hack2skill.com · Discord available |

### Prizes
| Place | Amount (per team) |
|-------|-------------------|
| Winner | $4,300 / ₹4,00,000 |
| 1st runner-up | $2,200 / ₹2,00,000 |
| 2nd runner-up | $1,590 / ₹1,50,000 |
| Consolation (up to 5 teams) | $530 / ₹50,000 |

Plus: recognition in the Snowflake ecosystem, chance to present to industry experts, APJ developer-community visibility.

### Evaluation Rubric
| Criterion | Weight | What it rewards |
|-----------|:------:|-----------------|
| **Technical Execution** | **40%** | Multi-step orchestration, error handling, decision branches, strong use of CoCo CLI + Agent Skills + tools |
| Real-World Relevance | 30% | Clearly defined business problem, realistic context, **measurable impact** |
| Solution Completeness | 30% | Full end-to-end: ingestion → reasoning → actionable output, minimal manual intervention |

> **Key insight:** Technical Execution is the single heaviest lever (40%) and it explicitly rewards *orchestration + decision branches* — this should drive the choice of problem statement.

### Timeline (2026)
| Date | Milestone |
|------|-----------|
| Jun 15 | Registration opens |
| Jun 25 | Problem Statement intro session |
| Jul 2 | Workshop 1 — CoCo CLI Starter |
| Jul 9 | Workshop 2 — Hands-on CoCo CLI |
| Jul 13 | Prototype submissions open |
| Jul 23 | AMA session |
| **Aug 2** | **Registration closes** |
| **Aug 6** | **Prototype submissions close** |
| Aug 7–22 | Evaluation period |
| Aug 24 | Final shortlist announced |
| Aug 26 | Induction session |
| **Sep 1–4** | **Grand Finale (Demo Day)** |

> ⏰ As of today (Jul 28, 2026): register before **Aug 2** and submit the prototype before **Aug 6** — ~9 days out.

### Workshops (recorded, on-demand)
- **Intro Session** — Shubhangi Singh, Head of Developer Marketing India, Snowflake
- **CoCo Starter** — Abhay Singh, Staff Data Engineer (Data Analytics & AI), Snowflake
- **Hands-on with CoCo CLI** — Sarita Priyadarshini, Principal Solution Engineer, Snowflake

---

## What CoCo CLI Actually Is (matters for strategy)

CoCo (**Cortex Code**) is **an agentic shell for Snowflake — not a chatbot.** It:

- Connects to your Snowflake account with existing auth; executes SQL, manages connections
- Reads/writes local repos (great for dbt projects & Streamlit apps)
- Orchestrates tools — bash commands, git operations, SQL queries
- Is customized via **`AGENTS.md`** files and **Agent Skills** (each skill = a folder with a `SKILL.md` playbook teaching a workflow)
- Ships with **50+ bundled skills** (agent creation, ML, data engineering, governance)
- Has RBAC, OS-level sandboxing, and risk assessment built in

It sits on top of Snowflake **Cortex**:
- **Cortex Analyst** — natural language → SQL over *structured* data
- **Cortex Search** — semantic search over *unstructured* docs
- **AISQL functions** — `AI_COMPLETE`, `AI_CLASSIFY`, `AI_FILTER`, `AI_AGG`, `PARSE_DOCUMENT`, etc.

**Takeaway:** winning entries make the agent *take actions* (write back to tables, draft outputs, branch on decisions), not just answer questions.

**Docs & references**
- CoCo overview: https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code
- Bundled skills: https://docs.snowflake.com/en/user-guide/cortex-code/bundled-skills
- Agent Skills repo (Snowflake-Labs): https://github.com/Snowflake-Labs/coco-skills
- Getting started with Cortex Agents + CoCo: https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-agents-with-coco/
- Best practices for CoCo CLI: https://www.snowflake.com/en/developers/guides/best-practices-coco-cli/

---

## Recommendation: Which Problem Statement to Win With

### Pick **PS-01 — Intelligent Workflow Automation Agent**, and fold in **PS-02** (structured + unstructured fusion).

**Why PS-01:** The rubric weights Technical Execution at 40%, rewarding multi-step orchestration + decision branches. PS-01 is the *only* statement whose brief explicitly asks for "2–3 modular Agent Skills," "orchestration," and "error handling + decision branches" — i.e. it is written to score maximally on the heaviest dimension. PS-03 (NL app) and PS-04 (copilot) tend to collapse into "a nice chatbot over data," which underweights orchestration.

### Concrete build: Supply-Chain / Operations **"Anomaly-to-Action" Agent**
*(Finance / AR-collections is an equally strong swap if you prefer dollar-denominated impact.)*

The agent runs a loop — **detect → diagnose → decide → act → verify** — as **3 modular Agent Skills**:

1. **Anomaly Detector** — Cortex Analyst over structured tables (inventory, orders, shipments) flags stockout risk / demand spike / late supplier.
2. **Context Enricher** — Cortex Search + `PARSE_DOCUMENT` over *unstructured* supplier contracts / emails / delivery PDFs to explain *why* (lead-time clauses, penalty terms). ← this is the **PS-02 fusion** that makes it look far more sophisticated than a single-modality entry.
3. **Action Orchestrator** — reasons over both, then **branches**: auto-reorder vs. escalate vs. substitute supplier — writes back to a Snowflake `actions` table, drafts the PO/email, with an explicit error/guardrail path.

### Why this wins the rubric
- **Technical Execution (40%)** — genuine multi-step orchestration + real decision branches + heavy CoCo Skills usage.
- **Real-World Relevance (30%)** — dollar-quantifiable: "cut stockout response from 3 days → 3 minutes / recovered $X."
- **Solution Completeness (30%)** — clean CLI demo from raw data → written-back action, minimal human input.

It's the only shape that maxes all three pillars at once, and it fuses two problem statements into one entry.

### Why not the others
- **PS-03 / PS-04** — risk becoming an undifferentiated chatbot; weak on the 40% orchestration weight.
- **PS-02 alone** — strong, but risks being "just a search demo." Rolling its structured+unstructured fusion *into* a PS-01 agent captures the best of both.

---

---

## Sharpened Idea (informed by how hackathons are actually won)

Winning hackathon lessons that override "generic best practices":
- **Specificity wins.** Not "an AI tool for businesses" but "an AI that does *this one thing* for *this exact person*." A narrow solution to a real pain is memorable; judges have seen 100 general-purpose tools.
- **Problem before product.** Make judges *feel the pain* first, then reveal the fix. The pitch is ~half the score.
- **Idea + presentation > raw code.** AI writes the code; you win on the idea, a flawless demo, and the ability to debug live. Scalability is a *second* conversation — prove the core first.

### Put a face on the agent: **Priya, a B2B collections analyst**

Every morning Priya stares at ~200 overdue invoices and *guesses* who to chase first. She dunns the customer who already emailed a dispute (annoying a good account) while the one genuinely about to default slips another week. DSO sits at 58 days — every day is cash locked up.

**The agent does exactly one job: decide who to chase, why, and how — then draft it.** Same 3-skill architecture as PS-01, now razor-specific:

1. **Prioritizer** — Cortex Analyst over aging + payment history (structured) → risk-of-non-payment score.
2. **Context Reader** — Cortex Search + `PARSE_DOCUMENT` over the *contract* (payment terms, penalties) and the *email thread* (open dispute?) — the unstructured fusion.
3. **Action Orchestrator** — **branches**: gentle reminder / dispute-hold / escalate-to-legal / offer payment-plan → drafts the email → writes to an `actions` table.

Why collections beats a generic "ops agent": the pain is visceral and dollar-denominated ("DSO 58 → 44, $X freed"), the persona is one real human, and the data is trivial to synthesize convincingly.

---

## 9-Day Execution Plan (today Jul 28 → submit Aug 6)

> Register by **Aug 2**, submit by **Aug 6**. Don't ride the deadline.

| Day | Date | Goal |
|----|------|------|
| 1 | Jul 29 | Install CoCo CLI, connect a Snowflake trial, run a bundled skill end-to-end. Watch both workshop recordings. Lock persona = Priya / collections. |
| 2 | Jul 30 | Build synthetic dataset: structured (customers, invoices, aging, payment history) + unstructured (contract PDFs w/ payment terms, email dispute threads). Load to Snowflake; set up Cortex Search on the docs. |
| 3 | Jul 31 | **Skill 1 — Prioritizer**: Cortex Analyst over aging → risk score / ranked chase list. |
| 4 | Aug 1 | **Skill 2 — Context Reader**: Cortex Search + `PARSE_DOCUMENT` → dispute detection, payment terms, right tone. |
| 5 | Aug 2 | **Skill 3 — Action Orchestrator**: decision branch + drafted email + write-back to `actions` table. **← REGISTER TODAY (deadline).** |
| 6 | Aug 3 | Wire the full detect→read→decide→act loop in CLI; add error/guardrail path; write `AGENTS.md`. |
| 7 | Aug 4 | Polish demo: before/after metrics (DSO, cash recovered); make the run deterministic & repeatable. |
| 8 | Aug 5 | Record demo video; write submission writeup; buffer for bugs. |
| 9 | Aug 6 | Final review + **submit** (early, not at midnight). |

---

## Pitch Skeleton (problem-first — feel the pain, then the fix)

1. **The pain (15s):** "Meet Priya, a collections analyst. Every morning: 200 overdue invoices, no idea who to chase first. She nags a customer who already disputed, misses the one about to default. DSO is 58 days — that's $X in frozen cash."
2. **The turn (5s):** "What if an agent did that triage overnight — and knew each customer's contract and email history?"
3. **The demo (60s):** Live CLI run — agent scores the list, reads the contract + email thread, **branches** (reminder vs. dispute-hold vs. escalate), drafts the message, logs the action. Show one guardrail/error case handled gracefully.
4. **The impact (10s):** "On our test set it prioritized correctly across N invoices — DSO 58 → 44, $X freed, zero good customers wrongly dunned."
5. **The close (10s):** "It's 3 modular CoCo Agent Skills — drop in any Snowflake account's AR data and it runs. Scaling to full AP/AR is the next step." (Scalability = the second conversation, only after the core lands.)

---

## Team Input & Synthesis (Eirene + casafurix)

### What the team proposed
- **Eirene — autonomous analytics loop:** a system that runs on its own (daily / weekly / monthly), detects sales growth or downfall, finds the *reasons*, generates reports, and gives specific suggestions ("this product isn't working, this one's in demand → do X"). Humans just **verify**; once approved, the **agent applies the fix itself**. Not one-off Q&A — a self-running analyst.
- **Eirene — PS read:** PS-01 doable with room for creative showstopper features; PS-02 risky (hallucination on unstructured data unless data is refined); PS-03 = crowded "AI assistant" space; PS-04 = basically a chatbot, only good with a strong niche.
- **casafurix:** combining multiple PS into one solution is "godly"; but the crucial thing is a **specific problem / narrow niche** where we can literally say "we solved *this* problem for *this* userbase."

### My assessment
- **Eirene's autonomy loop is the stronger *shape*** than a reactive triage — it maps directly onto PS-01's "autonomously execute" and "minimal manual intervention." The **verify → auto-apply gate is the showstopper**: most teams stop at insight and never *act*; an approval checkpoint + real action execution is what makes judges take notice.
- **Guard against the generic-tool trap:** "analyze any pattern, suggest anything" is exactly what the Reddit thread warns against, and it maximizes hallucination surface. Keep the autonomy but **bind it to one domain + a bounded menu of action types** (reorder / discount / delist / reallocate spend — not "anything").
- **Eirene's PS ratings are correct.** The PS-02 hallucination point is the reason to use unstructured data in a **bounded, retrieval-grounded, cited** way (Cortex Search over a few docs for the "why"), not as the whole product.
- **casafurix is right on both counts** — combine PS-01 + a slice of PS-02, and pin it to one named userbase.

### Unified concrete idea — "Merchandising Autopilot"
Persona: **Arjun, a merchandising manager at a mid-size D2C brand (~500 SKUs).** Every Monday he manually digs through sales reports, guesses which products are tanking vs. trending and *why*, then gut-decides reorders / discounts / delisting.

The agent, as a scheduled autonomous loop:
1. **Runs daily/weekly/monthly analysis on its own** — Cortex Analyst over sales/inventory (structured) → flags a SKU's growth or downfall against trend.
2. **Diagnoses the "why"** — Cortex Search + `PARSE_DOCUMENT` over **customer reviews + support tickets** (bounded, cited PS-02 unstructured fusion) → e.g., "returns spiked, reviews cite sizing."
3. **Recommends a bounded action + report** — reorder / discount / delist / reallocate spend, with the evidence.
4. **Human verifies → agent auto-applies** — writes to the reorder/pricing table, drafts the supplier PO. Approval gate + guardrail/rollback path = the showstopper.

This single flow contains **all three teammate ideas** (autonomy, verify-then-apply, narrow niche) **and all three problem-statement themes** (PS-01 orchestration + PS-02 unstructured + PS-03/04-style NL interaction), pinned to one named person.

> **Domain is still swappable** on the same architecture: collections/finance (Priya) or retail merchandising (Arjun). Pick by **which realistic dataset we can build most convincingly** — the team is leaning retail/sales, which fits Eirene's framing.

### Open decision for the team
- **Domain:** retail merchandising (Arjun) vs. finance collections (Priya) — decide by data availability. *Leaning: retail.*
- **Auto-apply scope:** keep "apply" = writing to a Snowflake table / drafting a PO (safe, demoable). Do **not** promise writing to a live production ERP.

---

## Defensibility — Beating the "Everyone Uses AI for Ideas" Problem

**The risk:** ~200 teams prompting an AI for "winning PS-01 idea" will converge on the same category — "autonomous ops/finance/retail analyst that suggests and acts." We cannot out-*idea* the field; the idea generator is shared. Differentiation must come from what AI **can't** hand a competitor.

### Three real moats (none of them is idea novelty)

1. **Insider domain knowledge.** AI gives generic *retail*. A team that actually worked in a specific vertical knows the unsexy pain + weird domain rules a generic prompt never surfaces — and that specificity is what makes the demo ring true and what a category-level copycat can't fake. **Biggest lever: pick the niche from a teammate's lived experience, not from AI's default list.**
2. **A Snowflake-native moat.** The test that makes the idea non-reproducible by a standalone Claude agent: *why must this live inside CoCo/Snowflake?* Answer = the moat — governed action write-back with **audit trail + RBAC**, running *where the enterprise data already sits*, combining Cortex Analyst + Search + AISQL in one governed loop. Pitch: "a generic AI agent can *suggest*; ours *acts inside the governed data cloud with an audit trail and role-based guardrails* — the version an enterprise would actually deploy."
3. **The closed act → verify → govern loop, not the analytics.** Analytics suggestions are the commoditized 90% everyone builds. The defensible 10% is governed execution with human approval, rollback, and audit (Eirene's verify-then-auto-apply gate). Lean the whole demo on that.

### Under-suggested niches (only if someone knows one)
AI defaults to retail / sales / finance / support. Higher-specificity, lower-competition verticals: freight/logistics brokerage margin leakage · QSR/restaurant food-waste & par-levels · insurance claims adjudication · clinic revenue-cycle denials · wholesale distributor rebate reconciliation · field-service parts forecasting · agri-commodity procurement.

### The decisive question for the team
**Does anyone have insider knowledge of — or realistic data from — a specific industry?** That answer picks the domain; it's our one unfair advantage. Merchandising/collections are acceptable *fallbacks* if nobody has a niche, but a domain a teammate actually lived beats both.

> **Principle:** We don't win on a novel idea (impossible — shared generators). We win on **domain-authentic specificity + a flawless narrow demo + a Snowflake-native governed action loop** a generic agent can't replicate.

---

## Real-World Pain Research (grounding the niche in actual unsolved problems)

> **Method note:** Reddit is blocked to the research crawler (both search and fetch), so these aren't literal Reddit quotes — they're the *same pains* corroborated by adjacent industry sources plus cited community sentiment (r/dataengineering, r/Accounting). Upside: every pain below comes with **hard numbers**, which directly feed the "measurable impact" rubric line (30%).

### Ranked pains

| Pain | Evidence (quantified) | PS fit | Snowflake moat | Crowded? |
|------|-----------------------|--------|----------------|----------|
| **Month-end close: reconciliation + "why did the number change"** | ~90 sec/transaction for a 2-person team; data split across CSV + vendor **PDF** statements + different charts of accounts; r/Accounting calls it a bottleneck of endless emails & re-exports | **PS-01 + PS-02** (PDF statements + structured GL) — near-perfect | **Very high** — financial data already in the warehouse; governed, **audit-trailed** write-back of adjusting entries is a real enterprise need | Low–med |
| **Freight brokerage margin leakage** | Mid-market broker loses **~$2.7M/yr** margin; 60% lose loads to slow quotes; pricing teams burn 4–6 hrs/week in spreadsheets | PS-01 (reframed as lane-profitability / carrier analytics) | High — lane/rate/carrier analytics fits the warehouse | **Low (under-suggested)** — needs domain data |
| **AR collections** (Priya) | **33%** of B2B invoices unpaid at 90 days; SMBs lack an AR team; fixed 45/60-day escalation cadence | PS-01 + PS-02 (contracts/email) | Med–high | Medium |
| **Restaurant par-levels / food waste** | **43%** of over-ordering is "habit not data"; automated par alerts cut over-ordering **18–28%** | PS-01 | **Low** — small restaurants aren't on Snowflake (needs chain/distributor angle) | Low |
| **MSP/IT ticket triage** | Triage errors cost an MSP **$80–120K/yr**; manual sorting = "surviving the queue" | PS-01 + PS-02 (tickets) | Low — tickets live in Zendesk, not Snowflake | **High (very crowded)** |
| **Recurring analytics/reporting** | 847 hrs/yr cleaning Excel; **50%** of data engineers cite manual processes as a top pain | PS-01 / PS-03 | Medium (generic) | **Highest — the AI-default trap** |

### Updated top pick: **Month-End Financial Close Agent**

It's the only option that simultaneously:
- Has a painful, quantified, *specific* workflow (not "generic analytics").
- Forces the **structured + unstructured fusion** naturally — vendor **PDF statements** vs. the **GL** (PS-02 inside PS-01).
- Hands us the **Snowflake-native moat for free** — governed, **auditable write-back of adjusting entries** is something a generic Claude agent can't do credibly, and exactly what a finance team needs.

Flow = Eirene's loop landing on a workflow judges recognize: **reconcile → flag variance → diagnose "why" (read the PDF statement / notes) → propose adjusting entry → human verifies → agent posts it (with audit trail).**

**Freight brokerage** = the highest-*defensibility* alternative (AI never defaults to it; "$2.7M margin leak" is a killer pitch number) — pick it only if a teammate has domain knowledge or we can build convincing lane/rate data.

### Sources
- Excel/reporting drudgery: [DEV — "847 hours cleaning Excel"](https://dev.to/vimal-patel/i-wasted-847-hours-last-year-cleaning-excel-files-heres-how-i-got-my-life-back-4hn3); [data.world — data engineer burnout survey](https://data.world/blog/why-so-blue-5-reasons-data-engineers-are-burnt-out)
- Collections: [Allianz-Trade — B2B debt collection (33% unpaid at 90 days)](https://www.allianz-trade.com/en_SG/insights/risk-management/how-does-business-debt-collection-work.html)
- Restaurant par-levels: [Supy — inventory techniques to reduce food waste](https://supy.io/blog/inventory-techniques-to-reduce-food-waste-in-restaurants)
- Freight brokerage: [Freightify — why spreadsheets fail freight pricing teams](https://freightify.com/blog/rethinking-pricing-in-freight-forwarding-beyond-spreadsheets); [LoadStop — inbound freight quote automation](https://loadstop.com/blog/inbound-freight-quote-automation)
- Ticket triage: [ConnectWise — automated ticket triage](https://www.connectwise.com/solutions/automated-ticket-triage); [Mizo — MSP triage priority matrix](https://mizo.tech/blog/ticket-triage-best-practices-priority-matrix/)
- Month-end close: [Numeric — month-end reconciliation](https://www.numeric.io/blog/month-end-reconciliation); [Tier2 Systems — real cost of manual matching](https://tier2systems.com/en/blog/account-reconciliation-costs/)
