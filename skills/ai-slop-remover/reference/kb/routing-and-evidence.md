---
title: Route a scoped UI improvement and calibrate its evidence
source: https://agentskills.io/specification
last_fetched: 2026-09-07
skills: [ai-slop-remover]
---

# Routing and evidence

The [Agent Skills specification](https://agentskills.io/specification) defines a skill's metadata and optional resources, and recommends progressive disclosure. This set's division of responsibilities is a maintainer workflow choice, not a runtime API or a quality guarantee.

| Situation | Minimum useful path |
| --- | --- |
| One visual detail with a known correction | Visual refinement and affected visual checks |
| Save or search feels unreliable | Flow refinement and real state assertions |
| Confusing labels, no layout request | Writing and checks for unchanged semantics/wrapping |
| “This looks AI-generated” with no diagnosis | Audit, highest-impact relevant specialist, quality gate |
| User only requests review | Audit or quality gate, evidence-backed recommendations |
| Runtime unavailable | Inspect source and supplied images; report unavailable checks |

Use the smallest fitting scope. A specialist's read-only finding is an input to the parent implementation request, not permission to edit when the user only requested review.

Package checks prove structure, hashes, links, and installation. A host discovery check proves that the host sees a skill. An actual skill trial needs a task, captured actions/output, and an assessment against observable expectations. Keep those claims separate.

## 리뷰 훅

- Is the selected skill responsible for the requested outcome?
- Does a small request stay small and a read-only request stay read-only?
- Does each finding explain a task consequence instead of a personal style preference?
- Are observed, inferred, and unverified results distinct?
- Are missing runtime tools disclosed without blocking unrelated useful work?
