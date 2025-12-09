import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  SafeAreaView,
  StatusBar,
  Alert,
  RefreshControl,
  Linking,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { Colors, ScanHistoryItem, ScanResult, getScoreColor, VectorAnalysis } from '../types';
import { scanUrl, extractDomain, isValidUrl } from '../utils/api';
import { getScanHistory, addToHistory, clearHistory, generateId } from '../utils/storage';

export function MainDashboard() {
  const [urlInput, setUrlInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<ScanHistoryItem[]>(() => getScanHistory());
  const [showResult, setShowResult] = useState(false);
  const [currentResult, setCurrentResult] = useState<ScanResult | null>(null);
  const [currentUrl, setCurrentUrl] = useState('');

  const refreshHistory = useCallback(() => {
    setHistory(getScanHistory());
  }, []);

  const handleScan = async () => {
    const url = urlInput.trim();

    if (!url) {
      Alert.alert('Error', 'Please enter a URL');
      return;
    }

    if (!isValidUrl(url)) {
      Alert.alert('Error', 'Please enter a valid URL starting with http:// or https://');
      return;
    }

    setLoading(true);
    setCurrentUrl(url);

    try {
      const result = await scanUrl(url);
      setCurrentResult(result);
      setShowResult(true);

      // Save to history
      addToHistory({
        id: generateId(),
        url: url,
        domain: extractDomain(url),
        score: result.ani_score,
        verdict: result.verdict,
        timestamp: Date.now(),
      });

      refreshHistory();
      setUrlInput('');
    } catch (error) {
      Alert.alert('Error', error instanceof Error ? error.message : 'Scan failed');
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryItemPress = (item: ScanHistoryItem) => {
    // Re-scan the URL
    setUrlInput(item.url);
    handleScan();
  };

  const handleClearHistory = () => {
    Alert.alert(
      'Clear History',
      'Are you sure you want to clear all scan history?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => {
            clearHistory();
            refreshHistory();
          },
        },
      ]
    );
  };

  const renderHistoryItem = ({ item }: { item: ScanHistoryItem }) => {
    const scoreColor = getScoreColor(item.score);
    const timeAgo = getTimeAgo(item.timestamp);

    return (
      <TouchableOpacity
        style={styles.historyItem}
        onPress={() => handleHistoryItemPress(item)}
        activeOpacity={0.7}
      >
        <View style={styles.historyLeft}>
          <Text style={styles.historyDomain}>{item.domain}</Text>
          <Text style={styles.historyTime}>{timeAgo}</Text>
        </View>
        <View style={styles.historyRight}>
          <Text style={[styles.historyScore, { color: scoreColor }]}>{item.score}</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.background} />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>ACUITY</Text>
        <Text style={styles.headerSubtitle}>// NARRATIVE INTEGRITY</Text>
      </View>

      {/* URL Input */}
      <View style={styles.inputSection}>
        <TextInput
          style={styles.input}
          placeholder="Paste article URL..."
          placeholderTextColor={Colors.textDim}
          value={urlInput}
          onChangeText={setUrlInput}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          returnKeyType="go"
          onSubmitEditing={handleScan}
          editable={!loading}
        />
        <TouchableOpacity
          style={[styles.scanButton, loading && styles.scanButtonDisabled]}
          onPress={handleScan}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator size="small" color={Colors.text} />
          ) : (
            <Text style={styles.scanButtonText}>SCAN</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* History Section */}
      <View style={styles.historySection}>
        <View style={styles.historyHeader}>
          <Text style={styles.historyTitle}>SCAN HISTORY</Text>
          {history.length > 0 && (
            <TouchableOpacity onPress={handleClearHistory}>
              <Text style={styles.clearButton}>CLEAR</Text>
            </TouchableOpacity>
          )}
        </View>

        {history.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>[]</Text>
            <Text style={styles.emptyText}>No scans yet</Text>
            <Text style={styles.emptyHint}>
              Paste a URL above or share from Safari
            </Text>
          </View>
        ) : (
          <FlatList
            data={history}
            keyExtractor={(item) => item.id}
            renderItem={renderHistoryItem}
            refreshControl={
              <RefreshControl
                refreshing={false}
                onRefresh={refreshHistory}
                tintColor={Colors.accent}
              />
            }
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.historyList}
          />
        )}
      </View>

      {/* Settings Link */}
      <TouchableOpacity
        style={styles.settingsLink}
        onPress={() => Linking.openURL('https://www.goanie.com/privacy.html')}
      >
        <Text style={styles.settingsText}>Privacy Policy</Text>
      </TouchableOpacity>

      {/* Result Modal */}
      <ResultModal
        visible={showResult}
        result={currentResult}
        url={currentUrl}
        onClose={() => setShowResult(false)}
      />
    </SafeAreaView>
  );
}

