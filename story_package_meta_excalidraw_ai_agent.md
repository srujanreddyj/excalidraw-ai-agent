# Story Package: Python-First AI Agentic System For Excalidraw

Company target: Meta  
Mode: REBUILD  
Resume bullet:

> Built a Python-first AI agentic system for a React/Excalidraw diagramming app, including tool-calling, plan-execute, structured tracing, feedback capture, eval automation, and a data flywheel that promotes real user interactions into regression test cases.

## 1. Source Assessment

Inputs used:

- Resume bullet supplied in the prompt.
- Repository materials in `/Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent`.
- Key docs: `README.md`, `eval_mental_model.md`, `python_agent/IMPLEMENTATION_PLAN.md`, `docs/DEPLOYMENT.md`.
- Key implementation files: `python_agent/src/diagram_agent/agent.py`, `api.py`, `tracing.py`, `flywheel.py`, `evals.py`, `cli.py`, `canvas.py`, `tools.py`, `planner.py`.
- Frontend trace and feedback integration files: `src/components/chat/ChatPanel.tsx`, `TracePanel.tsx`, related chat components.

Existing story-bank classification:

- REBUILD. No prior polished story-bank entry was provided. The repo contains strong technical source material and a mental model doc, but the interview story should be rebuilt fresh around senior platform/data-engineering signals.

What was inferred:

- ASSUMPTION: This is a side/project portfolio build rather than an internal Meta project.
- ASSUMPTION: The strongest interview positioning is not "I built a drawing app"; it is "I built the AI engineering/data infrastructure around an agent so behavior could be observed, evaluated, and improved."
- ASSUMPTION: The project was built under portfolio/demo constraints, so results should be framed as enabling impact and validated functionality, not production-scale user metrics.

Assumptions and guardrails:

- Do not claim production traffic, team leadership, or business metrics unless separately verified.
- Do not claim fine-tuning or model training. The flywheel creates regression/eval data, not training data.
- Do not claim mature enterprise observability. Current trace storage is local SQLite with CLI/API inspection and optional Braintrust export.
- Do not claim deep eval scoring is complete. Python evals currently include basic schema/keyword/no-overlap checks; richer TypeScript scorers and future assertions exist as directionally stronger pieces.

## 2. Canonical Resume Bullet

Interview-safe version:

> Built a Python-first AI engineering layer for a React/Excalidraw diagramming app, adding OpenAI tool-calling, planning-before-execution, SQLite-backed structured traces, user feedback capture, automated eval runs, and a curated data flywheel that turns real failed interactions into regression test cases.

Shorter resume version:

> Built a Python-first AI agent layer for a React/Excalidraw app with tool-calling, planning, structured tracing, feedback capture, eval automation, and a regression-data flywheel from real user interactions.

If you need to sound more data-platform oriented:

> Built the data and evaluation infrastructure around an AI diagramming agent: trace schemas, tool-event logging, feedback joins, regression-case promotion, CLI/API workflows, and automated eval reports for model/tool behavior.

## 3. Decode Summary

Primary behavioral themes:

- Ownership: You took an AI app beyond a simple LLM wrapper by owning the agent runtime, observability, feedback loop, and eval workflow.
- Ambiguity: There was no single "right" design for making an agent inspectable, so you decomposed the problem into traces, tool events, feedback, candidates, and regressions.
- Scope: The work spans frontend integration, FastAPI backend, OpenAI tool-calling, local persistence, CLI operations, eval automation, and deployment path.
- Growth: You can show a clear shift from "make it work" to "make failures inspectable and prevent regressions."

Primary technical themes:

- Agent architecture: plan, execute, tool loop, structured tool definitions, canvas simulator.
- Data platform architecture: trace tables, tool-event grain, feedback joins, candidate queue, generated regression dataset.
- Evaluation infrastructure: JSON datasets, CLI eval runner, reports, Braintrust export path, generated regressions.
- Reliability and debugging: trace IDs, persisted steps/errors/tool inputs/tool outputs/final canvas/latency.
- Human-in-the-loop curation: downvotes create candidates, but promotion is manual/curated to avoid noisy eval data.

Signal-area mapping:

