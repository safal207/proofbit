# ProofBit Commercial Wedge

## Executive decision

Do **not** lead with a processor sale.

The fastest path to revenue is a software-first proof-carrying action guard for consequential AI-agent operations. ProofBit supplies the semantics, fault corpus, conformance model, and future acceleration path. The commercial product can be called **ProofPath Deployment Guard** or **Proof-Carrying Action Guard**.

## Customer problem

AI agents increasingly perform actions rather than only generate text:

- production deployment;
- merge and release operations;
- IAM and cloud configuration;
- wallet and payment actions;
- smart-contract administration;
- destructive database or infrastructure changes;
- data export and secret-bearing tool calls.

Existing systems often record that a tool was called but cannot answer, in one portable evidence package:

1. Who requested the action?
2. What exact action was requested?
3. Which authority and policy allowed it?
4. Which artifact and system state were checked?
5. Was the authorization still fresh at execution time?
6. Was the authorization replayed or rebound to another action?
7. What actually happened after dispatch?

The paid outcome is not “a special bit.” It is a defensible answer to those questions.

## First product

### ProofPath Deployment Guard

One-line promise:

> **A consequential AI-agent action cannot reach the production effect boundary until intent, authority, policy, evidence, exact request binding, and current state have been checked; every allowed, rejected, or held action receives a verifiable record, and every execution receives a separate outcome receipt.**

Core flow:

```text
Action Request
-> Evidence collection
-> Policy evaluation
-> ACCEPT / REJECT / HOLD
-> Clearance / Permit
-> mandatory deployment or action gateway
-> Execution Receipt
-> offline verification and audit export
```

### Initial buyer profiles

Prioritize teams where one wrong autonomous action is materially expensive but a pilot can still be integrated quickly:

1. AI-native SaaS using coding or cloud agents;
2. platform engineering and DevSecOps teams;
3. fintech infrastructure with agentic payment or wallet workflows;
4. smart-contract teams with privileged administrative actions;
5. regulated companies introducing AI-assisted deployment or operations;
6. security vendors that need an independently testable action-assurance layer.

Avoid starting with broad consumer payments, insurance promises, a token marketplace, or “universal AI safety.”

## 14-day design-partner pilot

### Scope

```text
1 repository or action service
1 production-like workflow
1 target environment
1 policy pack
1 mandatory action gateway
6–12 adversarial scenarios
100–1,000 action evaluations
```

Required artifacts:

- canonical Action Request;
- authority and approval evidence;
- artifact or payload digest binding;
- policy version and epoch;
- `ACCEPT`, `REJECT`, or `HOLD` reason codes;
- consume-once permit or clearance;
- mandatory executor/gateway verification;
- separate execution/outcome receipt;
- offline verifier;
- pilot assurance report;
- regression fixtures retained in CI.

### Minimum fault scenarios

- artifact/request mismatch;
- missing approval;
- stale authority or epoch;
- state drift after approval;
- replayed permit;
- statement/action rebinding;
- provenance loss;
- false success after dispatch;
- alternate execution path that skips application validation;
- tampered evidence bundle;
- conflicting outcome;
- rollback or old-policy injection.

### Target metrics

```text
unsafe injected actions executed    = 0
certificate / permit verification   = 100%
evidence completeness               > 99%
false block rate                    < 2% target
local policy evaluation p95         < 1 second target
offline verification p95            < 500 ms target
time to reconstruct one incident    measured before / after
audit records inspected             measured before / after
```

These are pilot targets, not guaranteed service levels.

## Pricing hypotheses

Pricing is a commercial experiment, not a claim that the market has already accepted these numbers.

### Entry offers

| Offer | Starting hypothesis |
|---|---:|
| Early design-partner pilot | **$5,000–10,000** |
| Standard 14-day pilot | **$10,000–15,000** |
| 6–8 week integration and policy hardening | **$20,000–50,000** |
| Managed Control Cloud | **$750–5,000 / month** initially |
| Continuous assurance for one critical workflow | **$2,500–7,500 / month** hypothesis |
| Private enterprise witness / verification pool | **$50,000–250,000 / year** later |

A first customer may receive a lower price in exchange for:

- access to a real workflow;
- a public or anonymized case study;
- permission to retain benchmark fixtures;
- regular product feedback;
- a reference call after success.

Do not offer unpaid open-ended integration disguised as a “pilot.”

## Revenue model

Near-term:

