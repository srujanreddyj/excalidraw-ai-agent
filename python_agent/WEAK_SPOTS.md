# Weak Spots & Fixes — Python Agent Engineering System

> **Purpose of this doc.** This is the honest, code-grounded list of every weak spot in the
> Python agent system, *why each one matters* (especially in an interview), and *exactly how to
> fix it*. It exists so that the resume claim — "tool-calling, planning-before-action, structured
> tracing, feedback capture, eval automation, and a data flywheel" — is **defensible**, not just
> claimed.
>
> Think of this as the difference between a teacher who stamps "A+" on every exam without reading
> it, and a teacher who actually grades. Several parts of this system are currently stamping "A+".
> This doc finds every stamp and tells you how to turn it into real grading.

---

## How to read this doc

Each weak spot has:

- **ID** — a stable handle (WS-1, WS-2…) so we can refer to it in conversation.
- **Severity** — how badly it undermines the resume claim if an interviewer pokes at it.
- **Status** — `OPEN`, `IN PROGRESS`, or `FIXED`. Update this as we go.
- **The problem** — in plain English.
- **Where** — exact file and line numbers, so it's verifiable, not hand-waved.
- **Why it matters** — the interview risk.
- **How to fix it** — concrete steps.

### Severity legend

| Severity | Meaning |
|---|---|
| 🔴 **Critical** | A core resume claim is currently false or hollow. Fix before showing anyone. |
| 🟠 **High** | The claim is technically true but collapses under one good follow-up question. |
| 🟡 **Medium** | A quality/credibility gap. Won't sink you, but a sharp interviewer notices. |
| 🟢 **Low** | Polish. Worth doing, low risk if skipped. |

### Fix priority (recommended order)

1. **WS-1** — make evals actually run the AI (everything else depends on this).
2. **WS-2** — make planning real.
3. **WS-3** — connect the overlap grader (it already exists, just unplugged).
4. **WS-4** — score `expectedCharacteristics`, the rich signal you're currently ignoring.
5. **WS-5** — make promoted regressions capable of failing.
6. **WS-6** — produce and commit a real `generated_regressions.json`.
7. **WS-7 … WS-11** — credibility, fidelity, and framing.

---

## 🔴 WS-1 — Evals never call the LLM; they grade a hardcoded template

- **Severity:** 🔴 Critical
- **Status:** OPEN

**The problem.** Your eval runner is supposed to test your *AI agent*. It doesn't. It tests a
deterministic function that builds a generic left-to-right flow diagram from the prompt — no model
involved.

**Where.**
- `src/diagram_agent/evals.py:49` — calls `run_agent(case.input, planning=planning)` with **no
  `model_client`**.
- `src/diagram_agent/agent.py:103` — the real OpenAI tool-calling loop only runs
  `if model_client is not None:`.
- `src/diagram_agent/agent.py:210-241` — with no client, execution falls through to a hardcoded
  path: `select_flow_labels(prompt)` → `_build_flow_payload()` → always "Created a basic flow with
  N nodes."

**Why it matters.** This is the foundation everything else stands on. Your eval scores, your
planning-vs-no-planning comparison, your regression tests — *all of them are measuring a template,
not the model.* If an interviewer asks "so when you say planning improved your eval score, what was
the model doing?" the honest answer right now is "nothing, the model wasn't called." That single
admission unravels the whole story.

**How to fix it.**
1. Build a real model client (you already have `openai_client.py` — confirm it implements the
   `ModelClient` protocol: a `create_response(messages, tools)` method).
2. In `evals.py`, construct that client once and pass it into `run_agent(..., model_client=client)`.
3. Add a flag so you can still run the cheap/offline template path on purpose (e.g.
   `run_eval(..., use_model=True)`), but make **model-backed the default for any eval you cite.**
4. Re-run the golden eval and save a fresh report in `runs/`. *That* report is the one you talk
   about.

---

## 🔴 WS-2 — "Planning-before-action" is a hardcoded template, not planning

- **Severity:** 🔴 Critical
- **Status:** OPEN

**The problem.** `create_plan()` returns the **same three sentences for every prompt** and never
calls a model. "Draw a JWT auth flow" and "Draw a database schema" produce identical plans.

**Where.**
- `src/diagram_agent/planner.py:24-34` — `create_plan()` hardcodes `intent`, `steps`,
  `tools_likely_needed`, and even a `risks` entry that literally says *"until model planning is
  implemented."*

