# Aegis Chrome Extension MVP

A forensic news analysis tool that detects manipulation, bias, and logical fallacies in web articles.

## Architecture: "Injection on Demand"

- **Default State**: Extension does nothing (0% CPU usage)
- **User Action**: User clicks extension popup → clicks "Scan"
- **Injection**: Popup injects `content.js` to extract article text
- **Analysis**: Text sent to `background.js` → Backend API
- **Results**: Display A.N.I. score and manipulation analysis

## Files Structure

```
/aegis-extension-mvp
├── manifest.json        # Extension configuration (activeTab permissions)
├── background.js        # API handler & credit management
├── content.js           # Text extraction script
├── popup.html           # UI container (360px popup)
├── popup.js             # UI logic (vanilla JS)
├── icons/               # Extension icons (16px, 48px, 128px)
└── README.md           # This file
```

## Installation Instructions

1. **Open Chrome Extensions Page**:
   - Go to `chrome://extensions/`
   - Enable "Developer mode" (top right toggle)

2. **Load Extension**:
   - Click "Load unpacked"
   - Select the `aegis-extension-mvp` folder

3. **Test the Extension**:
   - Navigate to any news article
   - Click the Aegis extension icon
   - Click "Scan" to test text extraction

## Key Features

### Security & Privacy
- **activeTab permission**: Only accesses current page when user clicks scan
- **No persistent permissions**: Cannot read browsing history or other tabs
- **Local credit storage**: Tracks usage without server dependence

### Text Extraction
- **Smart content detection**: Finds `<article>`, `<main>`, or paragraphs
- **Noise filtering**: Removes ads, navigation, short snippets
- **Token optimization**: Truncates to 15,000 characters to control API costs

### State Management
- **Ready State**: Initial scan button
- **Scanning State**: Animated feedback with cycling status messages
- **Results State**: A.N.I. score display with summary
- **Upsell State**: Credit exhaustion handling
- **Error State**: Graceful failure handling

## Backend Integration

The extension is configured to send requests to:
```
POST https://api.your-backend.com/v1/scan
```

**Request payload**:
```json
{
  "url": "https://example.com/article",
  "text": "Article content..."
}
```

**Expected response**:
```json
{
  "ani_score": 42,
  "summary": "Analysis summary...",
  "verdict": "High Manipulation Detected"
}
```

## Development Notes

### For Google Chrome Store Approval
- Uses minimal permissions (`activeTab` only)
- No persistent background scripts
- Clear privacy-focused description
- User-initiated actions only

### Performance Optimizations
- Content script only loads on user action
- Text truncation prevents token overflow
- Local credit tracking reduces API calls
- Minimal DOM manipulation

### Next Steps
1. **Replace placeholder icons** with actual PNG files
2. **Connect to real backend API** (update URL in `background.js`)
3. **Add user authentication** for persistent credits
4. **Implement advanced text extraction** for specific news sites
5. **Add vector analysis UI** (authority, emotion, logic breakdown)

## Testing

To test locally:
1. Load extension in Chrome
2. Visit any article-based webpage
3. Open extension popup
4. Click "Scan" to trigger text extraction
5. Check browser console for extracted data

The extension will currently show mock results since the backend API endpoint is placeholder.