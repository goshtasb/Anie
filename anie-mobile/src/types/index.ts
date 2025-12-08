// API Types
export interface VectorAnalysis {
  score: number;
  status?: 'pass' | 'flag' | 'fail';
  issues?: string[];
  analysis?: string;  // Forensic analysis text from engine
}

export interface ScanResult {
  ani_score: number;
  verdict: string;
  summary: string;
  origin_location?: string;  // Geopolitical origin: "Moscow, Russia", "Washington, DC", "Global"
  url_hash?: string;  // V4.4: Nuclear hash for feedback association
  vectors?: {
    reality?: VectorAnalysis;
    tribal?: VectorAnalysis;
    neuro?: VectorAnalysis;
    logic?: VectorAnalysis;  // V4.0: Logical Integrity - detects Double Binds, False Dilemmas, Agency Deletion
  };
}

export interface ScanHistoryItem {
  id: string;
  url: string;
  domain: string;
  score: number;
  verdict: string;
  timestamp: number;
}

// Share Intent Types
export interface ShareIntentData {
  type: 'weburl' | 'text' | 'image' | string;
  value: string;
}

// Theme Colors
export const Colors = {
  background: '#000000',
  surface: '#111111',
  surfaceLight: '#1a1a1a',
  text: '#FFFFFF',
  textMuted: '#888888',
  textDim: '#555555',
  accent: '#4e54c8',
  accentLight: '#8f94fb',
  safe: '#00C851',
  warning: '#FFBB33',
  critical: '#FF4444',
  border: '#333333',
} as const;

export type ScoreColor = typeof Colors.safe | typeof Colors.warning | typeof Colors.critical;

export function getScoreColor(score: number): ScoreColor {
  if (score >= 70) return Colors.safe;
  if (score >= 40) return Colors.warning;
  return Colors.critical;
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return 'HIGH INTEGRITY';
  if (score >= 60) return 'MODERATE SPIN';
  if (score >= 40) return 'SIGNIFICANT BIAS';
  return 'PSYOP DETECTED';
}
