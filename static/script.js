async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const resultsContainer = document.getElementById('results');
    
    const query = searchInput.value.trim();
    if (!query) {
        showError('Please enter a search query');
        return;
    }

    // Reset UI
    searchButton.disabled = true;
    loadingIndicator.classList.remove('hidden');
    errorMessage.classList.add('hidden');
    resultsContainer.innerHTML = '';

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();
        console.log('Response data:', data); // Debug log
        
        if (data.error) {
            showError(data.error);
            return;
        }

        // Access curated_items directly since we fixed the backend response
        const results = data.curated_items || [];
        console.log('Parsed results:', results); // Debug log
        
        if (!results || results.length === 0) {
            showError('No results found');
            return;
        }

        // Clear previous results
        resultsContainer.innerHTML = '';

        // Display results
        results.forEach(result => {
            const card = document.createElement('div');
            card.className = 'result-card';
            
            const cardContent = `
                <h3>${result.title || 'Untitled'}</h3>
                ${result.url ? `<a href="${result.url}" target="_blank" class="url-link">${result.url}</a>` : ''}
                ${result.why_selected ? `
                    <div class="selection-reason">
                        <h4>Why Selected:</h4>
                        <p>${result.why_selected}</p>
                    </div>` : ''}
                ${result.quality_score ? `
                    <div class="quality-score">
                        <span class="score-tag">Quality Score: ${result.quality_score}</span>
                    </div>` : ''}
                ${result.relevance_factors?.length ? `
                    <div class="relevance">
                        <h4>Relevance Factors:</h4>
                        <div class="tags">
                            ${result.relevance_factors.map(factor => 
                                `<span class="tag relevance-tag">${factor}</span>`
                            ).join('')}
                        </div>
                    </div>` : ''}
            `;
            
            card.innerHTML = cardContent;
            resultsContainer.appendChild(card);
        });

    } catch (error) {
        console.error('Search error:', error);
        showError('An error occurred while fetching results');
    } finally {
        searchButton.disabled = false;
        loadingIndicator.classList.add('hidden');
    }
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}