- Scope: End-to-end system across React, FastAPI, OpenAI, SQLite, Typer CLI, evals, and deployment docs.
- Ownership: Strong if framed as "I designed and built the AI engineering layer."
- Ambiguity: Strong because agent quality was hard to debug without a trace/feedback/eval model.
- Perseverance: Use the staged maturity story: local traces first, eval skeleton next, feedback and promotion after.
- Conflict Resolution: Weak unless you add a real disagreement. Use "tradeoff" language rather than inventing conflict.
- Growth: Strong: learned to separate model claims from actual tool actions and turn subjective failures into test artifacts.
- Communication: Moderate: plan review UI, trace panel, CLI commands, readable reports.
- Leadership: Moderate: self-directed technical leadership; do not overclaim people leadership.

Natural Meta mapping:

- Move Fast: You built a working local-first system with CLI, API, and UI paths.
- Focus on Long-Term Impact: You invested in regression data and observability rather than only demo polish.
- Build Awesome Things: The project combines a real interactive product surface with serious AI/data infrastructure.
- Be Open / directness: You can talk honestly about current eval gaps and why staged architecture was deliberate.

Best-fit interview questions:

- "Tell me about a time you built a system from scratch."
- "Tell me about a technically complex project."
- "Tell me about a time you improved reliability or debuggability."
- "Tell me about a time you used data to improve a product/system."
- "Tell me about a time you handled ambiguity."
- "How do you evaluate or monitor AI systems?"
- "How would you design a feedback loop for an AI product?"

## 4. Select Positioning

Recommended catalog position:

- Core story for AI/data infrastructure, platform ownership, observability, and senior technical depth.
- Additional story for pure production-scale distributed systems, because this project is local/demo-scale unless you can verify hosted usage.

Best use cases:

- Senior Data Engineer / Data Platform Engineer loops where you need to show data contracts, traceability, feedback joins, and eval datasets.
- AI infrastructure or LLM application interviews where the interviewer is skeptical of "LLM wrapper" projects.
- Meta behavioral questions around ambiguity, ownership, and building mechanisms.

When to choose this story:

- Choose this over a dashboard/analytics story when the role values infrastructure, correctness, platform usability, and operational thinking.
- Choose this over a generic pipeline story when the interviewer asks about AI, model evaluation, feedback loops, or productized data systems.
- Do not choose it for "largest-scale data pipeline" unless you explicitly frame it as architecture depth rather than scale.

Scope / relevance / uniqueness / recency:

- Scope: High for a portfolio project; spans multiple system layers.
- Relevance: High for AI platform/data infrastructure roles.
- Uniqueness: High because it connects agent traces, feedback, and regression data in one loop.
- Recency: Strong if this is recent work; verify exact dates before interviewing.

## 5. Story Skeletons In CARL

### 30-Second Version

Context: I had a React/Excalidraw diagramming app where the agent could generate diagrams, but the real problem was that failures were hard to inspect. A user could say "the diagram is wrong," but I needed to know whether the plan was wrong, the tool call was wrong, or the canvas state was wrong.

Actions: I built a Python-first AI engineering layer around it: FastAPI endpoints, OpenAI tool-calling, a planning step, a canvas simulator, SQLite-backed structured traces, feedback capture, and a CLI pipeline that promotes downvoted traces into regression eval cases.

Results: The project became much more than an LLM wrapper. Every run had a trace ID, tool inputs and outputs, final canvas state, errors, latency, and feedback. Real user failures could become automated regression cases.

Learning: The biggest lesson was that for AI agents, observability and eval data are first-class product infrastructure, not cleanup work after the model is already built.

### 2-Minute Version

Context: I built a React/Excalidraw diagramming app with an AI agent, but I quickly ran into a classic agent problem: the output could look wrong for many different reasons. The model might misunderstand the prompt, plan the wrong diagram, call the wrong tool, pass malformed arguments, create overlapping shapes, or claim success without actually changing the canvas. If I only looked at the final diagram, I could not debug those layers separately.

Actions: I rebuilt the AI layer in Python so it behaved more like an inspectable platform. I added a FastAPI backend and CLI, an OpenAI tool loop, Pydantic tool schemas, a canvas simulator, and optional planning-before-execution. Then I designed a trace store in SQLite with separate grains for runs and tool events. Each run stores the prompt, plan, final text, final canvas JSON, steps, errors, latency, status, and tool-call count. Each tool event stores the trace ID, call index, tool name, input JSON, and output JSON.

I also added feedback capture. The UI and CLI can attach thumbs-up or thumbs-down feedback to a trace ID. A downvote creates an eval candidate, not an automatic test. From there, a CLI promotion step turns selected candidates into JSON regression cases, so real failures can be included in future eval runs.

