import { Button } from "@/components/ui/button";
import { useThreads } from "@/providers/Thread";
import { Thread } from "@langchain/langgraph-sdk";
import { useEffect } from "react";

import { getContentString } from "../utils";
import { useQueryState, parseAsBoolean } from "nuqs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import {
  ArrowLeftBoxSharp,
  ArrowRightBoxSharp,
} from "pixelarticons/react";
import { BrandMark } from "@/components/icons/brand-mark";

function ThreadList({
  threads,
  onThreadClick,
}: {
  threads: Thread[];
  onThreadClick?: (threadId: string) => void;
}) {
  const [threadId, setThreadId] = useQueryState("threadId");

  return (
    <div className="flex h-full w-full flex-col items-start justify-start gap-0.5 overflow-y-scroll px-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {threads.length === 0 && (
        <div className="px-2 py-6 text-xs leading-5 text-muted-foreground">
          Your conversations will appear here.
        </div>
      )}
      {threads.map((t) => {
        let itemText = t.thread_id;
        if (
          typeof t.values === "object" &&
          t.values &&
          "messages" in t.values &&
          Array.isArray(t.values.messages) &&
          t.values.messages?.length > 0
        ) {
          const firstMessage = t.values.messages[0];
          itemText = getContentString(firstMessage.content);
        }
        return (
          <div key={t.thread_id} className="w-full">
            <Button
              variant="ghost"
              className={`h-auto min-h-9 w-full justify-start px-2.5 py-2 text-left text-xs font-normal uppercase tracking-[0.02em] ${
                t.thread_id === threadId
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "hover:bg-muted"
              }`}
              onClick={(e) => {
                e.preventDefault();
                onThreadClick?.(t.thread_id);
                if (t.thread_id === threadId) return;
                setThreadId(t.thread_id);
              }}
            >
              <p className="truncate text-ellipsis">{itemText}</p>
            </Button>
          </div>
        );
      })}
    </div>
  );
}

function ThreadHistoryLoading() {
  return (
    <div className="flex h-full w-full flex-col gap-1 px-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <Skeleton key={`skeleton-${i}`} className="h-9 w-full" />
      ))}
    </div>
  );
}

export default function ThreadHistory() {
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(true),
  );
  const [, setThreadId] = useQueryState("threadId");

  const { getThreads, threads, setThreads, threadsLoading, setThreadsLoading } =
    useThreads();

  useEffect(() => {
    if (typeof window === "undefined") return;
    setThreadsLoading(true);
    getThreads()
      .then(setThreads)
      .catch(console.error)
      .finally(() => setThreadsLoading(false));
  }, []);

  return (
    <>
      <div className="hidden h-screen w-[260px] shrink-0 flex-col items-start justify-start gap-3 border-r border-sidebar-border bg-sidebar/95 lg:flex">
        <div className="flex w-full items-center justify-between px-3 pt-3">
          <div>
            <div className="flex items-center gap-2">
              <BrandMark className="size-4 text-foreground" />
              <h1 className="text-xs font-semibold uppercase tracking-[0.08em]">
                ChainSupport
              </h1>
            </div>
          </div>
          <Button
            className="size-8 hover:bg-muted"
            variant="ghost"
            size="icon"
            onClick={() => setChatHistoryOpen((p) => !p)}
          >
            {chatHistoryOpen ? (
              <ArrowLeftBoxSharp className="size-4" />
            ) : (
              <ArrowRightBoxSharp className="size-4" />
            )}
          </Button>
        </div>
        <div className="w-full px-3">
          <Button
            variant="outline"
            className="tech-panel h-9 w-full justify-start bg-card text-xs uppercase tracking-[0.05em] shadow-none"
            onClick={() => setThreadId(null)}
          >
            <span aria-hidden="true">+</span>
            New conversation
          </Button>
          <p className="micro-label mb-1 mt-5 px-1">HISTORY</p>
        </div>
        {threadsLoading ? (
          <ThreadHistoryLoading />
        ) : (
          <ThreadList threads={threads} />
        )}
      </div>
      <div className="lg:hidden">
        <Sheet
          open={!!chatHistoryOpen && !isLargeScreen}
          onOpenChange={(open) => {
            if (isLargeScreen) return;
            setChatHistoryOpen(open);
          }}
        >
          <SheetContent side="left" className="lg:hidden flex">
            <SheetHeader>
              <SheetTitle>History</SheetTitle>
            </SheetHeader>
            <ThreadList
              threads={threads}
              onThreadClick={() => setChatHistoryOpen((o) => !o)}
            />
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
