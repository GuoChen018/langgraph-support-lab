import { v4 as uuidv4 } from "uuid";
import { ReactNode, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useStreamContext } from "@/providers/Stream";
import { useState, FormEvent } from "react";
import { Button } from "../ui/button";
import { Checkpoint, Message } from "@langchain/langgraph-sdk";
import { AssistantMessage, AssistantMessageLoading } from "./messages/ai";
import { HumanMessage } from "./messages/human";
import {
  DO_NOT_RENDER_ID_PREFIX,
  ensureToolCallsHaveResponses,
} from "@/lib/ensure-tool-responses";
import { TooltipIconButton } from "./tooltip-icon-button";
import { useQueryState, parseAsBoolean } from "nuqs";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";
import ThreadHistory from "./history";
import { toast } from "sonner";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useTheme } from "next-themes";
import {
  ArrowDown,
  ArrowLeftBoxSharp,
  ArrowRightBoxSharp,
  ArrowUp,
  CloudSun,
  Moon,
  Pencil,
  Search,
} from "pixelarticons/react";
import { BrandMark } from "@/components/icons/brand-mark";

function StickyToBottomContent(props: {
  content: ReactNode;
  footer?: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  const context = useStickToBottomContext();
  return (
    <div
      ref={context.scrollRef}
      style={{ width: "100%", height: "100%" }}
      className={props.className}
    >
      <div ref={context.contentRef} className={props.contentClassName}>
        {props.content}
      </div>

      {props.footer}
    </div>
  );
}

function ScrollToBottom(props: { className?: string }) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();

  if (isAtBottom) return null;
  return (
    <Button
      variant="outline"
      className={props.className}
      onClick={() => scrollToBottom()}
    >
      <ArrowDown className="size-4" />
      <span>Scroll to bottom</span>
    </Button>
  );
}

function EnvironmentBadge() {
  return (
    <div className="micro-label flex items-center gap-1.5">
      <span className="size-1.5 bg-emerald-500" />
      [LOCAL]
    </div>
  );
}

function ThemeToggle() {
  const { setTheme } = useTheme();

  return (
    <TooltipIconButton
      size="sm"
      className="size-8 p-0"
      tooltip="Toggle theme"
      variant="ghost"
      onClick={() =>
        setTheme(
          document.documentElement.classList.contains("dark")
            ? "light"
            : "dark",
        )
      }
    >
      <Moon className="size-4 dark:hidden" />
      <CloudSun className="hidden size-4 dark:block" />
    </TooltipIconButton>
  );
}

