// popup.js
document.addEventListener('DOMContentLoaded', () => {
  const scanBtn = document.getElementById('scan-btn');
  const statusDiv = document.getElementById('status');
  const creditsSpan = document.getElementById('credits');

  // State management
  const states = {
    ready: document.getElementById('ready-state'),
    scanning: document.getElementById('scanning-state'),
    results: document.getElementById('results-state'),
    upsell: document.getElementById('upsell-state'),
    error: document.getElementById('error-state')
  };

  // Initialize credits display
  chrome.storage.local.get(['credits'], (result) => {
    const credits = result.credits || 5;
    creditsSpan.textContent = `${credits} Credits`;
  });

  // State switching function
  function showState(stateName) {
    Object.values(states).forEach(state => state.classList.add('hidden'));
    states[stateName].classList.remove('hidden');
  }

  // Scan button click handler
  scanBtn.addEventListener('click', async () => {
    try {
      // 1. Get current active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tab) {
        showError("No active tab found.");
        return;
      }

      // Show scanning state
      showState('scanning');
      statusDiv.textContent = "Extracting text...";

      // 2. Inject content.js to extract text
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      }, (results) => {
        if (chrome.runtime.lastError) {
          showError("Could not read page: " + chrome.runtime.lastError.message);
          return;
        }

        if (!results || !results[0] || !results[0].result) {
          showError("Could not read page content.");
          return;
        }

        const articleData = results[0].result;

        // Validate extracted data
        if (!articleData.text || articleData.text.length < 300) {
          showError("Not enough text to analyze (Minimum 300 words).");
          return;
        }

        statusDiv.textContent = "Analyzing Narrative Integrity...";

        // 3. Send text to Background for API processing
        chrome.runtime.sendMessage({
          action: "ANALYZE_TEXT",
          payload: articleData
        }, (response) => {
          if (chrome.runtime.lastError) {
            showError("Extension error: " + chrome.runtime.lastError.message);
            return;
          }

          if (response.status === "success") {
            // RENDER THE DOSSIER (State 3 from Golden Path)
            renderDossier(response.data);

            // TRIGGER IN-PAGE HIGHLIGHTS
            applyPageHighlights(tab.id, response.data);
          } else if (response.code === "NO_CREDITS") {
            // RENDER UPSELL (State 4)
            showState('upsell');
            // Update credits display
            creditsSpan.textContent = "0 Credits";
          } else {
            showError(response.message || "Analysis failed.");
          }
        });
      });
    } catch (error) {
      showError("Unexpected error: " + error.message);
    }
  });

  // Error handler
  function showError(message) {
    showState('error');
    document.getElementById('error-message').textContent = message;
  }

  // Dossier renderer
  function renderDossier(data) {
    // Update credits display first
    chrome.storage.local.get(['credits'], (result) => {
      const credits = result.credits || 0;
      creditsSpan.textContent = `${credits} Credits`;
    });

    // Set score and color
    const scoreValue = document.getElementById('score-value');
    const verdictBadge = document.getElementById('verdict-badge');
    const summary = document.getElementById('summary');
    const evidenceLocker = document.getElementById('evidence-locker');

    const score = data.ani_score || 50;
    scoreValue.textContent = score;

    // Color coding based on score
    let colorClass = 'verdict-red';
    if (score >= 70) colorClass = 'verdict-green';
    else if (score >= 40) colorClass = 'verdict-yellow';

    // Detect the "Killer" Vector that crashed the score
    let killerVector = null;
    let killerVectorName = null;
    if (score < 40 && data.vectors) {
      let lowestScore = 100;
      for (const [key, vec] of Object.entries(data.vectors)) {
        if (vec && vec.score < lowestScore) {
          lowestScore = vec.score;
          killerVector = key;
        }
      }
      if (killerVector) {
        const vectorLabels = {
          'reality': 'Reality Anchoring',
          'tribal': 'Tribal Engineering',
          'neuro': 'Intent Analysis',
          'reality_anchoring': 'Reality Anchoring',
          'tribal_engineering': 'Tribal Engineering',
          'neuro_linguistic': 'Intent Analysis'
        };
        killerVectorName = vectorLabels[killerVector] || killerVector.replace('_', ' ');
      }
    }

    // Update verdict with killer vector callout
    verdictBadge.textContent = data.verdict || "Analysis Complete";
    verdictBadge.className = `verdict-badge ${colorClass}`;
    scoreValue.style.color = colorClass === 'verdict-red' ? '#ef4444' :
                            colorClass === 'verdict-yellow' ? '#eab308' : '#22c55e';

    // Build summary with critical failure callout
    let summaryHtml = data.summary || "Analysis complete.";
    if (killerVectorName) {
      summaryHtml = `<span class="critical-warning">Critical Failure: ${killerVectorName}</span>${summaryHtml}`;
    }
    summary.innerHTML = summaryHtml;

    // Render Evidence Locker (Vector Breakdown) - pass killer vector to highlight it
    evidenceLocker.innerHTML = renderEvidenceLocker(data.vectors, killerVector);

    // Add click handlers for accordion
    evidenceLocker.querySelectorAll('.vector-header').forEach(header => {
      header.addEventListener('click', () => {
        const item = header.parentElement;
        item.classList.toggle('expanded');
        const details = item.querySelector('.vector-details');
        if (details) {
          details.style.display = item.classList.contains('expanded') ? 'block' : 'none';
        }
      });
    });

    // Auto-expand the killer vector
    if (killerVector) {
      const killerItem = evidenceLocker.querySelector('.vector-item.killer');
      if (killerItem) {
        killerItem.classList.add('expanded');
        const details = killerItem.querySelector('.vector-details');
        if (details) details.style.display = 'block';
      }
    }

    showState('results');
  }

  // Evidence Locker renderer
  function renderEvidenceLocker(vectors, killerVector = null) {
    if (!vectors || Object.keys(vectors).length === 0) {
      return '';
    }

    // Map backend vector keys to human-readable labels
    const vectorLabels = {
      'reality': 'Reality Anchoring',
      'tribal': 'Tribal Engineering',
      'neuro': 'Intent Analysis',
      // Legacy names (if backend uses these)
      'reality_anchoring': 'Reality Anchoring',
      'tribal_engineering': 'Tribal Engineering',
      'neuro_linguistic': 'Intent Analysis',
      // Original names
      'authority': 'Authority Check',
      'emotion': 'Emotional Language',
      'logic': 'Logical Structure',
      'headline': 'Headline Accuracy'
    };

    let html = '<div class="evidence-header">Forensic Breakdown</div>';

    for (const [key, vec] of Object.entries(vectors)) {
      if (!vec) continue;

      const label = vectorLabels[key] || key;
      const score = vec.score || 50;
      const isIssue = score < 70;
      const isKiller = key === killerVector;
      const icon = isKiller ? '💀' : (isIssue ? '⚠️' : '✓');
      const scoreClass = score < 40 ? 'low' : score < 70 ? 'mid' : 'high';

      html += `
        <div class="vector-item ${isIssue ? 'issue' : 'clean'} ${isKiller ? 'killer' : ''}">
          <div class="vector-header">
            <span class="vec-label">${icon} ${label}${isKiller ? ' (VETO)' : ''}</span>
            <span class="vec-score ${scoreClass}">${score}/100</span>
          </div>
          ${isIssue ? `
            <div class="vector-details" style="display: none;">
              <p class="analysis">${vec.analysis || 'No details available.'}</p>
              ${renderFlags(vec.flags)}
            </div>
          ` : ''}
        </div>
      `;
    }

    return html;
  }

  // Helper to render flagged quotes/evidence
  function renderFlags(flags) {
    if (!flags || flags.length === 0) return '';

    const list = Array.isArray(flags) ? flags : [flags];
    if (list.length === 0) return '';

    return `
      <div class="flag-list">
        <strong>Evidence Found:</strong>
        <ul>
          ${list.map(f => `<li>"${escapeHtml(f)}"</li>`).join('')}
        </ul>
      </div>
    `;
  }

  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Apply in-page highlights to the article
  async function applyPageHighlights(tabId, data) {
    console.log('applyPageHighlights called with:', JSON.stringify(data, null, 2));

    if (!data.vectors) {
      console.log('No vectors in data, skipping highlights');
      return;
    }

    // Extract all flagged quotes from vectors with issues
    const evidence = [];
    const vectorLabels = {
      'reality': 'Reality Anchoring Issue',
      'tribal': 'Tribal Engineering Detected',
      'neuro': 'Manipulative Intent'
    };

    // Find the killer vector
    let killerVector = null;
    if (data.ani_score < 40) {
      let lowestScore = 100;
      for (const [key, vec] of Object.entries(data.vectors)) {
        if (vec && vec.score < lowestScore) {
          lowestScore = vec.score;
          killerVector = key;
        }
      }
    }

    // Collect evidence from all problematic vectors
    for (const [key, vec] of Object.entries(data.vectors)) {
      console.log(`Vector ${key}:`, vec);
      // Include any vector with flags, regardless of score (for highlighting)
      if (!vec) {
        console.log(`Skipping ${key}: no data`);
        continue;
      }
      // Skip only perfect scores with no flags
      if (vec.score >= 95 && (!vec.flags || vec.flags.length === 0)) {
        console.log(`Skipping ${key}: score=${vec?.score}, no flags`);
        continue;
      }

      const severity = key === killerVector ? 'killer' : (vec.score < 40 ? 'critical' : 'warning');
      const reason = vectorLabels[key] || `${key} flagged`;

      if (vec.flags && Array.isArray(vec.flags)) {
        console.log(`Adding ${vec.flags.length} flags from ${key}`);
        vec.flags.forEach(flag => {
          evidence.push({
            text: flag,
            severity: severity,
            reason: reason
          });
        });
      } else {
        console.log(`No flags array in ${key}:`, vec.flags);
      }
    }

    console.log('Total evidence collected:', evidence.length, evidence);

    if (evidence.length === 0) {
      console.log('No evidence to highlight');
      return;
    }

    try {
      // 1. Inject the CSS
      await chrome.scripting.insertCSS({
        target: { tabId: tabId },
        files: ['highlights.css']
      });

      // 2. Inject highlighter function directly with evidence data
      await chrome.scripting.executeScript({
        target: { tabId: tabId },
        args: [evidence],
        func: (evidenceData) => {
          // Inline highlighter function
          function cleanPhrase(text) {
            if (!text) return '';

            // Try to extract quoted text if the flag contains a description followed by a quote
            // Pattern: "Description: 'actual quote'" or "Description: \"actual quote\""
            const quoteMatch = text.match(/['""'']([^'""'']{10,})['""'']/);
            if (quoteMatch) {
              text = quoteMatch[1];
            }

            return text
              .replace(/^["'""'']+|["'""'']+$/g, '')
              .replace(/\s+/g, ' ')
              .trim();
          }

          function findTextMatches(phrase) {
            const matches = [];
            const lowerPhrase = phrase.toLowerCase();

            const walker = document.createTreeWalker(
              document.body,
              NodeFilter.SHOW_TEXT,
              {
                acceptNode: function(node) {
                  const parent = node.parentElement;
                  if (!parent) return NodeFilter.FILTER_REJECT;
                  const tagName = parent.tagName.toLowerCase();
                  if (['script', 'style', 'noscript', 'textarea', 'input'].includes(tagName)) {
                    return NodeFilter.FILTER_REJECT;
                  }
                  if (parent.className && typeof parent.className === 'string' && parent.className.includes('anie-highlight')) {
                    return NodeFilter.FILTER_REJECT;
                  }
                  return NodeFilter.FILTER_ACCEPT;
                }
              }
            );

            let node;
            while (node = walker.nextNode()) {
              const text = node.nodeValue;
              const lowerText = text.toLowerCase();

              let index = lowerText.indexOf(lowerPhrase);
              if (index !== -1) {
                matches.push({ node, startIndex: index, endIndex: index + phrase.length });
                continue;
              }

              if (phrase.length > 30) {
                const fuzzyPhrase = lowerPhrase.substring(0, 30);
                index = lowerText.indexOf(fuzzyPhrase);
                if (index !== -1) {
                  let endIndex = Math.min(index + phrase.length, text.length);
                  matches.push({ node, startIndex: index, endIndex });
                }
              }
            }
            return matches;
          }

          function wrapTextNode(textNode, startIndex, endIndex, severity, reason) {
            const text = textNode.nodeValue;
            const parent = textNode.parentNode;

            if (!parent || parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE') return;
            if (parent.className && typeof parent.className === 'string' && parent.className.includes('anie-highlight')) return;

            const fragment = document.createDocumentFragment();

            if (startIndex > 0) {
              fragment.appendChild(document.createTextNode(text.substring(0, startIndex)));
            }

            const span = document.createElement('span');
            const highlightClass = severity === 'critical' ? 'anie-highlight-critical' :
                                  severity === 'killer' ? 'anie-highlight-critical anie-highlight-killer' :
                                  'anie-highlight-warning';
            span.className = highlightClass;
            span.setAttribute('data-anie-reason', reason || 'Flagged by Anie');
            span.textContent = text.substring(startIndex, endIndex);
            fragment.appendChild(span);

            if (endIndex < text.length) {
              fragment.appendChild(document.createTextNode(text.substring(endIndex)));
            }

            parent.replaceChild(fragment, textNode);
          }

          // Process evidence
          let highlightCount = 0;
          evidenceData.forEach(item => {
            const phrase = cleanPhrase(item.text);
            if (!phrase || phrase.length < 10) return;

            const matches = findTextMatches(phrase);
            matches.forEach(match => {
              try {
                wrapTextNode(match.node, match.startIndex, match.endIndex, item.severity, item.reason);
                highlightCount++;
              } catch (e) {
                console.log('Anie highlight skip:', e.message);
              }
            });
          });

          console.log('Anie: Applied ' + highlightCount + ' highlights');

          // Add tooltip positioning on hover
          document.querySelectorAll('[class*="anie-highlight"]').forEach(el => {
            el.addEventListener('mouseenter', function(e) {
              const reason = this.getAttribute('data-anie-reason');
              if (!reason) return;

              // Create or get tooltip element
              let tooltip = document.getElementById('anie-tooltip');
              if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.id = 'anie-tooltip';
                tooltip.style.cssText = `
                  position: fixed;
                  background: #1e293b;
                  color: #f8fafc;
                  padding: 10px 14px;
                  border-radius: 8px;
                  font-size: 13px;
                  font-weight: 500;
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                  line-height: 1.4;
                  z-index: 2147483647;
                  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
                  max-width: 300px;
                  pointer-events: none;
                  opacity: 0;
                  transition: opacity 0.2s;
                `;
                document.body.appendChild(tooltip);
              }

              tooltip.textContent = reason;
              tooltip.style.opacity = '1';

              // Position near the element
              const rect = this.getBoundingClientRect();
              tooltip.style.left = Math.max(10, rect.left) + 'px';
              tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';

              // If tooltip goes above viewport, show below
              if (rect.top - tooltip.offsetHeight - 8 < 10) {
                tooltip.style.top = (rect.bottom + 8) + 'px';
              }
            });

            el.addEventListener('mouseleave', function() {
              const tooltip = document.getElementById('anie-tooltip');
              if (tooltip) tooltip.style.opacity = '0';
            });
          });

          return { count: highlightCount };
        }
      });

      console.log('Highlights injection complete');

    } catch (error) {
      console.error('Failed to apply highlights:', error);
      console.error('Error details:', error.message, error.stack);
    }
  }

  // Event handlers for other buttons
  document.getElementById('scan-next').addEventListener('click', () => {
    showState('ready');
  });

  document.getElementById('maybe-later').addEventListener('click', () => {
    showState('ready');
  });

  document.getElementById('try-again').addEventListener('click', () => {
    showState('ready');
  });

  // Cycling scanning messages
  const scanningMessages = [
    'Extracting Article Text...',
    'Parsing Logical Structures...',
    'Cross-referencing Sentiment...',
    'Generating Verdict...'
  ];

  let messageIndex = 0;
  let scanningInterval;

  // Observer to start/stop message cycling
  const observer = new MutationObserver(() => {
    if (!states.scanning.classList.contains('hidden')) {
      // Start cycling messages
      messageIndex = 0;
      scanningInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % scanningMessages.length;
        statusDiv.textContent = scanningMessages[messageIndex];
      }, 800);
    } else {
      // Stop cycling
      if (scanningInterval) {
        clearInterval(scanningInterval);
        scanningInterval = null;
      }
    }
  });

  observer.observe(states.scanning, { attributes: true, attributeFilter: ['class'] });
});