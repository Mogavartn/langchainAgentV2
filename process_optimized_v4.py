import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Set, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import re
from dataclasses import dataclass
import traceback
from functools import lru_cache
from cachetools import TTLCache
import time
from collections import defaultdict
from enum import Enum

# Configuration optimisée du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="JAK Company RAG V4 API", version="6.0-Supabase-Driven")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vérification de la clé OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    logger.warning("OpenAI API Key not found - some features may not work")
else:
    os.environ["OPENAI_API_KEY"] = openai_key
    logger.info("OpenAI API Key configured")

# ============================================================================
# ENUMS ET CONSTANTES
# ============================================================================

class IntentType(Enum):
    """Types d'intentions détectées - maintenant basées sur les blocs Supabase"""
    BLOC_A = "BLOC A"
    BLOC_B1 = "BLOC B.1"
    BLOC_B2 = "BLOC B.2"
    BLOC_C = "BLOC C"
    BLOC_D1 = "BLOC D.1"
    BLOC_D2 = "BLOC D.2"
    BLOC_E = "BLOC E"
    BLOC_F = "BLOC F"
    BLOC_F1 = "BLOC F1"
    BLOC_F2 = "BLOC F2"
    BLOC_F3 = "BLOC F3"
    BLOC_G = "BLOC G"
    BLOC_H = "BLOC H"
    BLOC_I1 = "BLOC I1"
    BLOC_I2 = "BLOC I2"
    BLOC_J = "BLOC J"
    BLOC_K = "BLOC K"
    BLOC_L = "BLOC L"
    BLOC_M = "BLOC M"
    BLOC_LEGAL = "BLOC LEGAL"
    BLOC_AGRO = "BLOC AGRO"
    BLOC_GENERAL = "BLOC GENERAL"
    BLOC_51 = "BLOC 5.1"
    BLOC_52 = "BLOC 5.2"
    BLOC_53 = "BLOC 5.3"
    BLOC_54 = "BLOC 5.4"
    BLOC_61 = "BLOC 6.1"
    BLOC_62 = "BLOC 6.2"
    FALLBACK = "FALLBACK"

class FinancingType(Enum):
    """Types de financement"""
    DIRECT = "direct"
    OPCO = "opco"
    CPF = "cpf"
    UNKNOWN = "unknown"

# ============================================================================
# STORE DE MÉMOIRE OPTIMISÉ
# ============================================================================

