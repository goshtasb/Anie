// content.js - Anie Robust Text Extractor with Safety Net Protocol
// Strips ads, nav, comments, and noise to extract pure journalism
// V2.2: 3-tier fallback + SPA retry support (retry handled by popup.js)

(function() {
    /**
     * EXTRACT CANONICAL URL (The Universal ID)
     */
    function getCanonicalUrl() {
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical && canonical.href) return canonical.href;

        const ogUrl = document.querySelector('meta[property="og:url"]');
        if (ogUrl && ogUrl.content) return ogUrl.content;

        return window.location.href.split('?')[0].split('#')[0];
    }

    /**
     * TEXT CLEANER
     */
    function cleanText(text) {
        return text
            .replace(/\t/g, ' ')
            .replace(/\s+/g, ' ')
            .replace(/\n\s*\n/g, '\n\n')
            .trim();
    }

    /**
     * ROBUST EXTRACTION - "THE SAFETY NET PROTOCOL"
     * Plan A: Surgical (find article body)
     * Plan B: Paragraph aggregation
     * Plan C: Nuclear (raw body text)
     */
    function getMainContent() {
        const clone = document.body.cloneNode(true);

        // Remove noise elements
        const noiseSelectors = [
            'script', 'style', 'noscript', 'iframe', 'svg', 'canvas',
            'nav', 'footer', 'header', 'aside',
            '.ad', '.ads', '.advertisement', '.ad-container', '.ad-wrapper',
            '[class*="advert"]', '[id*="advert"]',
            '.social-share', '.share-buttons', '.social-links',
            '.comments', '.comment-section', '.disqus', '#comments',
            '.related-articles', '.recommended', '.trending', '.popular',
            '.newsletter-signup', '.popup', '.modal', '.cookie-banner',
            '.subscription-prompt', '.paywall',
            '[aria-hidden="true"]',
            '[role="complementary"]', '[role="navigation"]', '[role="banner"]',
            '[role="contentinfo"]',
            '[class*="stock"]', '[class*="ticker"]', '[class*="quote"]',
            '[class*="market"]', '[class*="price"]', '[class*="chart"]',
            '[data-symbol]', '[data-ticker]',
            '.stock-widget', '.market-data', '.quote-widget'
        ];

        noiseSelectors.forEach(selector => {
            try {
                clone.querySelectorAll(selector).forEach(el => el.remove());
            } catch (e) {}
        });

        // --- STRATEGY 1: SURGICAL ---
        const articleSelectors = [
            // Business Insider specific
            '[data-component="text-block"]',
            '[data-module="TextBlock"]',
            '.content-lock-content',
            '.article-body-content',
            '.post-content-body',
            '.premium-content',
            '[class*="ArticleBody"]',
            '[class*="articleBody"]',
            '[class*="article-body"]',
            '[class*="post-content"]',
            // Standard semantic
            '[itemprop="articleBody"]',
            'article',
            // Common CMS patterns
            '.story-body', '.article-body', '.article-content',
            '.post-content', '.entry-content', '#article-body',
            '.main-content', '.article__body',
            '[data-testid="article-body"]',
            '.story-content', '.body-content',
            // Structural
            '[role="main"]', 'main', '#main-content', '#content'
        ];

        let extractedText = "";

        for (const selector of articleSelectors) {
            try {
                const target = clone.querySelector(selector);
                if (target && target.innerText && target.innerText.length > 500) {
                    extractedText = target.innerText;
                    console.log("Acuity: Surgical extraction via:", selector);
                    break;
                }
            } catch (e) {}
        }

        // --- STRATEGY 2: PARAGRAPH AGGREGATION ---
        if (extractedText.length < 500) {
            console.log("Acuity: Surgical too short, trying paragraphs...");
            const paragraphs = Array.from(clone.querySelectorAll('p'));
            const goodParagraphs = paragraphs
                .map(p => p.innerText.trim())
                .filter(text => text.length > 40);

            if (goodParagraphs.length > 0) {
                extractedText = goodParagraphs.join('\n\n');
                console.log("Acuity: Found", goodParagraphs.length, "paragraphs");
            }
        }

        // --- STRATEGY 3: NUCLEAR ---
        if (extractedText.length < 300) {
            console.log("Acuity: Using raw body extraction");
            extractedText = clone.innerText;
        }

        return cleanText(extractedText);
    }

    // Execute extraction
    const content = getMainContent();
    console.log("Acuity: Extracted", content.length, "chars");

    return {
        url: getCanonicalUrl(),
        title: document.title,
        domain: window.location.hostname,
        text: content.substring(0, 15000)
    };
})();
