"""
Service de reranking pour améliorer la pertinence des résultats de recherche.
Utilise un modèle cross-encoder pour scorer la pertinence query-document.
"""
from typing import List, Tuple
from sentence_transformers import CrossEncoder
from app.models.document import DocumentChunk


class RerankerService:
    """
    Service de reranking avec cross-encoder.
    Améliore la précision du retrieval en réordonnant les chunks par pertinence réelle.
    """
    
    def __init__(self):
        # Modèle cross-encoder multilingue optimisé pour FR/EN
        # ms-marco-MiniLM est rapide et performant
        print("🔄 Chargement du modèle de reranking...")
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("✅ Modèle de reranking chargé")
    
    def rerank(
        self, 
        query: str, 
        chunks: List[DocumentChunk], 
        similarity_scores: List[float],
        top_k: int = None
    ) -> Tuple[List[DocumentChunk], List[float]]:
        """
        Rerank les chunks en fonction de leur pertinence réelle avec la query.
        
        Args:
            query: Question de l'utilisateur
            chunks: Liste des chunks récupérés
            similarity_scores: Scores de similarité vectorielle originaux
            top_k: Nombre de résultats à garder (None = tous)
        
        Returns:
            (chunks réordonnés, nouveaux scores)
        """
        if not chunks:
            return chunks, similarity_scores
        
        # Préparer les paires (query, document) pour le cross-encoder
        pairs = [[query, chunk.content] for chunk in chunks]
        
        # Scorer avec le cross-encoder (score entre -10 et +10 environ)
        print(f"🔄 Reranking de {len(chunks)} chunks...")
        cross_scores = self.model.predict(pairs)
        
        # Combiner chunks avec leurs nouveaux scores
        chunk_score_pairs = list(zip(chunks, cross_scores))
        
        # Trier par score décroissant
        chunk_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Limiter au top_k si spécifié
        if top_k:
            chunk_score_pairs = chunk_score_pairs[:top_k]
        
        # Séparer chunks et scores
        reranked_chunks = [pair[0] for pair in chunk_score_pairs]
        reranked_scores = [float(pair[1]) for pair in chunk_score_pairs]
        
        print(f"✅ Reranking terminé. Score max: {max(reranked_scores):.3f}, min: {min(reranked_scores):.3f}")
        
        return reranked_chunks, reranked_scores
