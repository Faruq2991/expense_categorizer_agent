import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Optional, Tuple

class VectorMatcherTool:
    def __init__(self, db_path: str = "data/keywords.db", model_name: str = 'all-MiniLM-L6-v2', threshold: float = 0.7):
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.embeddings_cache = self._load_embeddings()
        print(f"VectorMatcherTool initialized. Loaded {len(self.embeddings_cache)} embeddings.")

    def _load_embeddings(self) -> list[Tuple[str, str, np.ndarray]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT keyword, category, embedding FROM keyword_embeddings")
        embeddings_data = []
        for row in cursor.fetchall():
            keyword, category, embedding_blob = row
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            embeddings_data.append((keyword, category, embedding))
        conn.close()
        return embeddings_data

    def get_best_match(self, text: str) -> Optional[Tuple[str, float]]:
        if not self.embeddings_cache:
            print("No embeddings loaded for vector matching.")
            return None

        text_embedding = self.model.encode(text)
        
        best_match_category = None
        highest_similarity = -1.0

        for keyword, category, stored_embedding in self.embeddings_cache:
            similarity = cosine_similarity([text_embedding], [stored_embedding])[0][0]
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match_category = category
        
        if highest_similarity >= self.threshold:
            print(f"Vector Match: '{text}' -> '{best_match_category}' with similarity {highest_similarity:.2f}")
            return best_match_category, highest_similarity
        else:
            print(f"Vector Match: No confident match for '{text}'. Highest similarity: {highest_similarity:.2f} (Threshold: {self.threshold})")
            return None