- paid pilot;
- integration fee;
- SaaS subscription;
- usage fee per assured action;
- custom policy packs;
- continuous regression and audit export;
- specialist verification and incident reconstruction.

Later, after repeated usage:

- managed evidence and certificate service;
- curated automated witness orchestration;
- private enterprise verification pools;
- compliance evidence packages;
- long-term receipt storage;
- OEM/runtime licensing;
- FPGA or SoC IP licensing only after a physical demonstrator and design partner demand.

Do not begin with token issuance, mining, guaranteed coverage, permissionless witness markets, or financial insurance without licensed partners and capital.

## What ProofBit contributes to the product

ProofBit is valuable commercially even before a hardware win because it supplies:

1. a precise trust-state vocabulary;
2. exact action/statement binding;
3. freshness and replay semantics;
4. separate authorization and outcome models;
5. a canonical receipt format direction;
6. an adversarial benchmark corpus;
7. cross-language conformance experience;
8. enforcement-placement and privilege-boundary tests;
9. a future hardware acceleration path;
10. unusually honest claim discipline.

The customer does not need to know whether the implementation is called ProofBit, a capability, a signed permit, or a reference monitor. They need the unsafe path blocked and the decision reproducible.

## Competitive differentiation

The initial differentiation should not be “we invented tags.”

Lead with:

- exact request and artifact binding;
- mandatory control of the real side-effect path;
- separate execution outcome receipts;
- portable offline verification;
- frozen fault scenarios and reproducible evidence;
- `HOLD` as a first-class state when evidence is insufficient or conflicting;
- integration across agent intent, policy, state, executor, and audit;
- independent QA pressure-testing rather than policy theater.

## Sales proof required

Before claiming product-market fit, obtain:

- 3 design partners;
- at least 2 paid pilots;
- 1 workflow converted to recurring use;
- evidence of one prevented unsafe action or materially improved control;
- measured reduction in audit/reconstruction time;
- measured false-block and HOLD rates;
- a buyer who renews without the founder manually running every check.

## 90-day commercial plan

### Days 1–15 — package

- freeze one production-deploy policy;
- define Action Request, Permit/Clearance, and Receipt schemas;
- ship offline verifier CLI;
- create a 90-second demo;
- publish the benchmark/claim ledger;
- prepare a five-point pilot one-pager;
- identify 30 highly relevant teams.

### Days 16–45 — sell and integrate

- run focused outreach around one painful question;
- secure 3 design-partner conversations;
- close the first paid pilot;
- integrate one GitHub Actions or deployment gateway;
- retain every found fault as a regression test.

### Days 46–90 — prove repeatability

- complete 2–3 pilots;
- compare pre/post audit effort;
- convert at least one customer to recurring assurance;
- standardize adapters and policy packs;
- decide whether customer demand justifies the FPGA demonstrator as a product dependency or only as research/IP.

## Example outreach question

> When an AI coding or cloud agent requests a production action, can your team later prove that the exact artifact, authority, approvals, policy version, and current environment state were checked — and separately prove what the executor actually changed?

Follow with a narrow pilot, not a broad architecture lecture.

## Hardware commercialization gate

Do not sell hardware until all of the following exist:

- PB-HW-05 or PB-HW-06 shows a measurable advantage not reproduced by a strong conventional control;
- one named FPGA profile passes place-and-route;
- a physical board demo runs end to end;
- real latency/utilization/power observations exist;
- at least one design partner asks for lower-level enforcement or acceleration;
- the host interface and threat model are stable.

Until then, hardware is a research and IP-option track. Revenue comes from assurance workflows.

## Revenue scenarios

Illustrative execution scenarios, not forecasts:

| Scenario | Assumption | Approximate first-year revenue |
|---|---|---:|
| Conservative | 4 pilots x $10k + 2 recurring customers x $2k x 6 months | **$64k** |
| Base | 6 pilots x $15k + 3 recurring customers x $5k x 8 months | **$210k** |
| Strong | 3 deeper design partnerships x $75k + 6 customers x $7.5k x 12 months | **$765k** |

A path to very large revenue requires productization, enterprise distribution, partner channels, and licensing — not the founder personally performing more audits.

## Final commercial thesis

```text
Independent verification
-> paid pilot
-> deployment/action guard
-> continuous assurance
-> design partners
-> FPGA demonstrator
-> optional runtime / hardware IP licensing
```

The software product tests willingness to pay now. The hardware research preserves upside without making customer revenue wait for a chip.
