from sentence_transformers import SentenceTransformer
import sqlite3
import yaml
import os
import numpy as np

# Load the Sentence Transformer model
# You might want to choose a different model based on your needs
# For a list of models: https://www.sbert.net/docs/pretrained_models.html
model = SentenceTransformer('all-MiniLM-L6-v2')

# Database connection
def get_db_connection():
    conn = sqlite3.connect("data/keywords.db")
    conn.row_factory = sqlite3.Row
    return conn

def generate_and_store_embeddings():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the keyword_embeddings table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keyword_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            embedding BLOB NOT NULL
        );
    """)
    conn.commit()

    keywords_to_embed = []

    # 1. Get keywords from keyword_category table
    cursor.execute("SELECT keyword, category FROM keyword_category")
    for row in cursor.fetchall():
        keywords_to_embed.append((row['keyword'], row['category']))

    # 2. Get keywords/phrases from categories.yaml
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'config', 'categories.yaml'), 'r') as f:
            category_map = yaml.safe_load(f)
            for category, keywords in category_map.items():
                for keyword in keywords:
                    keywords_to_embed.append((keyword, category))
    except FileNotFoundError:
        print("Warning: categories.yaml not found. Skipping YAML keywords.")

    # Remove duplicates
    unique_keywords = {}
    for keyword, category in keywords_to_embed:
        if keyword not in unique_keywords:
            unique_keywords[keyword] = category

    print(f"Found {len(unique_keywords)} unique keywords to embed.")

    # Generate embeddings and store them
    for keyword, category in unique_keywords.items():
        try:
            embedding = model.encode(keyword)
            # Convert numpy array to bytes for storage
            embedding_bytes = embedding.tobytes()

            cursor.execute(
                "INSERT OR REPLACE INTO keyword_embeddings (keyword, category, embedding) VALUES (?, ?, ?)",
                (keyword, category, embedding_bytes)
            )
            print(f"Embedded and stored: {keyword}")
        except Exception as e:
            print(f"Error embedding '{keyword}': {e}")

    conn.commit()
    conn.close()
    print("Embedding generation complete.")

if __name__ == "__main__":
    generate_and_store_embeddings()
