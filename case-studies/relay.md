# Relay Desktop

**Local Windows dictation and meeting notes: on-device speech recognition first, cloud cleanup only when allowed.**

⟦HERO⟧

| Project | My role | Stack | Evidence |
|---|---|---|---|
| Personal project: a Windows-focused adaptation of the MIT-licensed [Handy](https://github.com/cjpais/Handy) | Designer and engineer of the adaptation | Rust · Tauri · React · local speech recognition | ⟦EVIDENCE-STRIP⟧ |

## The problem

Voice tools often trade privacy for convenience, require cloud accounts, or perform poorly on ordinary Windows hardware. People on locked-down or privacy-sensitive machines need dictation and meeting support that works without a GPU, administrator access or mandatory cloud processing.

## What's upstream and what's mine

Relay Desktop builds on Handy, an MIT-licensed open-source speech-to-text app, and keeps that attribution in the product and repository. ⟦DELTA⟧

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/diagrams/relay-dark.svg">
  <img alt="Relay Desktop architecture: local capture feeds an on-device CPU speech model that produces a live transcript usable with no network. An optional cleanup step runs locally or through an approved provider, and an offline policy gate allows or refuses provider routes before any socket opens. Results go to history and export for meeting workflows." src="../assets/diagrams/relay-light.svg" width="100%">
</picture>

Transcription and cleanup are separate paths. Local speech recognition produces usable text without a hosted model. Cleanup is optional, and a network policy decides each route, treating loopback and external destinations differently.

## Key decisions

- **Local transcription is the flagship path.** Everything useful works offline, and cloud cleanup is an optional extra.
- **Block before the socket.** Offline mode refuses cloud providers and model downloads before a connection opens, while still allowing loopback services. Refusals are visible, never silently bypassed.
- **Don't claim trust you can't show.** Portable packaging exists, but the build isn't described as signed or trusted until a real certificate and external verification back that up.

## What I built

- Segment-incremental local transcription on CPU.
- A Windows-first Tauri/Rust and React shell with Windows 10 and 11 design tokens, focus handling and responsive fallbacks.
- Offline-mode gates for cloud providers and model downloads.
- Optional local or subscription-backed cleanup adapters with visible status.
- Meeting workflows for questions, agendas, handoffs and transcript history.
- Portable packaging with version and stale-artifact safeguards.

## Evidence

⟦EVIDENCE⟧

## Scope and limits

- Authenticode signing, SmartScreen reputation and fresh-VM acceptance are deferred until a signing certificate is available.
- CPU transcription speed depends on the model, the device and the audio quality.
- Some cleanup behaviour depends on locally installed or subscription-backed tools.

[← Back to profile](../README.md)
