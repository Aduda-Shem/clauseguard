import { useEffect, useRef, useState } from "react";

import { apiErrorMessage } from "../api/client";
import { useChatMessages, useSendChatMessage } from "../api/hooks";

const SUGGESTIONS = [
  "What's the biggest risk in this contract?",
  "What are the payment terms?",
  "Can I terminate this early?",
  "What happens if I miss a deadline?",
];

export default function ContractChat({ contract }) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef(null);
  const messagesQuery = useChatMessages(contract.id);
  const sendMessage = useSendChatMessage(contract.id);
  const canChat = contract.status === "COMPLETE";

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messagesQuery.data, sendMessage.isPending]);

  const submit = async (question) => {
    const trimmed = question.trim();
    if (!trimmed || sendMessage.isPending) return;
    setDraft("");
    await sendMessage.mutateAsync(trimmed);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    submit(draft);
  };

  if (!canChat) {
    return (
      <div className="empty-panel">
        <p>Chat unlocks once this contract finishes reviewing.</p>
      </div>
    );
  }

  const messages = messagesQuery.data || [];

  return (
    <div className="chat-panel">
      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && !messagesQuery.isLoading && (
          <div className="chat-context-pill">
            <span>Ask anything about {contract.filename}</span>
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.role === "USER" ? "user" : "ai"}`}>
            {m.content}
          </div>
        ))}
        {sendMessage.isPending && (
          <div className="bubble ai bubble--thinking">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        )}
        {sendMessage.isError && <p className="form-error">{apiErrorMessage(sendMessage.error)}</p>}
      </div>

      <div className="suggest-row">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" className="suggest-chip" onClick={() => submit(s)}>
            {s}
          </button>
        ))}
      </div>

      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          placeholder="Ask a question about this contract..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button className="send-btn" type="submit" disabled={!draft.trim() || sendMessage.isPending} aria-label="Send">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M4 20l16-8L4 4v6l10 2-10 2v6z" fill="currentColor" />
          </svg>
        </button>
      </form>
    </div>
  );
}
