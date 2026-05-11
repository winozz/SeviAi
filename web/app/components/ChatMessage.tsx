import { useState } from "react";
import { motion } from "motion/react";
import { Bot, User, ThumbsUp, ThumbsDown, Check } from "lucide-react";
import { CampusMap, type MapData } from "./CampusMap";

interface ChatMessageProps {
  message: string;
  isBot: boolean;
  timestamp: string;
  intent?: string;
  confidence?: number;
  messageId?: number;
  mapData?: MapData | null;
  onFeedback?: (helpful: boolean) => void;
}

export function ChatMessage({
  message,
  isBot,
  timestamp,
  intent,
  confidence,
  messageId,
  mapData,
  onFeedback,
}: ChatMessageProps) {
  const [feedback, setFeedback] = useState<boolean | null>(null);
  const showDebugMeta = Boolean((import.meta as any).env?.VITE_SHOW_DEBUG_META);

  const handleFeedback = (helpful: boolean) => {
    if (feedback !== null) return;
    setFeedback(helpful);
    onFeedback?.(helpful);
  };

  const showFeedback = isBot && messageId !== undefined && !!onFeedback;
  const confidenceLabel =
    confidence === undefined
      ? null
      : confidence >= 0.8
      ? { text: "High confidence", color: "bg-green-100 text-green-700" }
      : confidence >= 0.5
      ? { text: "Medium confidence", color: "bg-amber-100 text-amber-700" }
      : { text: "Low confidence", color: "bg-red-100 text-red-700" };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 mb-4 ${isBot ? "justify-start" : "justify-end"}`}
    >
      {isBot && (
        <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}

      <div className={`flex flex-col ${isBot ? "items-start" : "items-end"} max-w-[75%]`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isBot ? "bg-gray-100 text-gray-900" : "bg-green-600 text-white"
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        </div>

        {isBot && mapData && (
          <div className="w-full mt-2 max-w-md">
            <CampusMap data={mapData} />
          </div>
        )}

        {isBot && showDebugMeta && (intent || confidenceLabel) && (
          <div className="flex flex-wrap gap-1.5 mt-1.5 px-2">
            {intent && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200">
                {intent}
              </span>
            )}
            {confidenceLabel && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${confidenceLabel.color}`}>
                {confidenceLabel.text}
                {confidence !== undefined && ` - ${Math.round(confidence * 100)}%`}
              </span>
            )}
          </div>
        )}

        <div className="flex items-center gap-2 mt-1 px-2">
          <span className="text-xs text-gray-500">{timestamp}</span>
          {showFeedback && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleFeedback(true)}
                disabled={feedback !== null}
                aria-label="Helpful"
                className={`p-1 rounded transition-colors ${
                  feedback === true
                    ? "text-green-600"
                    : "text-gray-400 hover:text-green-600 disabled:hover:text-gray-400"
                }`}
              >
                {feedback === true ? <Check className="w-3.5 h-3.5" /> : <ThumbsUp className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => handleFeedback(false)}
                disabled={feedback !== null}
                aria-label="Not helpful"
                className={`p-1 rounded transition-colors ${
                  feedback === false
                    ? "text-red-600"
                    : "text-gray-400 hover:text-red-600 disabled:hover:text-gray-400"
                }`}
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {!isBot && (
        <div className="w-8 h-8 rounded-full bg-green-700 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </motion.div>
  );
}
