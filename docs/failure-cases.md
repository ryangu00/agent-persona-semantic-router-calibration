# Chapter 9: Failure cases at the shipped setting

### Problem

Aggregates hide which requests got better and which got worse, and whether the remaining errors are low-confidence or confident.

### Mechanism and procedure

Replay the frozen baseline and shipped settings on the same cached vectors. Compare each outcome and persona, count paired gains and losses, and inspect every changed case; the following requests are paraphrases, not the private evaluation texts.

### Results (derived offline on 2026-10-03 from a replay, per case, production to shipped)

Transition counts over the 27 in-domain items (production outcome to shipped outcome): 9 items unchanged-exact, 3 escalated to exact, 3 escalated stays escalated, 3 sibling stays sibling, 3 wrong stays wrong, 2 wrong to exact, 1 exact to sibling, 1 escalated to sibling, 1 wrong to sibling, 1 exact to wrong. Nine of 27 items changed.

The nine changed items (request described in words, not verbatim):

| Request (paraphrase) | Production | Shipped | Score | Reading |
|---|---|---|---|---|
| Build a three-statement financial model | escalated | exact (financial analyst) | 0.904 | gain |
| Build an idempotent CI/CD pipeline with canary rollout | escalated | exact (devops) | 0.784 | gain |
| Design a partitioned ETL with backfill and de-duplication | escalated | exact (data engineer) | 0.723 | gain |
| Plan moderated usability interviews | wrong (feedback synthesiser) | exact (UX researcher) | 0.858 | gain |
| Keyword gap analysis and on-page SEO | wrong (search-query analyst) | exact (SEO specialist) | 0.742 | gain |
| Redesign onboarding screens for fewer drop-offs | escalated | sibling (a whimsy-injection design persona) | 0.771 | counted as sibling by category; arguably wrong |
| Map the end-to-end user journey | wrong (feedback synthesiser) | sibling (a Chinese UX researcher persona; the expected one is a UX architect) | 0.769 | better, still not exact |
| Threat-model an OAuth flow | exact (threat-detection persona) | sibling (security engineer) | 0.766 | loss; the label is debatable |
| Triage and respond to an escalating support ticket | exact (support operations persona, score 0.682) | wrong (customer service persona) | 0.840 | loss; the label is contested (Chapter 2) |

Remaining non-exact outcomes at the shipped setting (13 items): 3 escalated (an investment memo request; a launch blog post; an API contract-test request), 6 sibling, 4 wrong. Five of the 10 sibling-or-wrong items come from the keyword tier and cannot be changed by calibration: a latency root-cause request routed to an incident-response persona (a sibling by the gate rule but inside that item's accept set), the security-review request routed to a legal-document persona, the front-end request routed to a memory-backend persona, an engine-agnostic game-design request routed to an engine-specific gameplay scripter, and an infrastructure-monitoring request routed to a generic support-responder persona. The other five come from the semantic tier: wrong routes for a smart-contract audit request (a blockchain-security-auditor persona, 0.807, arguably a near-synonym but not in the accept set) and the contested support item (0.840); siblings for the threat-model, onboarding and user-journey items (0.766 to 0.771).

Scores of the non-correct semantic routes at the shipped setting: 0.766 to 0.840 (five of six). Failure signature to look for in a replay: a confident wrong route (score above the threshold by more than 0.04) rather than an escalation.

The small-sample A/B in Chapter 5 flagged the threat-model regression six days before activation; the full A/B listed it again with the new support-triage regression. Both were known, written down, and shipped with the decision.

### What did not work

- Counting "sibling" as success. The category-level rule gives credit to the whimsy-injection persona for an onboarding redesign.

### The rule

Read every changed case by hand; separate loss of a correct route from a contested label; and keep the list of known regressions with the release note.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
