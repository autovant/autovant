# Redactor

**Redactor's CLI and desktop sidecar install a network-rejecting process audit hook; the importable API leaves its host process unrestricted. This profile does not independently qualify current offline behavior.**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/redactor/redactor-review-dark.png">
  <img alt="Redactor portable app, Review before protecting: two synthetic files checked, claim-intake.md needing review and policyholders.csv ready. The privacy-safe preview lists detected categories such as payment card, date, email address and person name without showing any values. The evidence ledger shows hard offline, strict policy, safe mode and an authenticated engine." src="../assets/screens/redactor/redactor-review-light.png" width="100%">
</picture>

<sub>The packaged app reviewing two synthetic files before protecting them. The preview shows detected categories, never the values.</sub>

| Stack | Evidence | Checked |
|---|---|---|
| Python · Rust · Tauri · React · portable Windows packaging | Retained local record: 418 Python passes, 12 skips | 2026-10-17 run; 2026-10-28 copy audit |

## The problem

Teams want realistic documents for AI, analytics, testing and review without exposing the people and organisations inside them. A regex pass isn't enough. Files can be scanned, nested, malformed, encrypted or structurally ambiguous, and a copy that looks successful can be more dangerous than a clear refusal. Redactor is a local file-protection product for privacy-conscious operators, developers and regulated-workflow teams.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/diagrams/redactor-dark.svg">
  <img alt="Redactor architecture: files or folders pass an assurance check that either refuses them with a reason or sends them to the Python engine for detection and transformation. Safe mode writes irreversible output to an evidence ledger that verifies before publishing. Roundtrip mode writes protected output plus a separate encrypted map, and an explicit restore step rejects unknown tokens. The diagram does not qualify network behavior." src="../assets/diagrams/redactor-light.svg" width="100%">
</picture>

One authoritative Python engine owns detection, transformation, refusal and evidence semantics. The Tauri/Rust desktop shell and other integrations consume versioned contracts instead of reimplementing the privacy rules.

## Key decisions

- **Transform, recurse or refuse.** Every input gets classified. "Copied because the parser couldn't understand it" is never a success state. Legacy Office binaries, macro-enabled files, encrypted PDFs and unknown binaries are refused with a reason.
- **Irreversible by default.** Safe mode can't be undone. Roundtrip mode writes a separate, authenticated, encrypted restoration map that never travels with the protected files, and restore rejects malformed, unknown or ambiguous tokens. Tokens an LLM simply left out of its answer are allowed.
- **All or nothing for folders.** Directory jobs stage their outputs, and one failed item stops the set from being published as complete and safe.

## What I built

- A cross-platform Python engine and CLI with fail-closed format handling.
- A portable Windows desktop app that needs no admin install, with local engine authentication and a constrained WebView.
- Separate Safe and Roundtrip workflows, including a review of the restoration impact.
- Evidence ledgers, report schemas, dependency inventories, SBOM material and release verification.
- A source-release path that reopens its own archive and verifies every member's hash.

## Evidence

- **Retained local result:** `redactor@17294e59b5c2f07944dbfb8cb49cf46f3422a405:docs/evidence.md` (RDR-04) and `docs/evidence/verification.md` record 418 Python passes and 12 skips on 2026-10-17 at source `41e48f7`. This is a retained result, not a new run of the current default branch.
- **Historical package walkthrough:** the prior case study described Safe protect, Roundtrip protect, restore and refusal paths on synthetic files. The package execution receipt is not bundled here; this profile does not qualify a current portable build or the separate 0.2 candidate.
- **Offline boundary:** the same revision's `docs/evidence.md` (RDR-03) and `SECURITY.md` describe the network-rejecting process audit hook installed before CLI or desktop-sidecar dispatch. The importable API leaves its host process unrestricted; the guard does not cover embedding applications or external model conversations. Historical offline observations were not rerun here.

## Scope and limits

- Detection isn't infallible. OCR evidence so far is English-focused, and handwriting or low-quality scans can still be missed.
- Safe projection can reduce visual fidelity for some formats.
- The historical desktop capture showed a `.docm` as ready before protect refused it, and a generic check failure for a lone refused file. Those captured states are not evidence that the current app retains either behavior.
- Redactor is a privacy engineering tool, not a legal determination or a compliance certification.

[← Back to profile](../README.md)
