import { ScanResult } from '../types';

const API_URL = 'https://aegis-alpha.onrender.com/v1/scan';
const CHAT_URL = 'https://aegis-alpha.onrender.com/v1/chat';
const FEEDBACK_URL = 'https://aegis-alpha.onrender.com/v1/feedback';

export interface ChatTurn {
  question: string;
  reply: string;
}

export interface ChatResponse {
  reply: string;
  suggested_followups?: string[];
}

export async function scanUrl(url: string): Promise<ScanResult> {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url: url,
      text: '', // Backend will scrape
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export function extractDomain(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace('www.', '');
  } catch {
    return url.substring(0, 30);
  }
}

export function isValidUrl(text: string): boolean {
  try {
    const url = new URL(text);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

export function extractUrlFromText(text: string): string | null {
  // Try to find a URL in the text
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const matches = text.match(urlRegex);
  return matches ? matches[0] : null;
}

export async function askAnie(
  articleText: string,
  analysisContext: string,
  question: string,
  conversationHistory: ChatTurn[]
): Promise<ChatResponse> {
  const response = await fetch(CHAT_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: articleText,
      analysis_context: analysisContext,
      question: question,
      conversation_history: conversationHistory,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Chat failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// V4.4 Silent Feedback
export async function sendFeedback(
  urlHash: string,
  vote: 'UP' | 'DOWN',
  reason?: string
): Promise<boolean> {
  try {
    const response = await fetch(FEEDBACK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url_hash: urlHash,
        vote: vote,
        reason: reason,
      }),
    });

    return response.ok;
  } catch {
    return false;
  }
}