Results: That gave me an end-to-end data flywheel: user prompt -> agent run -> trace -> feedback -> candidate -> promoted regression -> eval automation. I could inspect whether a failure came from planning, tool selection, schema validation, or canvas mutation. I also kept the system interview-safe and extensible by starting with local deterministic artifacts before relying on external dashboards.

Learning: I learned to treat AI-agent quality as a data infrastructure problem. The important artifact is not only the answer; it is the lineage of how the answer was produced.

### 5-Minute Version

Context: The app started as a React and Excalidraw diagramming interface. Users could ask for diagrams through chat, and the agent would create or modify canvas elements. The problem was that agent failures were ambiguous. If a JWT flow was missing a refresh-token path, or boxes overlapped, or arrows were not bound correctly, the final image did not tell me where the failure happened. For a senior-level system, I wanted the agent to be observable, evaluable, and improvable from real interactions.

Actions: I split the system into a product surface and an AI engineering layer. The frontend stayed React/Excalidraw. I added a Python FastAPI backend with `/plan`, `/run`, `/feedback`, `/traces`, `/traces/{id}/tools`, and `/candidates` endpoints, plus a Typer CLI for running, inspecting, evaluating, and promoting cases.

On the agent side, I implemented a plan-execute path. The planner produces a structured plan with intent, steps, likely tools, and risks. The executor runs an OpenAI-style tool loop with tools like `queryCanvas`, `addElements`, `updateElements`, and `removeElements`. Tool inputs are validated with Pydantic, and a Python canvas simulator mutates element state so the system can reason about final canvas data, not just text.

The most important piece was the trace model. I created a SQLite trace store with four tables: `traces`, `tool_events`, `feedback`, and `eval_candidates`. The run grain is one agent execution. The tool-event grain is one tool call within a trace. Feedback joins to the trace ID. Eval candidates represent curated possible regressions. That let me separate "what the model said" from "what tools it actually called" and "what canvas state resulted."

Then I built the flywheel. A downvote creates an eval candidate. A promotion command reads the original trace, candidate, and feedback, builds a regression case, and writes it to `evals/datasets/generated_regressions.json`. The eval runner can then run golden datasets plus generated regressions and write reports. There is also a Braintrust export path, but I kept local JSON reports as a source of truth so the workflow was not vendor-locked.

Results: The result was a working AI-agent data loop: traces made runs debuggable, feedback made real failures discoverable, candidates added curation, and generated regressions made failures repeatable. I also had about 30 Python test files and multiple eval reports validating the system mechanics. The impact I would claim is enabling impact: this made the app much easier to debug and gave it a path to improve from real user interactions.

Learning: The senior lesson was that AI agent systems need data contracts and lineage just like batch or streaming platforms. Without structured traces and curated eval data, you are mostly arguing from screenshots and vibes.

### 10-15 Minute Deep-Dive Outline

Roadmap to say aloud:

> I will break this into four parts: first, why the original agent was hard to debug; second, the Python agent architecture; third, the trace/feedback/eval data model; and fourth, what worked, what was still weak, and what I would improve next.

1. Context and stakes

- React/Excalidraw app had an AI agent for creating and modifying diagrams.
- The core problem was not just generation; it was making agent behavior inspectable.
- Agent failures are multi-layered: prompt understanding, planning, tool choice, tool arguments, canvas mutation, final response.

2. Architecture

- Frontend: React + Excalidraw.
- Backend: Python FastAPI service.
- Agent: OpenAI Responses/tool-calling path plus deterministic local simulator for tests.
- Tools: query, add, update, remove canvas elements.
- Planner: off/required/auto modes.
- CLI: run, eval, traces, feedback, candidates, Braintrust export.

3. Data model

- `traces`: one row per agent run.
- `tool_events`: one row per tool call.
- `feedback`: one row per feedback event attached to a trace.
- `eval_candidates`: one row per trace selected as a possible regression.
- Generated regression dataset: JSON cases derived from promoted traces.

4. Operational flow

- UI calls `/plan`.
- User approves plan.
- UI calls `/run`.
- Python executes tool loop and mutates canvas.
- TraceStore persists run and tool events.
- UI exposes trace ID and trace panel.
- User feedback attaches to trace.
- Downvote creates candidate.
- CLI promotion creates regression case.
- Eval runner includes generated regressions.

5. Results

