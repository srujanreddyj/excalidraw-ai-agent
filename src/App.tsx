import { useState, useCallback, useEffect, useRef } from "react";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import {
  convertToExcalidrawElements,
  CaptureUpdateAction,
  newElementWith,
} from "@excalidraw/excalidraw";
import { useAgent } from "agents/react";
import { useAgentChat } from "@cloudflare/ai-chat/react";
import type { UIMessage } from "ai";
import Canvas from "./components/Canvas";
import ChatPanel from "./components/chat/ChatPanel";
import TracePanel, { type TraceViewData } from "./components/chat/TracePanel";
import { serializeCanvasState } from "./context/canvas-state";
import { findOverlaps } from "./context/overlaps";
import { applyCrossCallBindings, mergeBoundElements } from "./context/cross-call-bindings";
import "./App.css";

// One agent instance per page load. The canvas state lives only in the
// browser, so persisting chat history across refreshes would leave a dead
// conversation referencing diagrams that no longer exist.
const sessionId = crypto.randomUUID();
const defaultPythonAgentUrl = "http://127.0.0.1:8000";
const pythonAgentUrl = (
  import.meta.env.VITE_PYTHON_AGENT_URL ?? defaultPythonAgentUrl
).replace(/\/$/, "");

type Backend = "cloudflare" | "python";
type PythonHealth = "unknown" | "checking" | "online" | "offline";
type PythonStatus = "ready" | "planning" | "waiting_approval" | "executing";

interface PythonCanvasElement {
  id: string;
  type: "rectangle" | "ellipse" | "diamond" | "arrow" | "text";
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string | null;
  start_id?: string | null;
  end_id?: string | null;
}

interface PythonRunResult {
  final_text: string;
  canvas_elements: PythonCanvasElement[];
  trace_id: string;
  errors: string[];
}

interface Plan {
  intent: string;
  steps: string[];
  tools_likely_needed: string[];
  risks: string[];
}

interface PythonPlanResponse {
  prompt: string;
  plan: Plan;
}

// Recursively drop null valued fields. Our tool schemas use nullable
// rather than optional so OpenAI strict mode stays on, which means the
// agent always sends every field. The Excalidraw skeleton helper expects
// undefined for "use the default," not null, and chokes on `label: null`
// or `start: null`. Recursion is required because nested objects (label,
// start, end) also carry nullable fields like fontSize and textAlign.
function stripNulls(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stripNulls);
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      if (v !== null) out[k] = stripNulls(v);
    }
    return out;
  }
  return value;
}

function toPythonSkeletonElement(element: PythonCanvasElement): Record<string, unknown> {
  const base = {
    id: element.id,
    type: element.type,
    x: element.x,
    y: element.y,
    width: element.width,
    height: element.height,
  };

  if (element.type === "arrow") {
    return {
      ...base,
      start: element.start_id ? { id: element.start_id } : undefined,
      end: element.end_id ? { id: element.end_id } : undefined,
      label: element.text ? { text: element.text } : undefined,
    };
  }

  return {
    ...base,
    label: element.text ? { text: element.text } : undefined,
  };
}

function makeTextMessage(role: "user" | "assistant", text: string): UIMessage {
  return {
    id: crypto.randomUUID(),
    role,
    parts: [{ type: "text", text }],
  } as UIMessage;
}

function formatPlanMessage(plan: Plan): string {
  const steps = plan.steps.map((step, index) => `${index + 1}. ${step}`).join("\n");
  const tools = plan.tools_likely_needed.length > 0
    ? plan.tools_likely_needed.join(", ")
    : "none";
  const risks = plan.risks.length > 0
    ? plan.risks.map((risk) => `- ${risk}`).join("\n")
    : "- none";

  return `Plan ready. Review it, then click Execute.\n\nIntent: ${plan.intent}\n\nSteps:\n${steps}\n\nLikely tools: ${tools}\n\nRisks:\n${risks}`;
}

