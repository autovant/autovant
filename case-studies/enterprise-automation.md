# Enterprise automation tooling

**Tools for the engineering work around RPA delivery: artifact review, release building, OCR, and document extraction with human review.**

Three related private tools, shown here with synthetic data only. They aren't one deployed customer platform.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/enterprise/openvantage-review-station-dark.png">
  <img alt="OpenVantage review station: a synthetic scanned invoice marked SYNTHETIC SAMPLE with extracted fields boxed on the page, three cross-field validation issues such as line items and tax not reconciling with the total due, per-field image snippets, and Reject, Skip, Save and Accept actions." src="../assets/screens/enterprise/openvantage-review-station-light.png" width="100%">
</picture>

<sub>OpenVantage routes a synthetic invoice to review: three cross-field validation issues, each field boxed on the page, and an accept or reject decision for a person.</sub>

| Stack | Evidence | Checked |
|---|---|---|
| Python · FastAPI · React · TypeScript · Blue Prism XML · OCR | 31 review rules · 163 and 406 passing tests | 2026-10-16 |

## The problem

Enterprise automation teams do more than build bots. They interpret requirements, review platform artifacts, package releases, process documents, route uncertainty to people, and prove the result can be supported on locked-down machines. These tools turn recurring parts of that work into explicit, testable contracts.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/diagrams/enterprise-automation-dark.svg">
  <img alt="Two pipelines. Requirements or automation XML go through an engine client that validates, generates and packages artifacts, then through review, build and tests to a validated, importable release. Scanned documents go through CPU-first OCR and layout, then schema-bound classification and extraction, then a per-document confidence gate. Confident documents become a structured JSON result. Low-confidence documents go to a human review station first." src="../assets/diagrams/enterprise-automation-light.svg" width="100%">
</picture>

## The tools

| Tool | What it does |
|---|---|
| **Blue Prism Workbench** | Deterministic review of Blue Prism processes and objects, artifact generation, release building, plain-language explanation and test-case export. Generation, validation, layout and release packaging go through one engine client; the review rules still parse XML in-app. |
| **Scribe** | A no-admin OCR utility. One OCR engine sits behind both a headless JSON CLI and a desktop app, with deterministic page processing and a stable output contract. |
| **OpenVantage** | A CPU-first document pipeline: OCR, classification, schema-bound extraction and tables, with optional OCR-confidence calibration and a revision-aware human review station. Each stage can swap in a heavier model without reshaping the pipeline. |

## Key decisions

- **One engine for what ships.** Generation, validation, layout and release packaging go through one engine client, so the artifacts a release contains agree on what a file means. The rule-based review parses XML on its own.
- **Uncertainty routes to a person.** Documents with low confidence, failed validators or inconsistent fields go to a review station instead of being accepted silently. OCR confidence can be calibrated; extraction confidence is left uncalibrated by design.
- **Work on locked-down machines.** Scribe installs without admin rights and bundles pinned, hash-checked Tesseract and Poppler builds instead of relying on whatever is installed. OpenVantage keeps heavy model weights optional.

## Evidence

- **Blue Prism Workbench:** 31 review rules. The synthetic process returns the same 9 findings on every run (4 runs captured), and 163 backend unit tests passed on 2026-10-16.
- **OpenVantage:** 406 tests passed (1 skipped) on 2026-10-16.
- **Scribe:** the CLI returned its JSON contract on a synthetic two-page scan (95.1 mean word confidence). The full suite had 232 passing, 5 skipped and 1 failing test, a degraded-scan end-to-end case that is still open.

<img alt="Blue Prism Workbench analysis results for a synthetic process named Demo - Invoice Intake: 9 findings split into 3 errors, 4 warnings and 2 info, each with a severity, rule ID, category and message." src="../assets/screens/enterprise/bpw-review-results-light.png" width="100%">

<sub>Blue Prism Workbench reviewing a hand-written synthetic process: 9 findings with rule IDs, categories and messages.</sub>

## Scope and limits

- These are related tools, not evidence of a single customer deployment.
- OpenVantage doesn't claim accuracy parity with a tuned commercial document platform.
- No real Jira, Outlook, SharePoint, identity or customer-environment acceptance is claimed here. Test-case export writes Jira, Xray and Azure DevOps files; it isn't a live integration.

[← Back to profile](../README.md)
