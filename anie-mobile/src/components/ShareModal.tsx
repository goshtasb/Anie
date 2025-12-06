import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Dimensions,
  ScrollView,
  Image,
  ImageBackground,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { Colors, ScanResult, Coordinates, getScoreColor, getScoreLabel } from '../types';
import { scanUrl, extractDomain, extractUrlFromText, isValidUrl } from '../utils/api';
import { addToHistory, generateId } from '../utils/storage';

interface ShareModalProps {
  intentValue: string;
  intentType: string;
  onClose: () => void;
}

const { height: SCREEN_HEIGHT, width: SCREEN_WIDTH } = Dimensions.get('window');

// Mapbox Static Images API - Dark theme
const MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5pZWFpIiwiYSI6ImNtaXV1NDNxODF4Z2IzdG9iY2dmYjV5eWMifQ.XkJvuy_5Vku3KWqAhszJ-w';
const MAPBOX_STYLE = 'dark-v11';

function getMapboxStaticUrl(coords: Coordinates, zoom: number = 4): string {
  // Mapbox Static Images API URL
  // Format: https://api.mapbox.com/styles/v1/mapbox/{style}/static/{lon},{lat},{zoom}/{width}x{height}@2x?access_token={token}
  const width = Math.round(SCREEN_WIDTH);
  const height = Math.round(SCREEN_HEIGHT * 0.6);
  return `https://api.mapbox.com/styles/v1/mapbox/${MAPBOX_STYLE}/static/${coords.lon},${coords.lat},${zoom},0/${width}x${height}@2x?access_token=${MAPBOX_TOKEN}`;
}

export function ShareModal({ intentValue, intentType, onClose }: ShareModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [url, setUrl] = useState<string>('');
  const [mapUrl, setMapUrl] = useState<string | null>(null);

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

        // Generate map URL if coordinates are available
        if (scanResult.coordinates) {
          setMapUrl(getMapboxStaticUrl(scanResult.coordinates));
        }

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

  // Render the main content
  const renderContent = () => (
    <>
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
            {/* Geo-Intel Origin Tag */}
            {hasGeoIntel && (
              <View style={styles.geoIntelBadge}>
                <Text style={styles.geoIntelIcon}>📍</Text>
                <Text style={styles.geoIntelText}>ORIGIN: {result.origin_location?.toUpperCase()}</Text>
              </View>
            )}

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
    </>
  );

  // If we have coordinates and a map URL, render with map background
  if (mapUrl && result?.coordinates) {
    return (
      <View style={styles.overlay}>
        <TouchableOpacity style={styles.backdrop} onPress={onClose} activeOpacity={1} />

        <ImageBackground
          source={{ uri: mapUrl }}
          style={styles.mapBackground}
          imageStyle={styles.mapImage}
        >
          <BlurView intensity={80} tint="dark" style={styles.blurCard}>
            {renderContent()}
          </BlurView>
        </ImageBackground>
      </View>
    );
  }

  // Default: No map background (Global origin or no Mapbox token)
  return (
    <View style={styles.overlay}>
      <TouchableOpacity style={styles.backdrop} onPress={onClose} activeOpacity={1} />

      <View style={styles.modal}>
        {renderContent()}
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
  // Map background styles
  mapBackground: {
    minHeight: SCREEN_HEIGHT * 0.5,
    maxHeight: SCREEN_HEIGHT * 0.85,
    justifyContent: 'flex-end',
  },
  mapImage: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
  blurCard: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    overflow: 'hidden',
    minHeight: SCREEN_HEIGHT * 0.5,
    maxHeight: SCREEN_HEIGHT * 0.85,
    paddingBottom: 40,
  },
  // Default modal styles
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
  // Geo-Intel Badge
  geoIntelBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(78, 84, 200, 0.2)',
    borderWidth: 1,
    borderColor: Colors.accent,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginBottom: 20,
    alignSelf: 'center',
  },
  geoIntelIcon: {
    fontSize: 14,
    marginRight: 8,
  },
  geoIntelText: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.accent,
    letterSpacing: 1,
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
    backgroundColor: 'rgba(26, 26, 26, 0.8)',
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
