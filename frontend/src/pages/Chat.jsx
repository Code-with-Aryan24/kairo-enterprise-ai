
import { useState } from "react";
import { Send, Bot, User, FileText, ShieldCheck } from "lucide-react";

import PageHeader from "../components/common/PageHeader";
import { chatWithKairo } from "../services/api";

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (event) => {
    event.preventDefault();

    const query = input.trim();

    if (!query || loading) {
      return;
    }

    setError("");

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: query,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);

    setInput("");
    setLoading(true);

    try {
      const result = await chatWithKairo(query);

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: result.answer,
        sources: result.sources || [],
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Chat"
        description="Ask KAIRO questions using your enterprise knowledge."
      />

      <div className="mt-6 flex min-h-[600px] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white">

        {/* Chat messages */}
        <div className="flex-1 space-y-6 overflow-y-auto p-5 sm:p-6">

          {messages.length === 0 && (
            <div className="flex min-h-[420px] items-center justify-center">
              <div className="max-w-md text-center">

                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-50">
                  <Bot size={28} className="text-blue-600" />
                </div>

                <h2 className="mt-4 text-lg font-semibold text-slate-900">
                  Ask KAIRO
                </h2>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Ask questions about the knowledge you've uploaded.
                  KAIRO will retrieve relevant information and generate
                  a grounded response.
                </p>

              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === "user"
                  ? "justify-end"
                  : "justify-start"
              }`}
            >

              {message.role === "assistant" && (
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50">
                  <Bot size={18} className="text-blue-600" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-xl px-4 py-3 ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-slate-100 text-slate-800"
                }`}
              >

                {/* Message content */}
                <div className="flex items-start gap-2">

                  {message.role === "user" && (
                    <User size={16} className="mt-0.5 shrink-0" />
                  )}

                  <p className="whitespace-pre-wrap text-sm leading-6">
                    {message.content}
                  </p>

                </div>

                {/* Supporting sources */}
                {message.role === "assistant" &&
                  message.sources?.length > 0 && (

                    <div className="mt-4 border-t border-slate-200 pt-3">

                      <div className="mb-3 flex items-center justify-between gap-2">

                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Supporting Sources
                        </p>

                        <div className="flex items-center gap-1 text-xs text-emerald-700">
                          <ShieldCheck size={14} />
                          <span>Validated evidence</span>
                        </div>

                      </div>

                      <div className="space-y-3">

                        {message.sources.map((source, index) => {

                          const pageNumbers = source.page_numbers || [];

                          const supportingTexts =
                            source.supporting_text || [];

                          const score = Number(source.score);

                          return (
                            <div
                              key={`${source.document_id}-${source.chunk_id}`}
                              className="rounded-lg border border-slate-200 bg-white p-3"
                            >

                              {/* Source heading */}
                              <div className="flex flex-wrap items-center justify-between gap-2">

                                <div className="flex items-center gap-2 text-xs font-medium text-slate-700">

                                  <FileText
                                    size={15}
                                    className="shrink-0 text-blue-600"
                                  />

                                  <span>
                                    Source {index + 1} · Chunk {source.chunk_id}
                                  </span>

                                </div>

                                {Number.isFinite(score) && (
                                  <span className="text-xs text-slate-400">
                                    Score: {score.toFixed(2)}
                                  </span>
                                )}

                              </div>

                              {/* Page attribution */}
                              {pageNumbers.length > 0 && (
                                <div className="mt-2 flex flex-wrap items-center gap-1.5">

                                  <span className="text-xs text-slate-500">
                                    Cited page{pageNumbers.length > 1 ? "s" : ""}:
                                  </span>

                                  {pageNumbers.map((pageNumber) => (
                                    <span
                                      key={pageNumber}
                                      className="rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700"
                                    >
                                      Page {pageNumber}
                                    </span>
                                  ))}

                                </div>
                              )}

                              {/* Supporting quotations */}
                              {supportingTexts.length > 0 && (
                                <div className="mt-3 space-y-2">

                                  {supportingTexts.map((text, textIndex) => (
                                    <blockquote
                                      key={textIndex}
                                      className="rounded-md border-l-2 border-blue-400 bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-600"
                                    >
                                      "{text}"
                                    </blockquote>
                                  ))}

                                </div>
                              )}

                            </div>
                          );
                        })}

                      </div>
                    </div>
                  )}

              </div>
            </div>
          ))}

          {/* Loading */}
          {loading && (
            <div className="flex gap-3">

              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50">
                <Bot size={18} className="text-blue-600" />
              </div>

              <div className="rounded-xl bg-slate-100 px-4 py-3">
                <p className="text-sm text-slate-500">
                  KAIRO is thinking...
                </p>
              </div>

            </div>
          )}

          {/* Error */}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3">
              <p className="text-sm text-red-700">
                {error}
              </p>
            </div>
          )}

        </div>

        {/* Input */}
        <div className="border-t border-slate-200 p-4">

          <form
            onSubmit={handleSend}
            className="flex items-center gap-3"
          >

            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask KAIRO..."
              disabled={loading}
              className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-50"
            />

            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send size={18} />
            </button>

          </form>

        </div>

      </div>
    </div>
  );
}

export default Chat;