- Debuggable runs with trace IDs.
- Ability to inspect tool inputs and outputs.
- Feedback tied to actual execution lineage.
- Regression dataset from real interactions.
- Local eval reports and Braintrust export path.

6. Weaknesses and next iteration

- Python eval scoring is currently shallow.
- SQLite is appropriate for local/demo but not multi-user production.
- Feedback notes need richer taxonomy.
- Regression builder should convert feedback into structured assertions.
- For production, move traces to durable storage, add schema versioning, async jobs, richer metrics, privacy controls, and dashboarding.

## 6. CARL Breakdown

### Context

Strongest details to keep:

- The app was not only a diagram generator; it needed an inspectable agent workflow.
- Final screenshots were insufficient for debugging.
- Failures could occur at multiple boundaries: plan, tool choice, arguments, schema validation, canvas mutation, final text.

Weak or risky claims:

- Avoid "production-scale" unless you can prove it.
- Avoid "users at Meta" or "enterprise deployment."
- Avoid "the model learned from feedback" because this was eval/regression learning, not training.

Safe wording:

- "I treated it as an AI engineering/data infrastructure problem."
- "I built a local-first trace and eval loop."
- "The system created a path from real failures to regression tests."

Senior-level emphasis:

- You identified that the real bottleneck was observability and correctness, not calling an LLM.

### Actions

Strongest details to keep:

- FastAPI endpoints: `/plan`, `/run`, `/feedback`, `/traces`, `/candidates`.
- Tool loop with `queryCanvas`, `addElements`, `updateElements`, `removeElements`.
- Pydantic validation for tool inputs.
- SQLite trace store with run/tool/feedback/candidate tables.
- CLI commands for traces, feedback, candidates, evals, Braintrust export.
- Curated promotion instead of blindly turning every downvote into a test.

Weak or risky claims:

- Do not imply the eval scorer fully understands diagrams yet.
- Do not imply all frontend flows are production hardened.

Safe wording:

- "I started with local SQLite because I wanted deterministic, inspectable artifacts before adding external infrastructure."
- "The current regression case stores the human feedback as expected characteristics; the next step would be richer generated assertions."

Senior-level emphasis:

- You designed data grains and interfaces intentionally.
- You separated observability, feedback, curation, and eval execution.

### Results

Strongest details to keep:

- Every run can have a trace ID.
- Stored run data includes prompt, plan, final text, canvas JSON, steps, errors, latency, status, step count, tool-call count.
- Stored tool data includes ordered call index, tool name, input JSON, output JSON.
- Negative feedback creates eval candidates.
- Promotion writes generated regression cases.
- Eval runner can run multiple datasets and produce reports.

Weak or risky claims:

- Avoid unsupported latency, cost, quality, or adoption numbers.
- Avoid "reduced regressions by X%" unless measured.

Safe wording:

- "Measured impact was at the system level: I could inspect and reproduce agent failures."
- "Enabling impact was that real interactions could feed the regression suite."
- "I validated mechanics with tests and local eval reports rather than claiming production business impact."

Senior-level emphasis:

- Results are about mechanism quality: debuggability, repeatability, and future improvement loops.

### Learnings

Strongest details to keep:

- AI systems need lineage and data contracts.
- Feedback needs trace context.
- Not all user feedback should become an eval automatically.
- Local-first artifacts reduce vendor lock-in and improve debugging.

Weak or risky claims:

- Do not frame this as solved end-to-end at production maturity.

Safe wording:

- "I would now invest earlier in richer scoring contracts and schema versioning."
- "I learned to treat eval data quality like product data quality."

Senior-level emphasis:

- Reflection should sound like platform judgment, not just excitement about AI.

## 7. Technical Deep Dive

Architecture diagram:

```text
React + Excalidraw UI
  |
  | backend toggle, chat prompt, plan review, feedback, trace panel
  v
Python FastAPI service
  |-- GET  /health
  |-- POST /plan
  |-- POST /run
  |-- POST /feedback
  |-- GET  /traces
  |-- GET  /traces/{trace_id}
  |-- GET  /traces/{trace_id}/tools
  |-- GET  /traces/{trace_id}/feedback
  |-- GET  /candidates
  |
  v
Planner + Tool-Calling Agent
  |-- Plan: intent, steps, likely tools, risks
  |-- Tools: queryCanvas, addElements, updateElements, removeElements
  |-- Validation: Pydantic schemas
  |-- State: CanvasState simulator
  |
  v
TraceStore SQLite
  |-- traces
  |-- tool_events
  |-- feedback
  |-- eval_candidates
  |
  v
Flywheel + Evals
  |-- promote candidate
  |-- write generated_regressions.json
  |-- run eval datasets
  |-- write eval reports
  |-- optional Braintrust export
```

