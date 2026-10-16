# Redactor

**Hard-offline de-identification: every file is protected or refused, never passed through.**

⟦HERO⟧

| Project | My role | Stack | Evidence |
|---|---|---|---|
| Personal project, built outside client environments | Sole designer and engineer | Python · Rust · Tauri · React · portable Windows packaging | ⟦EVIDENCE-STRIP⟧ |

## The problem

Teams want realistic documents for AI, analytics, testing and review without exposing the people and organisations inside them. A regex pass isn't enough. Files can be scanned, nested, malformed, encrypted or structurally ambiguous, and a copy that looks successful can be more dangerous than a clear refusal. Redactor is a local file-protection product for privacy-conscious operators, developers and regulated-workflow teams.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/diagrams/redactor-dark.svg">
  <img alt="Redactor architecture, entirely hard-offline: files or folders pass an assurance check that either refuses them with a reason or sends them to the Python engine for detection and transformation. Safe mode writes irreversible output to an evidence ledger that verifies before publishing. Roundtrip mode writes protected output plus a separate encrypted map that stays on the machine, and an explicit restore step rejects unknown tokens." src="../assets/diagrams/redactor-light.svg" width="100%">
</picture>

One authoritative Python engine owns detection, transformation, refusal and evidence semantics. The Tauri/Rust desktop shell and other integrations consume versioned contracts instead of reimplementing the privacy rules.

## Key decisions

- **Transform, recurse or refuse.** Every input gets classified. "Copied because the parser couldn't understand it" is never a success state. Legacy Office binaries, macro-enabled files, encrypted PDFs and unknown binaries are refused with a reason.
- **Irreversible by default.** Safe mode can't be undone. Roundtrip mode writes a separate, authenticated, encrypted restoration map that never travels with the protected files, and restore rejects missing, malformed, unknown or ambiguous tokens.
- **All or nothing for folders.** Directory jobs stage their outputs, and one failed item stops the set from being published as complete and safe.

## What I built

- A cross-platform Python engine and CLI with fail-closed format handling.
- A portable Windows desktop app that needs no admin install, with local engine authentication and a constrained WebView.
- Separate Safe and Roundtrip workflows, including a review of the restoration impact.
- Evidence ledgers, report schemas, dependency inventories, SBOM material and release verification.
- A source-release path that reopens its own archive and verifies every member's hash.

## Evidence

⟦EVIDENCE⟧

## Scope and limits

- Detection isn't infallible. OCR evidence so far is English-focused, and handwriting or low-quality scans can still be missed.
- Safe projection can reduce visual fidelity for some formats.
- Redactor is a privacy engineering tool, not a legal determination or a compliance certification.

[← Back to profile](../README.md)
