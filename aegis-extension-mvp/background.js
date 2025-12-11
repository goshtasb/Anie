// background.js

// Production API URL (Render deployment)
const API_URL = 'https://aegis-alpha.onrender.com';

// Generate or retrieve a unique device ID for guest mode
async function getDeviceId() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['device_id'], (result) => {
      if (result.device_id) {
        resolve(result.device_id);
      } else {
        // Generate a new UUID-like device ID
        const newId = 'aegis_' + crypto.randomUUID();
        chrome.storage.local.set({ device_id: newId });
        resolve(newId);
      }
    });
  });
}

// Sync credits from server response
function syncCredits(creditsFromServer) {
  if (creditsFromServer !== null && creditsFromServer !== undefined) {
    chrome.storage.local.set({ credits: creditsFromServer });
  }
}

// Listen for messages from the Popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "ANALYZE_TEXT") {
    handleAnalyzeRequest(request, sendResponse);
    return true; // Keep the message channel open for async operations
  }

  if (request.action === "GET_CREDITS") {
    handleGetCredits(sendResponse);
    return true;
  }
});

async function handleAnalyzeRequest(request, sendResponse) {
  try {
    const deviceId = await getDeviceId();

    // Call Backend API
    const response = await fetch(`${API_URL}/v1/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: request.payload.url,
        text: request.payload.text,
        title: request.payload.title,
        domain: request.payload.domain,
        device_id: deviceId
      })
    });

    if (response.status === 402) {
      // No credits remaining
      syncCredits(0);
      sendResponse({ status: "error", code: "NO_CREDITS" });
      return;
    }

    if (!response.ok) {
      // Try to get error details from JSON, fall back to status text
      let errorMessage = `Server error (${response.status})`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (e) {
        // Response wasn't JSON (e.g., timeout error returns plain text)
        const text = await response.text().catch(() => '');
        if (text && text.length < 100) errorMessage = text;
      }
      sendResponse({ status: "error", message: errorMessage });
      return;
    }

    const data = await response.json();

    // Sync credits from server response
    syncCredits(data.credits_remaining);

    sendResponse({ status: "success", data: data });

  } catch (error) {
    console.error("Aegis API Error:", error);
    // Properly stringify error - error.toString() returns "[object Object]" for some errors
    const errorMessage = error.message || (typeof error === 'string' ? error : 'Network error - please try again');
    sendResponse({ status: "error", message: errorMessage });
  }
}

async function handleGetCredits(sendResponse) {
  try {
    const deviceId = await getDeviceId();

    const response = await fetch(`${API_URL}/v1/credits/${deviceId}`);

    if (response.ok) {
      const data = await response.json();
      syncCredits(data.credits);
      sendResponse({ status: "success", credits: data.credits });
    } else {
      // Fall back to local storage
      chrome.storage.local.get(['credits'], (result) => {
        sendResponse({ status: "success", credits: result.credits || 5 });
      });
    }
  } catch (error) {
    // Fall back to local storage on network error
    chrome.storage.local.get(['credits'], (result) => {
      sendResponse({ status: "success", credits: result.credits || 5 });
    });
  }
}
