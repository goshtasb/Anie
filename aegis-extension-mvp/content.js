// content.js - Anie Surgical Text Extractor
// Strips ads, nav, comments, and noise to extract pure journalism

(function() {
    /**
     * EXTRACT CANONICAL URL (The Universal ID)
     * This is the "True Name" of the article, ignoring ?utm_source, ?ref, etc.
     */
    function getCanonicalUrl() {
        // 1. Try the official canonical meta tag
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical && canonical.href) return canonical.href;

        // 2. Try Open Graph URL (common on news sites)
        const ogUrl = document.querySelector('meta[property="og:url"]');
        if (ogUrl && ogUrl.content) return ogUrl.content;

        // 3. Fallback: Strip search params and hash from current URL
        return window.location.href.split('?')[0].split('#')[0];
    }

    /**
     * SURGICAL TEXT EXTRACTION (The "Noise Filter")
     * Clones the DOM and aggressively cuts out non-journalistic content.
     */
    function getMainContent() {
        // 1. Clone the body so we don't break the user's visible page
        const clone = document.body.cloneNode(true);

        // 2. Define the "Noise" Selectors (Ads, Nav, Popups, Clickbait)
        const noiseSelectors = [
            // Technical elements
            'script', 'style', 'noscript', 'iframe', 'svg', 'canvas',
            // Structural noise
            'nav', 'footer', 'header', 'aside',
            // Ad-related
            '.ad', '.ads', '.advertisement', '.ad-container', '.ad-wrapper',
            '[class*="advert"]', '[id*="advert"]',
            // Social/sharing
            '.social-share', '.share-buttons', '.social-links',
            // Comments
            '.comments', '.comment-section', '.disqus', '#comments',
            // Related content (clickbait)
            '.related-articles', '.recommended', '.trending', '.popular',
            // Popups and banners
            '.newsletter-signup', '.popup', '.modal', '.cookie-banner',
            '.subscription-prompt', '.paywall',
            // ARIA hidden (invisible to users anyway)
            '[aria-hidden="true"]',
            // Semantic roles for non-content
            '[role="complementary"]', '[role="navigation"]', '[role="banner"]',
            '[role="contentinfo"]',
            // Stock tickers and financial widgets (real-time data, not article content)
            '[class*="stock"]', '[class*="ticker"]', '[class*="quote"]',
            '[class*="market"]', '[class*="price"]', '[class*="chart"]',
            '[data-symbol]', '[data-ticker]',
            '.stock-widget', '.market-data', '.quote-widget',
            '[class*="Stock"]', '[class*="Ticker"]', '[class*="Quote"]'
        ];

        // 3. Cut them out
        noiseSelectors.forEach(selector => {
            try {
                const elements = clone.querySelectorAll(selector);
                elements.forEach(el => el.remove());
            } catch (e) {
                // Invalid selector, skip
            }
        });

        // 4. Identify the "Organ" (The actual Article Body)
        // Priority order: most specific to least specific
        const article = clone.querySelector('[itemprop="articleBody"]') ||
                        clone.querySelector('article') ||
                        clone.querySelector('.article-body') ||
                        clone.querySelector('.story-body') ||
                        clone.querySelector('.article-content') ||
                        clone.querySelector('.post-content') ||
                        clone.querySelector('.entry-content') ||
                        clone.querySelector('main') ||
                        clone;

        // 5. Extract and Normalize
        let text = article.innerText || '';

        // Normalize whitespace
        text = text
            .replace(/\t/g, ' ')           // Replace tabs with spaces
            .replace(/ +/g, ' ')           // Collapse multiple spaces
            .replace(/\n\s*\n\s*\n/g, '\n\n') // Max 2 newlines
            .trim();

        return text;
    }

    // 6. Construct Payload
    const payload = {
        url: getCanonicalUrl(),
        title: document.title,
        domain: window.location.hostname,
        // Send the surgically cleaned text (max 15k chars)
        text: getMainContent().substring(0, 15000)
    };

    return payload;
})();
