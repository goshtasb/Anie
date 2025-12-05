import { MMKV } from 'react-native-mmkv';
import { ScanHistoryItem } from '../types';

const storage = new MMKV();

const HISTORY_KEY = 'scan_history';
const MAX_HISTORY_ITEMS = 50;

export function getScanHistory(): ScanHistoryItem[] {
  const data = storage.getString(HISTORY_KEY);
  if (!data) return [];
  try {
    return JSON.parse(data);
  } catch {
    return [];
  }
}

export function addToHistory(item: ScanHistoryItem): void {
  const history = getScanHistory();

  // Remove duplicate if exists
  const filtered = history.filter(h => h.url !== item.url);

  // Add new item at the beginning
  const updated = [item, ...filtered].slice(0, MAX_HISTORY_ITEMS);

  storage.set(HISTORY_KEY, JSON.stringify(updated));
}

export function clearHistory(): void {
  storage.delete(HISTORY_KEY);
}

export function getHistoryItem(id: string): ScanHistoryItem | undefined {
  const history = getScanHistory();
  return history.find(item => item.id === id);
}

export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}
