---
name: classiq
description: Entry point for Classiq tasks when the user's intent is ambiguous or spans multiple phases (e.g. "build and run", "implement a VQE", "help me with Classiq", "implement the quantum algorithm from this paper"). Routes to the correct specialized skill after reading the workflow. Do NOT use when the intent is clearly a single phase — prefer classiq-modeling, classiq-execution, classiq-analyzer, or classiq-post-processing directly.
---

# Classiq Orchestrator

You are the entry point for all Classiq quantum programming tasks. Your job is to read the workflow, identify which phase the user is asking for, and invoke the correct specialized skill.

## Step 1 — Read the workflow

Read `references/WORKFLOW.md` (located next to this file in the skill directory). It defines the full pipeline, the skill map, task complexity assessment, routing rules, and hard constraints. Follow it exactly.

## Step 2 — Assess task complexity

Before routing to any skill, classify the request using the **Task Complexity Assessment** in `WORKFLOW.md`:

- **Simple task** (named algorithm, single clear intent, maps to one catalog entry): route directly to the appropriate skill. The skill uses the library example as-is and adapts only what is necessary.
- **Complex task** (paper implementation, vague/open-ended description, multi-component design, full-pipeline request): run the **Complex Task Pre-Pipeline** from `WORKFLOW.md` first — understand algorithm design, scout library building blocks, compose the design — then emit the **Design Brief** (format in `WORKFLOW.md`) before routing to any skill. The Design Brief is the handoff artifact; do not route without it.

## Step 3 — Route to the correct skill

Based on the user's intent, invoke one of:

| Skill | When |
|-------|------|
| `classiq-modeling` | Write, design, implement, or debug a quantum circuit |
| `classiq-synthesis` | Synthesize a circuit: `synthesize()`, constraints, preferences, hardware targets |
| `classiq-execution` | Run, execute, sample, measure, variational optimization |
| `classiq-analyzer` | Analyze a synthesized circuit: gate counts, depth, hardware fit |
| `classiq-post-processing` | Parse or visualize execution outputs: DataFrames, histograms |

If the user asks for multiple phases (e.g. "write and run"), activate skills **sequentially** in pipeline order — never blend instructions from two skills in one response pass.

**Paper implementations**: always classified as complex. Run the Complex Task Pre-Pipeline first. Then translate every paper construct to Classiq APIs — do not reproduce numpy/scipy code verbatim.

When in doubt about scope, ask one clarifying question before writing any code.
