# Evidence ledger

This ledger applies to the current Git revision reported by the profile checker. Its source base is origin/main at b59f8645e7c64d08d9dd24e19a3a66681ebd28a4. The case-study pages do not pin most product-source revisions, so their metrics are dated statements from the publication rather than current product-source results.

The manifest in .portfolio/project.yaml is valid JSON, which is also valid YAML. The checker uses Python's standard library; no YAML or testing dependency is added.

| Claim ID | Exact published claim | Status | Evidence and limit |
|---|---|---|---|
| autovant-publication-scope | This repository publishes portfolio text, architecture diagrams, and screenshots; it does not include the private product applications. | verified | README.md and LICENSE.md describe publication material; the tracked inventory contains the profile, case studies, assets, and one diagram generator. |
| autovant-career-impact | Career impact since 2018: $1.5M+ saved · 20,000+ hours saved · 300+ end-to-end automation solutions · 8 years in enterprise automation | partially_verified | This is published in README.md; the repository contains no employer records or calculation to reproduce it. |
| autovant-conductor-tests | 2,764 Python and 231 UI tests · 19 ADRs | partially_verified | case-studies/conductor.md records this with a 2026-10-16 checked date. No source SHA, test output, or ADR inventory is included. |
| autovant-graphforge-tests | 18-case live evaluation · 428 backend and 38 browser tests | partially_verified | case-studies/graphforge.md records this with a 2026-10-16 checked date. The screenshot illustrates a human-interrupt state, not those tests. |
| autovant-mandate-guard-benchmark | 384 determinations, 0 differences over 5 runs · 172 tests | partially_verified | case-studies/mandate-guard.md records these with a 2026-10-16 checked date. Benchmark inputs and test output are not attached. |
| autovant-redactor-tests | 417 Python tests · packaged app run end to end | partially_verified | case-studies/redactor.md records the dated claim. The screenshot is not a package execution receipt. |
| autovant-relay-tests | 120 unit and 9 Playwright UI tests | partially_verified | case-studies/relay.md records the counts with a 2026-10-16 checked date and states Rust tests were not rerun that day. |
| autovant-enterprise-automation-tests | 31 review rules · 163 and 406 passing tests | partially_verified | case-studies/enterprise-automation.md says the counts span three related private tools, not one deployed customer platform. No source SHAs or test receipts are attached. |
| autovant-public-superpowers | It ships the 14 upstream skills, four Copilot prompt files, PowerShell and Bash installers, with a 9-check repository test suite. | partially_verified | README.md links the public repository and publishes the summary; the target revision and test output are not pinned here. |
| autovant-synthetic-case-study-captions | Case-study captions label example records as synthetic or sample data. | verified | Captions in the case-study files identify the screenshots as synthetic or sample. This verifies the published labels, not every pixel's provenance. |
| autovant-conductor-control-boundary | Case operations from intake to governed action: assistance advises, deterministic workers act, people decide. | partially_verified | The case-study text and SVG describe separate paths; private source and a revision-bound execution trace are absent. |
| autovant-mandate-control-boundary | Mandate Guard places the model outside the investment decision function; deterministic code evaluates the predicate and a person reviews the result. | partially_verified | The case-study text and SVG describe the boundary; no product revision or live decision trace is bound to this publication. |
| autovant-redactor-hard-offline | The case study describes Redactor as hard-offline: supported files are transformed and unsupported files are refused. This profile does not independently verify that guarantee. | unverified | This row summarizes the case study's intended hard-offline design. No packet capture, product source revision, or fresh refusal/egress test qualifies the no-pass-through guarantee. |
| autovant-relay-offline-gate | The Relay case study says a test blocks a cloud provider before any socket opens. | partially_verified | The dated case study records this test claim, but the test source, output, and product revision are not included. This does not qualify live network behavior. |

## Source-count discrepancies checked on 2026-10-25

- The profile records GraphForge as 428 backend and 38 browser tests on 2026-10-16. The current GraphForge origin/main at 14e3339d618c6b3b94c860f09ac9704904e09926 reports 442 tests collected, including 429 keyless-selected and 13 live-marked tests. Its [README](https://github.com/autovant/GraphForge/blob/14e3339d618c6b3b94c860f09ac9704904e09926/README.md) records 429 passing keyless server tests. These are different source snapshots and test scopes; collection counts are not passing counts. Keep the dated profile statement as partial and do not silently replace it.
- The profile records Mandate Guard as 172 tests on 2026-10-16. Current MandateGuard origin/main at e47b89310a86c90fd7cc0bc62f36d53a6ee8a95d reports 222 offline tests collected; its [README](https://github.com/autovant/MandateGuard/blob/e47b89310a86c90fd7cc0bc62f36d53a6ee8a95d/README.md) also records a qualified PR #13 result of 222 passed on Windows and 221 passed with one Windows-only launcher check skipped on Linux. Do not rewrite the older profile claim as if this current result were the same run.
- The profile records Redactor as 417 Python tests on 2026-10-16. Resume origin/main at ac1f7f235640ce4fcc9d95740948e41077cdd553 lists an older dated release figure of 325 Python plus 33 Rust tests from 2026-08-16 in its [content source](https://github.com/autovant/Resume/blob/ac1f7f235640ce4fcc9d95740948e41077cdd553/content/site.ts). These records conflict by date and source; this readiness branch does not reconcile them or change either product narrative.

## Evidence classes

- The profile text is a dated secondary record; it proves what was published, not the underlying product behavior.
- A screenshot supports the depicted UI state and its caption scope, not a test result, successful egress block, or connected-system action.
- A current source README can document a test count or result, but that does not retroactively qualify a different profile date or commit.
- Live-provider behavior, customer acceptance, hosted checks, and production readiness require separate evidence. None is inferred from this profile repository.

## Validation status for this change

This repository contains no application or product test suite. The profile checker validates required files, claim references, local links, public-doc hygiene, and Git state. The focused checker regression at scripts/portfolio_check_regression.py verifies that an external manifest is rejected without an unhandled exception. No private product test, package build, source run, live provider call, or customer workflow was executed for this documentation-only change.