**Why it matters.** "Planning-before-action" is one of your six headline claims. The demo script
runs `--planning required` and prints a plan that *looks* impressive. But the first follow-up —
"show me the plan for a different prompt" — reveals it's a Mad Libs template. That's worse than not
claiming planning at all, because it looks like you're trying to dress up something hollow.

**How to fix it.**
1. Make `create_plan()` (or a new `create_plan_with_model()`) do a **real model call with no
   tools**, asking for structured JSON matching the `Plan` schema (`intent`, `steps`,
   `tools_likely_needed`, `risks`).
2. Keep the hardcoded version as an explicit offline/test fallback — name it honestly, e.g.
   `create_stub_plan()`.
3. Verify plans differ across prompts. Run two different prompts with `--planning required` and
   confirm the plans are genuinely different. *Save those two outputs* — they're your proof.

---

## 🔴 WS-3 — `no_overlaps` is hardcoded `True`; the real grader exists but is unplugged

- **Severity:** 🔴 Critical
- **Status:** OPEN

**The problem.** The eval claims "no overlaps" on every single case without ever checking. The
maddening part: **you already wrote working overlap detection** — the eval just never calls it.

**Where.**
- `src/diagram_agent/evals.py:62` — `"no_overlaps": True` (hardcoded).
- `src/diagram_agent/canvas.py:67-85` — `find_overlaps()` is real, working code.
- `src/diagram_agent/canvas.py:101-112` — `_elements_overlap()` does correct rectangle-intersection
  geometry.

**Why it matters.** This is the exact failure your *flagship demo* promotes: a user downvotes
"boxes overlapped," it becomes a regression case… that can never catch overlapping boxes, because
the grader always says "no overlaps." The flywheel loops, but the final pipe isn't connected.

**How to fix it.**
1. In `evals.py`, rebuild a `CanvasState` from `result.canvas_elements` (or have `run_agent` return
   the `CanvasState`/its overlaps directly).
2. Replace `"no_overlaps": True` with `"no_overlaps": len(canvas.find_overlaps()) == 0`.
3. Add a deliberately-overlapping test case and confirm it now **fails**. A grader you've never seen
   fail is not yet a grader.

---

## 🟠 WS-4 — `expectedCharacteristics` is loaded but never scored (your richest signal, ignored)

- **Severity:** 🟠 High
- **Status:** OPEN

**The problem.** Every eval case carries a rich, human-written description of what a good answer
looks like (e.g. *"1 rectangle element"*, *"The rectangle has a label with content Hello"*). None
of it is used for scoring. Only `expectedKeywords` (a flat substring match) is checked.

**Where.**
- `src/diagram_agent/evals.py:8-14` — `EvalCase` *loads* `expectedCharacteristics`.
- `src/diagram_agent/evals.py:59-63` — scoring only uses `expectedKeywords`;
  `expectedCharacteristics` is never read.

**Why it matters.** Keyword matching is the weakest possible grader — the word "hello" can appear in
the text while the diagram is completely wrong. You wrote good rubric statements and then threw them
away. This is also the natural place to introduce an **LLM-as-judge** scorer, which is a strong
thing to be able to talk about.

**How to fix it.**
1. Add a scorer that checks each `expectedCharacteristic` against the produced canvas.
2. Two paths: (a) **deterministic** for structural ones (e.g. count rectangles, check a label
   exists), and/or (b) **LLM-as-judge** — send the rubric + the compact canvas to a model and ask
   "are these satisfied? answer per item with yes/no + reason."
3. If you use LLM-as-judge, store the judge's reasoning in the report so the score is auditable
   (and so you can defend it: "the judge is itself logged and inspectable").

---

## 🟠 WS-5 — Promoted regression cases can never fail (empty assertions by construction)

- **Severity:** 🟠 High
- **Status:** OPEN

**The problem.** When the flywheel promotes a downvoted trace into a regression case, it writes
`expectedKeywords: []` and stuffs the human note into `expectedCharacteristics` — which (per WS-4)
nothing scores. So a promoted regression case has **no checkable assertion** and passes
unconditionally, forever.

**Where.**
- `src/diagram_agent/flywheel.py:22-29` — `build_regression_case()` sets
  `expectedCharacteristics` from the human note but `expectedKeywords: []`.