export function Thread() {
  const [threadId, setThreadId] = useQueryState("threadId");
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(true),
  );
  const [input, setInput] = useState("");
  const [firstTokenReceived, setFirstTokenReceived] = useState(false);
  const [messagesVisible, setMessagesVisible] = useState(true);
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");

  const stream = useStreamContext();
  const messages = stream.messages;
  const isLoading = stream.isLoading;
  const scrollThreadKey = threadId ?? "new";

  const lastError = useRef<string | undefined>(undefined);
  const lastScrollThreadKey = useRef(scrollThreadKey);

  useEffect(() => {
    if (!stream.error) {
      lastError.current = undefined;
      return;
    }
    try {
      const message = (stream.error as any).message;
      if (!message || lastError.current === message) {
        // Message has already been logged. do not modify ref, return early.
        return;
      }

      // Message is defined, and it has not been logged yet. Save it, and send the error
      lastError.current = message;
      toast.error("An error occurred. Please try again.", {
        description: (
          <p>
            <strong>Error:</strong> <code>{message}</code>
          </p>
        ),
        richColors: true,
        closeButton: true,
      });
    } catch {
      // no-op
    }
  }, [stream.error]);

  // TODO: this should be part of the useStream hook
  const prevMessageLength = useRef(0);
  useEffect(() => {
    if (
      messages.length !== prevMessageLength.current &&
      messages?.length &&
      messages[messages.length - 1].type === "ai"
    ) {
      setFirstTokenReceived(true);
    }

    prevMessageLength.current = messages.length;
  }, [messages]);

  useEffect(() => {
    if (lastScrollThreadKey.current === scrollThreadKey) return;
    lastScrollThreadKey.current = scrollThreadKey;
    // Hide historical threads until the scroller has seated at the bottom.
    setMessagesVisible(scrollThreadKey === "new");
  }, [scrollThreadKey]);

  useEffect(() => {
    if (scrollThreadKey === "new" || messagesVisible) return;
    if (messages.length === 0) return;

    let cancelled = false;
    const reveal = () => {
      if (!cancelled) setMessagesVisible(true);
    };

    // Wait two frames so StickToBottom can apply its instant bottom scroll
    // before the message list becomes visible.
    const frame = requestAnimationFrame(() => {
      requestAnimationFrame(reveal);
    });

    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
    };
  }, [scrollThreadKey, messages.length, messagesVisible]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    setFirstTokenReceived(false);

    const newHumanMessage: Message = {
      id: uuidv4(),
      type: "human",
      content: input,
    };

    const toolMessages = ensureToolCallsHaveResponses(stream.messages);
    stream.submit(
      { messages: [...toolMessages, newHumanMessage] },
      {
        streamMode: ["values"],
        optimisticValues: (prev) => ({
          ...prev,
          messages: [
            ...(prev.messages ?? []),
            ...toolMessages,
            newHumanMessage,
          ],
        }),
      },
    );

    setInput("");
  };

  const handleRegenerate = (
    parentCheckpoint: Checkpoint | null | undefined,
  ) => {
    // Do this so the loading state is correct
    prevMessageLength.current = prevMessageLength.current - 1;
    setFirstTokenReceived(false);
    stream.submit(undefined, {
      checkpoint: parentCheckpoint,
      streamMode: ["values"],
    });
  };

  const chatStarted = !!threadId || !!messages.length;
  const hasNoAIOrToolMessages = !messages.find(
    (m) => m.type === "ai" || m.type === "tool",
  );

  return (
    <div className="flex w-full h-screen overflow-hidden">
      <div className="relative lg:flex hidden">
        <motion.div
          className="absolute z-20 h-full overflow-hidden border-r bg-white"
          style={{ width: 260 }}
          animate={
            isLargeScreen
              ? { x: chatHistoryOpen ? 0 : -260 }
              : { x: chatHistoryOpen ? 0 : -260 }
          }
          initial={{ x: -260 }}
          transition={
            isLargeScreen
              ? { type: "spring", stiffness: 300, damping: 30 }
              : { duration: 0 }
          }
        >
          <div className="relative h-full" style={{ width: 260 }}>
            <ThreadHistory />
          </div>
        </motion.div>
      </div>
      <motion.div
        className={cn(
          "relative flex min-w-0 flex-1 flex-col overflow-hidden bg-background/80",
          !chatStarted && "grid-rows-[1fr]",
        )}
        layout={isLargeScreen}
        animate={{
          marginLeft: chatHistoryOpen ? (isLargeScreen ? 260 : 0) : 0,
          width: chatHistoryOpen
            ? isLargeScreen
              ? "calc(100% - 260px)"
              : "100%"
            : "100%",
        }}
        transition={
          isLargeScreen
            ? { type: "spring", stiffness: 300, damping: 30 }
            : { duration: 0 }
        }
      >
        {!chatStarted && (
          <div className="absolute top-0 left-0 w-full flex items-center justify-between gap-3 p-2 pl-4 z-10">
            <div>
              {!chatHistoryOpen && (
                <Button
                  className="hover:bg-gray-100"
                  variant="ghost"
                  onClick={() => setChatHistoryOpen((p) => !p)}
                >
                  {chatHistoryOpen ? (
                    <ArrowLeftBoxSharp className="size-4" />
                  ) : (
                    <ArrowRightBoxSharp className="size-4" />
                  )}
                </Button>
              )}
            </div>
            <div className="absolute right-4 top-2 flex items-center gap-2">
              <EnvironmentBadge />
              <ThemeToggle />
            </div>
          </div>
        )}
        {chatStarted && (
          <div className="relative z-10 flex items-center justify-between gap-3 border-b bg-background/95 px-3 py-2">
            <div className="flex items-center justify-start gap-2 relative">
              <div className="absolute left-0 z-10">
                {!chatHistoryOpen && (
                  <Button
                    className="hover:bg-gray-100"
                    variant="ghost"
                    onClick={() => setChatHistoryOpen((p) => !p)}
                  >
                    {chatHistoryOpen ? (
                      <ArrowLeftBoxSharp className="size-4" />
                    ) : (
                      <ArrowRightBoxSharp className="size-4" />
                    )}
                  </Button>
                )}
              </div>
              <motion.button
                className="flex gap-2 items-center cursor-pointer"
                onClick={() => setThreadId(null)}
                animate={{
                  marginLeft: !chatHistoryOpen ? 48 : 0,
                }}
                transition={{
                  type: "spring",
                  stiffness: 300,
                  damping: 30,
                }}
              >
                <BrandMark className="size-4" />
                <div className="text-left">
                  <span className="block text-xs font-semibold uppercase tracking-[0.08em]">
                    ChainSupport
                  </span>
                  <span className="micro-label block">
                    support_agent // online
                  </span>
                </div>
              </motion.button>
            </div>

            <div className="flex items-center gap-4">
              <EnvironmentBadge />
              <ThemeToggle />
              <TooltipIconButton
                size="sm"
                className="size-8 p-0"
                tooltip="New thread"
                variant="ghost"
                onClick={() => setThreadId(null)}
              >
                <Pencil className="size-4" />
              </TooltipIconButton>
            </div>

          </div>
        )}

        <StickToBottom
          key={scrollThreadKey}
          className="relative flex-1 overflow-hidden"
          initial="instant"
          resize={isLoading ? "smooth" : "instant"}
        >
          <StickyToBottomContent
            className={cn(
              "absolute inset-0 overflow-y-scroll px-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
              !chatStarted && "flex flex-col items-stretch justify-center",
              chatStarted && "grid grid-rows-[1fr_auto]",
            )}
            contentClassName={cn(
              "pt-8 pb-14 max-w-3xl mx-auto flex flex-col gap-5 w-full",
              !chatStarted && "p-0",
              !messagesVisible && "invisible",
            )}
            content={
              <>
                {messages
                  .filter((m) => !m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX))
                  .map((message, index) =>
                    message.type === "human" ? (
                      <HumanMessage
                        key={message.id || `${message.type}-${index}`}
                        message={message}
                        isLoading={isLoading}
                      />
                    ) : (
                      <AssistantMessage
                        key={message.id || `${message.type}-${index}`}
                        message={message}
                        isLoading={isLoading}
                        handleRegenerate={handleRegenerate}
                      />
                    ),
                  )}
                {/* Special rendering case where there are no AI/tool messages, but there is an interrupt.
                    We need to render it outside of the messages list, since there are no messages to render */}
                {hasNoAIOrToolMessages && !!stream.interrupt && (
                  <AssistantMessage
                    key="interrupt-msg"
                    message={undefined}
                    isLoading={isLoading}
                    handleRegenerate={handleRegenerate}
                  />
                )}
                {isLoading && !firstTokenReceived && (
                  <AssistantMessageLoading />
                )}
              </>
            }
            footer={
              <div className="sticky bottom-0 flex flex-col items-center gap-7 bg-gradient-to-t from-background via-background/95 to-transparent pt-10">
                {!chatStarted && (
                  <div className="mx-auto flex max-w-xl flex-col items-center px-6 text-center">
                    <div className="tech-panel mb-4 flex size-10 items-center justify-center">
                      <Search className="size-4" />
                    </div>
                    <p className="micro-label mb-2">[SYSTEM READY]</p>
                    <h1 className="text-2xl font-medium uppercase tracking-[0.08em] sm:text-[28px]">
                      How can I help?
                    </h1>
                    <p className="mt-3 max-w-lg text-xs uppercase leading-6 tracking-[0.04em] text-muted-foreground">
                      Describe your LangChain issue. Include package versions
                      and the exact error when possible.
                    </p>
                  </div>
                )}

                <ScrollToBottom className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 animate-in fade-in-0 zoom-in-95" />

                <div className="tech-panel relative z-10 mx-auto mb-6 w-full max-w-2xl">
                  <span className="micro-label absolute -top-2 left-3 bg-background px-1.5">
                    INPUT // QUERY
                  </span>
                  <form
                    onSubmit={handleSubmit}
                    className="grid grid-rows-[1fr_auto] gap-2 max-w-3xl mx-auto"
                  >
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (
                          e.key === "Enter" &&
                          !e.shiftKey &&
                          !e.metaKey &&
                          !e.nativeEvent.isComposing
                        ) {
                          e.preventDefault();
                          const el = e.target as HTMLElement | undefined;
                          const form = el?.closest("form");
                          form?.requestSubmit();
                        }
                      }}
                      placeholder="Describe your LangChain or LangGraph issue…"
                      className="field-sizing-content min-h-14 resize-none border-none bg-transparent px-3.5 pt-4 text-xs uppercase leading-5 tracking-[0.03em] shadow-none outline-none ring-0 placeholder:text-muted-foreground/70 focus:outline-none focus:ring-0"
                    />

                    <div className="flex items-center justify-between p-2 pt-3">
                      <p className="micro-label px-1.5">
                        ENTER: SEND // SHIFT+ENTER: NEW LINE
                      </p>
                      {stream.isLoading ? (
                        <Button key="stop" onClick={() => stream.stop()}>
                          STOP
                        </Button>
                      ) : (
                        <Button
                          type="submit"
                          size="icon"
                          className="size-8 rounded-md shadow-none"
                          disabled={isLoading || !input.trim()}
                        >
                          <ArrowUp className="size-4" />
                          <span className="sr-only">Send</span>
                        </Button>
                      )}
                    </div>
                  </form>
                </div>
              </div>
            }
          />
        </StickToBottom>
      </motion.div>
    </div>
  );
}