Key systems and interfaces:

- React/Excalidraw frontend: product interaction surface.
- Python FastAPI backend: API surface for planning, execution, traces, and feedback.
- OpenAI tool loop: model proposes function calls; Python executes validated tools.
- Canvas simulator: stores diagram elements in memory during a run.
- TraceStore: persists structured run and tool-event records.
- Flywheel module: converts candidate traces into regression cases.
- Eval runner: loads JSON eval datasets, runs the agent, scores outputs, writes reports.
- Typer CLI: operational interface for local runs, trace inspection, feedback, promotion, evals, and Braintrust export.

Key datasets / schemas / grains / contracts:

- `traces`: grain is one agent run.
  - Fields include trace ID, input, plan JSON, final text, final canvas JSON, steps JSON, errors JSON, latency, step count, tool-call count, status, created time.
- `tool_events`: grain is one tool call within one trace.
  - Fields include trace ID, call index, tool call ID, tool name, input JSON, output JSON.
- `feedback`: grain is one feedback event attached to one trace.
  - Fields include trace ID, rating, note, created time.
- `eval_candidates`: grain is one trace selected as a possible regression.
  - Fields include trace ID, reason, status.
- Eval dataset JSON: grain is one eval case.
  - Fields include ID, input, expected characteristics, expected keywords, difficulty, category.

Operational flow:

```text
User prompt
  -> /plan
  -> structured plan returned
  -> user reviews/approves plan
  -> /run
  -> model/tool loop executes
  -> CanvasState mutates
  -> AgentRunResult created
  -> TraceStore.save_run persists trace and tool events
  -> frontend receives final text and trace ID
  -> user clicks feedback
  -> /feedback stores feedback
  -> downvote creates eval candidate
  -> CLI promotes selected candidate
  -> generated_regressions.json updated
  -> eval runner includes generated regression dataset
```

Quality, observability, validation, debugging:

- Tool inputs use Pydantic validation.
- Tool execution returns JSON-serializable outputs.
- Trace records include errors and status.
- Tool events preserve ordered inputs and outputs.
- Trace panel exposes prompt, final response, steps, errors, tool calls, feedback, latency.
- CLI can list traces, show trace details, and inspect tool events.
- Canvas simulator can detect obvious overlaps.
- Eval runner checks basic schema/keyword/no-overlap conditions in Python.

Scaling, reliability, and cost/performance tradeoffs:

- SQLite was chosen for local-first traceability, simplicity, and deterministic debugging.
- A production version should move traces to durable hosted storage, add indexing, retention policies, privacy filtering, and schema versioning.
- Planning-before-execution improves control on complex prompts but adds latency and model cost.
- The local deterministic backend supports cheap tests and demos without calling OpenAI.
- Braintrust export is useful for reporting, but local JSON reports avoid vendor lock-in.

Backfills, idempotency, failure handling, recovery patterns:

- Promotion is idempotent at the regression-case ID level by keying generated cases by `trace-regression-{trace_id}`.
- Failed runs still save traces with error status when errors are present in `AgentRunResult`.
- Candidate statuses support `new`, `ignored`, and `promoted`.
- The design supports re-running evals with multiple datasets, including generated regressions.
- For production, add replay/backfill commands that reprocess old traces into richer eval cases after schema changes.

Alternatives considered and why they were rejected:

- Logs only: rejected because logs do not give clean queryable grains for run, tool event, feedback, and candidate.
- Blindly promote all downvotes: rejected because user feedback can be vague, wrong, or non-actionable.
- External eval dashboard as source of truth: deferred because local artifacts were easier to debug and less vendor-coupled.
- TypeScript-only backend: kept as original path, but Python was better for AI/data engineering workflows, Pydantic schemas, CLI tooling, evals, and future ML infrastructure.
- Fine-tuning loop: rejected/deferred because the immediate problem was evaluation and regression safety, not model training.

## 8. Cross-Functional And Leadership Narrative

Partnership framing:

