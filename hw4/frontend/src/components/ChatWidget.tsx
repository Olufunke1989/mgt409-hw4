import { useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation } from "react-router-dom";
import { fetchChatHistory, sendChatMessage } from "../api";
import { useAuth } from "../auth";
import { useToast } from "../toast";
import { useChatResults } from "../chatResults";
import type { ChatMessage } from "../types";
import ChatText from "./ChatText";

const GREETING: ChatMessage = {
  role: "assistant",
  content:
    "Hi! I'm the Campus Customs assistant. Ask me about the shop, finding your way around the site, or what we carry.",
};

const SUGGESTIONS = ["Gift ideas under $40", "What hoodies do you have?", "Something warm in a large"];

function greetingFor(firstName: string | null, returning: boolean): ChatMessage {
  if (!firstName) return GREETING;
  return {
    role: "assistant",
    content: returning
      ? `Welcome back, ${firstName}! Here's our conversation from last time. What can I help you with today?`
      : `Hi ${firstName}! I'm the Campus Customs assistant. Your chats are saved to your account, so we can pick up where we left off.`,
  };
}

/** The page the customer is on, plus the product id when it's a product page. */
function currentPage(pathname: string) {
  const match = pathname.match(/^\/products\/([^/]+)$/);
  return { path: pathname, product_id: match ? decodeURIComponent(match[1]) : null };
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const { setResults } = useChatResults();
  const toast = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [greeting, setGreeting] = useState<ChatMessage>(GREETING);
  const { user, loading } = useAuth();
  const location = useLocation();
  const [draft, setDraft] = useState("");
  // A friendly hello next to the chat button, shown once per visit.
  const [teaser, setTeaser] = useState(false);
  useEffect(() => {
    if (sessionStorage.getItem("cc-teaser-seen")) return;
    const t = window.setTimeout(() => setTeaser(true), 2500);
    return () => window.clearTimeout(t);
  }, []);
  const hideTeaser = () => {
    setTeaser(false);
    sessionStorage.setItem("cc-teaser-seen", "1");
  };
  const [sending, setSending] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  // When someone logs in, load THEIR saved conversation. When they log out (or for
  // guests), start fresh so nobody sees another person's chat.
  useEffect(() => {
    if (loading) return;
    let cancelled = false;
    if (!user) {
      setGreeting(GREETING);
      setMessages([GREETING]);
      setResults(null);
      return;
    }
    fetchChatHistory().then((history) => {
      if (cancelled) return;
      const g = greetingFor(user.first_name, history.length > 0);
      setGreeting(g);
      setMessages([...history, g]);
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, loading]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function handleSubmit(e?: FormEvent, resend?: string, isRetry = Boolean(resend)) {
    e?.preventDefault();
    const text = (resend ?? draft).trim();
    if (!text || sending) return;
    // When retrying, drop the error note and the failed copy of the message first.
    const base = isRetry ? messages.filter((m) => !m.error).slice(0, -1) : messages;
    const history: ChatMessage[] = [...base, { role: "user", content: text }];
    setMessages(history);
    if (resend === undefined) setDraft("");
    setSending(true);
    // Send only real conversation turns: skip the greeting and any error notes.
    const result = await sendChatMessage(
      history
        .filter((m) => m !== greeting && !m.error && m.answeredBy !== "fallback")
        .map(({ role, content }) => ({ role, content })),
      currentPage(location.pathname),
    );
    setSending(false);
    // Show (or clear) product cards on the page when the assistant searched the catalogue.
    if (result.status === "ok" && result.searched) {
      // On a phone the chat fills the screen, so offer a quick way to see the new cards.
      if (result.products.length && window.matchMedia("(max-width: 640px)").matches) {
        toast(`${result.products.length} products added to the page`, "info", {
          label: "View",
          onClick: () => setOpen(false),
        });
      }
      setResults(
        result.products.length
          ? {
              query: result.searchQuery ?? "",
              total: result.totalMatches,
              products: result.products,
              seeAllPath: result.seeAllPath,
            }
          : null,
      );
    }
    setMessages((prev) => [
      ...prev,
      result.status === "ok"
        ? { role: "assistant", content: result.reply, products: result.products, answeredBy: result.answeredBy }
        : { role: "assistant", content: result.message, error: true, retryText: text },
    ]);
  }

  const isFresh = !messages.some((m) => m.role === "user");

  return (
    <div className="chat-root">
      {open && (
        <section className="chat-panel" role="dialog" aria-label="Campus Customs chat">
          <header className="chat-header">
            <span className="chat-avatar" aria-hidden="true">CC</span>
            <div className="chat-header-text">
              <p className="chat-title">Your personal shopper</p>
              <p className="chat-status">
                <span className="status-dot online" aria-hidden="true" /> Campus Customs · here to help
              </p>
            </div>
            <button className="icon-btn" aria-label="Close chat" onClick={() => setOpen(false)}>
              ✕
            </button>
          </header>
          <div className="chat-messages" ref={listRef} aria-live="polite">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`bubble bubble-${m.role} ${m.error || m.answeredBy === "fallback" ? "bubble-error" : ""}`}
              >
                {m.role === "assistant" ? <ChatText text={m.content} /> : m.content}
                {m.answeredBy === "database" && <span className="bubble-tag">⚡ Instant answer from our catalogue</span>}
                {m.retryText && (
                  <button className="chat-show-products" onClick={() => handleSubmit(undefined, m.retryText)} disabled={sending}>
                    Try again
                  </button>
                )}
                {m.role === "assistant" && m.products && m.products.length > 0 && (
                  <button
                    className="chat-show-products"
                    onClick={() =>
                      setResults({
                        query: "an earlier chat",
                        total: m.products!.length,
                        products: m.products!,
                        seeAllPath: null,
                      })
                    }
                  >
                    {m.products.length === 1 ? "Show this product" : `Show these ${m.products.length} products`}
                  </button>
                )}
              </div>
            ))}
            {isFresh && !sending && (
              <div className="chat-suggestions" aria-label="Suggested questions">
                {SUGGESTIONS.map((q) => (
                  <button key={q} onClick={() => handleSubmit(undefined, q, false)}>
                    {q}
                  </button>
                ))}
              </div>
            )}
            {sending && (
              <div className="bubble bubble-assistant typing" aria-label="Assistant is typing">
                <span />
                <span />
                <span />
              </div>
            )}
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <label htmlFor="chat-text" className="sr-only">
              Type your message
            </label>
            <textarea
              id="chat-text"
              ref={inputRef}
              rows={1}
              placeholder="Ask about sizes, gifts, prices…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
            />
            <button className="btn btn-primary" type="submit" disabled={!draft.trim() || sending}>
              Send
            </button>
          </form>
        </section>
      )}
      {!open && teaser && (
        <div className="chat-teaser" role="status">
          <button
            className="teaser-open"
            onClick={() => {
              hideTeaser();
              setOpen(true);
            }}
          >
            <strong>{user ? `Hi ${user.first_name}! 👋` : "Hi there! 👋"}</strong>
            Looking for a gift or the right size? I'm happy to help.
          </button>
          <button className="teaser-close" aria-label="Dismiss" onClick={hideTeaser}>
            ✕
          </button>
        </div>
      )}
      <button
        className={`chat-launcher ${open ? "is-open" : ""}`}
        aria-label={open ? "Close chat" : "Open chat with our shopping assistant"}
        aria-expanded={open}
        onClick={() => {
          hideTeaser();
          setOpen((o) => !o);
        }}
      >
        {open ? (
          "✕"
        ) : (
          <>
            <span className="launcher-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path
                  fill="currentColor"
                  d="M12 3c-5 0-9 3.4-9 7.6 0 2.4 1.3 4.5 3.4 5.9L5.6 20l4-2.1c.8.2 1.6.3 2.4.3 5 0 9-3.4 9-7.6S17 3 12 3Z"
                />
                <path fill="#ffe08a" d="M12 6.6l.9 2.2 2.3.2-1.8 1.5.6 2.3L12 11.6l-2 1.2.6-2.3-1.8-1.5 2.3-.2z" />
              </svg>
            </span>
            <span className="chat-launcher-label">Ask us</span>
          </>
        )}
      </button>
    </div>
  );
}
