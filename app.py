from flask import Flask, request, jsonify, render_template, send_from_directory
from simplified_recommendation_fixed import load_dataset, preprocess_data, ContentBasedRecommender
import os

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

# @app.route('/')
# def home():
#     return 'Hello, World!'

# @app.route('/')
# def index():
#     """Serve the main page"""
#     return send_from_directory('static', 'index.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    book_title = data.get('book_title', '')
    num_recommendations = int(data.get('num_recommendations', 5))
    
    if not book_title:
        return jsonify({'error': 'Book title is required'}), 400
    
    try:
        recommendations = recommender.get_recommendations(book_title, top_n=num_recommendations)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
