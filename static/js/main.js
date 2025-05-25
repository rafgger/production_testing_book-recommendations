async function getRecommendations() {
    const bookTitle = document.getElementById('book-title').value;
    const numRecommendations = document.getElementById('num-recommendations').value;
    const resultsList = document.getElementById('recommendations-list');
    
    if (!bookTitle) {
        alert('Please select a book');
        return;
    }
    
    // Show loading state
    resultsList.innerHTML = '<div class="loading">Loading recommendations...</div>';
    
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                book_title: bookTitle,
                num_recommendations: parseInt(numRecommendations)
            }),
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        displayRecommendations(data.recommendations);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while getting recommendations');
    }
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');
    container.innerHTML = '';
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<div class="no-results">No recommendations found</div>';
        return;
    }
    
    recommendations.forEach((book, index) => {
        const bookCard = document.createElement('div');
        bookCard.className = 'book-card';
        
        const imageUrl = book.image_url || 'https://via.placeholder.com/150x200?text=No+Image';
        
        bookCard.innerHTML = `
            <div class="book-image">
                <img src="${imageUrl}" alt="${book.title}">
            </div>
            <div class="book-info">
                <h3>${book.title}</h3>
                <p class="author">by ${book.author}</p>
                <p class="year">Published: ${book.year}</p>
                <p class="similarity">Similarity: ${(book.similarity_score * 100).toFixed(1)}%</p>
                ${book.note ? `<p class="note">${book.note}</p>` : ''}
            </div>
        `;
        container.appendChild(bookCard);
    });
}

async function loadBookTitles() {
    const select = document.getElementById('book-title');
    select.disabled = true;
    select.innerHTML = '<option value="">Loading book titles...</option>';
    
    try {
        const response = await fetch('/book-titles');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load book titles');
        }
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        if (!data.titles || !data.titles.length) {
            throw new Error('No books found in the database');
        }
        
        select.innerHTML = '<option value="">Select a book...</option>';
        data.titles.forEach(title => {
            const option = document.createElement('option');
            option.value = title;
            option.textContent = title;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading book titles:', error);
        select.innerHTML = '<option value="">Error loading books</option>';
        // Show error message in a more user-friendly way
        const container = document.getElementById('recommendations');
        container.innerHTML = `
            <div class="error-message">
                <p>Error loading book titles: ${error.message}</p>
                <button onclick="loadBookTitles()">Try Again</button>
            </div>
        `;
    } finally {
        select.disabled = false;
    }
}

// Load book titles when the page loads
document.addEventListener('DOMContentLoaded', loadBookTitles);

// Update the displayed value when the range input changes
document.getElementById('num-recommendations').addEventListener('input', function() {
    document.getElementById('num-recommendations-value').textContent = this.value;
});

document.getElementById('recommendation-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    await getRecommendations();
});
