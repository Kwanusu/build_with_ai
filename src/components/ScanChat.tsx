import { useState } from "react";
import { ApiError, askAboutScan, MAX_CHAT_MESSAGES, MAX_QUESTION_CHARS, type ChatMessage } from "../api";
import { CHAT } from "../content";
import { Button, Notice, Spinner, TextArea } from "./ui";

function messageOf(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Nothing has been changed.";
}

/** Questions about one finished scan. The server reads the scan itself, so only the conversation is sent. */
export function ScanChat({ scanId }: { scanId: number }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string>();

  // A conversation has to end on a question, so the server takes at most MAX_CHAT_MESSAGES - 1 of them in a row.
  const full = messages.length >= MAX_CHAT_MESSAGES - 1;

  async function ask(question: string) {
    const text = question.trim();
    if (!text || busy || full) return;
    const asked: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(asked);
    setDraft("");
    setProblem(undefined);
    setBusy(true);
    try {
      const reply = await askAboutScan(scanId, asked);
      setMessages([...asked, { role: "assistant", content: reply }]);
    } catch (error) {
      // Take the question back so it can be sent again, and so the conversation still alternates. If they have already
      // started typing something else while they waited, keep that.
      setMessages(messages);
      setDraft((current) => (current === "" ? text : current));
      setProblem(messageOf(error));
    } finally {
      setBusy(false);
    }
  }

  function startOver() {
    setMessages([]);
    setDraft("");
    setProblem(undefined);
  }

  return (
    <section className="flex flex-col gap-2 reading" aria-labelledby="chat-title">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="chat-title" className="type-h3">
          {CHAT.title}
        </h2>
        <Button expanded={open} onClick={() => setOpen(!open)}>
          {open ? CHAT.close : CHAT.open}
        </Button>
      </div>

      {open && (
        <div className="card flex flex-col gap-2">
          <p className="type-small c-muted">{CHAT.intro}</p>

          {messages.length > 0 && (
            <ol className="list-none p-0 m-0" aria-label={CHAT.conversation} aria-live="polite">
              {messages.map((message, index) => (
                <li key={index} className="flex flex-col gap-half py-2 border-b rule">
                  <p className="type-label c-muted">{message.role === "user" ? CHAT.you : CHAT.assistant}</p>
                  <p className="type-body whitespace-pre-wrap wrap-break-word">{message.content}</p>
                </li>
              ))}
            </ol>
          )}

          {busy && (
            <div className="flex items-center gap-1" role="status">
              <Spinner />
              <p className="type-small c-muted">{CHAT.reading}</p>
            </div>
          )}
          {problem && <Notice tone="error">{problem}</Notice>}

          {messages.length === 0 && !busy && (
            <div className="flex flex-wrap gap-1">
              {CHAT.starters.map((starter) => (
                <Button key={starter} size="sm" onClick={() => void ask(starter)}>
                  {starter}
                </Button>
              ))}
            </div>
          )}

          {full ? (
            <Notice tone="warning">{CHAT.full}</Notice>
          ) : (
            <TextArea
              id="chat-question"
              label={CHAT.label}
              value={draft}
              onChange={setDraft}
              onEnter={() => void ask(draft)}
              placeholder={CHAT.placeholder}
              helper={CHAT.helper}
              maxLength={MAX_QUESTION_CHARS}
              autoFocus
            />
          )}

          <div className="flex flex-wrap items-center gap-1">
            <Button onClick={() => void ask(draft)} disabled={busy || full || draft.trim() === ""} busy={busy}>
              {busy && <Spinner />}
              {busy ? CHAT.sending : CHAT.send}
            </Button>
            {messages.length > 0 && (
              <Button variant="plain" onClick={startOver} disabled={busy}>
                {CHAT.startOver}
              </Button>
            )}
          </div>

          <p className="type-small c-muted">{CHAT.aiNote}</p>
        </div>
      )}
    </section>
  );
}
