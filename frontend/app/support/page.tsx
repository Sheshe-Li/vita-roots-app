"use client";

import { useState, useRef, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Category = "general" | "account" | "billing";

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
}

interface Ticket {
  ticket_id: string;
  category: Category;
  agent_name: string;
  subject: string;
  status: string;
  initial_response: string;
  family_context?: {
    name: string;
    client_number: string;
    subscription: string;
    member_count: number;
  };
}

const AGENT_COLORS: Record<Category, string> = {
  general: "var(--moss)",
  account: "var(--clay)",
  billing: "var(--terracotta)",
};

const AGENT_LABELS: Record<Category, string> = {
  general: "General Support",
  account: "Account Support",
  billing: "Billing Support",
};

const CATEGORY_ICONS: Record<Category, string> = {
  general: "🌿",
  account: "👤",
  billing: "💳",
};

export default function SupportPage() {
  const [phase, setPhase] = useState<"landing" | "subject" | "chat">("landing");
  const [subject, setSubject] = useState("");
  const [clientNumber, setClientNumber] = useState("");
  const [initialMessage, setInitialMessage] = useState("");
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function startTicket() {
    if (!subject.trim() || !initialMessage.trim()) {
      setError("Please fill in both the subject and your message.");
      return;
    }
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/support/tickets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: subject.trim(),
          initial_message: initialMessage.trim(),
          client_number: clientNumber.trim() || undefined,
        }),
      });

      if (!res.ok) throw new Error("Failed to create support ticket.");

      const data = await res.json();
      const t: Ticket = data.data;
      setTicket(t);
      setMessages([
        { role: "user", content: initialMessage.trim() },
        {
          role: "assistant",
          content: t.initial_response,
          agent: t.agent_name,
        },
      ]);
      setPhase("chat");
    } catch (e) {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage() {
    if (!input.trim() || !ticket || streaming) return;
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setStreaming(true);

    // Add empty assistant message to stream into
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", agent: ticket.agent_name },
    ]);

    try {
      const params = new URLSearchParams({
        message: userMessage,
        ...(ticket ? {} : {}),
      });

      const res = await fetch(
        `${API_URL}/api/support/tickets/${ticket.ticket_id}/stream?${params}`,
        { method: "GET" }
      );

      if (!res.ok) throw new Error("Stream failed.");

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader.");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const parsed = JSON.parse(line.slice(6));
              if (parsed.text) {
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last.role === "assistant") {
                    updated[updated.length - 1] = {
                      ...last,
                      content: last.content + parsed.text,
                    };
                  }
                  return updated;
                });
              }
            } catch {}
          }
        }
      }
    } catch (e) {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.role === "assistant" && !last.content) {
          updated[updated.length - 1] = {
            ...last,
            content: "I encountered an error. Please try again.",
          };
        }
        return updated;
      });
    } finally {
      setStreaming(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const agentColor = ticket
    ? AGENT_COLORS[ticket.category as Category]
    : "var(--moss)";

  // ---------------------------------------------------------------------------
  // Landing phase
  // ---------------------------------------------------------------------------
  if (phase === "landing") {
    return (
      <div style={styles.page}>
        <nav style={styles.nav}>
          <a href="/" style={styles.logo}>Vita Roots</a>
          <span style={styles.navLabel}>Support Center</span>
        </nav>

        <div style={styles.landingContainer}>
          <div style={styles.landingHeader}>
            <div style={styles.leafAccent}>✦</div>
            <h1 style={styles.landingTitle}>How can we help?</h1>
            <p style={styles.landingSubtitle}>
              Our support specialists are ready to assist with any questions
              about your family&apos;s wellness journey.
            </p>
          </div>

          <div style={styles.categoryGrid}>
            {(["general", "account", "billing"] as Category[]).map((cat) => (
              <button
                key={cat}
                style={styles.categoryCard}
                onClick={() => setPhase("subject")}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = "translateY(-4px)";
                  (e.currentTarget as HTMLElement).style.borderColor = AGENT_COLORS[cat];
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
                  (e.currentTarget as HTMLElement).style.borderColor = "rgba(0,0,0,0.08)";
                }}
              >
                <span style={styles.categoryIcon}>{CATEGORY_ICONS[cat]}</span>
                <span style={styles.categoryLabel}>{AGENT_LABELS[cat]}</span>
                <span style={styles.categoryDesc}>
                  {cat === "general" && "Questions about features, meal plans, and wellness"}
                  {cat === "account" && "Profile settings, family members, preferences"}
                  {cat === "billing" && "Subscriptions, invoices, and plan changes"}
                </span>
              </button>
            ))}
          </div>

          <button style={styles.startButton} onClick={() => setPhase("subject")}>
            Start a conversation →
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Subject / intro phase
  // ---------------------------------------------------------------------------
  if (phase === "subject") {
    return (
      <div style={styles.page}>
        <nav style={styles.nav}>
          <a href="/" style={styles.logo}>Vita Roots</a>
          <button style={styles.backButton} onClick={() => setPhase("landing")}>
            ← Back
          </button>
        </nav>

        <div style={styles.formContainer}>
          <h2 style={styles.formTitle}>Tell us what you need</h2>
          <p style={styles.formSubtitle}>
            We&apos;ll route you to the right specialist automatically.
          </p>

          {error && <div style={styles.errorBox}>{error}</div>}

          <div style={styles.formGroup}>
            <label style={styles.label}>Client Number (optional)</label>
            <input
              style={styles.input}
              placeholder="e.g. VR-001001"
              value={clientNumber}
              onChange={(e) => setClientNumber(e.target.value)}
            />
            <span style={styles.hint}>
              Include your client number for faster account-specific support.
            </span>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Subject</label>
            <input
              style={styles.input}
              placeholder="Brief description of your question"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>How can we help?</label>
            <textarea
              style={{ ...styles.input, ...styles.textarea }}
              placeholder="Describe your question or concern in detail..."
              value={initialMessage}
              onChange={(e) => setInitialMessage(e.target.value)}
              rows={5}
            />
          </div>

          <button
            style={{
              ...styles.submitButton,
              opacity: loading ? 0.7 : 1,
            }}
            onClick={startTicket}
            disabled={loading}
          >
            {loading ? "Connecting to specialist..." : "Start conversation →"}
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Chat phase
  // ---------------------------------------------------------------------------
  return (
    <div style={styles.page}>
      <nav style={styles.nav}>
        <a href="/" style={styles.logo}>Vita Roots</a>
        <div style={styles.ticketInfo}>
          {ticket && (
            <>
              <span
                style={{
                  ...styles.agentBadge,
                  backgroundColor: agentColor,
                }}
              >
                {CATEGORY_ICONS[ticket.category as Category]} {ticket.agent_name}
              </span>
              <span style={styles.ticketId}>
                #{ticket.ticket_id.slice(0, 8).toUpperCase()}
              </span>
            </>
          )}
        </div>
      </nav>

      {ticket?.family_context && (
        <div style={styles.contextBar}>
          <span>
            {ticket.family_context.name} ·{" "}
            <strong>{ticket.family_context.client_number}</strong> ·{" "}
            {ticket.family_context.subscription}
          </span>
        </div>
      )}

      <div style={styles.chatContainer}>
        <div style={styles.messagesArea}>
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                ...styles.messageRow,
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              {msg.role === "assistant" && (
                <div
                  style={{
                    ...styles.agentAvatar,
                    backgroundColor: agentColor,
                  }}
                >
                  {ticket ? CATEGORY_ICONS[ticket.category as Category] : "🌿"}
                </div>
              )}
              <div
                style={{
                  ...styles.bubble,
                  ...(msg.role === "user"
                    ? styles.userBubble
                    : { ...styles.assistantBubble, borderLeftColor: agentColor }),
                }}
              >
                {msg.role === "assistant" && msg.agent && (
                  <span style={styles.agentLabel}>{msg.agent}</span>
                )}
                <p style={styles.bubbleText}>
                  {msg.content || (
                    <span style={styles.typingDots}>
                      <span>●</span>
                      <span>●</span>
                      <span>●</span>
                    </span>
                  )}
                </p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div style={styles.inputArea}>
          <textarea
            ref={inputRef}
            style={styles.chatInput}
            placeholder="Type your message... (Enter to send)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={3}
            disabled={streaming}
          />
          <button
            style={{
              ...styles.sendButton,
              backgroundColor: agentColor,
              opacity: streaming || !input.trim() ? 0.5 : 1,
            }}
            onClick={sendMessage}
            disabled={streaming || !input.trim()}
          >
            {streaming ? "..." : "→"}
          </button>
        </div>

        <p style={styles.disclaimer}>
          Vita Roots support is available 24/7. For urgent health concerns,
          please consult a licensed healthcare provider.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    backgroundColor: "var(--cream)",
    display: "flex",
    flexDirection: "column",
  },
  nav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "20px 40px",
    borderBottom: "1px solid rgba(0,0,0,0.06)",
    backgroundColor: "var(--warm-white)",
  },
  logo: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: "22px",
    fontWeight: 600,
    color: "var(--moss)",
    textDecoration: "none",
    letterSpacing: "0.02em",
  },
  navLabel: {
    fontSize: "13px",
    color: "var(--gold)",
    letterSpacing: "0.12em",
    textTransform: "uppercase",
  },
  backButton: {
    background: "none",
    border: "none",
    cursor: "pointer",
    color: "var(--bark)",
    fontSize: "14px",
    padding: "8px 0",
  },
  ticketInfo: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  agentBadge: {
    color: "white",
    fontSize: "12px",
    fontWeight: 600,
    padding: "4px 12px",
    borderRadius: "20px",
    letterSpacing: "0.04em",
  },
  ticketId: {
    fontSize: "12px",
    color: "var(--gold)",
    fontFamily: "monospace",
  },
  contextBar: {
    backgroundColor: "var(--mist)",
    padding: "10px 40px",
    fontSize: "13px",
    color: "var(--earth)",
  },
  landingContainer: {
    maxWidth: "800px",
    margin: "0 auto",
    padding: "80px 40px",
    textAlign: "center",
    flex: 1,
  },
  landingHeader: {
    marginBottom: "48px",
  },
  leafAccent: {
    fontSize: "24px",
    color: "var(--moss)",
    marginBottom: "16px",
    display: "block",
  },
  landingTitle: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: "52px",
    fontWeight: 600,
    color: "var(--earth)",
    margin: "0 0 16px",
    lineHeight: 1.1,
  },
  landingSubtitle: {
    fontSize: "16px",
    color: "var(--bark)",
    lineHeight: 1.7,
    maxWidth: "480px",
    margin: "0 auto",
  },
  categoryGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "20px",
    marginBottom: "40px",
  },
  categoryCard: {
    background: "var(--warm-white)",
    border: "1px solid rgba(0,0,0,0.08)",
    borderRadius: "12px",
    padding: "28px 20px",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
    transition: "transform 0.2s ease, border-color 0.2s ease",
    textAlign: "center",
  },
  categoryIcon: {
    fontSize: "28px",
    marginBottom: "4px",
  },
  categoryLabel: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: "18px",
    fontWeight: 600,
    color: "var(--earth)",
  },
  categoryDesc: {
    fontSize: "13px",
    color: "var(--bark)",
    lineHeight: 1.5,
  },
  startButton: {
    backgroundColor: "var(--moss)",
    color: "white",
    border: "none",
    borderRadius: "8px",
    padding: "16px 40px",
    fontSize: "15px",
    fontWeight: 600,
    cursor: "pointer",
    letterSpacing: "0.04em",
  },
  formContainer: {
    maxWidth: "560px",
    margin: "60px auto",
    padding: "0 40px",
  },
  formTitle: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: "36px",
    fontWeight: 600,
    color: "var(--earth)",
    margin: "0 0 8px",
  },
  formSubtitle: {
    fontSize: "15px",
    color: "var(--bark)",
    marginBottom: "32px",
  },
  errorBox: {
    backgroundColor: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: "8px",
    padding: "12px 16px",
    color: "#b91c1c",
    fontSize: "14px",
    marginBottom: "20px",
  },
  formGroup: {
    marginBottom: "20px",
  },
  label: {
    display: "block",
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--earth)",
    marginBottom: "8px",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  input: {
    width: "100%",
    padding: "12px 16px",
    borderRadius: "8px",
    border: "1px solid rgba(0,0,0,0.12)",
    backgroundColor: "var(--warm-white)",
    fontSize: "15px",
    color: "var(--earth)",
    outline: "none",
    fontFamily: "'Jost', system-ui, sans-serif",
  },
  textarea: {
    resize: "vertical",
    lineHeight: 1.6,
  },
  hint: {
    display: "block",
    fontSize: "12px",
    color: "var(--gold)",
    marginTop: "6px",
  },
  submitButton: {
    width: "100%",
    backgroundColor: "var(--moss)",
    color: "white",
    border: "none",
    borderRadius: "8px",
    padding: "16px",
    fontSize: "15px",
    fontWeight: 600,
    cursor: "pointer",
    letterSpacing: "0.04em",
    marginTop: "8px",
  },
  chatContainer: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    maxWidth: "800px",
    width: "100%",
    margin: "0 auto",
    padding: "0 24px 24px",
  },
  messagesArea: {
    flex: 1,
    overflowY: "auto",
    padding: "24px 0",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    minHeight: "400px",
    maxHeight: "60vh",
  },
  messageRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
  },
  agentAvatar: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "16px",
    flexShrink: 0,
    marginTop: "4px",
  },
  bubble: {
    maxWidth: "70%",
    borderRadius: "12px",
    padding: "14px 18px",
  },
  userBubble: {
    backgroundColor: "var(--moss)",
    color: "white",
    borderRadius: "12px 12px 0 12px",
  },
  assistantBubble: {
    backgroundColor: "var(--warm-white)",
    border: "1px solid rgba(0,0,0,0.06)",
    borderLeft: "3px solid",
    borderRadius: "0 12px 12px 12px",
  },
  agentLabel: {
    display: "block",
    fontSize: "11px",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "var(--gold)",
    marginBottom: "6px",
  },
  bubbleText: {
    margin: 0,
    fontSize: "15px",
    lineHeight: 1.65,
    whiteSpace: "pre-wrap",
  },
  typingDots: {
    display: "inline-flex",
    gap: "4px",
    color: "var(--mist)",
  },
  inputArea: {
    display: "flex",
    gap: "12px",
    alignItems: "flex-end",
    borderTop: "1px solid rgba(0,0,0,0.06)",
    paddingTop: "16px",
  },
  chatInput: {
    flex: 1,
    padding: "12px 16px",
    borderRadius: "8px",
    border: "1px solid rgba(0,0,0,0.12)",
    backgroundColor: "var(--warm-white)",
    fontSize: "15px",
    color: "var(--earth)",
    outline: "none",
    resize: "none",
    fontFamily: "'Jost', system-ui, sans-serif",
    lineHeight: 1.5,
  },
  sendButton: {
    color: "white",
    border: "none",
    borderRadius: "8px",
    width: "48px",
    height: "48px",
    fontSize: "20px",
    cursor: "pointer",
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  disclaimer: {
    fontSize: "12px",
    color: "var(--mist)",
    textAlign: "center",
    marginTop: "12px",
  },
};
