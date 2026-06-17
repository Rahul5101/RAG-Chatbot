export type Role = "user" | "assistant";

export interface ChatSession {
  session_id: string;
  title: string;
  created_at?: string;
}

export interface SourceMeta {
  source?: string;
  page?: number | string;
  signed_url?: string;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  role: Role;
  response: string;
  bold_words?: string[];
  meta_data?: SourceMeta[];
  follow_up?: string | null;
  table_data?: string[];
  ucid?: string | null;
  created_at?: string;
}

export interface QueryResponse {
  response?: string;
  answer?: string;
  bold_words?: string[];
  meta_data?: SourceMeta[];
  follow_up?: string | null;
  table_data?: string[];
  confidence_score?: number | string;
  ucid?: string | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function createSession(title = "New Chat") {
  return request<{ session_id: string; title: string }>("/chat/session", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function listSessions() {
  return request<{ total_sessions: number; sessions: ChatSession[] }>("/sessions");
}

export async function getSessionChats(sessionId: string) {
  try {
    return await request<{ session_id: string; total_messages: number; chats: ChatMessage[] }>(
      `/sessions/${sessionId}/chats`,
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return { session_id: sessionId, total_messages: 0, chats: [] };
    }
    throw error;
  }
}

export async function askQuestion(sessionId: string, question: string, answerType: "normal" | "deepthink") {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify({
      question,
      answer_type: answerType,
      session_id: sessionId,
    }),
  });
}
