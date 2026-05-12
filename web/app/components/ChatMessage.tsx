import { useState } from "react";
import { motion } from "motion/react";
import { Bot, User, ThumbsUp, ThumbsDown, Check, X } from "lucide-react";
import { CampusMap, type MapData } from "./CampusMap";

export interface FeedbackSubmission {
  helpful: boolean;
  reason?: string;
  comment?: string;
}

// Reason taxonomy — keep in sync with backend FEEDBACK_REASONS in api/app.py
// and the /feedback/reasons endpoint. Inlined here so the picker renders
// without an extra API round-trip on first use.
const POSITIVE_REASONS: { code: string; label: string }[] = [
  { code: "accurate", label: "Got my answer" },
  { code: "clear", label: "Easy to understand" },
  { code: "helpful", label: "Pointed me the right way" },
  { code: "other", label: "Something else" },
];

const NEGATIVE_REASONS: { code: string; label: string }[] = [
  { code: "wrong_info", label: "Contains incorrect info" },
  { code: "wrong_topic", label: "Answered something else" },
  { code: "incomplete", label: "Missing key details" },
  { code: "outdated", label: "Looks out of date" },
  { code: "confusing", label: "Hard to understand" },
  { code: "other", label: "Something else" },
];

interface ChatMessageProps {
  message: string;
  isBot: boolean;
  timestamp: string;
  intent?: string;
  confidence?: number;
  messageId?: number;
  mapData?: MapData | null;
  onFeedback?: (submission: FeedbackSubmission) => void;
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
  // Three-state UI: null = not yet rated, true/false = thumbs picked, plus
  // a separate `submitted` flag once the user finalises (with or without reason).
  const [thumb, setThumb] = useState<boolean | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [selectedReason, setSelectedReason] = useState<string | null>(null);
  const [comment, setComment] = useState("");

  const showDebugMeta = Boolean((import.meta as any).env?.VITE_SHOW_DEBUG_META);

  const handleThumb = (helpful: boolean) => {
    if (submitted || thumb !== null) return;
    setThumb(helpful);
    // Don't submit yet — give the user a chance to pick a reason.
  };

  const handleSubmit = () => {
    if (thumb === null || submitted) return;
    onFeedback?.({
      helpful: thumb,
      reason: selectedReason ?? undefined,
      comment: comment.trim() ? comment.trim() : undefined,
    });
    setSubmitted(true);
  };

  const handleSkip = () => {
    if (thumb === null || submitted) return;
    // Send the bare thumb signal without reason/comment.
    onFeedback?.({ helpful: thumb });
    setSubmitted(true);
  };

  const handleCancel = () => {
    if (submitted) return;
    setThumb(null);
    setSelectedReason(null);
    setComment("");
  };

  const showFeedback = isBot && messageId !== undefined && !!onFeedback;
  const showReasonPicker = showFeedback && thumb !== null && !submitted;
  const reasonOptions = thumb ? POSITIVE_REASONS : NEGATIVE_REASONS;

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
                onClick={() => handleThumb(true)}
                disabled={thumb !== null}
                aria-label="Helpful"
                className={`p-1 rounded transition-colors ${
                  thumb === true
                    ? "text-green-600"
                    : "text-gray-400 hover:text-green-600 disabled:hover:text-gray-400"
                }`}
              >
                {submitted && thumb === true ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <ThumbsUp className="w-3.5 h-3.5" />
                )}
              </button>
              <button
                onClick={() => handleThumb(false)}
                disabled={thumb !== null}
                aria-label="Not helpful"
                className={`p-1 rounded transition-colors ${
                  thumb === false
                    ? "text-red-600"
                    : "text-gray-400 hover:text-red-600 disabled:hover:text-gray-400"
                }`}
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {showReasonPicker && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.2 }}
            className="w-full mt-2 px-2"
          >
            <div className="rounded-lg border border-gray-200 bg-white p-3 text-sm shadow-sm">
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-xs font-medium text-gray-700">
                  {thumb ? "What worked well?" : "What went wrong?"}{" "}
                  <span className="text-gray-400">(optional)</span>
                </span>
                <button
                  onClick={handleCancel}
                  aria-label="Cancel feedback"
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="flex flex-wrap gap-1.5 mb-2">
                {reasonOptions.map((opt) => {
                  const active = selectedReason === opt.code;
                  return (
                    <button
                      key={opt.code}
                      onClick={() =>
                        setSelectedReason(active ? null : opt.code)
                      }
                      className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                        active
                          ? thumb
                            ? "bg-green-600 text-white border-green-600"
                            : "bg-red-600 text-white border-red-600"
                          : "bg-gray-50 text-gray-700 border-gray-200 hover:border-gray-400"
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>

              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder={
                  thumb
                    ? "Anything else you'd like us to know? (optional)"
                    : "Tell us more so we can fix it (optional)"
                }
                rows={2}
                maxLength={500}
                className="w-full text-xs rounded-md border border-gray-200 px-2 py-1.5 resize-none focus:outline-none focus:border-gray-400"
              />

              <div className="flex items-center justify-end gap-2 mt-2">
                <button
                  onClick={handleSkip}
                  className="text-xs px-2 py-1 rounded text-gray-500 hover:text-gray-700"
                >
                  Skip
                </button>
                <button
                  onClick={handleSubmit}
                  className={`text-xs px-3 py-1 rounded font-medium ${
                    thumb
                      ? "bg-green-600 text-white hover:bg-green-700"
                      : "bg-red-600 text-white hover:bg-red-700"
                  }`}
                >
                  Send feedback
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {!isBot && (
        <div className="w-8 h-8 rounded-full bg-green-700 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </motion.div>
  );
}
