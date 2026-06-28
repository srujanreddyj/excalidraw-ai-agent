import type { UIMessage } from "ai";
import MarkdownRenderer from "./MarkdownRenderer";
import ToolStatus from "../streaming/ToolStatus";
import "../streaming/streaming.css";

interface MessageBubbleProps {
  message: UIMessage;
  onFeedback?: (traceId: string, rating: "up" | "down") => void;
  onViewTrace?: (traceId: string) => void;
}

function getTextContent(message: UIMessage): string {
  return (
    message.parts
      ?.filter((part) => part.type === "text")
      .map((part) => part.text)
      .join("\n") ?? ""
  );
}

function extractTraceId(message: UIMessage): string | null {
  const match = getTextContent(message).match(/Trace:\s*(trace_[a-zA-Z0-9_]+)/);
  return match?.[1] ?? null;
}

export default function MessageBubble({
  message,
  onFeedback,
  onViewTrace,
}: MessageBubbleProps) {
  const traceId = message.role === "assistant" ? extractTraceId(message) : null;

  return (
    <div className={`message-bubble ${message.role}`}>
      <div className="message-role">
        {message.role === "user" ? "You" : "Assistant"}
      </div>
      <div className="message-content">
        {message.parts?.map((part, i) => {
          // Plain text part
          if (part.type === "text") {
            if (message.role === "assistant") {
              return <MarkdownRenderer key={i} content={part.text} />;
            }
            return <p key={i}>{part.text}</p>;
          }

          // Tool call part: type is `tool-<toolName>` (e.g. tool-generateDiagram)
          if (part.type?.startsWith("tool-")) {
            const toolName = part.type.replace("tool-", "");
            const toolPart = part as { state?: string };
            const status =
              toolPart.state === "output-available"
                ? "complete"
                : toolPart.state === "output-error"
                  ? "error"
                  : "running";
            return <ToolStatus key={i} name={toolName} status={status} />;
          }

          return null;
        })}
      </div>
      {traceId && (onFeedback || onViewTrace) && (
        <div className="message-actions" aria-label="Trace actions">
          {onViewTrace && (
            <button type="button" onClick={() => onViewTrace(traceId)}>
              View trace
            </button>
          )}
          {onFeedback && (
            <>
              <button type="button" onClick={() => onFeedback(traceId, "up")}>
                Good
              </button>
              <button type="button" onClick={() => onFeedback(traceId, "down")}>
                Bad
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
