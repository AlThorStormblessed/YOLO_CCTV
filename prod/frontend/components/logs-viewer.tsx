"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import type { LogEntry } from "@/components/yolo-detection-dashboard";

interface LogsViewerProps {
  logs: LogEntry[];
}

export function LogsViewer({ logs }: LogsViewerProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollArea = scrollAreaRef.current;
      scrollArea.scrollTop = scrollArea.scrollHeight;
    }
  }, [logs]);

  const getLogTypeClass = (type: string) => {
    switch (type) {
      case "info":
        return "bg-slate-800";
      case "warning":
        return "bg-amber-950 text-amber-200";
      case "error":
        return "bg-red-950 text-red-200";
      case "detection":
        return "bg-slate-900 text-cyan-200 font-medium";
      default:
        return "bg-slate-800";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch (e) {
      return timestamp;
    }
  };

  // Helper function to highlight Yash and other names in detection logs
  const highlightPersonNames = (text: string, personNames?: string[]) => {
    if (!personNames || personNames.length === 0) return text;

    let result = text;
    personNames.forEach((name) => {
      // Create a regular expression to match the name (case sensitive)
      const regex = new RegExp(`(${name})`, "g");
      // Replace with highlighted version
      result = result.replace(
        regex,
        `<span class="text-yellow-300 font-bold">$1</span>`
      );
    });

    return result;
  };

  return (
    <div className="border rounded-md">
      <ScrollArea className="h-[500px] w-full" ref={scrollAreaRef}>
        <div className="p-4 bg-slate-950 text-slate-100 font-mono text-sm">
          {logs.length === 0 ? (
            <div className="text-center text-slate-500 py-4">No logs yet</div>
          ) : (
            logs.map((log, index) => (
              <div
                key={index}
                className={`p-2 mb-2 rounded ${getLogTypeClass(log.type)}`}
              >
                <div className="flex items-start">
                  <span className="text-slate-400 text-xs mr-2">
                    [{formatTimestamp(log.timestamp)}]
                  </span>

                  {log.raw_text ? (
                    <pre className="whitespace-pre-wrap m-0 font-mono text-xs">
                      {log.raw_text.split("\n").map((line, i) => {
                        // Highlight person names in detection lines
                        if (
                          i === 0 &&
                          log.type === "detection" &&
                          log.details?.person_names?.length
                        ) {
                          // Parse the line to extract the frame number, dimensions, count, and names parts
                          const match = line.match(
                            /^(\d+): (\d+x\d+) (\d+) (.+?)(?:, \d+\.\d+ms)?$/
                          );

                          if (match) {
                            const [_, frameNum, dimensions, count, names] =
                              match;

                            // Split names by comma if multiple
                            const namesList = names.split(", ");

                            return (
                              <div key={i}>
                                <span>
                                  {frameNum}: {dimensions} {count}{" "}
                                </span>
                                {namesList.map((name, j) => (
                                  <span
                                    key={j}
                                    className="text-yellow-300 font-bold"
                                  >
                                    {name}
                                    {j < namesList.length - 1 ? ", " : ""}
                                  </span>
                                ))}
                                {line.includes("ms") && (
                                  <span>, {line.split(", ").pop()}</span>
                                )}
                              </div>
                            );
                          }
                        }
                        // Highlight known person names in any line
                        if (log.details?.person_names?.length) {
                          return (
                            <div
                              key={i}
                              dangerouslySetInnerHTML={{
                                __html: highlightPersonNames(
                                  line,
                                  log.details.person_names
                                ),
                              }}
                            />
                          );
                        }
                        return <div key={i}>{line}</div>;
                      })}
                    </pre>
                  ) : (
                    <span>{log.message}</span>
                  )}
                </div>

                {log.type === "detection" && log.details && (
                  <div className="mt-2 ml-4 pl-3 border-l-2 border-cyan-700 text-xs">
                    {log.details.classes &&
                    Object.keys(log.details.classes).length > 0 ? (
                      <div className="mb-1">
                        <span className="text-slate-400">Detected: </span>
                        {Object.entries(log.details.classes).map(
                          ([className, count], i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="ml-1 bg-slate-800 text-emerald-300"
                            >
                              {className} ({count})
                            </Badge>
                          )
                        )}
                      </div>
                    ) : log.details.person_names &&
                      log.details.person_names.length > 0 ? (
                      <div className="mb-1">
                        <span className="text-slate-400">
                          Detected persons:{" "}
                        </span>
                        {log.details.person_names.map((name, i) => (
                          <Badge
                            key={i}
                            variant="outline"
                            className="ml-1 bg-slate-800 text-yellow-300 font-bold"
                          >
                            {name}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <div className="mb-1 text-slate-400">
                        No objects detected
                      </div>
                    )}

                    {log.details.speed && (
                      <div className="text-slate-400">{log.details.speed}</div>
                    )}

                    {log.details.shape && (
                      <div className="text-slate-400">
                        Image shape: {log.details.shape}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
