"use client";
import React, { useState, useRef, useEffect } from "react";
import { X, Send, Bot, User, Sparkles, ChevronDown } from "lucide-react";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

const INITIAL_MESSAGES: Message[] = [
    {
        id: "1",
        role: "assistant",
        content:
            "Hi! I'm HouSmart AI. I've analyzed 1248 Highland Avenue thoroughly. Ask me anything about this property — valuation, risks, investment potential, or local market trends.",
        timestamp: new Date(),
    },
];

const QUICK_PROMPTS = [
    "Is this a good investment?",
    "Explain the transit catalyst",
    "What's the cap rate mean?",
    "Compare to similar homes",
];

const MOCK_RESPONSES: Record<string, string> = {
    "Is this a good investment?":
        "Based on our analysis, **Yes** — this property scores 94% AI confidence for a Strong Buy. The upcoming light rail station (0.3mi, 2027) is expected to drive a 10–15% price premium. Combined with the RSL zoning for ADU (+800 sqft), you have strong upside potential. Your projected 5-year ROI of 42.5% is well above the Seattle market average of ~28%.",
    "Explain the transit catalyst":
        "A new Sound Transit light rail station is scheduled to open **0.3 miles** from this property in **2027**. Historical data shows properties within half a mile of Seattle light rail stations appreciated **12.4% on average** in the 2 years following opening. This makes the transit factor one of the strongest upside signals in our model.",
    "What's the cap rate mean?":
        "The **Cap Rate (Capitalization Rate)** of 5.2% means that at the current asking price, the property generates a 5.2% annual return on investment from rental income alone (before financing). For the Seattle Queen Anne market, the average cap rate is ~5.0%, so this property is slightly above market average — a positive signal.",
    "Compare to similar homes":
        "I've compared this to the 3 closest comparable listings:\n\n• **1422 Highland Dr** (94% match) — $1.35M, $7,050/mo rent, 4bd/3ba\n• **1520 6th Ave W** (88% match) — $1.12M, $5,150/mo rent, 3bd/2ba  \n• **1308 Bigelow Ave N** (72% match) — $1.45M, $8,900/mo rent, 4bd/3.5ba\n\nAt $1.24M, this property is **undervalued by ~4.2%** compared to the neighborhood average, making it an attractive entry point.",
};

function formatMessage(text: string): React.ReactNode {
    const lines = text.split("\n");
    return lines.map((line, i) => {
        const formatted = line
            .split(/(\*\*[^*]+\*\*)/g)
            .map((part, j) =>
                part.startsWith("**") && part.endsWith("**") ? (
                    <strong key={j} className="font-semibold text-[#101828]">
                        {part.slice(2, -2)}
                    </strong>
                ) : (
                    part
                )
            );
        return (
            <span key={i}>
                {formatted}
                {i < lines.length - 1 && <br />}
            </span>
        );
    });
}

