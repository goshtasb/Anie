// content.js - Aegis/Anie Content Extractor

(function() {
    // 1. EXTRACT CANONICAL URL (The Stable Identity)
    // This NEVER changes regardless of ads, tracking params, or refreshes
    function getCanonicalUrl() {
        // Priority 1: <link rel="canonical"> - The article's True Name
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

    // 2. EXTRACT ARTICLE TEXT (Clean - avoids sidebar/ad noise)
    function getMainContent() {
        // Try to find the specific article body to avoid Sidebar/Footer noise
        const article = document.querySelector('article') ||
                        document.querySelector('[itemprop="articleBody"]') ||
                        document.querySelector('.article-body') ||
                        document.querySelector('.story-body') ||
                        document.querySelector('main');

        if (article) {
            return article.innerText;
        }

        // Fallback: Aggressive filtering - only substantial paragraphs
        const paragraphs = Array.from(document.querySelectorAll('p'));
        const content = paragraphs
            .map(p => p.innerText)
            .filter(text => text.length > 50)
            .join('\n\n');

        return content || document.body.innerText;
    }

    // 3. Build payload with STABLE identity
    const payload = {
        url: getCanonicalUrl(),  // Stable ID - survives refreshes and ad changes
        title: document.title,
        domain: window.location.hostname,
        text: getMainContent().substring(0, 15000)
    };

    return payload;
})();