- SWE/frontend: The React app needed a clean way to choose the Python backend, display health, show trace IDs, submit feedback, and inspect traces.
- Infra/platform: The backend needed clear API endpoints, local persistence, CLI commands, and deployment options.
- Data/ML/AI: The agent needed tool schemas, eval cases, reports, feedback capture, and a promotion path from real interactions to regressions.
- PM/product: The feedback workflow had to preserve user context and not interrupt the main diagramming experience.

Disagreement or ambiguity moments:

- The main ambiguity was where to invest: diagram-generation quality versus observability/evals.
- The senior framing: "I decided that without traces and regression data, quality improvements would be hard to measure, so I built the measurement loop first."

How you created clarity:

- Defined clear data grains: run, tool event, feedback event, eval candidate, eval case.
- Defined operational commands: run, eval, traces, feedback, candidates, export.
- Kept UI and backend responsibilities separated.

Personal ownership:

- Say: "I designed and built the Python AI engineering layer and the trace/feedback/eval flywheel."
- Say: "I wired the frontend enough to expose backend health, trace inspection, and feedback."
- Avoid: "I led a team" unless true.
- Avoid: "I owned production at scale" unless true.

## 9. Failure Modes

Realistic hard problem:

- Failure: The final diagram could be wrong, but the failure source was ambiguous.
- Detection: A bad output or user downvote only said "the result is wrong"; trace inspection was needed to see whether the model planned incorrectly, skipped a tool, passed bad arguments, or produced overlapping elements.
- Debugging: Tool events made it possible to compare the model's final claim against actual tool calls and canvas mutations.
- Change afterward: You introduced structured traces, ordered tool events, and feedback attached to trace IDs.
- What you would do differently now: Define richer eval assertions earlier, especially for arrow binding, expected element counts, ID preservation, and layout overlap thresholds.

Near-miss to discuss:

- The system could have blindly converted every downvote into a permanent regression. That would pollute eval data with vague or subjective feedback.
- You avoided that by using an `eval_candidates` queue and manual promotion.
- Senior learning: Feedback ingestion needs data quality controls just like any production data pipeline.

Technical weakness to own:

- Current Python scoring is still basic. It validates mechanics but does not fully judge diagram semantics.
- Strong answer: "I intentionally built the pipeline first, then would improve scorer depth with structured expected assertions and possibly model-assisted judging for semantics."

## 10. Drill-Down Question Bank

### Ownership And Scope

1. What did you personally build?
   - Probing: Whether you are overstating ownership.
   - Model answer: "I built the Python AI engineering layer: FastAPI endpoints, tool loop, planner integration, trace store, feedback/candidate flow, eval runner, CLI commands, and promotion pipeline. The React/Excalidraw surface already existed and I wired it to use the Python backend and inspect traces."
   - Trap: Claiming broad team leadership or production ownership you cannot support.

2. Why was this more than an LLM wrapper?
   - Probing: Systems depth.
   - Model answer: "The key work was around the model: typed tools, canvas state, structured traces, feedback joins, eval candidates, regression promotion, and eval automation. The model call is only one component."
   - Trap: Talking only about prompts.

3. What was the hardest part?
   - Probing: Senior judgment.
   - Model answer: "Designing the data loop so failures were inspectable and reusable. The technical challenge was less about calling OpenAI and more about preserving lineage from prompt to plan to tool calls to canvas state to feedback."
   - Trap: Saying "integrating the API" was hardest.

### Architecture And Tradeoffs

4. Why Python instead of keeping everything in TypeScript?
   - Probing: Tradeoff awareness.
   - Model answer: "The frontend and original agent path were TypeScript, but Python gave me a better AI/data engineering surface for Pydantic schemas, CLI tooling, evals, trace processing, and future ML workflows."
   - Trap: Dismissing TypeScript as bad.

5. Why SQLite?
   - Probing: Storage judgment.
   - Model answer: "For the portfolio/demo stage, SQLite was the right local-first store: deterministic, inspectable, cheap, and enough to prove the data model. In production I would move to durable hosted storage with indexing, retention, privacy controls, and schema versioning."
   - Trap: Pretending SQLite is production-scale for multi-user traffic.

6. What is the grain of your trace tables?
   - Probing: Data modeling skill.
   - Model answer: "`traces` is one row per agent run. `tool_events` is one row per tool call within a run. `feedback` is one row per feedback event attached to a trace. `eval_candidates` is one row per trace selected for possible regression promotion."
   - Trap: Vague "we logged everything."

