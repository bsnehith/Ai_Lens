import { useEffect, useRef, useState } from "react";
import { Bot, Send } from "lucide-react";
import { starterMessages } from "../data/mockData";
import { sendChatQuestion } from "../api/client";

export default function ChatPreview() {
  const [messages, setMessages] = useState(starterMessages);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const feedRef = useRef(null);
  const quickPrompts = [
    "What changed in AI this week?",
    "Any major funding rounds this week?",
    "Top model launches in last 7 days",
  ];

  useEffect(() => {
    if (!feedRef.current) {
      return;
    }
    feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [messages, loading]);

  const send = async () => {
    const clean = text.trim();
    if (!clean || loading) {
      return;
    }
    setMessages((prev) => [...prev, { role: "user", content: clean }]);
    setText("");
    setLoading(true);
    try {
      const response = await sendChatQuestion({ question: clean });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          sources: Array.isArray(response.sources) ? response.sources : [],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Could not connect to backend. Start the backend server and try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="chat" className="section">
      <div className="section-title">
        <h2>Agent chat preview</h2>
        <p>Ask domain questions and show grounded answers once backend APIs are connected.</p>
      </div>

      <div className="chat-quick-row">
        {quickPrompts.map((prompt) => (
          <button key={prompt} type="button" className="chat-chip" onClick={() => setText(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <div className="chat-panel">
        <div ref={feedRef} className="chat-feed">
          {messages.map((message, index) => (
            <article key={`${message.role}-${index}`} className={`bubble ${message.role}`}>
              {message.role === "assistant" && <Bot size={16} />}
              <div>
                <p>{message.content}</p>
                {message.sources?.length ? (
                  <div className="bubble-sources">
                    {message.sources.map((source, sourceIndex) => (
                      <a
                        key={`${source.title}-${sourceIndex}`}
                        href={source.url || "#"}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(event) => {
                          if (!source.url) {
                            event.preventDefault();
                          }
                        }}
                      >
                        {source.title}
                      </a>
                    ))}
                  </div>
                ) : null}
              </div>
            </article>
          ))}
          {loading ? (
            <article className="bubble assistant typing-bubble">
              <Bot size={16} />
              <div className="typing-dots">
                <span />
                <span />
                <span />
              </div>
            </article>
          ) : null}
        </div>
        <div className="chat-compose">
          <input
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && send()}
            placeholder="Ask: what are this week's key AI trends?"
          />
          <button type="button" onClick={send} disabled={loading}>
            <Send size={16} />
          </button>
        </div>
      </div>
    </section>
  );
}
