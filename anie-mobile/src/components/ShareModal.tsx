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
  Share,
} from 'react-native';
import { Colors, ScanResult, getScoreColor, getScoreLabel } from '../types';
import { scanUrl, extractDomain, extractUrlFromText, isValidUrl, askAnie, ChatTurn, sendFeedback } from '../utils/api';
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

  // V4.4 Feedback state - Deep Capture Protocol
  const [feedbackState, setFeedbackState] = useState<'idle' | 'collecting' | 'submitted'>('idle');
  const [selectedReason, setSelectedReason] = useState<string | null>(null);
  const [additionalContext, setAdditionalContext] = useState('');

  // Error categories mapping to engine vectors
  const FEEDBACK_REASONS = [
    { label: "Factually Wrong", code: "ERR_REALITY", desc: "Wrong numbers or sources" },
    { label: "Missed Sarcasm/Satire", code: "ERR_CONTEXT", desc: "It's a joke or nuance" },
    { label: "False Alarm", code: "ERR_FALSE_POS", desc: "Article is actually clean" },
    { label: "Missed Manipulation", code: "ERR_FALSE_NEG", desc: "It's toxic but got a pass" },
  ];

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

  // V4.4 Feedback handler - Deep Capture Protocol
  const handleThumbsUp = async () => {
    if (!result?.url_hash || feedbackState !== 'idle') return;
    const success = await sendFeedback(result.url_hash, 'UP');
    if (success) {
      setFeedbackState('submitted');
    }
  };

  const handleThumbsDown = () => {
    if (!result?.url_hash || feedbackState !== 'idle') return;
    // Don't send yet - open the reason collector
    setFeedbackState('collecting');
  };

  const handleSubmitDownvote = async () => {
    if (!result?.url_hash || !selectedReason) return;

    // Build reason string: CODE + optional context
    const reasonString = additionalContext.trim()
      ? `${selectedReason}: ${additionalContext.trim()}`
      : selectedReason;

    const success = await sendFeedback(result.url_hash, 'DOWN', reasonString);
    if (success) {
      setFeedbackState('submitted');
    }
  };

  const handleCancelFeedback = () => {
    setFeedbackState('idle');
    setSelectedReason(null);
    setAdditionalContext('');
  };

  // Share result via native share sheet
  const handleShareResult = async () => {
    if (!result) return;

    try {
      await Share.share({
        message: `I just scanned this article with ACUITY:\n\nScore: ${result.ani_score}/100 - ${getScoreLabel(result.ani_score)}\n"${result.verdict}"\n\nCheck it yourself: https://anieai.netlify.app`,
      });
    } catch (error) {
      console.error('[Share] Failed:', error);
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

              {/* V4.4 Feedback UI - Deep Capture Protocol */}
              <View style={styles.feedbackContainer}>
                {feedbackState === 'submitted' ? (
                  <Text style={styles.feedbackThanks}>Thanks for your feedback!</Text>
                ) : feedbackState === 'collecting' ? (
                  // Deep Capture: Reason Selection
                  <View style={styles.deepCaptureContainer}>
                    <Text style={styles.deepCaptureTitle}>What went wrong?</Text>
                    <View style={styles.reasonGrid}>
                      {FEEDBACK_REASONS.map((reason) => (
                        <TouchableOpacity
                          key={reason.code}
                          style={[
                            styles.reasonBtn,
                            selectedReason === reason.code && styles.reasonBtnSelected,
                          ]}
                          onPress={() => setSelectedReason(reason.code)}
                        >
                          <Text style={[
                            styles.reasonLabel,
                            selectedReason === reason.code && styles.reasonLabelSelected,
                          ]}>{reason.label}</Text>
                          <Text style={styles.reasonDesc}>{reason.desc}</Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                    <TextInput
                      style={styles.contextInput}
                      placeholder="Tell us more (optional)..."
                      placeholderTextColor="#555"
                      value={additionalContext}
                      onChangeText={setAdditionalContext}
                      multiline
                      maxLength={500}
                    />
                    <View style={styles.deepCaptureActions}>
                      <TouchableOpacity style={styles.cancelBtn} onPress={handleCancelFeedback}>
                        <Text style={styles.cancelBtnText}>Cancel</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.submitBtn, !selectedReason && styles.submitBtnDisabled]}
                        onPress={handleSubmitDownvote}
                        disabled={!selectedReason}
                      >
                        <Text style={styles.submitBtnText}>Submit</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ) : (
                  // Initial state: thumbs up/down
                  <>
                    <Text style={styles.feedbackLabel}>Was this helpful?</Text>
                    <TouchableOpacity style={styles.feedbackBtn} onPress={handleThumbsUp}>
                      <Text style={styles.feedbackEmoji}>👍</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.feedbackBtn} onPress={handleThumbsDown}>
                      <Text style={styles.feedbackEmoji}>👎</Text>
                    </TouchableOpacity>
                  </>
                )}
              </View>

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

              {/* Action Buttons */}
              <View style={styles.actionButtons}>
                <TouchableOpacity style={styles.shareBtn} onPress={handleShareResult}>
                  <Text style={styles.shareBtnText}>📤 SHARE RESULT</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.doneBtn} onPress={onClose}>
                  <Text style={styles.doneText}>CLOSE</Text>
                </TouchableOpacity>
              </View>
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
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  shareBtn: {
    flex: 1,
    backgroundColor: Colors.accent,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  shareBtnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 13,
    letterSpacing: 1,
  },
  doneBtn: {
    flex: 1,
    backgroundColor: '#333',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
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
  // V4.4 Feedback Styles
  feedbackContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 16,
    paddingVertical: 8,
  },
  feedbackLabel: {
    color: '#888',
    fontSize: 12,
    fontFamily: 'Menlo',
  },
  feedbackBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: '#444',
    alignItems: 'center',
    justifyContent: 'center',
  },
  feedbackEmoji: {
    fontSize: 18,
  },
  feedbackThanks: {
    color: Colors.safe,
    fontSize: 12,
    fontFamily: 'Menlo',
  },
  // Deep Capture Protocol Styles
  deepCaptureContainer: {
    width: '100%',
    paddingVertical: 12,
  },
  deepCaptureTitle: {
    fontFamily: 'Menlo',
    fontSize: 12,
    color: Colors.critical,
    letterSpacing: 1,
    marginBottom: 12,
    textAlign: 'center',
  },
  reasonGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  reasonBtn: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 8,
    padding: 10,
  },
  reasonBtnSelected: {
    borderColor: Colors.critical,
    backgroundColor: 'rgba(255, 68, 68, 0.1)',
  },
  reasonLabel: {
    color: '#ccc',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 2,
  },
  reasonLabelSelected: {
    color: Colors.critical,
  },
  reasonDesc: {
    color: '#666',
    fontSize: 10,
  },
  contextInput: {
    backgroundColor: '#111',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 13,
    minHeight: 60,
    textAlignVertical: 'top',
    marginBottom: 12,
  },
  deepCaptureActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  cancelBtn: {
    flex: 1,
    backgroundColor: '#222',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelBtnText: {
    color: '#888',
    fontWeight: '600',
    fontSize: 13,
  },
  submitBtn: {
    flex: 1,
    backgroundColor: Colors.critical,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitBtnDisabled: {
    opacity: 0.4,
  },
  submitBtnText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 13,
  },
});
