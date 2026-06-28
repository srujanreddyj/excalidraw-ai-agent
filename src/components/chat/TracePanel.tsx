interface TraceDetail {
  trace_id: string;
  input: string;
  final_text: string;
  status: string;
  latency_ms: number;
  step_count: number;
  tool_call_count: number;
  steps_json: string;
  errors_json: string;
  created_at: string;
}

interface TraceToolEvent {
  call_index: number;
  tool_call_id: string | null;
  tool_name: string;
  input_json: string;
  output_json: string;
}

interface TraceFeedback {
  rating: string;
  note: string;
  created_at: string;
}

export interface TraceViewData {
  trace: TraceDetail;
  tools: TraceToolEvent[];
  feedback: TraceFeedback[];
}

interface TracePanelProps {
  data: TraceViewData | null;
  loadingTraceId: string | null;
  error: string | null;
  onClose: () => void;
}

function parseJsonArray(value: string): unknown[] {
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function compactJson(value: string): string {
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}

export default function TracePanel({
  data,
  loadingTraceId,
  error,
  onClose,
}: TracePanelProps) {
  const steps = data ? parseJsonArray(data.trace.steps_json) : [];
  const errors = data ? parseJsonArray(data.trace.errors_json) : [];

  return (
    <aside className="trace-panel" aria-label="Trace details">
      <div className="trace-panel-header">
        <div>
          <div className="trace-panel-eyebrow">Trace</div>
          <h3>{loadingTraceId ?? data?.trace.trace_id ?? "Trace details"}</h3>
        </div>
        <button type="button" onClick={onClose} aria-label="Close trace panel">
          Close
        </button>
      </div>

      {error && <div className="trace-panel-error">{error}</div>}
      {loadingTraceId && !data && !error && (
        <div className="trace-panel-loading">Loading trace...</div>
      )}

      {data && (
        <div className="trace-panel-body">
          <section>
            <h4>Run</h4>
            <dl className="trace-metadata">
              <div>
                <dt>Status</dt>
                <dd>{data.trace.status}</dd>
              </div>
              <div>
                <dt>Latency</dt>
                <dd>{data.trace.latency_ms.toFixed(0)}ms</dd>
              </div>
              <div>
                <dt>Steps</dt>
                <dd>{data.trace.step_count}</dd>
              </div>
              <div>
                <dt>Tools</dt>
                <dd>{data.trace.tool_call_count}</dd>
              </div>
            </dl>
          </section>

          <section>
            <h4>Prompt</h4>
            <p>{data.trace.input}</p>
          </section>

          <section>
            <h4>Final</h4>
            <p>{data.trace.final_text}</p>
          </section>

          <section>
            <h4>Steps</h4>
            <ol className="trace-list">
              {steps.map((step, index) => (
                <li key={`${String(step)}-${index}`}>{String(step)}</li>
              ))}
            </ol>
          </section>

          {errors.length > 0 && (
            <section>
              <h4>Errors</h4>
              <ul className="trace-list">
                {errors.map((item, index) => (
                  <li key={`${String(item)}-${index}`}>{String(item)}</li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h4>Tool Calls</h4>
            {data.tools.length === 0 ? (
              <p>No tool calls recorded.</p>
            ) : (
              data.tools.map((tool) => (
                <details key={`${tool.tool_name}-${tool.call_index}`}>
                  <summary>
                    {tool.call_index}. {tool.tool_name}
                  </summary>
                  <pre>{compactJson(tool.input_json)}</pre>
                  <pre>{compactJson(tool.output_json)}</pre>
                </details>
              ))
            )}
          </section>

          <section>
            <h4>Feedback</h4>
            {data.feedback.length === 0 ? (
              <p>No feedback yet.</p>
            ) : (
              <ul className="trace-list">
                {data.feedback.map((item, index) => (
                  <li key={`${item.created_at}-${index}`}>
                    {item.rating}: {item.note}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </aside>
  );
}