class OptimizedMemoryStore:
    """Store de mémoire optimisé avec TTL et limites"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._store = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self._access_count = defaultdict(int)
        self._bloc_history = defaultdict(set)
        self._conversation_context = defaultdict(dict)
    
    def get(self, key: str) -> List[Dict]:
        """Récupère les messages d'une session"""
        self._access_count[key] += 1
        return self._store.get(key, [])
    
    def set(self, key: str, value: List[Dict]):
        """Définit les messages d'une session (limite à 10 messages)"""
        if len(value) > 10:
            value = value[-10:]
        self._store[key] = value
    
    def add_message(self, session_id: str, message: str, role: str = "user"):
        """Ajoute un message à la session"""
        messages = self.get(session_id)
        messages.append({"role": role, "content": message})
        self.set(session_id, messages)
    
    def add_bloc_presented(self, session_id: str, bloc_type: str):
        """Marque un bloc comme présenté"""
        self._bloc_history[session_id].add(bloc_type)
    
    def has_bloc_been_presented(self, session_id: str, bloc_type: str) -> bool:
        """Vérifie si un bloc a déjà été présenté"""
        return bloc_type in self._bloc_history[session_id]
    
    def set_conversation_context(self, session_id: str, context_key: str, value: Any):
        """Définit un contexte de conversation"""
        self._conversation_context[session_id][context_key] = value
    
    def get_conversation_context(self, session_id: str, context_key: str, default: Any = None) -> Any:
        """Récupère un contexte de conversation"""
        return self._conversation_context[session_id].get(context_key, default)
    
    def clear(self, session_id: str):
        """Nettoie une session"""
        if session_id in self._store:
            del self._store[session_id]
        if session_id in self._bloc_history:
            del self._bloc_history[session_id]
        if session_id in self._conversation_context:
            del self._conversation_context[session_id]
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du store"""
        return {
            "total_sessions": len(self._store),
            "total_bloc_history": len(self._bloc_history),
            "total_contexts": len(self._conversation_context),
            "most_accessed": max(self._access_count.items(), key=lambda x: x[1]) if self._access_count else None
        }

# Instance globale du store de mémoire
memory_store = OptimizedMemoryStore()

# ============================================================================
# MOTEUR DE DÉTECTION OPTIMISÉ POUR SUPABASE
# ============================================================================

class SupabaseDrivenDetectionEngine:
    """Moteur de détection basé sur les blocs Supabase"""
    
    def __init__(self):
        # Mots-clés organisés par bloc avec frozenset pour O(1) lookup
        self._init_bloc_keywords()
    
    def _init_bloc_keywords(self):
        """Initialise les mots-clés par bloc selon la logique Supabase"""
        self.bloc_keywords = {
            IntentType.BLOC_A: frozenset([
                "paiement", "payé", "payée", "payer", "argent", "facture", "débit", "prélèvement",
                "virement", "chèque", "carte bancaire", "cb", "mastercard", "visa"
            ]),
            IntentType.BLOC_B1: frozenset([
                "affiliation", "affilié", "affiliée", "programme affiliation", "mail affiliation",
                "email affiliation", "courriel affiliation"
            ]),
            IntentType.BLOC_B2: frozenset([
                "c'est quoi un ambassadeur", "qu'est ce qu'un ambassadeur", "définition ambassadeur",
                "ambassadeur définition", "expliquer ambassadeur"
            ]),
            IntentType.BLOC_C: frozenset([
                "cpf", "compte personnel formation", "formation cpF", "financement cpF",
                "droit formation", "mon compte formation"
            ]),
            IntentType.BLOC_D1: frozenset([
                "devenir ambassadeur", "comment devenir ambassadeur", "postuler ambassadeur",
                "candidature ambassadeur", "rejoindre ambassadeur"
            ]),
            IntentType.BLOC_D2: frozenset([
                "c'est quoi un ambassadeur", "qu'est ce qu'un ambassadeur", "définition ambassadeur"
            ]),
            IntentType.BLOC_E: frozenset([
                "processus ambassadeur", "étapes ambassadeur", "comment ça marche ambassadeur",
                "procédure ambassadeur"
            ]),
            IntentType.BLOC_F: frozenset([
                "paiement formation", "payé formation", "facture formation", "débit formation"
            ]),
            IntentType.BLOC_F1: frozenset([
                "cpf bloqué", "dossier bloqué", "blocage cpF", "problème cpF", "délai cpF"
            ]),
            IntentType.BLOC_F2: frozenset([
                "cpf dossier bloqué", "blocage dossier cpF", "problème dossier cpF"
            ]),
            IntentType.BLOC_F3: frozenset([
                "opco", "opérateur compétences", "délai opco", "blocage opco", "problème opco"
            ]),
            IntentType.BLOC_G: frozenset([
                "parler humain", "contacter humain", "appeler", "téléphoner", "conseiller",
                "assistant", "aide humaine"
            ]),
            IntentType.BLOC_H: frozenset([
                "prospect", "devis", "tarif", "prix", "coût", "formation", "programme",
                "offre", "catalogue"
            ]),
            IntentType.BLOC_I1: frozenset([
                "entreprise", "société", "professionnel", "auto-entrepreneur", "salarié"
            ]),
            IntentType.BLOC_I2: frozenset([
                "ambassadeur vendeur", "vendeur", "commercial", "vente"
            ]),
            IntentType.BLOC_J: frozenset([
                "paiement direct", "paiement immédiat", "payer maintenant"
            ]),
            IntentType.BLOC_K: frozenset([
                "formations disponibles", "catalogue formation", "programmes formation",
                "spécialités", "domaines formation"
            ]),
            IntentType.BLOC_L: frozenset([
                "délai dépassé", "retard paiement", "paiement en retard", "délai expiré"
            ]),
            IntentType.BLOC_M: frozenset([
                "après choix", "formation choisie", "inscription", "confirmation"
            ]),
            IntentType.BLOC_LEGAL: frozenset([
                "légal", "droit", "juridique", "avocat", "procédure", "recours"
            ]),
            IntentType.BLOC_AGRO: frozenset([
                "agressif", "énervé", "fâché", "colère", "insulte", "grossier", "impoli"
            ]),
            IntentType.BLOC_GENERAL: frozenset([
                "bonjour", "salut", "hello", "qui êtes-vous", "jak company", "présentation"
            ]),
            IntentType.BLOC_51: frozenset([
                "cpf dossier bloqué", "blocage administratif", "délai administratif"
            ]),
            IntentType.BLOC_52: frozenset([
                "relance", "suivi", "nouvelle", "après escalade"
            ]),
            IntentType.BLOC_53: frozenset([
                "seuils fiscaux", "micro-entreprise", "fiscal", "impôts"
            ]),
            IntentType.BLOC_54: frozenset([
                "sans réseaux sociaux", "pas de réseaux", "pas instagram", "pas snapchat"
            ]),
            IntentType.BLOC_61: frozenset([
                "escalade admin", "administrateur", "responsable", "manager"
            ]),
            IntentType.BLOC_62: frozenset([
                "escalade co", "commercial", "vendeur", "conseiller"
            ])
        }
    
    @lru_cache(maxsize=100)
    def _has_keywords(self, message_lower: str, keyword_set: frozenset) -> bool:
        """Vérifie si le message contient les mots-clés d'un bloc"""
        return any(keyword in message_lower for keyword in keyword_set)
    
    @lru_cache(maxsize=50)
    def _detect_financing_type(self, message_lower: str) -> FinancingType:
        """Détecte le type de financement"""
        if any(word in message_lower for word in ["cpf", "compte personnel formation"]):
            return FinancingType.CPF
        elif any(word in message_lower for word in ["opco", "opérateur compétences"]):
            return FinancingType.OPCO
        elif any(word in message_lower for word in ["direct", "immédiat", "maintenant"]):
            return FinancingType.DIRECT
        return FinancingType.UNKNOWN
    
    @lru_cache(maxsize=50)
    def _extract_time_info(self, message_lower: str) -> Dict:
        """Extrait les informations temporelles"""
        time_patterns = {
            "jours": r"(\d+)\s*jour",
            "semaines": r"(\d+)\s*semaine",
            "mois": r"(\d+)\s*mois",
            "années": r"(\d+)\s*année"
        }
        
        time_info = {}
        for unit, pattern in time_patterns.items():
            match = re.search(pattern, message_lower)
            if match:
                time_info[unit] = int(match.group(1))
        
        return time_info
    
    def _convert_to_days(self, time_info: Dict) -> int:
        """Convertit les informations temporelles en jours"""
        total_days = 0
        if "jours" in time_info:
            total_days += time_info["jours"]
        if "semaines" in time_info:
            total_days += time_info["semaines"] * 7
        if "mois" in time_info:
            total_days += time_info["mois"] * 30
        if "années" in time_info:
            total_days += time_info["années"] * 365
        return total_days