- Combined with `evals.py:59-63` (only keywords are scored) → empty keywords → `missing_keywords`
  empty → `expected_keywords_present = True` → `passed = True`, always.

**Why it matters.** The entire *point* of the data flywheel is "real failures become tests that
catch the failure if it comes back." Right now a promoted regression is guaranteed green. It's a
regression test that structurally cannot detect a regression.

**How to fix it.** (Depends on WS-3 and WS-4.)
1. When promoting, **encode the failure as a real, checkable assertion.** Example: feedback "boxes
   overlapped" → set an expectation like `no_overlaps: required`, which WS-3's grader can fail.
2. Auto-extract keywords from the original prompt as a minimum-signal fallback so the case isn't
   assertion-empty.
3. Where the failure is fuzzy, attach it as an `expectedCharacteristic` and rely on the WS-4 judge.
4. Test the loop end-to-end: promote a known-bad trace, re-run evals, confirm the new case **fails**
   until the agent is fixed, then **passes** after. That demonstrated transition is the whole story.

---

## 🟠 WS-6 — `generated_regressions.json` does not exist (the flywheel has no committed output)

- **Severity:** 🟠 High
- **Status:** OPEN

**The problem.** The plan, the mental model, and the demo script all reference
`evals/datasets/generated_regressions.json`. It isn't in the repo — only `golden.json` and
`golden_2.json` exist.

**Where.**
- `evals/datasets/` — contains `golden.json`, `golden_2.json` only.
- Referenced as the flywheel output in `src/diagram_agent/flywheel.py` (`promote_candidate`) and the
  demo in `IMPLEMENTATION_PLAN.md`.

**Why it matters.** "Data flywheel that promotes real interactions into regression cases" is a
claim with **no artifact behind it**. If asked "show me a generated regression," there's nothing to
show. The flywheel may run, but it has never visibly produced its output.

**How to fix it.** (Do after WS-5 so the output is meaningful.)
1. Run a real agent run → downvote it → promote it.
2. Confirm `generated_regressions.json` is written with a *checkable* case.
3. Commit it. One genuine, defensible example beats an empty promise.

---

## 🟡 WS-7 — Two diverging agents: evals test the Python simulator, not the product users touch

- **Severity:** 🟡 Medium
- **Status:** OPEN

**The problem.** There are two agents: the existing TS/Excalidraw one (what users actually use) and
the Python one (what evals run). They have separate, copied system prompts and separate canvas
logic. Your evals validate the Python *simulator*, not the real product.

**Where.**
- `src/diagram_agent/prompts.py` (Python `SYSTEM_PROMPT`, copied from `src/agent-core.ts`).
- `src/diagram_agent/canvas.py` — an in-memory simulator, not the real Excalidraw scene.

**Why it matters.** The claim says the flywheel promotes "real user interactions." But real users
hit the TS/Cloudflare app, while evals and traces run against the Python sim. A careful interviewer
will ask "are you testing the thing users actually use?" — and right now the answer is "no, a
parallel reimplementation."

**How to fix it.** Pick one honest framing and make it true:
- **Option A (cleanest story):** wire the real frontend to the Python backend (the plan's
  "later, the same frontend can be wired to a Python backend") so there's one agent.
- **Option B (honest narrative):** explicitly present the Python layer as an *offline evaluation
  harness / engineering sandbox* that mirrors the production prompt — and say so plainly. Then keep
  the prompts in sync deliberately (single source, generated into both).

---

## 🟡 WS-8 — "Real user interactions" — there are no real users yet

- **Severity:** 🟡 Medium
- **Status:** OPEN

**The problem.** The flywheel narrative implies a stream of real usage. This is a portfolio project;
the traces are self-generated.

**Why it matters.** "Promotes *real user* interactions" overstates it. If asked "how many real users,
how many promoted cases?", the honest numbers are small. Overclaiming is the fastest way to lose
credibility.

**How to fix it.** Reframe honestly and it's still strong: *"I built the full flywheel
infrastructure so that when real usage exists, failures automatically become regression tests. I
validated it end-to-end with seeded interactions."* That claims the engineering (true) without
claiming traffic you don't have.

---

## 🟡 WS-9 — Canvas simulator is low-fidelity vs. real Excalidraw

- **Severity:** 🟡 Medium
- **Status:** OPEN