7. Why have eval candidates instead of directly writing regression tests?
   - Probing: Data quality.
   - Model answer: "Feedback is noisy. A downvote may reflect vague expectations or a non-actionable complaint. The candidate queue gives me a curation step before polluting the regression suite."
   - Trap: Treating all feedback as equally valid.

### Data Quality / Observability / Correctness

8. How did you debug a wrong diagram?
   - Probing: Operational maturity.
   - Model answer: "I would open the trace, check the plan, inspect ordered tool events, compare tool inputs/outputs to final canvas JSON, and then see whether feedback pointed to layout, missing entities, wrong labels, or arrow bindings."
   - Trap: Only saying "I looked at logs."

9. What correctness checks existed?
   - Probing: Honest eval depth.
   - Model answer: "In Python, the first checks were schema validity, expected keywords, and no obvious overlaps. The repo also has TypeScript scorers for structure, connectivity, labels, bound arrows, and overlaps. I would be clear that semantic diagram judging is a next iteration."
   - Trap: Overselling eval maturity.

10. How did you separate model claims from actual actions?
    - Probing: Agent-specific insight.
    - Model answer: "Tool events store the actual tool name, input JSON, and output JSON. So if the assistant says it created a JWT flow, I can verify whether it actually called `addElements` with the expected nodes and arrows."
    - Trap: Trusting final assistant text.

11. How did feedback connect to data?
    - Probing: Join correctness.
    - Model answer: "Feedback is stored by trace ID. That means a thumbs-down joins to the original prompt, plan, tool calls, final canvas, latency, and errors."
    - Trap: Feedback without lineage.

### Platform / Infra / Scaling / Reliability

12. What would break first at production scale?
    - Probing: Scalability honesty.
    - Model answer: "SQLite and synchronous local eval workflows would be the first limits. I would move traces to durable storage, put eval generation behind async jobs, add indexes and retention, and separate online request latency from offline evaluation."
    - Trap: Claiming the demo architecture is already production-ready.

13. How would you make it reliable for many users?
    - Probing: Production design.
    - Model answer: "I would add durable trace storage, request IDs, schema versions, privacy filters, background workers for eval promotion, retry/idempotency semantics for writes, and dashboards for failure rates by prompt category/tool/error type."
    - Trap: Only adding more model retries.

14. How did you think about cost?
    - Probing: Cost/performance.
    - Model answer: "Planning improves control but adds model calls. I made planning configurable: off, required, and auto. The local deterministic backend also lets tests run without model cost."
    - Trap: Saying cost was irrelevant.

15. What would you backfill?
    - Probing: Data platform thinking.
    - Model answer: "If I improved the regression schema, I would backfill older traces into richer eval cases, preserving trace IDs and schema versions so I could compare old and new scorer behavior."
    - Trap: No replay strategy.

### Stakeholders / Conflict / Leadership

16. How would you explain this to a PM?
    - Probing: Communication.
    - Model answer: "I would say: when a user says the diagram is bad, we can now see exactly what happened and decide whether that failure should become an automated test. That shortens the loop from complaint to durable quality improvement."
    - Trap: Overly technical answer.

17. What tradeoff did you have to defend?
    - Probing: Influence.
    - Model answer: "I prioritized trace/eval infrastructure over immediately adding more diagram features because without measurement, every quality improvement would be anecdotal."
    - Trap: Framing every tradeoff as obvious.

18. What was team-owned versus personally owned?
    - Probing: Integrity.
    - Model answer: "This was a project where I personally owned the Python agentic system and data flywheel. I should not represent it as a large team delivery unless I am talking about the general product architecture."
    - Trap: Inflated scope.

### Metrics And Result Attribution

19. What impact can you quantify?
    - Probing: Evidence.
    - Model answer: "I would avoid fake product metrics. The defensible numbers are system artifacts: trace tables, CLI/API workflows, test coverage, eval reports, and generated regressions. The impact is enabling impact: failures became inspectable and promotable into tests."
    - Trap: Inventing adoption or accuracy numbers.

20. How would you measure success in production?
    - Probing: Metrics design.
    - Model answer: "I would track task success rate, user feedback rate, downvote categories, regression pass rate, tool error rate, invalid schema rate, overlap/layout failure rate, latency, cost per successful run, and recurrence of previously promoted failures."
    - Trap: Only tracking thumbs up/down.

21. How do you attribute an improvement?
    - Probing: Experimentation maturity.
    - Model answer: "I would run evals before and after a prompt/tool/model change on the same golden and regression datasets, compare pass rates by category, and keep online feedback as a separate signal because user mix can shift."
    - Trap: Confusing eval improvement with product impact.

