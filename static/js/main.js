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

    // Filter out books with no similarity
    const filteredRecommendations = recommendations.filter(book => book.similarity_score > 0);

    if (!filteredRecommendations || filteredRecommendations.length === 0) {
        container.innerHTML = '<div class="no-results">No recommendations found</div>';
        return;
    }

    filteredRecommendations.forEach((book, index) => {
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
    const datalist = document.getElementById('book-titles');
    datalist.innerHTML = ''; // Clear any placeholder or existing options

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

        const prioritizedTitles = [
            'To Kill a Mockingbird',
            'Lord of the Rings',
            'Harry Potter and the Prisoner of Azkaban'
        ];

        const uniqueTitles = new Set();

        // Add prioritized titles first
        prioritizedTitles.forEach(title => {
            if (!uniqueTitles.has(title)) {
                uniqueTitles.add(title);
                const option = document.createElement('option');
                option.value = title;
                datalist.appendChild(option);
            }
        });

        // Add a horizontal line (visual separation)
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.value = '──────────';
        datalist.appendChild(separator);

        // Add the rest of the titles
        data.titles.forEach(title => {
            if (!uniqueTitles.has(title)) {
                uniqueTitles.add(title);
                const option = document.createElement('option');
                option.value = title;
                datalist.appendChild(option);
            }
        });
    } catch (error) {
        console.error('Error loading book titles:', error);
        datalist.innerHTML = '<option value="Error loading books">';
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
