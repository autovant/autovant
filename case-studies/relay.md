# Relay Desktop

**Local Windows dictation and meeting notes: on-device speech recognition first, cloud cleanup only when allowed.**

A Windows-focused adaptation of the MIT-licensed [Handy](https://github.com/cjpais/Handy).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/screens/relay/relay-privacy-dark.png">
  <img alt="Relay Settings, Privacy tab: a synthetic capture showing offline mode, user-triggered model downloads, opt-in cloud AI providers and webview policy controls." src="../assets/screens/relay/relay-privacy-light.png" width="100%">
</picture>

<sub>Settings, Privacy, captured with sample data and a test-harness backend; live transcription isn't shown. The source policy permits a user-started first-run model download when no model is available. No dedicated analytics SDK was found in the manifests; local activity telemetry exists.</sub>

| Stack | Evidence | Checked |
|---|---|---|
| Rust · Tauri · React · sherpa-onnx speech recognition | Source policy and historical local test records | 2026-10-28 copy audit |

## The problem

Voice tools often trade privacy for convenience, require cloud accounts, or perform poorly on ordinary Windows hardware. People on locked-down or privacy-sensitive machines need dictation and meeting support that works without a GPU, administrator access or mandatory cloud processing.

## What's upstream and what's mine

Relay started as a fork of Handy, an MIT-licensed open-source speech-to-text app, which supplied the Tauri shell, the audio pipeline and the settings foundation. Handy's credit and license are kept in the repository. Relay adds:

- **A CPU-first engine:** sherpa-onnx Parakeet TDT with a segment-incremental pipeline.
- **Offline mode as a policy boundary:** cloud provider routes are refused, loopback stays allowed, and a user-started first-run model download is an explicit exception when no model is available.
- **Meetings:** microphone and system-audio capture in one transcript, opt-in live notes, agenda readiness, questions about the meeting, and a handoff package written to a local project folder.
- **Windows paste hardening:** clipboard-sequence checks and a paste fallback that respects Windows integrity levels.
- **The Windows 11 interface,** portable packaging with a version guard, and command-line meeting controls.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/diagrams/relay-dark.svg">
  <img alt="Relay Desktop architecture: local capture feeds an on-device CPU speech model that produces a live transcript usable with no network. An optional cleanup step runs locally or through an approved provider, and an offline policy gate allows or refuses provider routes before any socket opens. Results go to history and export for meeting workflows." src="../assets/diagrams/relay-light.svg" width="100%">
</picture>

Transcription and cleanup are separate paths. Local speech recognition produces usable text without a hosted model. Cleanup is optional, and a network policy decides each route, treating loopback and external destinations differently.

## Key decisions

- **Local transcription is the flagship path.** Once a model is available, local transcription does not require hosted cleanup. Cloud cleanup is optional.
- **Make network policy explicit.** Offline mode refuses cloud providers while allowing loopback. Model-download policy includes the explicit first-run exception described above; it is not a blanket download ban.
- **Don't claim trust you can't show.** Portable packaging exists, but the build isn't described as signed or trusted until a real certificate and external verification back that up.

## What I built

- Segment-incremental local transcription on CPU.
- A Windows-first Tauri/Rust and React shell with Windows 10 and 11 design tokens, focus handling and responsive fallbacks.
- Offline-mode gates for cloud providers and model downloads.
- Optional local or subscription-backed cleanup adapters with visible status.
- Meeting workflows for questions, agendas, handoffs and transcript history.
- Portable packaging with version and stale-artifact safeguards.

## Evidence

- **Source and retained checks:** `relay-desktop@ca11978f47e7a3604e94be9a203c339fe920a241:docs/evidence.md` records the current proof limits; `docs/relay-ui-polish-evidence.md` retains older local checks. The prior 120-unit-test headline is omitted because a matching primary receipt was not identified.
- **Offline policy:** the same revision's `src-tauri/src/net_policy.rs` contains the provider and first-run download rules. This source inspection is not a current network trace or live transcription result.
- **Performance:** no fresh device-specific transcription benchmark is claimed in this profile.

## Scope and limits

- Authenticode signing, SmartScreen reputation and fresh-VM acceptance are deferred until a signing certificate is available.
- CPU transcription speed depends on the model, the device and the audio quality.
- Some cleanup behaviour depends on locally installed or subscription-backed tools.

[← Back to profile](../README.md)
