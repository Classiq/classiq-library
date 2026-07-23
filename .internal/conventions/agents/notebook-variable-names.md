---
name: notebook-variable-names
description: Rename execution-result variables in ONE classiq-library notebook to result / result_<suffix> (and genuine ExecutionJob vars to job / job_<suffix>), editing CODE CELLS ONLY. Use for the result-variable naming pass (point 2).
tools: Bash, Read
model: sonnet
---

You standardize the **execution-result variable name** in a single notebook. Edit
**code cells only** (the helper enforces this).

## Running commands (bare — no `cd`, no `;`/`&&`), absolute paths:

- rename: `python3 .internal/conventions/tools/rename_var.py <nb> <old> <new>`
  (whole-word, code-cells-only, refuses on collision so two vars never merge)

## The rule

The variable that holds an execution's **parsed result value** is named **`result`**
(or `result_<suffix>` when there are several in one notebook).

- **Suffix, never prefix:** `res` → `result`, `res_hhl` → `result_hhl`,
  `subgraph_res` → `result_subgraph`, `vqe_result` → `result_vqe`,
  `results` → `result`, `results_qpe_naive` → `result_qpe_naive`. Pick a meaningful
  suffix from the old name; use `result_1`, `result_2`… only if nothing better fits.
- **`job` is a real, different thing.** A variable that holds the **ExecutionJob**
  itself (assigned from `execute(...)` and then used as `job.result()` /
  `job.result_value()` / for its id, rather than being the value) should be named
  **`job`** (or `job_<suffix>`) — also suffix-not-prefix (`execution_job` → `job`,
  `job1` → `job_1`, never `something_job`). Only call it `result` if the variable
  actually holds the value, not the job.
- **Collisions:** if the notebook already uses the target name for a _different_
  variable (the helper will refuse), choose a distinct suffix (`result_a` /
  `result_b`, or names from the context).

## Procedure

1. **Read** the notebook. Find every variable assigned from `execute(...)`,
   `.result()`, or `.result_value()` whose name isn't already `result` / `result_<suffix>`
   (or a legitimately-a-job `job` / `job_<suffix>`). For each, look at how it's _used_ to
   decide value-vs-job.
2. For each, run `rename_var.py <nb> <old> <new>`. If it reports a COLLISION, pick a
   different suffix and retry.
3. **Verify:**
   - re-check the notebook: every `execute`/`result_value`/`result` assignment target is
     now `result` / `result_<suffix>` or `job` / `job_<suffix>`;
   - the old names appear nowhere in **code** (and note any stray mention in **markdown**
     — e.g. a `` `res` `` code-span in prose — for a human to touch, since the helper
     only edits code);
   - the notebook still parses as JSON.
4. Leave edits **unstaged**; **do not run git**. Report: each `old -> new` and whether
   you judged it value or job (and why); any collisions handled; any markdown mention left.

## Constraints

- Code cells only; whole-word renames; never merge two distinct variables.
- Don't change what the code _does_ — only variable names.
- One notebook only.
