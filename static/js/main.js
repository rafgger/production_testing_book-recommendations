async function getRecommendations() {
    const bookTitle = document.getElementById('bookTitle').value;
    const numRecommendations = document.getElementById('numRecommendations').value;
    
    if (!bookTitle) {
        alert('Please enter a book title');
        return;
    }
    
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
    const container = document.getElementById('recommendations');
    container.innerHTML = '';
    
    recommendations.forEach((book, index) => {
        const bookCard = document.createElement('div');
        bookCard.className = 'book-card';
        bookCard.innerHTML = `
            <img src="${book.image_url}" alt="${book.title}" style="max-width: 100px; height: 150px; object-fit: contain;">
            <h3>${index + 1}. ${book.title}</h3>
            <p><strong>Author:</strong> ${book.author}</p>
            <p><strong>Year:</strong> ${book.year}</p>
            <p><strong>Similarity:</strong> ${book.similarity_score.toFixed(4)}</p>
            ${book.note ? `<p><em>${book.note}</em></p>` : ''}
        `;
        container.appendChild(bookCard);
    });
}
