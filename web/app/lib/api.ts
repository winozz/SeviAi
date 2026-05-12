const API_BASE_URL =
  (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

export interface ChatRequest {
  message: string;
  user_id?: string;
  session_id?: string;
}

export interface MapData {
  place_id: string;
  label: string;
}

export interface MapPlace {
  place_id: string;
  label: string;
  short: string;
  full: string;
  walk_minutes_from_gate: number;
  direction_from_gate: string;
  x: number | null;
  y: number | null;
  w: number | null;
  h: number | null;
}

export interface CampusMapPayload {
  gate: { x: number; y: number };
  viewbox: { width: number; height: number };
  places: MapPlace[];
}

export interface ChatResponse {
  response: string;
  intent: string;
  confidence: number;
  user_id?: string | null;
  session_id?: string | null;
  message_id?: number | null;
  map_data?: MapData | null;
}

export interface FeedbackRequest {
  message_id?: number;
  user_id?: string;
  session_id?: string;
  intent?: string;
  rating?: number;
  helpful?: boolean;
  /** Structured reason code from /feedback/reasons (e.g. "wrong_info", "accurate"). */
  reason?: string;
  /** Optional free-text reason supplied by the user. */
  comment?: string;
  suggested_intent?: string;
}

export interface FeedbackReasonOption {
  code: string;
  label: string;
}

export interface FeedbackReasonsResponse {
  positive: FeedbackReasonOption[];
  negative: FeedbackReasonOption[];
}

export interface IntentSummary {
  tag: string;
  description?: string;
  patterns?: string[];
  responses?: string[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  chat: (body: ChatRequest) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  batchChat: (requests: ChatRequest[]) =>
    request<ChatResponse[]>("/batch", {
      method: "POST",
      body: JSON.stringify(requests),
    }),

  getIntents: () => request<any>("/intents"),

  getIntent: (tag: string) =>
    request<any>(`/intents/${encodeURIComponent(tag)}`),

  submitFeedback: (body: FeedbackRequest) =>
    request<any>("/feedback", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getFeedbackReasons: () => request<FeedbackReasonsResponse>("/feedback/reasons"),

  getFeedbackStats: () => request<any>("/feedback/stats"),

  getConversation: (userId: string) =>
    request<any>(`/conversation/${encodeURIComponent(userId)}`),

  clearConversation: (userId: string) =>
    request<any>(`/conversation/${encodeURIComponent(userId)}`, {
      method: "DELETE",
    }),

  getTodayStats: () => request<any>("/logs/today"),

  getFallbacks: (limit = 100) =>
    request<any>(`/logs/fallbacks?limit=${limit}`),

  getIntentLogs: () => request<any>("/logs/intents"),

  getModelInfo: () => request<any>("/model/info"),

  getCampusMap: () => request<CampusMapPayload>("/map"),

  getPlace: (placeId: string) =>
    request<MapPlace>(`/map/${encodeURIComponent(placeId)}`),
};
