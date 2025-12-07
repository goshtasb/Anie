import AsyncStorage from '@react-native-async-storage/async-storage';
import { ScanHistoryItem } from '../types';

const HISTORY_KEY = 'scan_history';
const MAX_HISTORY_ITEMS = 50;

// In-memory cache for synchronous access
let historyCache: ScanHistoryItem[] = [];
let initialized = false;

// Initialize cache from AsyncStorage
async function initCache(): Promise<void> {
  if (initialized) return;
  try {
    const data = await AsyncStorage.getItem(HISTORY_KEY);
    if (data) {
      historyCache = JSON.parse(data);
    }
    initialized = true;
  } catch {
    historyCache = [];
    initialized = true;
  }
}

// Call this early in app startup
initCache();

export function getScanHistory(): ScanHistoryItem[] {
  return historyCache;
}

export function addToHistory(item: ScanHistoryItem): void {
  // Remove duplicate if exists
  const filtered = historyCache.filter(h => h.url !== item.url);

  // Add new item at the beginning
  historyCache = [item, ...filtered].slice(0, MAX_HISTORY_ITEMS);

  // Persist async (fire and forget)
  AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(historyCache)).catch(() => {});
}

export function clearHistory(): void {
  historyCache = [];
  AsyncStorage.removeItem(HISTORY_KEY).catch(() => {});
}

export function getHistoryItem(id: string): ScanHistoryItem | undefined {
  return historyCache.find(item => item.id === id);
}

export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}