function VectorCard({
  title,
  score,
  status = 'pass',
  issues = [],
}: {
  title: string;
  score: number;
  status?: 'pass' | 'flag' | 'fail';
  issues?: string[];
}) {
  const statusColors = {
    pass: Colors.safe,
    flag: Colors.warning,
    fail: Colors.critical,
  };
  const statusColor = statusColors[status];

  return (
    <View style={vectorStyles.card}>
      <View style={vectorStyles.cardHeader}>
        <Text style={vectorStyles.cardTitle}>{title}</Text>
        <Text style={[vectorStyles.cardScore, { color: statusColor }]}>{score}</Text>
      </View>
      <View style={[vectorStyles.statusBadge, { backgroundColor: statusColor + '20' }]}>
        <Text style={[vectorStyles.statusText, { color: statusColor }]}>
          {status.toUpperCase()}
        </Text>
      </View>
      {issues.length > 0 && (
        <View style={vectorStyles.issuesList}>
          {issues.slice(0, 2).map((issue, index) => (
            <Text key={index} style={vectorStyles.issueText}>• {issue}</Text>
          ))}
        </View>
      )}
    </View>
  );
}

function ResultModal({
  visible,
  result,
  url,
  onClose,
}: {
  visible: boolean;
  result: ScanResult | null;
  url: string;
  onClose: () => void;
}) {
  if (!result) return null;

  const scoreColor = getScoreColor(result.ani_score);
  const vectors = result.vectors;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={modalStyles.overlay}>
        <FlatList
          data={[1]} // Single item to enable scrolling
          keyExtractor={() => 'result'}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={modalStyles.scrollContent}
          renderItem={() => (
            <View style={modalStyles.content}>
              <View style={modalStyles.header}>
                <Text style={modalStyles.headerTitle}>SCAN COMPLETE</Text>
                <TouchableOpacity onPress={onClose}>
                  <Text style={modalStyles.closeText}>CLOSE</Text>
                </TouchableOpacity>
              </View>

              <Text style={modalStyles.domain}>{extractDomain(url)}</Text>

              {/* Geo-Intel Origin Badge */}
              {result.origin_location && result.origin_location !== 'Global' && (
                <View style={modalStyles.geoIntelBadge}>
                  <Text style={modalStyles.geoIntelText}>
                    ORIGIN: {result.origin_location.toUpperCase()}
                  </Text>
                </View>
              )}

              <View style={modalStyles.scoreSection}>
                <Text style={[modalStyles.score, { color: scoreColor }]}>
                  {result.ani_score}
                </Text>
                <Text style={[modalStyles.verdict, { color: scoreColor }]}>
                  {result.verdict}
                </Text>
              </View>

              {result.summary && (
                <Text style={modalStyles.summary}>{result.summary}</Text>
              )}

              {/* Forensic Breakdown */}
              {vectors && (
                <View style={vectorStyles.container}>
                  <Text style={vectorStyles.sectionTitle}>FORENSIC BREAKDOWN</Text>

                  {vectors.reality && (
                    <VectorCard
                      title="REALITY ANCHORING"
                      score={vectors.reality.score}
                      status={vectors.reality.status}
                      issues={vectors.reality.issues}
                    />
                  )}

                  {vectors.tribal && (
                    <VectorCard
                      title="TRIBAL ENGINEERING"
                      score={vectors.tribal.score}
                      status={vectors.tribal.status}
                      issues={vectors.tribal.issues}
                    />
                  )}

                  {vectors.neuro && (
                    <VectorCard
                      title="NEURO-LINGUISTIC"
                      score={vectors.neuro.score}
                      status={vectors.neuro.status}
                      issues={vectors.neuro.issues}
                    />
                  )}

                  {vectors.logic && (
                    <VectorCard
                      title="LOGICAL INTEGRITY"
                      score={vectors.logic.score}
                      status={vectors.logic.status}
                      issues={vectors.logic.issues}
                    />
                  )}
                </View>
              )}
            </View>
          )}
        />
      </View>
    </Modal>
  );
}

