import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  Brain,
  Menu,
  MessageSquarePlus,
  PanelLeftClose,
  RefreshCw,
  Send,
  Sparkles,
  User,
} from "lucide-react";
import {
  askQuestion,
  ChatMessage,
  ChatSession,
  createSession,
  getSessionChats,
  listSessions,
  QueryResponse,
} from "./api";

const ACTIVE_SESSION_KEY = "rag-chatbot-active-session";

function queryToMessage(response: QueryResponse): ChatMessage {
  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    response: response.response ?? response.answer ?? "",
    bold_words: response.bold_words ?? [],
    meta_data: response.meta_data ?? [],
    follow_up: response.follow_up ?? null,
    table_data: response.table_data ?? [],
    ucid: response.ucid ?? null,
  };
}

function renderText(text: string) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br />");

  return { __html: escaped };
}

export default function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [answerType, setAnswerType] = useState<"normal" | "deepthink">("normal");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [error, setError] = useState<string>("");
  const endRef = useRef<HTMLDivElement | null>(null);
  const hasBootedRef = useRef(false);

  const activeSession = useMemo(
    () => sessions.find((session) => session.session_id === activeSessionId),
    [activeSessionId, sessions],
  );

  const refreshSessions = useCallback(async () => {
    const data = await listSessions();
    setSessions((current) => {
      const savedIds = new Set(data.sessions.map((session) => session.session_id));
      const localEmptySessions = current.filter(
        (session) => !savedIds.has(session.session_id),
      );
      return [...localEmptySessions, ...data.sessions];
    });
    return data.sessions;
  }, []);

  const openSession = useCallback(async (sessionId: string) => {
    setError("");
    setActiveSessionId(sessionId);
    localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
    const data = await getSessionChats(sessionId);
    setMessages(data.chats);
  }, []);

  const startNewChat = useCallback(async () => {
    setError("");
    const session = await createSession();
    const newSession = { session_id: session.session_id, title: session.title };
    setSessions((current) => [newSession, ...current]);
    setActiveSessionId(session.session_id);
    localStorage.setItem(ACTIVE_SESSION_KEY, session.session_id);
    setMessages([]);
    setQuestion("");
  }, []);

  useEffect(() => {
    async function boot() {
      if (hasBootedRef.current) return;
      hasBootedRef.current = true;

      try {
        const loadedSessions = await refreshSessions();
        const storedId = localStorage.getItem(ACTIVE_SESSION_KEY);
        const initialId = storedId && loadedSessions.some((session) => session.session_id === storedId)
          ? storedId
          : loadedSessions[0]?.session_id;

        if (initialId) {
          await openSession(initialId);
        } else {
          await startNewChat();
        }
      } catch (bootError) {
        setError(bootError instanceof Error ? bootError.message : "Unable to load chats.");
      }
    }

    boot();
  }, [openSession, refreshSessions, startNewChat]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || !activeSessionId || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      response: trimmedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setIsLoading(true);
    setError("");

    try {
      const answer = await askQuestion(activeSessionId, trimmedQuestion, answerType);
      setMessages((current) => [...current, queryToMessage(answer)]);
      setSessions((current) =>
        current.map((session) =>
          session.session_id === activeSessionId && session.title === "New Chat"
            ? { ...session, title: trimmedQuestion }
            : session,
        ),
      );
      await refreshSessions();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "The backend could not answer this question.");
      setMessages((current) => current.filter((message) => message.id !== userMessage.id));
      setQuestion(trimmedQuestion);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${isSidebarOpen ? "open" : "closed"}`}>
        <div className="sidebar-header">
          <button className="icon-button" onClick={() => setIsSidebarOpen(false)} title="Collapse sidebar">
            <PanelLeftClose size={18} />
          </button>
          <button className="new-chat" onClick={startNewChat}>
            <MessageSquarePlus size={18} />
            <span>New chat</span>
          </button>
        </div>

        <div className="session-list">
          {sessions.map((session) => (
            <button
              key={session.session_id}
              className={`session-item ${session.session_id === activeSessionId ? "active" : ""}`}
              onClick={() => openSession(session.session_id)}
              title={session.session_id}
            >
              <span>{session.title || "New Chat"}</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="chat-pane">
        <header className="topbar">
          {!isSidebarOpen && (
            <button className="icon-button" onClick={() => setIsSidebarOpen(true)} title="Open sidebar">
              <Menu size={19} />
            </button>
          )}
          <div>
            <h1>{activeSession?.title || "RAG Chatbot"}</h1>
            <p>{activeSessionId ? `Session ${activeSessionId}` : "Connecting to backend"}</p>
          </div>
          <button className="icon-button" onClick={refreshSessions} title="Refresh sessions">
            <RefreshCw size={18} />
          </button>
        </header>

        <section className="messages" aria-live="polite">
          {messages.length === 0 && (
            <div className="empty-state">
              <Sparkles size={28} />
              <h2>Ask your knowledge base anything.</h2>
              <p>Each chat uses its own session id and can be resumed from the saved SQLite history.</p>
            </div>
          )}

          {messages.map((message) => (
            <article key={message.id} className={`message-row ${message.role}`}>
              <div className="avatar">{message.role === "user" ? <User size={18} /> : <Bot size={18} />}</div>
              <div className="message-content">
                <div className="message-text" dangerouslySetInnerHTML={renderText(message.response)} />

                {message.table_data?.filter(Boolean).map((table, index) => (
                  <pre className="table-block" key={`${message.id}-table-${index}`}>{table}</pre>
                ))}

                {message.meta_data && message.meta_data.length > 0 && (
                  <div className="sources">
                    {message.meta_data.slice(0, 6).map((source, index) => {
                      const label = [source.source, source.page ? `p. ${source.page}` : ""].filter(Boolean).join(" - ");
                      return source.signed_url ? (
                        <a key={`${message.id}-source-${index}`} href={source.signed_url} target="_blank" rel="noreferrer">
                          {label || `Source ${index + 1}`}
                        </a>
                      ) : (
                        <span key={`${message.id}-source-${index}`}>{label || `Source ${index + 1}`}</span>
                      );
                    })}
                  </div>
                )}

                {message.follow_up && <button className="follow-up" onClick={() => setQuestion(message.follow_up ?? "")}>{message.follow_up}</button>}
              </div>
            </article>
          ))}

          {isLoading && (
            <article className="message-row assistant">
              <div className="avatar"><Bot size={18} /></div>
              <div className="message-content loading-answer">
                <span />
                <span />
                <span />
              </div>
            </article>
          )}
          <div ref={endRef} />
        </section>

        {error && <div className="error-banner">{error}</div>}

        <form className="composer" onSubmit={handleSubmit}>
          <div className="mode-toggle" role="group" aria-label="Answer mode">
            <button type="button" className={answerType === "normal" ? "selected" : ""} onClick={() => setAnswerType("normal")}>
              <Sparkles size={16} />
              <span>Normal</span>
            </button>
            <button type="button" className={answerType === "deepthink" ? "selected" : ""} onClick={() => setAnswerType("deepthink")}>
              <Brain size={16} />
              <span>Deepthink</span>
            </button>
          </div>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="Message the RAG chatbot"
            rows={1}
          />
          <button className="send-button" disabled={!question.trim() || isLoading || !activeSessionId} title="Send message">
            <Send size={18} />
          </button>
        </form>
      </main>
    </div>
  );
}
