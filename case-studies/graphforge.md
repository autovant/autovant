# GraphForge

**Visually author, run, inspect and export stateful LangGraph workflows.**

<img alt="GraphForge: a real LangGraph run of an incident-triage graph paused at the Escalation review interrupt, with the reviewer editing the dispatch note before choosing Approve, Save edits and resume, or Reject." src="../assets/screens/graphforge/graphforge-human-interrupt.png" width="100%">

<sub>A real LangGraph run paused at a human-review gate. The reviewer edits the dispatch note before resuming. Synthetic incident data.</sub>

| Stack | Evidence | Checked |
|---|---|---|
| Python · LangGraph · FastAPI · React · React Flow · SQLite | 18-case live evaluation · 428 backend and 38 browser tests | 2026-10-16 |

## The problem

Agent workflows are hard to trust when their state, routing, tools, checkpoints and failure behaviour live only in handwritten code. Visual builders help people understand a graph, but most stop at a diagram or a mocked run and can't produce something you can deploy. GraphForge is for engineers and technical operators who want to draw a stateful agent graph, run the real runtime, pause for human decisions, inspect what happened, and leave with runnable Python.

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/diagrams/graphforge-dark.svg">
  <img alt="GraphForge architecture: the visual canvas edits a typed graph IR, the single source of truth. The graph assistant drafts a typed Blueprint, which pure code compiles into IR. The IR is validated and compiled to the LangGraph runtime, and the same IR exports to standalone Python. The runtime calls tools and MCP servers, pauses at human interrupts and writes checkpoints for replay." src="../assets/diagrams/graphforge-light.svg" width="100%">
</picture>

The typed graph IR is the system boundary. The canvas edits it, and the validator, runtime and exporter consume it. AI drafting and the assistant never write IR directly: they produce a typed Blueprint that pure code compiles into IR. That keeps the canvas from drifting into an untestable second implementation of the workflow.

## Key decisions

- **Compile to the real runtime, not an animation.** Runs execute LangGraph with streaming state, checkpoints and interrupts, so what you watch on the canvas is the execution itself. The cost: model calls make demos slow, and the walkthroughs say when a wait has been sped up.
- **The assistant proposes; validation decides.** AI-drafted graph changes appear as a preview and only apply after the Blueprint validates. This takes a little longer than direct edits, but the graph is never left half-valid.
- **Govern what can be governed, and say what isn't.** MCP tools go through a server-side registry and allowlist, with typed allowed and blocked audit events. Code and tool nodes run in subprocesses with hard timeouts, which is process isolation, not a security sandbox. HTTP nodes are bounded by a timeout only.

## What I built

- A typed visual authoring surface over React Flow, with graph drafting through a deterministic Blueprint-to-IR compiler and plan previews.
- Real LangGraph execution with streaming state, SQLite checkpoint history, human-in-the-loop interrupts and replay from any earlier checkpoint.
- MCP tool governance (registry, allowlist, audit events) and timeout-bounded HTTP, code and tool nodes.
- Standalone Python export that runs outside the product.
- Regenerable walkthrough recordings whose captions are tied to asserted UI states.

## Evidence

- **Live evaluation (2026-08-10):** 17 of 18 cases executed to completion (94.4%). The one failure, a human-interrupt change-approval case missing a required input, stays in the published results.
- **Tests (2026-10-16):** 428 backend tests and 38 Playwright browser tests passed. The browser suite builds the incident-triage graph in the UI and runs it with a real HTTP call, a human interrupt, three runs and code export.
- **Export:** a code-generation test runs the exported Python as a standalone file in a subprocess.
- **Scope:** 11 node types and 13 starter patterns.

## Scope and limits

- Code nodes can do anything the local user can. GraphForge isn't a sandbox for untrusted graphs.
- Local tool and MCP evidence isn't proof of a production sandbox or a multi-tenant deployment.
- Runs through a subscription CLI don't report comparable per-call API cost, so cost is reported as unavailable rather than estimated.
- Exported code still needs normal review, dependency management and deployment controls.

[← Back to profile](../README.md)
