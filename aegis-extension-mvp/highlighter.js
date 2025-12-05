// highlighter.js - Anie In-Page Evidence Highlighter
// Applies forensic highlights to flagged text in the article

(function() {
    // Prevent double-initialization
    if (window.__ANIE_HIGHLIGHTER_LOADED__) return;
    window.__ANIE_HIGHLIGHTER_LOADED__ = true;

    /**
     * HIGHLIGHT PHRASES IN THE DOM
     * Uses TreeWalker to find text nodes and wrap matches in styled spans
     */
    function highlightPhrases(evidence) {
        if (!evidence || evidence.length === 0) return { count: 0 };

        let highlightCount = 0;

        // Process each evidence item
        evidence.forEach(item => {
            const phrase = cleanPhrase(item.text);
            if (!phrase || phrase.length < 10) return; // Skip very short phrases

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

        console.log(`Anie: Applied ${highlightCount} highlights`);
        return { count: highlightCount };
    }

    /**
     * CLEAN UP PHRASE for fuzzy matching
     */
    function cleanPhrase(text) {
        if (!text) return '';
        return text
            .replace(/^["'""'']+|["'""'']+$/g, '') // Remove surrounding quotes
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim();
    }

    /**
     * FIND TEXT MATCHES using TreeWalker
     * Returns array of {node, startIndex, endIndex}
     */
    function findTextMatches(phrase) {
        const matches = [];
        const lowerPhrase = phrase.toLowerCase();

        // Use TreeWalker to iterate through all text nodes
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    // Skip script, style, and already-highlighted content
                    const parent = node.parentElement;
                    if (!parent) return NodeFilter.FILTER_REJECT;

                    const tagName = parent.tagName.toLowerCase();
                    if (['script', 'style', 'noscript', 'textarea', 'input'].includes(tagName)) {
                        return NodeFilter.FILTER_REJECT;
                    }

                    // Skip our own highlights
                    if (parent.className && parent.className.includes('anie-highlight')) {
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

            // Try exact match first
            let index = lowerText.indexOf(lowerPhrase);
            if (index !== -1) {
                matches.push({
                    node: node,
                    startIndex: index,
                    endIndex: index + phrase.length
                });
                continue;
            }

            // Try fuzzy match (first 30 chars)
            if (phrase.length > 30) {
                const fuzzyPhrase = lowerPhrase.substring(0, 30);
                index = lowerText.indexOf(fuzzyPhrase);
                if (index !== -1) {
                    // Find end of sentence or phrase boundary
                    let endIndex = Math.min(index + phrase.length, text.length);
                    matches.push({
                        node: node,
                        startIndex: index,
                        endIndex: endIndex
                    });
                }
            }
        }

        return matches;
    }

    /**
     * WRAP TEXT NODE with highlight span
     * Non-destructive: preserves original text structure
     */
    function wrapTextNode(textNode, startIndex, endIndex, severity, reason) {
        const text = textNode.nodeValue;
        const parent = textNode.parentNode;

        // Safety checks
        if (!parent || parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE') return;
        if (parent.className && parent.className.includes('anie-highlight')) return;

        // Create document fragment for replacement
        const fragment = document.createDocumentFragment();

        // Text before highlight
        if (startIndex > 0) {
            fragment.appendChild(document.createTextNode(text.substring(0, startIndex)));
        }

        // The highlighted span
        const span = document.createElement('span');
        const highlightClass = severity === 'critical' ? 'anie-highlight-critical' :
                              severity === 'killer' ? 'anie-highlight-critical anie-highlight-killer' :
                              'anie-highlight-warning';
        span.className = highlightClass;
        span.setAttribute('data-anie-reason', reason || 'Flagged by Anie');
        span.textContent = text.substring(startIndex, endIndex);
        fragment.appendChild(span);

        // Text after highlight
        if (endIndex < text.length) {
            fragment.appendChild(document.createTextNode(text.substring(endIndex)));
        }

        // Replace the original text node
        parent.replaceChild(fragment, textNode);
    }

    /**
     * CLEAR ALL HIGHLIGHTS
     * Removes all Anie highlights from the page
     */
    function clearHighlights() {
        const highlights = document.querySelectorAll('[class*="anie-highlight"]');
        highlights.forEach(el => {
            const text = el.textContent;
            el.replaceWith(document.createTextNode(text));
        });
        console.log('Anie: Cleared all highlights');
    }

    // LISTENER: Wait for messages from popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "HIGHLIGHT_EVIDENCE") {
            const result = highlightPhrases(request.evidence);
            sendResponse({ status: "success", ...result });
            return true;
        }

        if (request.action === "CLEAR_HIGHLIGHTS") {
            clearHighlights();
            sendResponse({ status: "cleared" });
            return true;
        }
    });

    console.log('Anie Highlighter: Ready');
})();
