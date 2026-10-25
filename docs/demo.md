# 5–10 minute interview walkthrough

## Problem frame (30–60 seconds)

Describe the recurring engineering problem: operational workflows need a clear authority boundary, a human review path, and evidence that says what was actually checked. The portfolio is a set of selected examples, not one integrated product.

## Walkthrough

1. **Show the profile (one minute):** Orient the interviewer to the case studies and architecture diagrams. State that source for the private products is not in this repository.
2. **Choose one case study (two minutes):** Use GraphForge for graph authoring and human interrupts, Mandate Guard for deterministic evaluation, or Redactor for the documented offline/refusal boundary. Do not imply that a screenshot is a live app.
3. **Trace the architecture (one to two minutes):** Follow input, interpretation, deterministic control, review, and evidence in the case diagram. Explain which part is documented and which behavior needs source evidence.
4. **Discuss decisions (one to two minutes):** Cover three choices, such as separating advisory output from action, routing uncertainty to a person, and preserving a source-linked audit record.
5. **Inspect evidence and failure handling (one minute):** Open the case study's dated evidence and limits. For GraphForge, mention the retained missing-input failure in its dated evaluation. For Mandate Guard, keep test counts tied to their date and revision. For Redactor, state that the profile does not independently qualify the hard-offline guarantee.
6. **Close (one minute):** Name what would be required for a real product demo: the approved source checkout and commit, local test receipts, any needed native/provider qualification, and human acceptance. These are outside this publication repository.

## What this repository can demonstrate

It can demonstrate the portfolio structure, architecture explanations, static diagrams, and labeled synthetic or sample screenshots. It has no local product runtime, install command, application test suite, credentials, or external provider integration.

## Interview questions to invite

- Which step may use a model, and which step is owned by deterministic code?
- What happens when source evidence is missing or confidence is low?
- Which screenshot is synthetic, and what evidence would prove the described runtime behavior?
- Which claims are tied to a revision and which remain self-reported?
- What would you qualify before using the system with a connected enterprise service?
