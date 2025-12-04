import React, { useState, useEffect } from 'react';
import './AegisExtensionPopup.css';

interface ScanData {
  score: number;
  verdict: string;
  summary: string;
  vectors: {
    authority: { score: string; details: string };
    emotion: { score: string; details: string };
    logic: { count: string; details: string };
  };
}

interface AegisState {
  type: 'ready' | 'scanning' | 'dossier' | 'upsell' | 'error';
  credits: number;
  scanData?: ScanData;
  errorMessage?: string;
}

const AegisExtensionPopup: React.FC = () => {
  const [state, setState] = useState<AegisState>({
    type: 'ready',
    credits: 5
  });

  const [expandedVector, setExpandedVector] = useState<string | null>(null);
  const [scanningText, setScanningText] = useState(0);

  const scanningMessages = [
    'Extracting Article Text...',
    'Parsing Logical Structures...',
    'Cross-referencing Sentiment...',
    'Generating Verdict...'
  ];

  useEffect(() => {
    if (state.type === 'scanning') {
      const interval = setInterval(() => {
        setScanningText(prev => (prev + 1) % scanningMessages.length);
      }, 800);

      // Simulate scan completion after 3.2 seconds
      const timeout = setTimeout(() => {
        setState(prev => ({
          ...prev,
          type: 'dossier',
          credits: prev.credits - 1,
          scanData: {
            score: 42,
            verdict: 'High Manipulation Detected',
            summary: 'This article relies heavily on emotional language and unnamed sources to frame a negative narrative, despite lacking primary evidence.',
            vectors: {
              authority: {
                score: 'Low',
                details: 'Found 4 instances of "Sources say" without naming them.'
              },
              emotion: {
                score: 'High Risk',
                details: '35% of adjectives used are high-arousal (e.g., "Catastrophic", "Vile").'
              },
              logic: {
                count: '2 Found',
                details: 'Ad Hominem detected in paragraph 3.'
              }
            }
          }
        }));
      }, 3200);

      return () => {
        clearInterval(interval);
        clearTimeout(timeout);
      };
    }
  }, [state.type]);

  const handleScan = () => {
    if (state.credits === 0) {
      setState(prev => ({ ...prev, type: 'upsell' }));
      return;
    }
    setState(prev => ({ ...prev, type: 'scanning' }));
  };

  const handleCancel = () => {
    setState(prev => ({ ...prev, type: 'ready' }));
  };

  const handleScanNext = () => {
    setState(prev => ({ ...prev, type: 'ready', scanData: undefined }));
  };

  const handleGetCredits = () => {
    window.open('https://aegis.ai/billing', '_blank');
  };

  const handleMaybeLater = () => {
    setState(prev => ({ ...prev, type: 'ready' }));
  };

  const getScoreColor = (score: number) => {
    if (score <= 39) return 'red';
    if (score <= 69) return 'yellow';
    return 'green';
  };

  const toggleVector = (vectorName: string) => {
    setExpandedVector(expandedVector === vectorName ? null : vectorName);
  };

  return (
    <div className="aegis-popup">
      <header className="aegis-header">
        <div className="aegis-logo">
          <span className="shield-icon">🛡️</span>
          <span className="logo-text">AEGIS</span>
        </div>
        <div className={`credit-badge ${state.credits === 0 ? 'zero-credits' : ''}`}>
          <span className={`credit-dot ${state.credits > 0 ? 'green' : 'red'}`}></span>
          <span>{state.credits} Credits</span>
        </div>
      </header>

      {state.type === 'ready' && (
        <main className="ready-state">
          <div className="hero-section">
            <button className="scan-button pulsing" onClick={handleScan}>
              <span className="scan-icon">🔍</span>
            </button>
            <h2>Analyze this Page</h2>
            <p className="subtext">Forensic scan for manipulation & bias.</p>
          </div>
        </main>
      )}

      {state.type === 'scanning' && (
        <main className="scanning-state">
          <div className="scanning-animation">
            <div className="radar-sweep"></div>
          </div>
          <div className="scanning-status">
            <p>{scanningMessages[scanningText]}</p>
          </div>
          <button className="cancel-button" onClick={handleCancel}>
            Cancel
          </button>
        </main>
      )}

      {state.type === 'dossier' && state.scanData && (
        <main className="dossier-state">
          <div className="analysis-header">
            <span className="check-icon">✓</span>
            <span>Analysis Complete</span>
          </div>

          <div className="score-section">
            <div className={`score-display ${getScoreColor(state.scanData.score)}`}>
              <div className="score-value">{state.scanData.score}</div>
              <div className="score-label">A.N.I. Score</div>
            </div>
            <div className={`verdict-badge ${getScoreColor(state.scanData.score)}`}>
              {state.scanData.verdict}
            </div>
          </div>

          <div className="summary-section">
            <p>{state.scanData.summary}</p>
          </div>

          <div className="vectors-section">
            <div className="vector-item">
              <div className="vector-header" onClick={() => toggleVector('authority')}>
                <div className="vector-left">
                  <span className="vector-icon">🏛️</span>
                  <span>Authority</span>
                </div>
                <span className="vector-score">{state.scanData.vectors.authority.score}</span>
              </div>
              {expandedVector === 'authority' && (
                <div className="vector-details">
                  {state.scanData.vectors.authority.details}
                </div>
              )}
            </div>

            <div className="vector-item">
              <div className="vector-header" onClick={() => toggleVector('emotion')}>
                <div className="vector-left">
                  <span className="vector-icon">💓</span>
                  <span>Emotion</span>
                </div>
                <span className="vector-score">{state.scanData.vectors.emotion.score}</span>
              </div>
              {expandedVector === 'emotion' && (
                <div className="vector-details">
                  {state.scanData.vectors.emotion.details}
                </div>
              )}
            </div>

            <div className="vector-item">
              <div className="vector-header" onClick={() => toggleVector('logic')}>
                <div className="vector-left">
                  <span className="vector-icon">🧠</span>
                  <span>Logic</span>
                </div>
                <span className="vector-score">{state.scanData.vectors.logic.count}</span>
              </div>
              {expandedVector === 'logic' && (
                <div className="vector-details">
                  {state.scanData.vectors.logic.details}
                </div>
              )}
            </div>
          </div>

          <div className="sticky-footer">
            <button className="scan-next-button" onClick={handleScanNext}>
              Scan Next
            </button>
          </div>
        </main>
      )}

      {state.type === 'upsell' && (
        <main className="upsell-state">
          <div className="upsell-icon">🔒</div>
          <h2>Forensic Limits Reached</h2>
          <p>You have used your free daily scans. Refuel to continue uncovering the truth.</p>
          <button className="get-credits-button" onClick={handleGetCredits}>
            Get 50 Credits for $5
          </button>
          <button className="maybe-later-button" onClick={handleMaybeLater}>
            Maybe Later
          </button>
        </main>
      )}

      {state.type === 'error' && (
        <main className="error-state">
          <div className="error-icon">⚠️</div>
          <h2>Scan Failed</h2>
          <p>{state.errorMessage || 'An unexpected error occurred.'}</p>
          <button className="try-again-button" onClick={() => setState(prev => ({ ...prev, type: 'ready' }))}>
            Try Again
          </button>
        </main>
      )}

      <footer className="aegis-footer">
        <a href="#" className="footer-link">
          <span>Dashboard</span>
          <span className="external-icon">↗</span>
        </a>
        <a href="#" className="footer-link">
          <span>Settings</span>
          <span className="gear-icon">⚙️</span>
        </a>
      </footer>
    </div>
  );
};

export default AegisExtensionPopup;