function formatPythonBackendError(error: unknown): string {
  if (error instanceof TypeError) {
    return `Python backend is offline at ${pythonAgentUrl}. Start it with: cd python_agent && uv run uvicorn diagram_agent.api:app --host 127.0.0.1 --port 8000 --reload`;
  }

  return error instanceof Error ? error.message : "Python backend request failed";
}

export default function App() {
  const [excalidrawAPI, setExcalidrawAPI] =
    useState<ExcalidrawImperativeAPI | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [backend, setBackend] = useState<Backend>("cloudflare");
  const [pythonMessages, setPythonMessages] = useState<UIMessage[]>([]);
  const [pythonStatus, setPythonStatus] = useState<PythonStatus>("ready");
  const [pythonHealth, setPythonHealth] = useState<PythonHealth>("unknown");
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);
  const [pendingPlan, setPendingPlan] = useState<Plan | null>(null);
  const [traceViewData, setTraceViewData] = useState<TraceViewData | null>(null);
  const [loadingTraceId, setLoadingTraceId] = useState<string | null>(null);
  const [traceViewError, setTraceViewError] = useState<string | null>(null);
  const pythonActivityLabel =
    pythonStatus === "planning"
      ? "Planning..."
      : pythonStatus === "waiting_approval"
        ? "Waiting for approval"
        : pythonStatus === "executing"
          ? "Executing..."
          : null;

  // Hold the latest excalidrawAPI in a ref so onToolCall (captured once at
  // hook init) always reads the live API instead of a stale closure copy.
  const excalidrawAPIRef = useRef<ExcalidrawImperativeAPI | null>(null);
  useEffect(() => {
    excalidrawAPIRef.current = excalidrawAPI;
  }, [excalidrawAPI]);

  const checkPythonHealth = useCallback(async () => {
    setPythonHealth("checking");
    try {
      const response = await fetch(`${pythonAgentUrl}/health`);
      const isOnline = response.ok;
      setPythonHealth(isOnline ? "online" : "offline");
      return isOnline;
    } catch {
      setPythonHealth("offline");
      return false;
    }
  }, []);

  useEffect(() => {
    if (backend === "python") {
      void checkPythonHealth();
    }
  }, [backend, checkPythonHealth]);

  const handleApiReady = useCallback((api: ExcalidrawImperativeAPI) => {
    setExcalidrawAPI(api);
  }, []);

  const agent = useAgent({ agent: "design-agent", name: sessionId });

  // All four canvas tools are client side. The worker streams the call here,
  // we apply it to the live Excalidraw scene, and submit the result via
  // addToolOutput so the agent loop resumes.
  const { messages, sendMessage, status } = useAgentChat({
    agent,
    onToolCall: async ({ toolCall, addToolOutput }) => {
      const api = excalidrawAPIRef.current;
      if (!api) {
        addToolOutput({ toolCallId: toolCall.toolCallId, output: { error: "canvas not ready" } });
        return;
      }

      if (toolCall.toolName === "queryCanvas") {
        addToolOutput({
          toolCallId: toolCall.toolCallId,
          output: { summary: serializeCanvasState(api.getSceneElements() as unknown[]) },
        });
        return;
      }

      if (toolCall.toolName === "addElements") {
        const { elements } = toolCall.input as { elements: unknown[] };
        // Strip null fields recursively before handing to
        // convertToExcalidrawElements. Our nullable schema forces the model
        // to send every field, but the skeleton helper expects undefined
        // (not null) for "use the default" and chokes on `label: null` or
        // `start: null`.
        const cleaned = elements.map(stripNulls) as Record<string, unknown>[];
        const newOnes = convertToExcalidrawElements(cleaned as never, { regenerateIds: false });

        // Patch arrow bindings that reference shapes already on the canvas
        // (the helper only resolves bindings within its own input batch).
        // See src/context/cross-call-bindings.ts for the gory details.
        const existingScene = api.getSceneElements();
        const { arrowsByTargetId } = applyCrossCallBindings(
          cleaned,
          newOnes as unknown as { id: string; startBinding?: unknown; endBinding?: unknown }[],
          existingScene as unknown as { id: string }[]
        );
        const patchedExisting = existingScene.map((el) => {
          const incoming = arrowsByTargetId.get(el.id);
          if (!incoming || incoming.length === 0) return el;
          const merged = mergeBoundElements(
            el as unknown as { id: string; boundElements?: readonly { id: string; type: string }[] },
            incoming
          );
          return newElementWith(el, { boundElements: merged } as never);
        });

        const next = [...patchedExisting, ...newOnes];
        api.updateScene({ elements: next, captureUpdate: CaptureUpdateAction.IMMEDIATELY });
        api.scrollToContent(next, { fitToContent: true });
        // Detect overlaps in the post-add scene and surface them in the
        // tool result so the agent's next reasoning step sees collisions
        // and can self correct via updateElements. Same finding the
        // noOverlaps eval scorer would report.
        const overlaps = findOverlaps(next as unknown[]);
        addToolOutput({
          toolCallId: toolCall.toolCallId,
          output: { added: newOnes.length, overlaps },
        });
        return;
      }

      if (toolCall.toolName === "updateElements") {
        const { updates } = toolCall.input as {
          updates: { id: string; fields: Record<string, unknown> }[];
        };
        const byId = new Map(
          updates.map((u) => [u.id, stripNulls(u.fields) as Record<string, unknown>])
        );
        const next = api.getSceneElements().map((el) => {
          const fields = byId.get(el.id);
          return fields && Object.keys(fields).length > 0
            ? newElementWith(el, fields as never)
            : el;
        });
        api.updateScene({ elements: next, captureUpdate: CaptureUpdateAction.IMMEDIATELY });
        addToolOutput({ toolCallId: toolCall.toolCallId, output: { updated: byId.size } });
        return;
      }

      if (toolCall.toolName === "removeElements") {
        const { ids } = toolCall.input as { ids: string[] };
        const remove = new Set(ids);
        const next = api.getSceneElements().filter((el) => !remove.has(el.id));
        api.updateScene({ elements: next, captureUpdate: CaptureUpdateAction.IMMEDIATELY });
        addToolOutput({ toolCallId: toolCall.toolCallId, output: { removed: remove.size } });
        return;
      }
    },
  });

  const applyPythonRunResult = useCallback((result: PythonRunResult) => {
    const api = excalidrawAPIRef.current;
    if (!api) {
      throw new Error("Canvas is not ready");
    }

    const skeleton = result.canvas_elements.map(toPythonSkeletonElement);
    const next = convertToExcalidrawElements(skeleton as never, {
      regenerateIds: false,
    });
    api.updateScene({
      elements: next,
      captureUpdate: CaptureUpdateAction.IMMEDIATELY,
    });
    api.scrollToContent(next, { fitToContent: true });
  }, []);

  const sendPythonMessage = useCallback(
    async (message: { role: "user"; parts: { type: "text"; text: string }[] }) => {
      const prompt = message.parts.map((part) => part.text).join("\n").trim();
      if (!prompt) return;

      setPythonMessages((current) => [...current, makeTextMessage("user", prompt)]);
      setPythonStatus("planning");
      setPendingPrompt(null);
      setPendingPlan(null);

      try {
        if (pythonHealth === "offline") {
          const isOnline = await checkPythonHealth();
          if (!isOnline) {
            throw new TypeError("Python backend offline");
          }
        }

        const response = await fetch(`${pythonAgentUrl}/plan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt,
            planner_backend: "openai",
          }),
        });

        if (!response.ok) {
          throw new Error(`Python backend returned ${response.status}`);
        }

        const result = (await response.json()) as PythonPlanResponse;
        setPythonHealth("online");
        setPendingPrompt(result.prompt);
        setPendingPlan(result.plan);
        setPythonStatus("waiting_approval");
        setPythonMessages((current) => [
          ...current,
          makeTextMessage("assistant", formatPlanMessage(result.plan)),
        ]);
      } catch (error) {
        if (error instanceof TypeError) {
          setPythonHealth("offline");
        }
        const message = formatPythonBackendError(error);
        setPythonMessages((current) => [
          ...current,
          makeTextMessage("assistant", `Python backend error: ${message}`),
        ]);
      } finally {
        setPythonStatus((current) =>
          current === "planning" ? "ready" : current
        );
      }
    },
    [checkPythonHealth, pythonHealth]
  );

  const executePythonPlan = useCallback(async () => {
    if (!pendingPrompt || !pendingPlan) return;

    const prompt = pendingPrompt;
    const approvedPlan = pendingPlan;

    setPendingPrompt(null);
    setPendingPlan(null);
    setPythonStatus("executing");

    try {
      if (pythonHealth === "offline") {
        const isOnline = await checkPythonHealth();
        if (!isOnline) {
          throw new TypeError("Python backend offline");
        }
      }

      const response = await fetch(`${pythonAgentUrl}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          backend: "openai",
          planning: "required",
          approved_plan: approvedPlan,
        }),
      });

      if (!response.ok) {
        throw new Error(`Python backend returned ${response.status}`);
      }

      const result = (await response.json()) as PythonRunResult;
      setPythonHealth("online");
      applyPythonRunResult(result);

      const suffix = result.trace_id ? `\n\nTrace: ${result.trace_id}` : "";
      const errorSuffix =
        result.errors.length > 0 ? `\n\nErrors: ${result.errors.join("; ")}` : "";
      setPythonMessages((current) => [
        ...current,
        makeTextMessage("assistant", `${result.final_text}${suffix}${errorSuffix}`),
      ]);
      setPythonStatus("ready");
    } catch (error) {
      if (error instanceof TypeError) {
        setPythonHealth("offline");
      }
      const message = formatPythonBackendError(error);
      setPythonMessages((current) => [
        ...current,
        makeTextMessage("assistant", `Python backend error: ${message}`),
      ]);
    } finally {
      setPythonStatus((current) =>
        current === "executing" ? "ready" : current
      );
    }
  }, [applyPythonRunResult, checkPythonHealth, pendingPlan, pendingPrompt, pythonHealth]);

  const cancelPythonPlan = useCallback(() => {
    setPendingPrompt(null);
    setPendingPlan(null);
    setPythonStatus("ready");
    setPythonMessages((current) => [
      ...current,
      makeTextMessage("assistant", "Plan canceled."),
    ]);
  }, []);

  const sendPythonFeedback = useCallback(
    async (traceId: string, rating: "up" | "down") => {
      try {
        if (pythonHealth === "offline") {
          const isOnline = await checkPythonHealth();
          if (!isOnline) {
            throw new TypeError("Python backend offline");
          }
        }

        const response = await fetch(`${pythonAgentUrl}/feedback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            trace_id: traceId,
            rating,
            note: `UI thumbs ${rating}`,
          }),
        });

        if (!response.ok) {
          throw new Error(`Python backend returned ${response.status}`);
        }

        setPythonHealth("online");
        setPythonMessages((current) => [
          ...current,
          makeTextMessage(
            "assistant",
            rating === "down"
              ? `Feedback saved for ${traceId}. This trace is now an eval candidate.`
              : `Feedback saved for ${traceId}.`
          ),
        ]);
      } catch (error) {
        if (error instanceof TypeError) {
          setPythonHealth("offline");
        }
        const message = formatPythonBackendError(error);
        setPythonMessages((current) => [
          ...current,
          makeTextMessage("assistant", `Feedback error: ${message}`),
        ]);
      }
    },
    [checkPythonHealth, pythonHealth]
  );

  const viewPythonTrace = useCallback(
    async (traceId: string) => {
      setLoadingTraceId(traceId);
      setTraceViewError(null);
      setTraceViewData(null);

      try {
        if (pythonHealth === "offline") {
          const isOnline = await checkPythonHealth();
          if (!isOnline) {
            throw new TypeError("Python backend offline");
          }
        }

        const [traceResponse, toolsResponse, feedbackResponse] = await Promise.all([
          fetch(`${pythonAgentUrl}/traces/${traceId}`),
          fetch(`${pythonAgentUrl}/traces/${traceId}/tools`),
          fetch(`${pythonAgentUrl}/traces/${traceId}/feedback`),
        ]);

        if (!traceResponse.ok) {
          throw new Error(`Trace request returned ${traceResponse.status}`);
        }
        if (!toolsResponse.ok) {
          throw new Error(`Trace tools request returned ${toolsResponse.status}`);
        }
        if (!feedbackResponse.ok) {
          throw new Error(`Trace feedback request returned ${feedbackResponse.status}`);
        }

        setPythonHealth("online");
        setTraceViewData({
          trace: await traceResponse.json(),
          tools: await toolsResponse.json(),
          feedback: await feedbackResponse.json(),
        });
      } catch (error) {
        if (error instanceof TypeError) {
          setPythonHealth("offline");
        }
        setTraceViewError(formatPythonBackendError(error));
      } finally {
        setLoadingTraceId(null);
      }
    },
    [checkPythonHealth, pythonHealth]
  );

  return (
    <div className={`app ${theme}`}>
      <div className="canvas-container">
        <Canvas onApiReady={handleApiReady} onThemeChange={setTheme} />
      </div>
      <ChatPanel
        messages={backend === "python" ? pythonMessages : messages}
        sendMessage={backend === "python" ? sendPythonMessage : sendMessage}
        status={backend === "python" ? pythonStatus : status}
        backend={backend}
        onBackendChange={setBackend}
        onFeedback={backend === "python" ? sendPythonFeedback : undefined}
        onViewTrace={backend === "python" ? viewPythonTrace : undefined}
        activityLabel={backend === "python" ? pythonActivityLabel : null}
        pythonHealth={pythonHealth}
        pythonAgentUrl={pythonAgentUrl}
      />
      {backend === "python" && (traceViewData || loadingTraceId || traceViewError) && (
        <TracePanel
          data={traceViewData}
          loadingTraceId={loadingTraceId}
          error={traceViewError}
          onClose={() => {
            setTraceViewData(null);
            setLoadingTraceId(null);
            setTraceViewError(null);
          }}
        />
      )}
      {backend === "python" && pendingPlan && (
        <div
          style={{
            position: "fixed",
            right: 16,
            bottom: 16,
            zIndex: 1001,
            width: 340,
            maxHeight: "45vh",
            overflow: "auto",
            padding: 12,
            border: "1px solid #d0d0d0",
            borderRadius: 8,
            background: theme === "dark" ? "#2a2a2a" : "#fff",
            color: theme === "dark" ? "#e0e0e0" : "#222",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.18)",
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 12,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 8 }}>Review Plan</div>
          <div style={{ marginBottom: 8 }}>{pendingPlan.intent}</div>
          <ol style={{ margin: "0 0 8px 18px", padding: 0 }}>
            {pendingPlan.steps.map((step, index) => (
              <li key={`${step}-${index}`} style={{ marginBottom: 4 }}>
                {step}
              </li>
            ))}
          </ol>
          {pendingPlan.risks.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>Risks</div>
              <ul style={{ margin: "0 0 0 18px", padding: 0 }}>
                {pendingPlan.risks.map((risk, index) => (
                  <li key={`${risk}-${index}`} style={{ marginBottom: 4 }}>
                    {risk}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              onClick={executePythonPlan}
              disabled={pythonStatus === "executing"}
              style={{
                flex: 1,
                padding: "8px 10px",
                border: 0,
                borderRadius: 6,
                background: "#2196f3",
                color: "#fff",
                cursor: "pointer",
                fontFamily: "inherit",
              }}
            >
              {pythonStatus === "executing" ? "Executing..." : "Execute"}
            </button>
            <button
              type="button"
              onClick={cancelPythonPlan}
              disabled={pythonStatus === "executing"}
              style={{
                padding: "8px 10px",
                border: "1px solid #bbb",
                borderRadius: 6,
                background: "transparent",
                color: "inherit",
                cursor: "pointer",
                fontFamily: "inherit",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