### ML / AI / Experimentation Specifics

22. Did the model train on user feedback?
    - Probing: Honesty.
    - Model answer: "No. The feedback became eval/regression data. That is different from fine-tuning. I would only use it for training after stronger consent, privacy, labeling, and quality controls."
    - Trap: Saying "the model learned" imprecisely.

23. Why planning before execution?
    - Probing: Agent design.
    - Model answer: "Planning creates a structured intermediate artifact: intent, steps, likely tools, risks. It helps with complex prompts and gives the user/system something to inspect before tool execution, but I made it configurable because it adds latency."
    - Trap: Planning for every trivial request without tradeoff.

24. What makes evals hard here?
    - Probing: AI eval sophistication.
    - Model answer: "Diagram quality is partly structural and partly semantic. Keywords are not enough. Good evals need shape counts, labels, connectivity, arrow binding, overlap checks, preservation of existing IDs, and maybe human/model-assisted semantic judging."
    - Trap: Claiming a simple keyword check proves quality.

25. What would you build next?
    - Probing: Roadmap quality.
    - Model answer: "I would add richer assertion schemas, scorer versioning, trace schema versioning, production storage, async eval jobs, privacy filtering, and dashboards that slice failures by prompt category, tool, and regression history."
    - Trap: Saying "more data" without mechanisms.

## 11. Safe Wording And Guardrails

Phrases to use:

- "Python-first AI engineering layer."
- "Structured trace store."
- "Tool-event grain."
- "Feedback attached to trace lineage."
- "Curated regression promotion."
- "Local-first eval artifacts."
- "Enabling impact rather than production business impact."
- "Plan-execute path with configurable planning."
- "The flywheel improves eval coverage, not model weights."

Phrases to avoid:

- "Production-grade at scale" unless verified.
- "The model learned from feedback."
- "Fully automated self-improving agent."
- "Reduced errors by X%" without measurement.
- "Led a team" unless true.
- "Streaming pipeline" unless you explicitly mean event-like flow, not actual streaming infra.
- "Meta project" or any implication this was done inside Meta.

Handling uncertain numbers:

- Say: "I do not want to overclaim a metric I did not instrument."
- Say: "The measured artifacts were traces, eval reports, generated regression cases, and test coverage."
- Say: "In production, I would measure pass rate, recurrence rate, downvote rate, tool error rate, latency, and cost per successful run."

Avoiding analytics-only framing:

- Lead with trace schemas, data grains, lineage, idempotent promotion, eval automation, and operational workflows.
- Use dashboards/metrics only as future observability surfaces, not as the core accomplishment.

Staying honest on "I" vs "we":

- Use "I" for the architecture and implementation you personally built.
- Use "the system" for behavior that emerges from multiple components.
- Use "we" only if discussing a real team context.

## 12. Gaps And Anchors

Information still missing:

- Exact project timeline and whether it was solo or collaborative.
- Any real user/demo feedback examples and the number of promoted regression cases.
- Whether the hosted demo was deployed and used externally.
- Exact eval pass/fail trend before and after adding generated regressions.
- Any cost, latency, or reliability measurements from OpenAI-backed runs.

What to verify before using this in an interview:

- Confirm whether `generated_regressions.json` currently exists and how many cases it contains.
- Confirm which eval reports are representative.
- Run one clean demo flow and save a trace ID you can talk through.
- Verify whether the frontend feedback note supports free-text or only thumbs up/down in the current UI.
- Verify dates so you can place the story accurately on your resume.

Anchor keywords to memorize:

- Trace lineage
- Tool-event grain
- Feedback-to-regression flywheel
- Curated eval candidates
- Plan-execute observability

Top signals to lead with:

- Primary: You turned an AI-agent product into an inspectable data/evaluation system.
- Secondary: You made real user failures reusable through a curated regression-data flywheel.

Should this be rebuilt further?

- The story package is strong enough for interview practice now.
- Rebuild further only after adding exact timeline, one concrete failure example, number of eval cases/regressions, and one measured before/after comparison.

## Optional Prep Menu

1. Create a 60-second Meta behavioral answer from this.
2. Create a hostile technical mock-interview script.
3. Create a one-page cheat sheet with only anchors, diagrams, and safe wording.
4. Add one verified demo trace and turn it into a concrete failure/debugging example.