# ============================================================================
# STRUCTURE DE DÉCISION RAG OPTIMISÉE
# ============================================================================

@dataclass
class SupabaseRAGDecision:
    """Structure de décision RAG basée sur Supabase"""
    bloc_type: IntentType
    search_query: str
    context_needed: List[str]
    priority_level: str
    should_escalade: bool
    system_instructions: str
    financing_type: Optional[FinancingType] = None
    time_info: Optional[Dict] = None
    session_id: str = "default"

# ============================================================================
# MOTEUR RAG OPTIMISÉ POUR SUPABASE
# ============================================================================

class SupabaseRAGEngine:
    """Moteur RAG optimisé pour la logique Supabase"""
    
    def __init__(self):
        self.detection_engine = SupabaseDrivenDetectionEngine()
    
    async def analyze_intent(self, message: str, session_id: str = "default") -> SupabaseRAGDecision:
        """Analyse l'intention et retourne la décision RAG basée sur Supabase"""
        message_lower = message.lower()
        
        # Détection du bloc principal
        detected_bloc = self._detect_primary_bloc(message_lower)
        
        # Logique spéciale pour les paiements CPF avec délai
        if self._should_apply_payment_filtering(message_lower, session_id):
            return self._create_payment_filtering_decision(message, session_id)
        
        # Logique spéciale pour les ambassadeurs
        if detected_bloc in [IntentType.BLOC_D1, IntentType.BLOC_D2]:
            return self._create_ambassador_decision(message, session_id)
        
        # Logique spéciale pour les formations
        if detected_bloc in [IntentType.BLOC_H, IntentType.BLOC_K]:
            return self._create_formation_decision(message, session_id)
        
        # Logique spéciale pour l'agressivité
        if detected_bloc == IntentType.BLOC_AGRO:
            return self._create_aggressive_decision(message, session_id)
        
        # Logique spéciale pour l'escalade
        if detected_bloc in [IntentType.BLOC_61, IntentType.BLOC_62]:
            return self._create_escalade_decision(message, session_id)
        
        # Décision par défaut basée sur le bloc détecté
        return self._create_default_decision(detected_bloc, message, session_id)
    
    def _detect_primary_bloc(self, message_lower: str) -> IntentType:
        """Détecte le bloc principal selon la logique Supabase"""
        # Priorité absolue pour les définitions
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.bloc_keywords[IntentType.BLOC_B2]):
            return IntentType.BLOC_B2
        
        # Priorité pour les problèmes de paiement
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.bloc_keywords[IntentType.BLOC_A]):
            return IntentType.BLOC_A
        
        # Vérification de tous les blocs par ordre de priorité
        priority_order = [
            IntentType.BLOC_F1, IntentType.BLOC_F2, IntentType.BLOC_F3,  # Paiements spéciaux
            IntentType.BLOC_C, IntentType.BLOC_D1, IntentType.BLOC_D2,  # CPF et Ambassadeurs
            IntentType.BLOC_G, IntentType.BLOC_H, IntentType.BLOC_K,    # Contact et Formations
            IntentType.BLOC_LEGAL, IntentType.BLOC_AGRO,                # Légal et Agressivité
            IntentType.BLOC_61, IntentType.BLOC_62,                     # Escalades
            IntentType.BLOC_GENERAL                                      # Général
        ]
        
        for bloc_type in priority_order:
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.bloc_keywords[bloc_type]):
                return bloc_type
        
        return IntentType.FALLBACK
    
    def _should_apply_payment_filtering(self, message_lower: str, session_id: str) -> bool:
        """Détermine si on doit appliquer le filtrage de paiement"""
        financing_type = self.detection_engine._detect_financing_type(message_lower)
        time_info = self.detection_engine._extract_time_info(message_lower)
        total_days = self.detection_engine._convert_to_days(time_info)
        
        # Logique de filtrage selon la logique n8n
        return (financing_type == FinancingType.CPF and 
                total_days > 45 and 
                not memory_store.has_bloc_been_presented(session_id, "BLOC_F1"))
    
    def _create_payment_filtering_decision(self, message: str, session_id: str) -> SupabaseRAGDecision:
        """Crée une décision pour le filtrage de paiement"""
        return SupabaseRAGDecision(
            bloc_type=IntentType.BLOC_F1,
            search_query="CPF question dossier bloqué filtrage",
            context_needed=["paiement", "cpf", "filtrage"],
            priority_level="CRITICAL",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Poser d'abord la question de filtrage BLOC F1.
            Ne pas donner d'informations complètes avant la réponse du client.
            Focus sur la clarification du problème de paiement CPF.""",
            financing_type=FinancingType.CPF,
            session_id=session_id
        )
    
    def _create_ambassador_decision(self, message: str, session_id: str) -> SupabaseRAGDecision:
        """Crée une décision pour les ambassadeurs"""
        bloc_type = IntentType.BLOC_D1 if "devenir" in message.lower() else IntentType.BLOC_D2
        return SupabaseRAGDecision(
            bloc_type=bloc_type,
            search_query=f"ambassadeur {bloc_type.value.lower()}",
            context_needed=["ambassadeur", "affiliation"],
            priority_level="HIGH",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le bloc ambassadeur correspondant.
            Reproduire MOT POUR MOT avec TOUS les emojis.
            Ne pas mélanger avec d'autres blocs.""",
            session_id=session_id
        )
    
    def _create_formation_decision(self, message: str, session_id: str) -> SupabaseRAGDecision:
        """Crée une décision pour les formations"""
        return SupabaseRAGDecision(
            bloc_type=IntentType.BLOC_K,
            search_query="formations disponibles catalogue programmes",
            context_needed=["formation", "programme", "catalogue"],
            priority_level="MEDIUM",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le bloc formation.
            Présenter le catalogue complet avec toutes les spécialités.
            Maintenir le ton chaleureux JAK Company.""",
            session_id=session_id
        )
    
    def _create_aggressive_decision(self, message: str, session_id: str) -> SupabaseRAGDecision:
        """Crée une décision pour l'agressivité"""
        return SupabaseRAGDecision(
            bloc_type=IntentType.BLOC_AGRO,
            search_query="agressivité impolitesse recadrage",
            context_needed=["agressivité", "recadrage"],
            priority_level="CRITICAL",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Appliquer le BLOC AGRO.
            Recadrer poliment mais fermement.
            Proposer une solution constructive.""",
            session_id=session_id
        )
    
    def _create_escalade_decision(self, message: str, session_id: str) -> SupabaseRAGDecision:
        """Crée une décision pour l'escalade"""
        bloc_type = IntentType.BLOC_61 if "admin" in message.lower() else IntentType.BLOC_62
        return SupabaseRAGDecision(
            bloc_type=bloc_type,
            search_query=f"escalade {bloc_type.value.lower()}",
            context_needed=["escalade", "contact"],
            priority_level="CRITICAL",
            should_escalade=True,
            system_instructions="""RÈGLE ABSOLUE : Appliquer le bloc d'escalade correspondant.
            Rediriger vers le bon interlocuteur.
            Assurer le suivi du dossier.""",
            session_id=session_id
        )
    
    def _create_default_decision(self, bloc_type: IntentType, message: str, session_id: str) -> SupabaseRAGDecision:
        """Crée une décision par défaut basée sur le bloc détecté"""
        return SupabaseRAGDecision(
            bloc_type=bloc_type,
            search_query=f"{bloc_type.value.lower()} {message[:50]}",
            context_needed=[bloc_type.value.lower()],
            priority_level="MEDIUM",
            should_escalade=False,
            system_instructions=f"""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le {bloc_type.value}.
            Reproduire MOT POUR MOT avec TOUS les emojis.
            Ne pas mélanger avec d'autres blocs.""",
            session_id=session_id
        )

# Instance globale du moteur RAG
rag_engine = SupabaseRAGEngine()

# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.get("/")
async def root():
    """Endpoint racine avec informations sur l'API"""
    return {
        "message": "JAK Company RAG V4 API - Supabase Driven",
        "version": "6.0",
        "status": "active",
        "features": [
            "Supabase-driven bloc detection",
            "Optimized memory management",
            "Context-aware decision making",
            "Real-time intent analysis"
        ],
        "endpoints": {
            "POST /optimize_rag": "Analyze message and return RAG decision",
            "GET /health": "Health check",
            "POST /clear_memory/{session_id}": "Clear session memory",
            "GET /memory_status": "Memory store statistics"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de santé de l'API"""
    try:
        # Vérifications de base
        checks = {
            "api_status": "healthy",
            "memory_store": "operational",
            "detection_engine": "ready",
            "rag_engine": "ready",
            "openai_key": "configured" if openai_key else "missing"
        }
        
        # Statistiques de mémoire
        memory_stats = memory_store.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": checks,
            "memory_stats": memory_stats,
            "version": "6.0-Supabase-Driven"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/optimize_rag")
async def optimize_rag_decision(request: Request):
    """Endpoint principal pour l'optimisation RAG basée sur Supabase"""
    start_time = time.time()
    
    try:
        # Récupération des données de la requête
        body = await request.json()
        message = body.get("message", "").strip()
        session_id = body.get("session_id", "default_session")
        
        if not message:
            return await _create_error_response("INVALID_INPUT", "Message is required", session_id, time.time() - start_time)
        
        # Ajout du message à la mémoire
        memory_store.add_message(session_id, message, "user")
        
        # Analyse de l'intention avec le moteur Supabase
        rag_decision = await rag_engine.analyze_intent(message, session_id)
        
        # Marquer le bloc comme présenté si nécessaire
        if not rag_decision.should_escalade:
            memory_store.add_bloc_presented(session_id, rag_decision.bloc_type.value)
        
        # Construction de la réponse optimisée
        response = {
            "status": "success",
            "session_id": session_id,
            "processing_time": round(time.time() - start_time, 3),
            "bloc_type": rag_decision.bloc_type.value,
            "search_query": rag_decision.search_query,
            "context_needed": rag_decision.context_needed,
            "priority_level": rag_decision.priority_level,
            "should_escalade": rag_decision.should_escalade,
            "system_instructions": rag_decision.system_instructions,
            "financing_type": rag_decision.financing_type.value if rag_decision.financing_type else None,
            "time_info": rag_decision.time_info,
            "message": message,
            "timestamp": time.time()
        }
        
        logger.info(f"RAG decision for session {session_id}: {rag_decision.bloc_type.value}")
        return response
        
    except Exception as e:
        logger.error(f"Error in optimize_rag: {e}")
        logger.error(traceback.format_exc())
        return await _create_error_response("PROCESSING_ERROR", str(e), session_id, time.time() - start_time)

async def _create_error_response(error_type: str, message: str, session_id: str, processing_time: float):
    """Crée une réponse d'erreur standardisée"""
    return {
        "status": "error",
        "error_type": error_type,
        "message": message,
        "session_id": session_id,
        "processing_time": round(processing_time, 3),
        "timestamp": time.time()
    }

@app.post("/clear_memory/{session_id}")
async def clear_memory(session_id: str):
    """Nettoie la mémoire d'une session spécifique"""
    try:
        memory_store.clear(session_id)
        return {
            "status": "success",
            "message": f"Memory cleared for session {session_id}",
            "session_id": session_id,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")

@app.get("/memory_status")
async def memory_status():
    """Retourne les statistiques du store de mémoire"""
    try:
        stats = memory_store.get_stats()
        return {
            "status": "success",
            "memory_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory status: {str(e)}")

# ============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)