"""
Utility functions for neural features with graceful degradation
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None
    logger.warning("NumPy not available - neural features will be limited")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    TfidfVectorizer = None
    cosine_similarity = None
    KMeans = None
    logger.warning("Scikit-learn not available - neural features will be limited")

try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    tf = None
    logger.warning("TensorFlow not available - neural features will be limited")

class NeuralProcessor:
    """
    Neural processing with fallback for missing dependencies
    """
    
    def __init__(self):
        self.available_features = {
            'text_analysis': HAS_NUMPY and HAS_SKLEARN,
            'clustering': HAS_NUMPY and HAS_SKLEARN,
            'neural_network': HAS_TENSORFLOW,
            'feature_extraction': HAS_NUMPY and HAS_SKLEARN
        }
    
    def extract_text_features(self, texts: List[str]) -> Optional[List]:
        """
        Extract text features using TF-IDF with fallback
        """
        if not self.available_features['feature_extraction']:
            logger.warning("Feature extraction not available - returning simple text lengths")
            return [len(text) for text in texts]
        
        try:
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            features = vectorizer.fit_transform(texts)
            return features.toarray().tolist()
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return [len(text) for text in texts]
    
    def cluster_texts(self, texts: List[str], n_clusters: int = 5) -> List[int]:
        """
        Cluster texts with fallback
        """
        if not self.available_features['clustering']:
            logger.warning("Clustering not available - returning random clusters")
            return [i % n_clusters for i in range(len(texts))]
        
        try:
            features = self.extract_text_features(texts)
            if features is None:
                return [0] * len(texts)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(features)
            return clusters.tolist()
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return [0] * len(texts)
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Simple sentiment analysis with fallback
        """
        if not self.available_features['text_analysis']:
            # Simple rule-based sentiment
            positive_words = ['good', 'great', 'awesome', 'amazing', 'love', 'like', 'happy']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'sad', 'angry']
            
            words = text.lower().split()
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            if positive_count > negative_count:
                sentiment = 'positive'
            elif negative_count > positive_count:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'confidence': 0.5,
                'positive_score': positive_count / len(words) if words else 0,
                'negative_score': negative_count / len(words) if words else 0
            }
        
        # Would implement more sophisticated sentiment analysis here
        # For now, return the same rule-based approach
        return self.analyze_sentiment(text)
    
    def get_user_recommendations(self, user_id: str, user_features: Dict) -> List[str]:
        """
        Get user recommendations with fallback
        """
        if not self.available_features['neural_network']:
            logger.warning("Neural recommendations not available - returning popular content")
            return ['popular_content_1', 'popular_content_2', 'popular_content_3']
        
        # Would implement neural network recommendations here
        return ['neural_recommendation_1', 'neural_recommendation_2', 'neural_recommendation_3']

# Global processor instance
neural_processor = NeuralProcessor()

def is_neural_available() -> bool:
    """Check if neural features are available"""
    return any(neural_processor.available_features.values())

def get_available_features() -> Dict[str, bool]:
    """Get available neural features"""
    return neural_processor.available_features.copy()
