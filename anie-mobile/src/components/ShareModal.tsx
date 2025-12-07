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
  const hasGeoIntel = result?.origin_location && result.origin_location !== 'Global';

  return (
    <View style={styles.overlay}>
      <TouchableOpacity style={styles.backdrop} onPress={onClose} activeOpacity={1} />

      <View style={styles.modal}>
        {/* Handle bar */}
        <View style={styles.handleBar} />

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>ACUITY // SCAN</Text>
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
              <Text style={styles.loadingText}>DECRYPTING NARRATIVE...</Text>
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
              {/* Geo-Intel Origin Tag */}
              {hasGeoIntel && (
                <View style={styles.geoIntelBadge}>
                  <Text style={styles.geoIntelText}>ORIGIN: {result.origin_location?.toUpperCase()}</Text>
                </View>
              )}

              {/* Score */}
              <View style={styles.scoreSection}>
                <View style={[styles.scoreCircle, { borderColor: scoreColor }]}>
                  <Text style={[styles.score, { color: scoreColor }]}>
                    {result.ani_score}
                  </Text>
                </View>
                <Text style={[styles.scoreLabel, { color: scoreColor }]}>
                  {scoreLabel}
                </Text>
              </View>

              {/* Verdict */}
              <Text style={styles.verdict}>{result.verdict}</Text>

              {/* Summary */}
              {result.summary && (
                <View style={styles.summaryBox}>
                  <Text style={styles.summaryLabel}>EXECUTIVE SUMMARY</Text>
                  <Text style={styles.summary}>{result.summary}</Text>
                </View>
              )}

              {/* Vector Breakdown */}
              {result.vectors && (
                <View style={styles.vectorsSection}>
                  <Text style={styles.vectorsTitle}>FORENSIC BREAKDOWN</Text>

                  {result.vectors.reality_anchoring && (
                    <VectorRow
                      label="Reality Anchoring"
                      score={result.vectors.reality_anchoring.score}
                      analysis={result.vectors.reality_anchoring.analysis}
                    />
                  )}

                  {result.vectors.tribal_engineering && (
                    <VectorRow
                      label="Tribal Engineering"
                      score={result.vectors.tribal_engineering.score}
                      analysis={result.vectors.tribal_engineering.analysis}
                    />
                  )}

                  {result.vectors.neuro_linguistic && (
                    <VectorRow
                      label="Neuro-Linguistic"
                      score={result.vectors.neuro_linguistic.score}
                      analysis={result.vectors.neuro_linguistic.analysis}
                    />
                  )}
                </View>
              )}

              {/* Close Button */}
              <TouchableOpacity style={styles.doneBtn} onPress={onClose}>
                <Text style={styles.doneText}>CLOSE DOSSIER</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Bottom spacer */}
          <View style={{ height: 40 }} />
        </ScrollView>
      </View>
    </View>
  );
}

function VectorRow({
  label,
  score,
  analysis,
}: {
  label: string;
  score: number;
  analysis?: string;
}) {
  const color = getScoreColor(score);
  const isIssue = score < 80;

  // Only show vectors with issues (score < 80)
  if (!isIssue) return null;

  return (
    <View style={styles.vectorRow}>
      <View style={styles.vectorHeader}>
        <Text style={styles.vectorLabel}>{label.toUpperCase()}</Text>
        <Text style={[styles.vectorScore, { color }]}>{score}/100</Text>
      </View>
      {analysis && (
        <Text style={styles.vectorAnalysis}>{analysis}</Text>
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
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  modal: {
    backgroundColor: '#0a0a0a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    minHeight: SCREEN_HEIGHT * 0.5,
    maxHeight: SCREEN_HEIGHT * 0.85,
    borderTopWidth: 1,
    borderColor: '#333',
  },
  handleBar: {
    width: 40,
    height: 4,
    backgroundColor: '#333',
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
    borderBottomColor: '#222',
  },
  headerTitle: {
    fontFamily: 'Menlo',
    fontSize: 12,
    color: '#666',
    letterSpacing: 2,
    fontWeight: '900',
  },
  closeButton: {
    padding: 8,
  },
  closeText: {
    fontFamily: 'Menlo',
    fontSize: 12,
    color: '#fff',
    fontWeight: 'bold',
  },
  urlText: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: '#444',
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
    paddingVertical: 80,
  },
  loadingText: {
    marginTop: 20,
    color: '#666',
    fontFamily: 'Menlo',
    fontSize: 12,
    letterSpacing: 1,
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
  // Geo-Intel Badge
  geoIntelBadge: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(78, 84, 200, 0.15)',
    borderWidth: 1,
    borderColor: Colors.accent,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginBottom: 20,
    alignSelf: 'center',
  },
  geoIntelText: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.accent,
    letterSpacing: 1,
    fontWeight: '600',
  },
  scoreSection: {
    alignItems: 'center',
    marginBottom: 20,
  },
  scoreCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 4,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  score: {
    fontSize: 36,
    fontFamily: 'Menlo',
    fontWeight: '900',
  },
  scoreLabel: {
    fontFamily: 'Menlo',
    fontSize: 12,
    letterSpacing: 2,
    fontWeight: '700',
  },
  verdict: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 16,
  },
  summaryBox: {
    marginBottom: 20,
  },
  summaryLabel: {
    fontFamily: 'Menlo',
    fontSize: 10,
    color: '#444',
    letterSpacing: 1,
    marginBottom: 8,
    fontWeight: '900',
  },
  summary: {
    color: '#ccc',
    fontSize: 15,
    lineHeight: 24,
  },
  vectorsSection: {
    borderTopWidth: 1,
    borderTopColor: '#222',
    paddingTop: 20,
  },
  vectorsTitle: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: '#444',
    letterSpacing: 2,
    marginBottom: 16,
  },
  vectorRow: {
    marginBottom: 16,
    backgroundColor: '#111',
    borderRadius: 8,
    padding: 12,
  },
  vectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  vectorLabel: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  vectorScore: {
    fontFamily: 'Menlo',
    fontSize: 14,
    fontWeight: '900',
  },
  vectorAnalysis: {
    color: '#888',
    fontSize: 12,
    lineHeight: 18,
    marginTop: 6,
  },
  doneBtn: {
    backgroundColor: '#333',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
  },
  doneText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
    letterSpacing: 1,
  },
});
