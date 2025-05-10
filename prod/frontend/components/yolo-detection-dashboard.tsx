"use client";

import { useState, useEffect } from "react";
import { io, type Socket } from "socket.io-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Loader2,
  AlertCircle,
  Trash2,
  Play,
  Square,
  RefreshCw,
  Database,
} from "lucide-react";
import { ConnectionStatus } from "@/components/connection-status";
import { LogsViewer } from "@/components/logs-viewer";

// Types
export interface LogEntry {
  timestamp: string;
  message: string;
  type: "info" | "warning" | "error" | "detection";
  stream_id?: string;
  frame_number?: number;
  details?: {
    classes?: Record<string, number>;
    person_names?: string[];
    valid_detections?: number;
    speed?: string;
    shape?: string;
  };
  raw_text?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://model.viewer.in";
const SOCKET_URL =
  process.env.NEXT_PUBLIC_SOCKET_URL || "https://model.viewer.in";

export function YoloDetectionDashboard() {
  // State
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    "connected" | "disconnected" | "connecting"
  >("disconnected");
  const [streamUrl, setStreamUrl] = useState("");
  const [urlType, setUrlType] = useState<"rtsp" | "video">("rtsp");
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStreamId, setCurrentStreamId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [seenLogIds, setSeenLogIds] = useState<Set<string>>(new Set());
  const [statusMessage, setStatusMessage] = useState("Ready to process stream");
  const [statusType, setStatusType] = useState<
    "default" | "error" | "warning" | "success"
  >("default");
  const [detectionCount, setDetectionCount] = useState(0);
  const [debugMode, setDebugMode] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const maxReconnectAttempts = 10;
  const [streamComplete, setStreamComplete] = useState(false);
  const [autoDetectStream, setAutoDetectStream] = useState(false);

  // Initialize Socket.IO connection
  useEffect(() => {
    initSocket();

    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  const initSocket = () => {
    if (socket) {
      socket.disconnect();
    }

    setConnectionStatus("connecting");

    const socketUrl =
      process.env.NEXT_PUBLIC_SOCKET_URL || "https://model.viewer.in";
    console.log(`Connecting to Socket.IO at ${socketUrl}`);

    try {
      const newSocket = io(socketUrl, {
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        timeout: 20000,
        transports: ["websocket", "polling"],
      });

      newSocket.on("connect", () => {
        console.log("Socket.IO connected");
        setConnectionStatus("connected");
        setReconnectAttempts(0);
        addLogEntry({
          timestamp: new Date().toISOString(),
          message: "Socket.IO connected to server",
          type: "info",
        });
      });

      newSocket.on("connect_error", (error) => {
        console.error("Socket.IO connection error:", error);
        setConnectionStatus("disconnected");
        setReconnectAttempts((prev) => prev + 1);

        addLogEntry({
          timestamp: new Date().toISOString(),
          message: `Socket.IO connection error: ${error.message}`,
          type: "error",
        });
      });

      newSocket.on("disconnect", (reason) => {
        console.log("Socket.IO disconnected:", reason);
        setConnectionStatus("disconnected");

        addLogEntry({
          timestamp: new Date().toISOString(),
          message: `Socket.IO disconnected: ${reason}`,
          type: "warning",
        });
      });

      newSocket.on("log_message", (data: LogEntry) => {
        console.log("Received log message:", data);

        // First, check if we need to auto-detect a stream
        if (!currentStreamId && data.stream_id) {
          console.log(`Auto-detecting stream: ${data.stream_id}`);
          setCurrentStreamId(data.stream_id);
          setAutoDetectStream(true);

          // If it's detection data, we should show the stream as active
          if (data.type === "detection") {
            setIsProcessing(true);
            setStreamComplete(false);
            showStatus(`Auto-detected stream: ${data.stream_id}`, "success");
          }
        }

        // Ignore logs for other streams if we already have a stream ID
        if (
          currentStreamId &&
          data.stream_id &&
          data.stream_id !== currentStreamId
        ) {
          console.log(
            `Ignoring log for different stream ID: ${data.stream_id} (current: ${currentStreamId})`
          );
          return;
        }

        // Always add the log entry, regardless of current stream state
        addLogEntry(data);

        // Handle detection logs
        if (data.type === "detection") {
          console.log("Detection log received:", data);

          // Add debugging info
          if (debugMode) {
            console.table(data.details?.classes);
          }

          // Increment detection counter if there are valid detections
          if (
            data.details?.valid_detections &&
            data.details.valid_detections > 0
          ) {
            setDetectionCount((prev) => prev + 1);
          }
        }

        // Update status based on log message
        if (data.type === "error") {
          updateStreamStatus("error", `Error: ${data.message}`);
        } else if (
          data.type === "info" &&
          data.message === "Stream processing stopped"
        ) {
          updateStreamStatus("stopped");
          console.log("Stream processing complete");
        }
      });

      setSocket(newSocket);
    } catch (error) {
      console.error("Error initializing Socket.IO:", error);
      setConnectionStatus("disconnected");
      addLogEntry({
        timestamp: new Date().toISOString(),
        message: `Error initializing Socket.IO: ${
          error instanceof Error ? error.message : String(error)
        }`,
        type: "error",
      });
    }
  };

  const addLogEntry = (entry: LogEntry) => {
    const logId = `${entry.timestamp}-${
      entry.frame_number || 0
    }-${entry.message.substring(0, 20)}`;

    setSeenLogIds((prev) => {
      if (prev.has(logId)) {
        console.log(`Skipping duplicate log: ${logId}`);
        return prev;
      }

      const newSet = new Set(prev);
      newSet.add(logId);

      setLogs((prevLogs) => {
        if (entry.type === "detection" && entry.frame_number) {
          const newLogs = [...prevLogs, entry];

          return newLogs
            .sort((a, b) => {
              if (
                a.type === "detection" &&
                b.type === "detection" &&
                a.frame_number !== undefined &&
                b.frame_number !== undefined
              ) {
                return b.frame_number - a.frame_number;
              }
              return 0;
            })
            .slice(0, 1000);
        }

        return [entry, ...prevLogs].slice(0, 1000);
      });

      return newSet;
    });
  };

  const showStatus = (
    message: string,
    type: "default" | "error" | "warning" | "success" = "default"
  ) => {
    setStatusMessage(message);
    setStatusType(type);
  };

  const updateStreamStatus = (
    status: "stopped" | "error" | "running",
    message?: string
  ) => {
    setIsProcessing(status === "running");

    if (status === "stopped") {
      // Don't reset currentStreamId yet, as we need to keep receiving logs
      setStreamComplete(true);
    } else {
      setStreamComplete(false);
    }

    // Update UI state based on status
    switch (status) {
      case "running":
        showStatus(message || `Processing stream`, "success");
        break;
      case "stopped":
        showStatus(message || "Stream processing stopped", "default");
        break;
      case "error":
        showStatus(message || "Error processing stream", "error");
        break;
    }
  };

  const handleStartStream = async () => {
    if (!streamUrl.trim()) {
      showStatus("Please enter a URL", "error");
      return;
    }

    // Check socket connection first
    if (!socket || !socket.connected) {
      showStatus(
        "Socket.IO is not connected. Please reconnect first.",
        "error"
      );
      return;
    }

    showStatus("Connecting to stream...", "default");

    try {
      // Reset state for new stream
      setDetectionCount(0);
      setLogs([]);
      setSeenLogIds(new Set());
      setStreamComplete(false);
      setAutoDetectStream(false);

      // Release any previous stream ID
      setCurrentStreamId(null);

      const apiUrl = `${API_URL}/api/start_stream`;
      console.log(`Sending request to: ${apiUrl}`);

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: streamUrl,
          debug_mode: debugMode,
        }),
      });

      const responseData = await response.json();
      console.log("Start stream response:", responseData);

      if (!response.ok) {
        throw new Error(responseData.error || "Failed to start stream");
      }

      // Set the new stream ID
      const newStreamId = responseData.stream_id;
      setCurrentStreamId(newStreamId);
      updateStreamStatus("running", `Processing stream: ${streamUrl}`);

      // Add initial log entry
      addLogEntry({
        timestamp: new Date().toISOString(),
        message: `Starting stream processing for: ${streamUrl}`,
        type: "info",
        stream_id: newStreamId,
      });
    } catch (error) {
      console.error("Start stream error:", error);
      updateStreamStatus(
        "error",
        `Error: ${error instanceof Error ? error.message : String(error)}`
      );

      addLogEntry({
        timestamp: new Date().toISOString(),
        message: `Error starting stream: ${
          error instanceof Error ? error.message : String(error)
        }`,
        type: "error",
      });
    }
  };

  const handleStopStream = async () => {
    if (!currentStreamId || !isProcessing) return;

    try {
      showStatus("Stopping stream...", "warning");

      const apiUrl = `${API_URL}/api/stop_stream/${currentStreamId}`;

      const response = await fetch(apiUrl, {
        method: "POST",
      });

      const responseData = await response.json();
      console.log("Stop stream response:", responseData);

      if (!response.ok) {
        throw new Error(responseData.error || "Failed to stop stream");
      }

      // Change UI state to indicate stopping
      updateStreamStatus("stopped", "Stopping stream...");

      addLogEntry({
        timestamp: new Date().toISOString(),
        message: `Requested to stop stream: ${currentStreamId}`,
        type: "info",
        stream_id: currentStreamId,
      });
    } catch (error) {
      console.error("Stop stream error:", error);
      updateStreamStatus(
        "error",
        `Error: ${error instanceof Error ? error.message : String(error)}`
      );
      addLogEntry({
        timestamp: new Date().toISOString(),
        message: `Error stopping stream: ${
          error instanceof Error ? error.message : String(error)
        }`,
        type: "error",
        stream_id: currentStreamId,
      });
    }
  };

  const handleClearLogs = () => {
    setLogs([]);
    setDetectionCount(0);
    addLogEntry({
      timestamp: new Date().toISOString(),
      message: "Logs cleared",
      type: "info",
    });
  };

  const handleReconnect = () => {
    addLogEntry({
      timestamp: new Date().toISOString(),
      message: "Manually reconnecting Socket.IO...",
      type: "info",
    });
    initSocket();
  };

  const handleSampleUrl = (type: "rtsp" | "video") => {
    const sampleUrls = {
      rtsp: "rtsp://admin123:admin123@103.100.219.14:8555/11",
      video:
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    };

    setUrlType(type);
    setStreamUrl(sampleUrls[type]);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-center md:text-4xl dark:text-black">
          YOLO Object Detection Logs
        </h1>
        <p className="text-muted-foreground text-center">
          Monitor real-time object detection from video streams
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-12">
        {/* Connection Status Card */}
        <Card className="md:col-span-4">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="h-5 w-5" />
              Connection Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <ConnectionStatus status={connectionStatus} />
                <span className="font-medium">
                  {connectionStatus === "connected"
                    ? "Connected"
                    : connectionStatus === "connecting"
                    ? "Connecting..."
                    : "Disconnected"}
                </span>
              </div>

              <div className="text-sm text-muted-foreground">
                Socket URL: {SOCKET_URL}
              </div>

              <Button
                onClick={handleReconnect}
                variant="outline"
                className="w-full"
                disabled={connectionStatus === "connecting"}
              >
                {connectionStatus === "connecting" ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Reconnect Socket
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Stream Control Card */}
        <Card className="md:col-span-8">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Stream Control</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Tabs
                defaultValue="rtsp"
                value={urlType}
                onValueChange={(value) => setUrlType(value as "rtsp" | "video")}
              >
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="rtsp">RTSP Stream</TabsTrigger>
                  <TabsTrigger value="video">Video URL</TabsTrigger>
                </TabsList>

                <div className="mt-4">
                  <div className="flex space-x-2">
                    <Input
                      value={streamUrl}
                      onChange={(e) => setStreamUrl(e.target.value)}
                      placeholder={
                        urlType === "rtsp"
                          ? "Enter RTSP URL (e.g., rtsp://username:password@ip:port/stream)"
                          : "Enter video URL (e.g., https://example.com/video.mp4)"
                      }
                      disabled={isProcessing}
                    />

                    {!isProcessing ? (
                      <Button
                        onClick={handleStartStream}
                        disabled={!socket?.connected}
                      >
                        <Play className="mr-2 h-4 w-4" />
                        Start
                      </Button>
                    ) : (
                      <Button onClick={handleStopStream} variant="destructive">
                        <Square className="mr-2 h-4 w-4" />
                        Stop
                      </Button>
                    )}
                  </div>
                </div>
              </Tabs>

              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleSampleUrl("rtsp")}
                  disabled={isProcessing}
                >
                  Sample RTSP
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleSampleUrl("video")}
                  disabled={isProcessing}
                >
                  Sample Video
                </Button>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="debug-mode"
                  checked={debugMode}
                  onCheckedChange={setDebugMode}
                  disabled={isProcessing}
                />
                <Label htmlFor="debug-mode">
                  Debug Mode (more detailed logging)
                </Label>
              </div>

              <Alert
                variant={statusType === "error" ? "destructive" : "default"}
              >
                {statusType === "error" && <AlertCircle className="h-4 w-4" />}
                <AlertDescription>{statusMessage}</AlertDescription>
              </Alert>

              {currentStreamId && (
                <div className="text-sm">
                  <span className="font-medium">Stream ID:</span>{" "}
                  {currentStreamId}
                  <Badge
                    variant={
                      isProcessing
                        ? "success"
                        : streamComplete
                        ? "outline"
                        : "default"
                    }
                    className="ml-2"
                  >
                    {isProcessing
                      ? "Active"
                      : streamComplete
                      ? "Completed"
                      : "Stopped"}
                  </Badge>
                  {autoDetectStream && (
                    <Badge
                      variant="outline"
                      className="ml-2 text-amber-500 border-amber-500"
                    >
                      Auto-detected
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Logs Card */}
      <Card>
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Detection Logs</CardTitle>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" onClick={handleClearLogs}>
              <Trash2 className="mr-2 h-4 w-4" />
              Clear Logs
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-sm">
                Total detections: {detectionCount}
              </Badge>

              {isProcessing && (
                <div className="flex items-center">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  <span className="text-sm">Processing stream...</span>
                </div>
              )}
            </div>

            <LogsViewer logs={logs} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