function getTimeAgo(timestamp: number): string {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(timestamp).toLocaleDateString();
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 10,
  },
  headerTitle: {
    fontFamily: 'Menlo',
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.text,
    letterSpacing: 4,
  },
  headerSubtitle: {
    fontFamily: 'Menlo',
    fontSize: 12,
    color: Colors.accent,
    letterSpacing: 2,
    marginTop: 4,
  },
  inputSection: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: Colors.text,
    fontSize: 15,
    fontFamily: 'Menlo',
  },
  scanButton: {
    backgroundColor: Colors.accent,
    borderRadius: 12,
    paddingHorizontal: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanButtonDisabled: {
    opacity: 0.7,
  },
  scanButtonText: {
    fontFamily: 'Menlo',
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
    letterSpacing: 2,
  },
  historySection: {
    flex: 1,
    paddingHorizontal: 20,
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  historyTitle: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.textDim,
    letterSpacing: 2,
  },
  clearButton: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.critical,
    letterSpacing: 1,
  },
  historyList: {
    paddingTop: 8,
  },
  historyItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    marginVertical: 4,
  },
  historyLeft: {
    flex: 1,
  },
  historyDomain: {
    color: Colors.text,
    fontSize: 14,
    fontWeight: '500',
  },
  historyTime: {
    color: Colors.textDim,
    fontSize: 11,
    marginTop: 4,
  },
  historyRight: {
    marginLeft: 12,
  },
  historyScore: {
    fontFamily: 'Menlo',
    fontSize: 20,
    fontWeight: 'bold',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontFamily: 'Menlo',
    fontSize: 40,
    color: Colors.border,
    marginBottom: 16,
  },
  emptyText: {
    color: Colors.textMuted,
    fontSize: 16,
    marginBottom: 8,
  },
  emptyHint: {
    color: Colors.textDim,
    fontSize: 13,
    textAlign: 'center',
  },
  settingsLink: {
    paddingVertical: 16,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  settingsText: {
    color: Colors.textDim,
    fontSize: 12,
  },
});

const modalStyles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  content: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
    alignSelf: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerTitle: {
    fontFamily: 'Menlo',
    fontSize: 12,
    color: Colors.accent,
    letterSpacing: 2,
  },
  closeText: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.textMuted,
    letterSpacing: 1,
  },
  domain: {
    fontFamily: 'Menlo',
    fontSize: 11,
    color: Colors.textDim,
    marginBottom: 20,
  },
  scoreSection: {
    alignItems: 'center',
    marginBottom: 16,
  },
  score: {
    fontSize: 64,
    fontFamily: 'Menlo',
    fontWeight: 'bold',
  },
  verdict: {
    fontFamily: 'Menlo',
    fontSize: 12,
    letterSpacing: 2,
    marginTop: 4,
  },
  summary: {
    color: Colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    textAlign: 'center',
  },
  geoIntelBadge: {
    alignSelf: 'center',
    backgroundColor: 'rgba(78, 84, 200, 0.2)',
    borderWidth: 1,
    borderColor: Colors.accent,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 6,
    marginBottom: 16,
  },
  geoIntelText: {
    fontFamily: 'Menlo',
    fontSize: 10,
    color: Colors.accent,
    letterSpacing: 1,
  },
});

const vectorStyles = StyleSheet.create({
  container: {
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  sectionTitle: {
    fontFamily: 'Menlo',
    fontSize: 10,
    color: Colors.textDim,
    letterSpacing: 2,
    marginBottom: 12,
    textAlign: 'center',
  },
  card: {
    backgroundColor: Colors.background,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardTitle: {
    fontFamily: 'Menlo',
    fontSize: 10,
    color: Colors.text,
    letterSpacing: 1,
    fontWeight: '600',
  },
  cardScore: {
    fontFamily: 'Menlo',
    fontSize: 18,
    fontWeight: 'bold',
  },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginBottom: 8,
  },
  statusText: {
    fontFamily: 'Menlo',
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 1,
  },
  issuesList: {
    marginTop: 4,
  },
  issueText: {
    fontFamily: 'Menlo',
    fontSize: 10,
    color: Colors.textMuted,
    lineHeight: 16,
    marginBottom: 4,
  },
});
