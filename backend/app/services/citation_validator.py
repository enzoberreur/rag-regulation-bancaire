"""
Service de validation des citations pour détecter les hallucinations.
Vérifie que toutes les citations <mark> correspondent à du texte réel dans le contexte.
"""
import re
from typing import List, Dict
from difflib import SequenceMatcher
from app.models.document import DocumentChunk


class CitationValidator:
    """
    Valide que les citations dans la réponse du LLM sont correctes.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Args:
            strict_mode: Si True, utilise exact match uniquement. 
                        Si False, accepte fuzzy match à 90%+
        """
        self.strict_mode = strict_mode
    
    def validate_response(
        self, 
        response_text: str, 
        context_chunks: List[DocumentChunk]
    ) -> Dict[str, any]:
        """
        Vérifie que toutes les citations <mark> sont dans le contexte.
        
        Args:
            response_text: Réponse générée par le LLM (HTML avec <mark> tags)
            context_chunks: Chunks utilisés comme contexte
        
        Returns:
            {
                "is_valid": bool,  # True si toutes les citations sont valides
                "total_citations": int,  # Nombre total de citations
                "valid_citations": int,  # Nombre de citations valides
                "invalid_citations": List[str],  # Texte des citations invalides
                "warnings": List[str],  # Avertissements (fuzzy matches)
                "hallucination_rate": float,  # % de citations invalides
                "details": List[Dict]  # Détails pour chaque citation
            }
        """
        # Extraire toutes les citations <mark>
        citations = self._extract_citations(response_text)
        
        if not citations:
            return {
                "is_valid": True,
                "total_citations": 0,
                "valid_citations": 0,
                "invalid_citations": [],
                "warnings": [],
                "hallucination_rate": 0.0,
                "details": []
            }
        
        # Construire un texte unique avec tout le contexte
        full_context = "\n\n".join([chunk.content for chunk in context_chunks])
        
        # Valider chaque citation
        valid_count = 0
        invalid_citations = []
        warnings = []
        details = []
        
        for citation in citations:
            citation_text = citation["text"]
            citation_source = citation["source"]
            
            # Vérifier si la citation existe dans le contexte
            validation = self._validate_single_citation(citation_text, full_context, context_chunks)
            
            details.append({
                "text": citation_text[:100],  # Preview
                "source": citation_source,
                "is_valid": validation["found"],
                "match_type": validation["match_type"],
                "match_ratio": validation["match_ratio"],
                "found_in_chunk": validation["chunk_index"]
            })
            
            if validation["found"]:
                valid_count += 1
                if validation["match_type"] == "fuzzy":
                    warnings.append(
                        f"Citation approximative (match {validation['match_ratio']:.1%}): {citation_text[:80]}..."
                    )
            else:
                invalid_citations.append(citation_text[:150])
        
        hallucination_rate = (len(citations) - valid_count) / len(citations) if citations else 0.0
        
        return {
            "is_valid": len(invalid_citations) == 0,
            "total_citations": len(citations),
            "valid_citations": valid_count,
            "invalid_citations": invalid_citations,
            "warnings": warnings,
            "hallucination_rate": hallucination_rate,
            "details": details
        }
    
    def _extract_citations(self, response_text: str) -> List[Dict[str, str]]:
        """
        Extrait toutes les citations <mark> du texte.
        
        Returns:
            Liste de dicts avec {text, source}
        """
        citations = []
        
        # Pattern pour <mark data-source="...">texte</mark>
        pattern = r'<mark[^>]*data-source="([^"]*)"[^>]*>(.*?)</mark>'
        matches = re.finditer(pattern, response_text, re.DOTALL)
        
        for match in matches:
            source = match.group(1)
            text = match.group(2)
            
            # Nettoyer le texte (enlever HTML, espaces multiples)
            text = re.sub(r'<[^>]+>', '', text)  # Enlever HTML
            text = re.sub(r'\s+', ' ', text)  # Normaliser espaces
            text = text.strip()
            
            if text:  # Ignorer les citations vides
                citations.append({
                    "text": text,
                    "source": source
                })
        
        return citations
    
    def _validate_single_citation(
        self, 
        citation_text: str, 
        full_context: str,
        chunks: List[DocumentChunk]
    ) -> Dict[str, any]:
        """
        Valide une seule citation.
        
        Returns:
            {
                "found": bool,
                "match_type": "exact" | "fuzzy" | "none",
                "match_ratio": float,
                "chunk_index": int or None
            }
        """
        citation_clean = citation_text.strip()
        
        # 1. Exact match (prioritaire)
        if citation_clean in full_context:
            # Trouver dans quel chunk
            chunk_index = self._find_chunk_index(citation_clean, chunks)
            return {
                "found": True,
                "match_type": "exact",
                "match_ratio": 1.0,
                "chunk_index": chunk_index
            }
        
        # 2. Fuzzy match (si pas strict mode)
        if not self.strict_mode:
            best_ratio = 0.0
            best_chunk_index = None
            
            for i, chunk in enumerate(chunks):
                # Chercher des sous-chaînes similaires
                ratio = SequenceMatcher(None, citation_clean, chunk.content).ratio()
                
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_chunk_index = i
                
                # Si on trouve un excellent match (90%+), accepter
                if ratio >= 0.90:
                    return {
                        "found": True,
                        "match_type": "fuzzy",
                        "match_ratio": ratio,
                        "chunk_index": best_chunk_index
                    }
            
            # Si meilleur match est acceptable (85%+)
            if best_ratio >= 0.85:
                return {
                    "found": True,
                    "match_type": "fuzzy",
                    "match_ratio": best_ratio,
                    "chunk_index": best_chunk_index
                }
        
        # 3. Pas trouvé
        return {
            "found": False,
            "match_type": "none",
            "match_ratio": 0.0,
            "chunk_index": None
        }
    
    def _find_chunk_index(self, text: str, chunks: List[DocumentChunk]) -> int:
        """Trouve l'index du chunk contenant le texte."""
        for i, chunk in enumerate(chunks):
            if text in chunk.content:
                return i
        return -1
    
    def format_validation_report(self, validation: Dict) -> str:
        """
        Formate un rapport lisible de la validation.
        
        Args:
            validation: Résultat de validate_response()
        
        Returns:
            Rapport texte formaté
        """
        report = []
        report.append("=" * 80)
        report.append("📋 RAPPORT DE VALIDATION DES CITATIONS")
        report.append("=" * 80)
        
        report.append(f"\n✅ Citations valides: {validation['valid_citations']}/{validation['total_citations']}")
        report.append(f"❌ Citations invalides: {len(validation['invalid_citations'])}")
        report.append(f"⚠️  Avertissements: {len(validation['warnings'])}")
        report.append(f"📊 Taux d'hallucination: {validation['hallucination_rate']:.1%}")
        
        if validation['invalid_citations']:
            report.append("\n❌ CITATIONS INVALIDES (HALLUCINATIONS):")
            for i, citation in enumerate(validation['invalid_citations'], 1):
                report.append(f"   {i}. {citation}")
        
        if validation['warnings']:
            report.append("\n⚠️  AVERTISSEMENTS:")
            for warning in validation['warnings']:
                report.append(f"   - {warning}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