**The problem.** The simulator uses fixed defaults (width 120, height 60), doesn't expand shape
labels into child text elements, and "binds" arrows by merely storing `start_id`/`end_id`. The plan
promised richer behavior (label expansion, real binding).

**Where.**
- `src/diagram_agent/canvas.py:3-12` — fixed default sizes.
- `src/diagram_agent/canvas.py:31-34` — `add_elements` just stores; no label expansion, no binding
  logic.
- Compare to plan's stated behavior, `IMPLEMENTATION_PLAN.md:134-150`.

**Why it matters.** "Passes in the simulator" doesn't guarantee "correct in real Excalidraw." Your
overlap check (once enabled, WS-3) uses default sizes that may not match real rendered sizes, so it
can both miss real overlaps and flag false ones.

**How to fix it.**
1. Either raise simulator fidelity for the dimensions that affect scoring (sizes, label-as-child),
2. or state the simplification explicitly and scope your eval claims to what the simulator actually
   models. Honesty about scope is a strength, not a weakness.

---

## 🟢 WS-10 — Dead code and message-format confusion in the agent loop

- **Severity:** 🟢 Low
- **Status:** OPEN

**The problem.** `agent.py` is littered with commented-out blocks and mixes two OpenAI message
formats (a `role: "tool"` block, commented out, vs. the `function_call` / `function_call_output`
format in use). This suggests the live LLM path may not have been exercised end-to-end against real
OpenAI.

**Where.**
- `src/diagram_agent/agent.py:88-96, 105-109, 171-178` — commented-out blocks.
- `src/diagram_agent/agent.py:179-194` — `function_call` / `function_call_output` message shaping.

**Why it matters.** Reviewers read code. Dead code and two competing message formats signal "I wasn't
sure this worked." It also raises the risk that the real loop breaks the moment a model is plugged
in (relevant to WS-1).

**How to fix it.**
1. Delete the commented-out code.
2. Run the real loop once against OpenAI end-to-end and confirm tool results feed back correctly.
3. Add one integration-style test (mocked client) asserting the message sequence is well-formed.

---

## 🟢 WS-11 — `schema_valid` is hardcoded `True`

- **Severity:** 🟢 Low
- **Status:** OPEN

**The problem.** Like `no_overlaps`, `schema_valid` is hardcoded. It's *partially* excused because
Pydantic validates elements on construction, so invalid shapes can't reach the canvas — but the
eval still isn't *measuring* anything, so it can't report a violation if validation is ever relaxed.

**Where.**
- `src/diagram_agent/evals.py:60` — `"schema_valid": True`.

**Why it matters.** Minor, but it's a third hardcoded score sitting next to two critical ones. When
you fix WS-1/WS-3, fix this too so all three scores are genuinely computed and the suite has zero
stamps left.

**How to fix it.** Validate `result.canvas_elements` against the Pydantic schemas explicitly in the
eval and set `schema_valid` from the result, even if it's almost always true — so the score reflects
a real check.

---

## Quick status board

| ID | Severity | Title | Status |
|---|---|---|---|
| WS-1 | 🔴 | Evals never call the LLM | OPEN |
| WS-2 | 🔴 | Planning is a hardcoded template | OPEN |
| WS-3 | 🔴 | `no_overlaps` hardcoded; grader unplugged | OPEN |
| WS-4 | 🟠 | `expectedCharacteristics` never scored | OPEN |
| WS-5 | 🟠 | Promoted regressions can't fail | OPEN |
| WS-6 | 🟠 | No committed `generated_regressions.json` | OPEN |
| WS-7 | 🟡 | Evals test the sim, not the real product | OPEN |
| WS-8 | 🟡 | No real users behind "real interactions" | OPEN |
| WS-9 | 🟡 | Low-fidelity canvas simulator | OPEN |
| WS-10 | 🟢 | Dead code / message-format confusion | OPEN |
| WS-11 | 🟢 | `schema_valid` hardcoded | OPEN |

---

## The one-sentence summary

The **architecture** (trace → feedback → candidate → regression → eval) is genuinely good — the
pipes are well laid. The problem is that the **graders are mostly stamps and the agent/planner used
by evals is mostly hardcoded**, so the loop currently can't measure quality or catch a regression.
Fix WS-1 through WS-5 and the resume claim goes from "true on paper" to "true and demonstrable."
