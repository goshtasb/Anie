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

    // For MVP, create mock data if API returns minimal response
    const mockData = {
      ani_score: data.ani_score || 42,
      summary: data.summary || "This article relies heavily on emotional language and unnamed sources to frame a negative narrative, despite lacking primary evidence.",
      verdict: data.verdict || "High Manipulation Detected"
    };

    // Set score and color
    const scoreValue = document.getElementById('score-value');
    const verdictBadge = document.getElementById('verdict-badge');
    const summary = document.getElementById('summary');

    scoreValue.textContent = mockData.ani_score;
    verdictBadge.textContent = mockData.verdict;
    summary.textContent = mockData.summary;

    // Color coding based on score
    let colorClass = 'verdict-red';
    if (mockData.ani_score >= 70) colorClass = 'verdict-green';
    else if (mockData.ani_score >= 40) colorClass = 'verdict-yellow';

    verdictBadge.className = `verdict-badge ${colorClass}`;
    scoreValue.style.color = colorClass === 'verdict-red' ? '#ef4444' :
                            colorClass === 'verdict-yellow' ? '#eab308' : '#22c55e';

    showState('results');
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