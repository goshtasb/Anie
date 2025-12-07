import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Dimensions,
  ScrollView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Colors, ScanResult, getScoreColor, getScoreLabel } from '../types';
import { scanUrl, extractDomain, extractUrlFromText, isValidUrl, askAnie, ChatTurn } from '../utils/api';
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

  // Interrogation Mode state
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'anie'; text: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<ChatTurn[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([
    'Explain the score',
    'What manipulation tactics?',
    'Is this biased?',
  ]);
  const chatScrollRef = useRef<ScrollView>(null);

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

  // Build analysis context for chat
  const analysisContext = result
    ? `Score: ${result.ani_score}/100. ${result.verdict}. ${result.summary}`
    : '';

  const handleAskAnie = async (question: string) => {
    if (!question.trim() || !result) return;

    // Add user message to chat
    setChatMessages(prev => [...prev, { role: 'user', text: question }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await askAnie(
        '', // article text is stored on backend via cache
        analysisContext,
        question,
        conversationHistory
      );

      // Add Anie's response
      setChatMessages(prev => [...prev, { role: 'anie', text: response.reply }]);

      // Update conversation history
      setConversationHistory(prev => [...prev, { question, reply: response.reply }]);

      // Update suggested questions
      if (response.suggested_followups && response.suggested_followups.length > 0) {
        setSuggestedQuestions(response.suggested_followups);
      }

      // Scroll to bottom
      setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: true }), 100);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'anie', text: 'Error: Could not reach Anie. Try again.' }]);
    } finally {
      setChatLoading(false);
    }
  };

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

                  {result.vectors.reality && (
                    <VectorRow
                      label="Reality Anchoring"
                      score={result.vectors.reality.score}
                      analysis={result.vectors.reality.analysis}
                    />
                  )}

                  {result.vectors.tribal && (
                    <VectorRow
                      label="Tribal Engineering"
                      score={result.vectors.tribal.score}
                      analysis={result.vectors.tribal.analysis}
                    />
                  )}

                  {result.vectors.neuro && (
                    <VectorRow
                      label="Neuro-Linguistic"
                      score={result.vectors.neuro.score}
                      analysis={result.vectors.neuro.analysis}
                    />
                  )}

                  {result.vectors.logic && (
                    <VectorRow
                      label="Logical Integrity"
                      score={result.vectors.logic.score}
                      analysis={result.vectors.logic.analysis}
                    />
                  )}
                </View>
              )}

              {/* Interrogation Mode - Chat Section */}
              <View style={styles.chatSection}>
                <Text style={styles.chatTitle}>💬 INTERROGATION MODE</Text>

                {/* Suggested Questions Chips */}
                {chatMessages.length === 0 && (
                  <ScrollView
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    style={styles.chipsScroll}
                  >
                    {suggestedQuestions.map((q, i) => (
                      <TouchableOpacity
                        key={i}
                        style={styles.chip}
                        onPress={() => handleAskAnie(q)}
                      >
                        <Text style={styles.chipText}>{q}</Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                )}

                {/* Chat Messages */}
                {chatMessages.length > 0 && (
                  <ScrollView
                    ref={chatScrollRef}
                    style={styles.chatHistory}
                    showsVerticalScrollIndicator={false}
                  >
                    {chatMessages.map((msg, i) => (
                      <View
                        key={i}
                        style={[
                          styles.chatBubble,
                          msg.role === 'user' ? styles.userBubble : styles.anieBubble,
                        ]}
                      >
                        <Text style={styles.chatBubbleText}>{msg.text}</Text>
                      </View>
                    ))}
                    {chatLoading && (
                      <View style={[styles.chatBubble, styles.anieBubble]}>
                        <Text style={styles.chatBubbleText}>Analyzing...</Text>
                      </View>
                    )}
                  </ScrollView>
                )}

                {/* Follow-up Chips (after conversation started) */}
                {chatMessages.length > 0 && !chatLoading && (
                  <ScrollView
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    style={styles.chipsScroll}
                  >
                    {suggestedQuestions.map((q, i) => (
                      <TouchableOpacity
                        key={i}
                        style={styles.chip}
                        onPress={() => handleAskAnie(q)}
                      >
                        <Text style={styles.chipText}>{q}</Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                )}

                {/* Chat Input */}
                <View style={styles.chatInputRow}>
                  <TextInput
                    style={styles.chatInput}
                    placeholder="Ask Anie about this article..."
                    placeholderTextColor="#666"
                    value={chatInput}
                    onChangeText={setChatInput}
                    onSubmitEditing={() => handleAskAnie(chatInput)}
                    returnKeyType="send"
                  />
                  <TouchableOpacity
                    style={[styles.chatSendBtn, chatLoading && styles.chatSendBtnDisabled]}
                    onPress={() => handleAskAnie(chatInput)}
                    disabled={chatLoading || !chatInput.trim()}
                  >
                    <Text style={styles.chatSendText}>ASK</Text>
                  </TouchableOpacity>
                </View>
              </View>

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
  // Interrogation Mode - Chat Styles
  chatSection: {
    borderTopWidth: 1,
    borderTopColor: '#222',
    paddingTop: 20,
    marginTop: 20,
  },
  chatTitle: {
    fontFamily: 'Menlo',
    fontSize: 12,
    color: '#00f0ff',
    letterSpacing: 1,
    marginBottom: 12,
  },
  chipsScroll: {
    marginBottom: 12,
  },
  chip: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: '#444',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginRight: 8,
  },
  chipText: {
    color: '#aaa',
    fontSize: 12,
  },
  chatHistory: {
    maxHeight: 200,
    marginBottom: 12,
  },
  chatBubble: {
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    maxWidth: '85%',
  },
  userBubble: {
    backgroundColor: Colors.accent,
    alignSelf: 'flex-end',
  },
  anieBubble: {
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
    alignSelf: 'flex-start',
  },
  chatBubbleText: {
    color: '#fff',
    fontSize: 14,
    lineHeight: 20,
  },
  chatInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  chatInput: {
    flex: 1,
    backgroundColor: '#111',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 14,
  },
  chatSendBtn: {
    backgroundColor: Colors.accent,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  chatSendBtnDisabled: {
    opacity: 0.5,
  },
  chatSendText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
});
