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

    // 2. Extract Metadata
    const payload = {
        title: document.title,
        url: window.location.href,
        domain: window.location.hostname,
        // TRUNCATE to 3000 words to prevent token overflow/cost spikes
        text: getMainContent().substring(0, 15000)
    };

    // 3. Return data to the Popup
    return payload;
})();