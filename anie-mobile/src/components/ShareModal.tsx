import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Dimensions,
  ScrollView,
} from 'react-native';
import { Colors, ScanResult, getScoreColor, getScoreLabel } from '../types';
import { scanUrl, extractDomain, extractUrlFromText, isValidUrl } from '../utils/api';
import { addToHistory, generateId } from '../utils/storage';

interface ShareModalProps {
  intentValue: string;
  intentType: string;
  onClose: () => void;
}

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

export function ShareModal({ intentValue, intentType, onClose }: ShareModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [url, setUrl] = useState<string>('');

  useEffect(() => {
    async function analyze() {
      try {
        // Determine the URL to scan
        let targetUrl = intentValue;

        if (intentType === 'text' && !isValidUrl(intentValue)) {
          // Try to extract URL from shared text
          const extracted = extractUrlFromText(intentValue);
          if (extracted) {
            targetUrl = extracted;
          } else {
            throw new Error('No valid URL found in shared content');
          }
        }

        if (intentType === 'image') {
          throw new Error('Image analysis requires Pro Tier. Please share a URL instead.');
        }

        setUrl(targetUrl);

        // Scan the URL
        const scanResult = await scanUrl(targetUrl);
        setResult(scanResult);

        // Save to history
        addToHistory({
          id: generateId(),
          url: targetUrl,
          domain: extractDomain(targetUrl),
          score: scanResult.ani_score,
          verdict: scanResult.verdict,
          timestamp: Date.now(),
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Analysis failed');
      } finally {
        setLoading(false);
      }
    }

    analyze();
  }, [intentValue, intentType]);

  const scoreColor = result ? getScoreColor(result.ani_score) : Colors.textMuted;
  const scoreLabel = result ? getScoreLabel(result.ani_score) : '';

  return (
    <View style={styles.overlay}>
      <TouchableOpacity style={styles.backdrop} onPress={onClose} activeOpacity={1} />

      <View style={styles.modal}>
        {/* Handle bar */}
        <View style={styles.handleBar} />

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>AXIOM // SCAN</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeText}>CLOSE</Text>
          </TouchableOpacity>
        </View>

        {/* URL Display */}
        {url && (
          <Text style={styles.urlText} numberOfLines={1}>
            {extractDomain(url)}
          </Text>
        )}

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Loading State */}
          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={Colors.accent} />
              <Text style={styles.loadingText}>Analyzing narrative structure...</Text>
            </View>
          )}

          {/* Error State */}
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorIcon}>!</Text>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Result State */}
          {result && (
            <View style={styles.resultContainer}>
              {/* Score */}
              <View style={styles.scoreSection}>
                <Text style={[styles.score, { color: scoreColor }]}>
                  {result.ani_score}
                </Text>
                <Text style={[styles.scoreLabel, { color: scoreColor }]}>
                  {scoreLabel}
                </Text>
              </View>

              {/* Verdict */}
              <Text style={styles.verdict}>{result.verdict}</Text>

              {/* Summary */}
              {result.summary && (
                <Text style={styles.summary}>{result.summary}</Text>
              )}

              {/* Vector Breakdown */}
              {result.vectors && (
                <View style={styles.vectorsSection}>
                  <Text style={styles.vectorsTitle}>FORENSIC BREAKDOWN</Text>

                  {result.vectors.reality_anchoring && (
                    <VectorRow
                      label="Reality Anchoring"
                      score={result.vectors.reality_anchoring.score}
                      issues={result.vectors.reality_anchoring.issues}
                    />
                  )}

                  {result.vectors.tribal_engineering && (
                    <VectorRow
                      label="Tribal Engineering"
                      score={result.vectors.tribal_engineering.score}
                      issues={result.vectors.tribal_engineering.issues}
                    />
                  )}

                  {result.vectors.neuro_linguistic && (
                    <VectorRow
                      label="Neuro-Linguistic"
                      score={result.vectors.neuro_linguistic.score}
                      issues={result.vectors.neuro_linguistic.issues}
                    />
                  )}
                </View>
              )}
            </View>
          )}
        </ScrollView>
      </View>
    </View>
  );
}

function VectorRow({
  label,
  score,
  issues,
}: {
  label: string;
  score: number;
  issues: string[];
}) {
  const color = getScoreColor(score);

  // Only show vectors with issues (score < 80)
  if (score >= 80) return null;

  return (
    <View style={styles.vectorRow}>
      <View style={styles.vectorHeader}>
        <Text style={styles.vectorLabel}>{label}</Text>
        <Text style={[styles.vectorScore, { color }]}>{score}/100</Text>
      </View>
      {issues.length > 0 && (
        <View style={styles.issuesList}>
          {issues.map((issue, i) => (
            <Text key={i} style={styles.issueText}>
              {issue}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modal: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    minHeight: SCREEN_HEIGHT * 0.5,
    maxHeight: SCREEN_HEIGHT * 0.85,
    paddingBottom: 40,
  },
  handleBar: {
    width: 40,
    height: 4,
    backgroundColor: Colors.border,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontFamily: 'Menlo',
    fontSize: 14,
    color: Colors.accent,
    letterSpacing: 2,
  },
  closeButton: {
    padding: 8,
  },
  closeText: {
    fontFamily: 'Menlo',
    fontSize: 12,
    color: Colors.textMuted,
    letterSpacing: 1,
  },
  urlText: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.textDim,
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    marginTop: 16,
    color: Colors.textMuted,
    fontFamily: 'Menlo',
    fontSize: 12,
  },
  errorContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  errorIcon: {
    fontSize: 48,
    color: Colors.critical,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  errorText: {
    color: Colors.critical,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
  },
  resultContainer: {
    paddingVertical: 20,
  },
  scoreSection: {
    alignItems: 'center',
    marginBottom: 20,
  },
  score: {
    fontSize: 72,
    fontFamily: 'Menlo',
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontFamily: 'Menlo',
    fontSize: 12,
    letterSpacing: 2,
    marginTop: 4,
  },
  verdict: {
    color: Colors.text,
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 12,
  },
  summary: {
    color: Colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 24,
  },
  vectorsSection: {
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    paddingTop: 20,
  },
  vectorsTitle: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.textDim,
    letterSpacing: 2,
    marginBottom: 16,
  },
  vectorRow: {
    marginBottom: 16,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 8,
    padding: 12,
  },
  vectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  vectorLabel: {
    color: Colors.text,
    fontSize: 13,
    fontWeight: '500',
  },
  vectorScore: {
    fontFamily: 'Menlo',
    fontSize: 12,
    fontWeight: '600',
  },
  issuesList: {
    marginTop: 8,
  },
  issueText: {
    color: Colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },
});