export const AIChatWidget: React.FC = () => {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
    const [input, setInput] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (open) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [open]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    const sendMessage = (text?: string) => {
        const content = text ?? input.trim();
        if (!content) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsTyping(true);

        // Simulate AI response
        setTimeout(() => {
            const reply =
                MOCK_RESPONSES[content] ??
                "Great question! Based on the data for 1248 Highland Avenue, our AI model suggests this aligns with the current market dynamics in Queen Anne. The 142 data points we analyzed support a strong appreciation trajectory, particularly given the 2027 light rail catalyst and the RSL zoning flexibility. Would you like me to dive deeper into any specific aspect?";
            const assistantMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: reply,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMsg]);
            setIsTyping(false);
        }, 1200);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <>
            {/* Chat dialog */}
            {open && (
                <div className="fixed bottom-20 right-5 z-50 w-[360px] max-h-[560px] flex flex-col bg-white border border-[#E5E7EB] rounded-2xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-2 duration-200">
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 bg-[#101828] text-white">
                        <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-full bg-white/15 flex items-center justify-center">
                                <Sparkles size={13} className="text-white" />
                            </div>
                            <div>
                                <p className="text-[12px] font-semibold leading-tight">HouSmart AI</p>
                                <p className="text-[10px] text-white/60 leading-tight">Property Intelligence</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setOpen(false)}
                            className="w-6 h-6 rounded-md hover:bg-white/10 flex items-center justify-center transition"
                        >
                            <ChevronDown size={14} className="text-white/80" />
                        </button>
                    </div>

                    {/* Context pill */}
                    <div className="px-4 py-2 bg-[#F8FAFC] border-b border-[#F3F4F6]">
                        <div className="flex items-center gap-1.5 text-[10px] text-[#6B7280]">
                            <div className="w-1.5 h-1.5 rounded-full bg-[#12B76A]" />
                            Analyzing: <span className="font-semibold text-[#344054]">1248 Highland Avenue</span>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3 min-h-0 max-h-[340px]">
                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={`flex gap-2 items-start ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                            >
                                {/* Avatar */}
                                <div
                                    className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${msg.role === "assistant"
                                            ? "bg-[#101828]"
                                            : "bg-[#EFF8FF]"
                                        }`}
                                >
                                    {msg.role === "assistant" ? (
                                        <Bot size={11} className="text-white" />
                                    ) : (
                                        <User size={11} className="text-[#1D4ED8]" />
                                    )}
                                </div>

                                {/* Bubble */}
                                <div
                                    className={`max-w-[260px] px-3 py-2 rounded-xl text-[11px] leading-relaxed ${msg.role === "assistant"
                                            ? "bg-[#F9FAFB] text-[#344054] rounded-tl-none border border-[#F3F4F6]"
                                            : "bg-[#101828] text-white rounded-tr-none"
                                        }`}
                                >
                                    {formatMessage(msg.content)}
                                </div>
                            </div>
                        ))}

                        {/* Typing indicator */}
                        {isTyping && (
                            <div className="flex gap-2 items-start">
                                <div className="w-6 h-6 rounded-full bg-[#101828] flex items-center justify-center shrink-0">
                                    <Bot size={11} className="text-white" />
                                </div>
                                <div className="bg-[#F9FAFB] border border-[#F3F4F6] px-3 py-2.5 rounded-xl rounded-tl-none flex items-center gap-1">
                                    {[0, 1, 2].map((i) => (
                                        <span
                                            key={i}
                                            className="w-1.5 h-1.5 bg-[#9CA3AF] rounded-full animate-bounce"
                                            style={{ animationDelay: `${i * 0.15}s` }}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>

                    {/* Quick prompts */}
                    {messages.length === 1 && (
                        <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                            {QUICK_PROMPTS.map((p) => (
                                <button
                                    key={p}
                                    onClick={() => sendMessage(p)}
                                    className="text-[10px] px-2.5 py-1 rounded-full bg-[#F3F4F6] text-[#374151] border border-[#E5E7EB] hover:bg-[#E9EBF0] transition whitespace-nowrap"
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Input */}
                    <div className="px-3 py-3 border-t border-[#F3F4F6] flex items-center gap-2">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about this property…"
                            className="flex-1 text-[11px] px-3 py-2 bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#101828]/20 text-[#101828] placeholder-[#9CA3AF] transition"
                        />
                        <button
                            onClick={() => sendMessage()}
                            disabled={!input.trim() || isTyping}
                            className="w-8 h-8 rounded-lg bg-[#101828] flex items-center justify-center hover:bg-[#1D2939] disabled:opacity-40 disabled:cursor-not-allowed transition shrink-0"
                        >
                            <Send size={12} className="text-white" />
                        </button>
                    </div>
                </div>
            )}

            {/* Floating trigger button */}
            <button
                onClick={() => setOpen((v) => !v)}
                className="fixed bottom-5 right-5 z-50 w-12 h-12 rounded-full bg-[#101828] flex items-center justify-center shadow-xl hover:bg-[#1D2939] hover:scale-105 transition-all duration-200"
                aria-label="Open AI Chat"
            >
                {open ? (
                    <X size={18} className="text-white" />
                ) : (
                    <Sparkles size={18} className="text-white" />
                )}
            </button>
        </>
    );
};
