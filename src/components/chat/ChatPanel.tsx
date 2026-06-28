import { useState } from "react";
import type { UIMessage } from "ai";
import MessageList from "./MessageList";
import "./chat.css";

interface ChatPanelProps {
  messages: UIMessage[];
  sendMessage: (message: { role: "user"; parts: { type: "text"; text: string }[] }) => void;
  status: string;
  backend: "cloudflare" | "python";
  onBackendChange: (backend: "cloudflare" | "python") => void;
  onFeedback?: (traceId: string, rating: "up" | "down") => void;
  onViewTrace?: (traceId: string) => void;
  activityLabel?: string | null;
  pythonHealth?: "unknown" | "checking" | "online" | "offline";
  pythonAgentUrl?: string;
}

export default function ChatPanel({
  messages,
  sendMessage,
  status,
  backend,
  onBackendChange,
  onFeedback,
  onViewTrace,
  activityLabel,
  pythonHealth = "unknown",
  pythonAgentUrl,
}: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage({
      role: "user",
      parts: [{ type: "text", text: input }],
    });
    setInput("");
  };

  const isStreaming =
    status === "submitted" ||
    status === "streaming" ||
    status === "planning" ||
    status === "executing";

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-title">
          <h2>Chat</h2>
          {activityLabel && <span className="agent-activity">{activityLabel}</span>}
        </div>
        <div className="chat-header-controls">
          <div className="backend-toggle" aria-label="Agent backend">
            <button
              type="button"
              className={backend === "cloudflare" ? "active" : ""}
              onClick={() => onBackendChange("cloudflare")}
            >
              Cloudflare
            </button>
            <button
              type="button"
              className={backend === "python" ? "active" : ""}
              onClick={() => onBackendChange("python")}
            >
              Python
            </button>
          </div>
          <a
            href="#viewer"
            className="viewer-header-link"
            title="Open diagram viewer for human scoring"
          >
            viewer
          </a>
        </div>
      </div>
      {backend === "python" && (
        <div
          className={`backend-health ${pythonHealth}`}
          title={pythonAgentUrl ? `Python API: ${pythonAgentUrl}` : undefined}
        >
          <span className="backend-health-dot" />
          <span>
            Python backend{" "}
            {pythonHealth === "checking"
              ? "checking"
              : pythonHealth === "online"
                ? "online"
                : pythonHealth === "offline"
                  ? "offline"
                  : "not checked"}
          </span>
        </div>
      )}
      {activityLabel && (
        <div className="agent-activity-card" role="status" aria-live="polite">
          <span className="agent-activity-dot" />
          <span>{activityLabel}</span>
        </div>
      )}
      <MessageList
        messages={messages}
        onFeedback={onFeedback}
        onViewTrace={onViewTrace}
      />
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Describe a diagram..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isStreaming}
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={isStreaming || !input.trim()}
        >
          {isStreaming ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
