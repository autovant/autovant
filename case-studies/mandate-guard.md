# Mandate Guard

**Investment restrictions turned into predicates, decided by deterministic code, reviewed by a person.**

<img alt="Mandate Guard document-review workspace: a synthetic temporary waiver letter with a highlighted passage, and a waiver impact memo whose numbered evidence links point to the exact source passages. The memo needs review and a reviewer must confirm the interpretation." src="../assets/screens/mandate-guard/interpretation-evidence.png" width="100%">

<sub>The document-review workspace on a synthetic agreement and waiver. Each conclusion links to the passage it rests on, and a reviewer must confirm the interpretation.</sub>

| Stack | Evidence | Checked |
|---|---|---|
| Python · FastAPI · hybrid retrieval · LLM parsing · MCP · vanilla JS | 1,706 offline tests passed · 16/16 local walkthrough checks | 2026-10-28 |

## The problem

Investment restrictions are written in natural language, but compliance decisions have to be deterministic, explainable and reconstructable. If a language model makes the final call, the same clause can produce different answers, and a reasonable-sounding answer may not cover every holding it affects. Mandate Guard is for compliance reviewers and engineering teams who want help interpreting clauses without handing decision authority to a model.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/diagrams/mandate-guard-dark.svg">
  <img alt="Mandate Guard architecture: a natural-language restriction clause goes to a tiered parser. A deterministic grammar reads most clauses; for the rest, the model proposes a structured predicate that must pass grounding and roundtrip checks. A pure deterministic evaluator applies the predicate to the complete holdings set. The determination goes to a source-linked human review and to a tamper-evident, hash-chained audit log." src="../assets/diagrams/mandate-guard-light.svg" width="100%">
</picture>

The model sits outside the decision function. A deterministic grammar reads supported clauses, and the model can propose a structured predicate for the rest. Deterministic code then scopes the holdings, aggregates exposure, applies thresholds and emits the determination, so the decision path can be tested and replayed. The bundled offline example uses no model calls.

## Key decisions

- **The model never decides compliance.** It proposes a predicate only when the grammar can't read a clause, and that predicate must pass grounding and roundtrip checks before anything evaluates it. Given the same validated predicate and holdings, the evaluator returns the same determination. A wrong predicate can still produce a wrong result, which is why review stays human.
- **Evaluate the whole portfolio, every time.** Determinations cover the complete in-scope holdings set rather than a convenient sample, so no holding falls outside a decision.
- **Local by default, explicit egress.** Documents are extracted and reviewed locally. If a provider route is configured, the app names it and asks for confirmation before sending bounded extracted text. It never sends original files, local paths or credentials. Missing documents and context overflow stop the operation, and conflicting evidence holds it for human review, instead of quietly narrowing the input.

## What I built

- Tiered restriction parsing with grounding and roundtrip validation.
- A pure deterministic evaluator over complete holdings sets.
- Entitlement, retrieval zoning, redaction, prompt-injection handling, a kill switch and audit controls.
- A source-linked document-review workspace with local storage and explicit egress consent.
- Review-memo exports (JSON, CSV and HTML) that snapshot each source's ID, filename, role and SHA-256.
- An MCP server that applies the same entitlement, guardrail, kill-switch and audit controls.
- Evaluation artifacts for determinism, routing, retrieval, latency and boundary behaviour.

## Evidence

- **Offline suite (2026-10-28):** 1,706 tests passed with no failures, errors or skips. Source receipt: `MandateGuard@4b5f51dedd1184a3171ecd6685e875bf34a82668:docs/verification/offline-suite-fc4e996.json`, testing source `fc4e996a7e8a0f92a70818d30994703fcebfb43c`.
- **Local walkthrough:** 16/16 browser checks passed with zero model calls. Receipts at the same default-branch revision: `docs/verification/run-ps1-browser-fc4e996.json` and `docs/verification/standalone-app-fidelity-ledger.md`. Demo-ready applies to the bundled offline example only.
- **Synthetic determinism benchmark:** 16 restrictions × 24 synthetic portfolios, 384 determinations and 0 differences over five runs, with equal audit heads. `MandateGuard@4b5f51dedd1184a3171ecd6685e875bf34a82668:docs/verification/offline-engine-2026-10-26.json` records a rerun against source `6f7ea69`; `evidence/determinism_report.json` and `evidence/determinism_output.txt` retain the benchmark record. It uses synthetic inputs and cached predicates, with no live parsing. It is not an accuracy, provider-cost or model-qualification result.
- **Local-model qualification:** CLOSED, NOT CONVERGED. The development run met the all-repeat correctness criterion on 7/14 cases against 12 required. Held-out and browser qualification were not run, and no model was qualified. Source: `MandateGuard@4b5f51dedd1184a3171ecd6685e875bf34a82668:docs/qualification/local-ollama-qwen35-2026-10-26/README.md`; closure is the owner's 2026-10-28 decision.

<img alt="Mandate Guard workbench: rule R-163 checked against synthetic portfolio PF-0201. Exposure is 4.40% of net asset value across three in-scope holdings against a 4% limit, so the result is a breach with a cure deadline and a remediation playbook. The clause was read by the deterministic grammar, with no model involved." src="../assets/screens/mandate-guard/workbench-breach.png" width="100%">

<sub>One rule against one synthetic portfolio, decided in code: 4.40% exposure against a 4% limit, the in-scope holdings, the cure deadline and the remediation playbook.</sub>

## Scope and limits

- Repeatable determinations show repeatability, not clause-level accuracy. A wrong model-generated predicate can still produce a wrong result.
- Offline suite and walkthrough success do not qualify a local model or establish live-provider, customer or production readiness.
- The retrieval reranker was tuned on its evaluation set. Recall needs a held-out split before it generalises.
- Cached predicates aren't individually approved by a person before they're reused across portfolios.
- The audit chain is tamper-evident, not tamper-proof.
- The standalone local app has no authentication or rate limiting yet.
- It supports compliance review. It doesn't replace accountable human or legal judgment.

[← Back to profile](../README.md)
