// content.js
(function() {
    // 1. Heuristic: Find the biggest text container
    function getMainContent() {
        // Try to find semantic tags first
        const article = document.querySelector('article');
        if (article) return article.innerText;

        const main = document.querySelector('main');
        if (main) return main.innerText;

        // Fallback: Get all paragraphs and join them
        const paragraphs = Array.from(document.querySelectorAll('p'));
        // Filter out tiny snippets (ads, nav links)
        const content = paragraphs
            .map(p => p.innerText)
            .filter(text => text.length > 50)
            .join('\n\n');

        return content || document.body.innerText; // Last resort
    }

    // 2. Get Canonical URL (strips tracking garbage)
    function getCanonicalUrl() {
        // Priority 1: <link rel="canonical"> - the article's "True Name"
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical && canonical.href) {
            return canonical.href;
        }

        // Priority 2: og:url meta tag (common on news sites)
        const ogUrl = document.querySelector('meta[property="og:url"]');
        if (ogUrl && ogUrl.content) {
            return ogUrl.content;
        }

        // Priority 3: Strip query params from current URL
        const url = new URL(window.location.href);
        return url.origin + url.pathname;
    }

    // 3. Extract Metadata
    const payload = {
        title: document.title,
        url: getCanonicalUrl(),  // Clean URL for consistent caching
        domain: window.location.hostname,
        // TRUNCATE to 3000 words to prevent token overflow/cost spikes
        text: getMainContent().substring(0, 15000)
    };

    // 4. Return data to the Popup
    return payload;
})();