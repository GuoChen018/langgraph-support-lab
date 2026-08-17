import { parsePartialJson } from "@langchain/core/output_parsers";
import { useStreamContext } from "@/providers/Stream";
import { AIMessage, Checkpoint, Message } from "@langchain/langgraph-sdk";
import { getContentString } from "../utils";
import { BranchSwitcher, CommandBar } from "./shared";
import { MarkdownText } from "../markdown-text";
import { cn } from "@/lib/utils";
import { ToolCalls, ToolResult } from "./tool-calls";
import { MessageContentComplex } from "@langchain/core/messages";
import { useQueryState, parseAsBoolean } from "nuqs";
import { Database, RobotFaceSharp } from "pixelarticons/react";

function parseAnthropicStreamedToolCalls(
  content: MessageContentComplex[],
): AIMessage["tool_calls"] {
  const toolCallContents = content.filter((c) => c.type === "tool_use" && c.id);

  return toolCallContents.map((tc) => {
    const toolCall = tc as Record<string, any>;
    let json: Record<string, any> = {};
    if (toolCall?.input) {
      try {
        json = parsePartialJson(toolCall.input) ?? {};
      } catch {
        // Pass
      }
    }
    return {
      name: toolCall.name ?? "",
      id: toolCall.id ?? "",
      args: json,
      type: "tool_call",
    };
  });
}

export function AssistantMessage({
  message,
  isLoading,
  handleRegenerate,
}: {
  message: Message | undefined;
  isLoading: boolean;
  handleRegenerate: (parentCheckpoint: Checkpoint | null | undefined) => void;
}) {
  const content = message?.content ?? [];
  const contentString = getContentString(content);
  const [hideToolCalls] = useQueryState(
    "hideToolCalls",
    parseAsBoolean.withDefault(false),
  );

  const thread = useStreamContext();
  const isLastMessage =
    thread.messages[thread.messages.length - 1].id === message?.id;
  const meta = message ? thread.getMessagesMetadata(message) : undefined;
  const evidenceCount = thread.values.evidence?.length ?? 0;

  const parentCheckpoint = meta?.firstSeenState?.parent_checkpoint;
  const anthropicStreamedToolCalls = Array.isArray(content)
    ? parseAnthropicStreamedToolCalls(content)
    : undefined;

  const hasToolCalls =
    message &&
    "tool_calls" in message &&
    message.tool_calls &&
    message.tool_calls.length > 0;
  const toolCallsHaveContents =
    hasToolCalls &&
    message.tool_calls?.some(
      (tc) => tc.args && Object.keys(tc.args).length > 0,
    );
  const hasAnthropicToolCalls = !!anthropicStreamedToolCalls?.length;
  const isToolResult = message?.type === "tool";

  if (isToolResult && hideToolCalls) {
    return null;
  }

  return (
    <div className="group mr-auto flex w-full max-w-3xl items-start gap-3">
      {isToolResult ? (
        <ToolResult message={message} />
      ) : (
        <>
          <div className="tech-panel mt-1 flex size-7 shrink-0 items-center justify-center text-primary">
            <RobotFaceSharp className="size-4" />
          </div>
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            {isLastMessage && evidenceCount > 0 && (
              <div className="micro-label flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5">
                  <Database className="size-3.5" />
                  {evidenceCount} sources reviewed
                </span>
              </div>
            )}

            {contentString.length > 0 && (
              <div className="py-1 text-sm leading-7">
                <MarkdownText>{contentString}</MarkdownText>
              </div>
            )}

            {!hideToolCalls && (
              <>
                {(hasToolCalls && toolCallsHaveContents && (
                  <ToolCalls toolCalls={message.tool_calls} />
                )) ||
                  (hasAnthropicToolCalls && (
                    <ToolCalls toolCalls={anthropicStreamedToolCalls} />
                  )) ||
                  (hasToolCalls && <ToolCalls toolCalls={message.tool_calls} />)}
              </>
            )}

            <div
              className={cn(
                "mr-auto flex items-center gap-2 transition-opacity",
                "opacity-0 group-focus-within:opacity-100 group-hover:opacity-100",
              )}
            >
              <BranchSwitcher
                branch={meta?.branch}
                branchOptions={meta?.branchOptions}
                onSelect={(branch) => thread.setBranch(branch)}
                isLoading={isLoading}
              />
              <CommandBar
                content={contentString}
                isLoading={isLoading}
                isAiMessage={true}
                handleRegenerate={() => handleRegenerate(parentCheckpoint)}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function AssistantMessageLoading() {
  return (
    <div className="mr-auto flex items-start gap-3">
      <div className="tech-panel flex size-7 items-center justify-center text-primary">
        <RobotFaceSharp className="size-4" />
      </div>
      <div className="micro-label flex h-7 items-center gap-2">
        <div className="flex items-center gap-1">
          <div className="h-1 w-1 animate-[pulse_1.5s_ease-in-out_infinite] rounded-full bg-foreground/50"></div>
          <div className="h-1 w-1 animate-[pulse_1.5s_ease-in-out_0.5s_infinite] rounded-full bg-foreground/50"></div>
          <div className="h-1 w-1 animate-[pulse_1.5s_ease-in-out_1s_infinite] rounded-full bg-foreground/50"></div>
        </div>
        <span>SEARCHING // DOCS + ISSUES + RELEASES</span>
      </div>
    </div>
  );
}
