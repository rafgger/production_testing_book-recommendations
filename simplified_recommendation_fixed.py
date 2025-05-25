"""
Simplified Book Recommendation System Implementation

This script implements a content-based filtering approach for book recommendations
with memory efficiency in mind. It focuses on providing recommendations based on
book metadata similarity.
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import kagglehub
from kagglehub import KaggleDatasetAdapter
import gc  # Garbage collector for memory management

# Data Loading Functions
def load_dataset():
    """Load the book recommendation dataset from Kaggle"""
    print("Loading dataset...")
    
    # Load books data
    books_df = pd.read_csv('Books.csv')#, encoding='ISO-8859-1', on_bad_lines='skip')
    # kagglehub.load_dataset(
    #     KaggleDatasetAdapter.PANDAS,
    #     "arashnic/book-recommendation-dataset",
    #     "Books.csv"
    # )
    
    print("Books dataset loaded successfully!")
    return books_df

# Data Preprocessing Functions
def preprocess_data(books_df, sample_size=10000, query_books=None):
    """Preprocess the dataset for memory-efficient recommendation algorithms"""
    print("Preprocessing data...")
    
    # Ensure query books are in our dataset before sampling
    query_books_df = pd.DataFrame()
    if query_books:
        for query in query_books:
            query_lower = query.lower()
            matching_books = books_df[books_df['Book-Title'].str.lower().str.contains(query_lower)]
            if not matching_books.empty:
                query_books_df = pd.concat([query_books_df, matching_books])
    
    # Sample from remaining books to reduce memory usage
    if not query_books_df.empty:
        other_books = books_df[~books_df.index.isin(query_books_df.index)]
    else:
        other_books = books_df
        
    if len(other_books) > sample_size:
        sampled_books = other_books.sample(sample_size, random_state=42)
        # Combine query books with sampled books
        if not query_books_df.empty:
            books_df = pd.concat([query_books_df, sampled_books])
        else:
            books_df = sampled_books
    
    # Clean book titles (remove special characters, convert to lowercase)
    books_df['Book-Title'] = books_df['Book-Title'].str.lower()
    books_df['Book-Title'] = books_df['Book-Title'].apply(lambda x: re.sub(r'[^\w\s]', '', str(x)))
    
    # Clean author names
    books_df['Book-Author'] = books_df['Book-Author'].str.lower()
    books_df['Book-Author'] = books_df['Book-Author'].apply(lambda x: re.sub(r'[^\w\s]', '', str(x)))
    
    # Convert Year-Of-Publication to numeric, handling errors
    books_df['Year-Of-Publication'] = pd.to_numeric(books_df['Year-Of-Publication'], errors='coerce')
    
    # Create a combined feature for content-based filtering
    books_df['combined_features'] = books_df['Book-Title'] + ' ' + books_df['Book-Author'] + ' ' + books_df['Publisher'].fillna('')
    
    print(f"Data preprocessing completed! Working with {len(books_df)} books.")
    
    # Print info about query books in the dataset
    if query_books:
        for query in query_books:
            query_lower = query.lower()
            count = len(books_df[books_df['Book-Title'].str.contains(query_lower)])
            print(f"'{query}' books in dataset: {count}")
    
    return books_df

# Content-Based Filtering Implementation
class ContentBasedRecommender:
    """Content-based book recommendation system"""
    
    def __init__(self, books_df, max_features=5000):
        """Initialize the recommender with books dataframe"""
        self.books_df = books_df
        self.max_features = max_features  # Limit vocabulary size
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english', 
            max_features=max_features,  # Limit features to save memory
            dtype=np.float32  # Use float32 instead of float64 to save memory
        )
        self.tfidf_matrix = None
        
    def fit(self):
        """Create the TF-IDF matrix"""
        print("Fitting content-based recommender...")
        
        # Create TF-IDF matrix
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.books_df['combined_features'])
            
        print(f"Content-based recommender fitted with {self.tfidf_matrix.shape[1]} features!")
        
    def get_recommendations(self, book_title, top_n=10):
        """
        Recommend books similar to the given book title
        
        Args:
            book_title (str): Title of the book to find recommendations for
            top_n (int): Number of recommendations to return
            
        Returns:
            list: List of recommended book titles
        """
        # Clean and standardize the input book title
        book_title = book_title.lower()
        book_title = re.sub(r'[^\w\s]', '', book_title)
        
        # Find the book in our dataset
        matching_books = self.books_df[self.books_df['Book-Title'].str.contains(book_title)]
        
        if matching_books.empty:
            print(f"Book '{book_title}' not found in the dataset.")
            # Return popular books as fallback
            popular_books = self.books_df.head(top_n)
            recommendations = []
            for _, book in popular_books.iterrows():
                book_info = {
                    'title': book['Book-Title'],
                    'author': book['Book-Author'],
                    'year': book['Year-Of-Publication'],
                    'image_url': book.get('Image-URL-M', '/static/images/placeholder.png'),
                    'similarity_score': 0.0,
                    'note': 'Fallback recommendation (query not found)'
                }
                recommendations.append(book_info)
            return recommendations
        
        # Use the first matching book
        book_idx = matching_books.index[0]
        
        # Get the book vector
        book_vector = self.tfidf_matrix[book_idx:book_idx+1]
        
        # Compute similarity with all other books
        # Using batch processing to avoid memory issues
        batch_size = 1000
        n_books = self.tfidf_matrix.shape[0]
        n_batches = (n_books + batch_size - 1) // batch_size
        
        similarities = []
        for i in range(n_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, n_books)
            
            # Skip empty batches
            if start_idx >= n_books or start_idx >= end_idx:
                continue
                
            try:
                # Compute cosine similarity for this batch
                batch_sim = cosine_similarity(
                    book_vector, 
                    self.tfidf_matrix[start_idx:end_idx]
                ).flatten()
                
                # Store indices and similarities
                for j, sim in enumerate(batch_sim):
                    if start_idx + j != book_idx:  # Skip the book itself
                        similarities.append((start_idx + j, sim))
            except ValueError as e:
                print(f"Error processing batch {i}: {e}")
                continue
            
            # Force garbage collection after each batch
            gc.collect()
        
        # Sort by similarity and get top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similarities = similarities[:top_n]
        
        # If no similar books found, return fallback recommendations
        if not top_similarities:
            print(f"No similar books found for '{book_title}'.")
            # Return popular books as fallback
            popular_books = self.books_df.head(top_n)
            recommendations = []
            for _, book in popular_books.iterrows():
                if book.name != book_idx:  # Skip the query book
                    book_info = {
                        'title': book['Book-Title'],
                        'author': book['Book-Author'],
                        'year': book['Year-Of-Publication'],
                        'image_url': book.get('Image-URL-M', '/static/images/placeholder.png'),
                        'similarity_score': 0.0,
                        'note': 'Fallback recommendation (no similar books found)'
                    }
                    recommendations.append(book_info)
            return recommendations[:top_n]
        
        # Return recommended books with similarity scores
        recommendations = []
        for idx, sim in top_similarities:
            book = self.books_df.iloc[idx]
            book_info = {
                'title': book['Book-Title'],
                'author': book['Book-Author'],
                'year': book['Year-Of-Publication'],
                'image_url': book.get('Image-URL-M', '/static/images/placeholder.png'),
                'similarity_score': sim
            }
            recommendations.append(book_info)

        return recommendations

# Function to try different query books
def get_recommendations_for_queries(recommender, queries):
    """Get recommendations for multiple query books"""
    results = {}
    
    for query in queries:
        print(f"\nGetting recommendations for '{query}':")
        
        try:
            recommendations = recommender.get_recommendations(query)
            for i, rec in enumerate(recommendations, 1):
                similarity = rec.get('similarity_score', 0.0)
                note = rec.get('note', '')
                print(f"{i}. {rec['title']} by {rec['author']} ({rec['year']}) - Similarity: {similarity:.4f} {note}")
            
            results[query] = recommendations
            
            # Save recommendations to file
            with open(f'/home/ubuntu/{query.replace(" ", "_")}_recommendations.txt', 'w') as f:
                f.write(f"Content-Based Recommendations for '{query}':\n\n")
                
                for i, rec in enumerate(recommendations, 1):
                    similarity = rec.get('similarity_score', 0.0)
                    note = rec.get('note', '')
                    f.write(f"{i}. {rec['title']} by {rec['author']} ({rec['year']}) - Similarity: {similarity:.4f} {note}\n")
        except Exception as e:
            print(f"Error getting recommendations for '{query}': {e}")
            results[query] = []
    
    return results

# Main function to run the recommendation system
def main():
    """Main function to run the simplified book recommendation system"""
    # Load dataset
    books_df = load_dataset()
    
    # Define query books
    queries = ["Lord of the Rings", "Harry Potter", "Pride and Prejudice"]
    
    # Preprocess data with sampling for memory efficiency
    sample_size = 10000  # Adjust based on available memory
    books_df = preprocess_data(books_df, sample_size=sample_size, query_books=queries)
    
    # Initialize and fit content-based recommender
    recommender = ContentBasedRecommender(books_df, max_features=3000)
    recommender.fit()
    
    # Get recommendations for query books
    results = get_recommendations_for_queries(recommender, queries)
    
    # Save a summary of the approach
    with open('/home/ubuntu/recommendation_approach_summary.md', 'w') as f:
        f.write("# Book Recommendation System: Approach Summary\n\n")
        
        f.write("## Implementation Approach\n")
        f.write("This implementation uses a content-based filtering approach to recommend books similar to a given query book. ")
        f.write("The system analyzes book metadata (title, author, publisher) to find books with similar characteristics.\n\n")
        
        f.write("## Memory Efficiency Techniques\n")
        f.write("1. **Data Sampling**: Working with a subset of the full dataset to reduce memory requirements\n")
        f.write("2. **Batch Processing**: Computing similarities in batches to avoid loading the entire similarity matrix into memory\n")
        f.write("3. **Feature Limitation**: Restricting the TF-IDF vectorizer to a maximum number of features\n")
        f.write("4. **Data Type Optimization**: Using float32 instead of float64 to reduce memory usage\n")
        f.write("5. **Garbage Collection**: Explicitly calling the garbage collector after memory-intensive operations\n\n")
        
        f.write("## Limitations\n")
        f.write("1. **Limited Dataset**: Using a sample of the full dataset means some potentially relevant books may be excluded\n")
        f.write("2. **Content-Only Approach**: This implementation relies solely on book metadata and doesn't incorporate user ratings\n")
        f.write("3. **Cold Start Problem**: New books without established metadata would be difficult to recommend\n")
        f.write("4. **Limited Features**: Only using title, author, and publisher may miss other important book characteristics\n\n")
        
        f.write("## Potential Improvements\n")
        f.write("1. **Hybrid Approach**: Combining content-based filtering with collaborative filtering for better recommendations\n")
        f.write("2. **Additional Features**: Incorporating book descriptions, genres, or tags for richer content analysis\n")
        f.write("3. **Distributed Computing**: Using technologies like Spark for processing the full dataset\n")
        f.write("4. **Advanced Algorithms**: Implementing matrix factorization or deep learning approaches for better recommendations\n")
        f.write("5. **Evaluation Framework**: Adding quantitative evaluation metrics to measure recommendation quality\n\n")
        
        f.write("## Production Considerations\n")
        f.write("For a production environment, the system would need:\n")
        f.write("1. **Scalable Infrastructure**: Cloud-based or distributed computing resources\n")
        f.write("2. **Incremental Updates**: Ability to update the model as new books are added\n")
        f.write("3. **API Layer**: RESTful API for client applications to request recommendations\n")
        f.write("4. **Caching**: Caching popular recommendations to improve response time\n")
        f.write("5. **Monitoring**: Performance and quality monitoring systems\n")
    
    return recommender, results

if __name__ == "__main__":
    main()
