from flask import Flask, request, jsonify, render_template, send_from_directory
from recommendations import load_dataset, preprocess_data, ContentBasedRecommender
import os
import numpy as np

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')

# Initialize the recommendation system
print("Initializing recommendation system...")
books_df = load_dataset()
books_df = preprocess_data(books_df, sample_size=10000)
recommender = ContentBasedRecommender(books_df, max_features=3000)
recommender.fit()
print("Recommendation system initialized!")

# Cache for book titles
cached_titles = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/book-titles', methods=['GET'])
def book_titles():
    """Endpoint to get all available book titles for the dropdown"""
    global cached_titles
    try:
        if cached_titles is None:
            if 'Book-Title' not in books_df.columns:
                return jsonify({'error': 'Book-Title column not found in dataset'}), 400

            titles = books_df['Book-Title'].dropna().unique().tolist()
            cached_titles = sorted(titles)[:30000]  # Limit to 1000 titles for performance

        return jsonify({'titles': cached_titles})
    except Exception as e:
        print(f"Error in /book-titles endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    book_title = data.get('book_title', '')
    num_recommendations = int(data.get('num_recommendations', 5))

    if not book_title:
        return jsonify({'error': 'Book title is required'}), 400

    try:
        # Dynamically preprocess the dataset and initialize the recommender
        books_df = preprocess_data(load_dataset(), sample_size=10000, query_books=[book_title])
        dynamic_recommender = ContentBasedRecommender(books_df, max_features=3000)
        dynamic_recommender.fit()

        # Get recommendations
        recommendations = dynamic_recommender.get_recommendations(book_title, top_n=num_recommendations)

        # Convert float32 and int64 values to standard Python types for JSON serialization
        recommendations = [{key: (float(value) if isinstance(value, np.float32) else int(value) if isinstance(value, np.int64) else value) for key, value in rec.items()} for rec in recommendations]

        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
