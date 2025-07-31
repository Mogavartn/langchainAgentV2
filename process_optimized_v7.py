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

app = FastAPI(title="JAK Company RAG V7 API", version="9.0-Payment-Logic-Fixed")

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
# STORE DE MÉMOIRE OPTIMISÉ V6
# ============================================================================

class OptimizedMemoryStoreV7:
    """Store de mémoire optimisé avec TTL et limites - Version 7 avec logique de paiement corrigée"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._store = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self._access_count = defaultdict(int)
        self._bloc_history = defaultdict(list)  # Changé en list pour garder l'ordre
        self._conversation_context = defaultdict(dict)
        self._last_response = defaultdict(str)  # NOUVEAU V6: Dernière réponse donnée
    
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
        messages.append({"role": role, "content": message, "timestamp": time.time()})
        self.set(session_id, messages)
    
    def add_bloc_presented(self, session_id: str, bloc_id: str):
        """Marque un bloc comme présenté - NOUVEAU V6: Garde l'ordre chronologique"""
        if session_id not in self._bloc_history:
            self._bloc_history[session_id] = []
        self._bloc_history[session_id].append(bloc_id)
        # Garder seulement les 5 derniers blocs
        if len(self._bloc_history[session_id]) > 5:
            self._bloc_history[session_id] = self._bloc_history[session_id][-5:]
    
    def has_bloc_been_presented(self, session_id: str, bloc_id: str) -> bool:
        """Vérifie si un bloc a déjà été présenté"""
        return bloc_id in self._bloc_history.get(session_id, [])
    
    def get_last_bloc(self, session_id: str) -> Optional[str]:
        """NOUVEAU V6: Récupère le dernier bloc présenté"""
        history = self._bloc_history.get(session_id, [])
        return history[-1] if history else None
    
    def get_last_n_blocs(self, session_id: str, n: int = 3) -> List[str]:
        """NOUVEAU V6: Récupère les n derniers blocs présentés"""
        history = self._bloc_history.get(session_id, [])
        return history[-n:] if len(history) >= n else history
    
    def set_conversation_context(self, session_id: str, context_key: str, value: Any):
        """Définit un contexte de conversation"""
        self._conversation_context[session_id][context_key] = value
    
    def get_conversation_context(self, session_id: str, context_key: str, default: Any = None) -> Any:
        """Récupère un contexte de conversation"""
        return self._conversation_context[session_id].get(context_key, default)
    
    def set_last_response(self, session_id: str, response: str):
        """NOUVEAU V6: Enregistre la dernière réponse donnée"""
        self._last_response[session_id] = response
    
    def get_last_response(self, session_id: str) -> str:
        """NOUVEAU V7: Récupère la dernière réponse donnée"""
        return self._last_response.get(session_id, "")
    
    def set_payment_context(self, session_id: str, financing_type: str, time_info: Dict, total_days: int):
        """Sauvegarde le contexte de paiement pour une session"""
        payment_context = {
            "financing_type": financing_type,
            "time_info": time_info,
            "total_days": total_days,
            "timestamp": time.time()
        }
        self.set_conversation_context(session_id, "payment_context", payment_context)
    
    def get_payment_context(self, session_id: str) -> Optional[Dict]:
        """Récupère le contexte de paiement pour une session"""
        return self.get_conversation_context(session_id, "payment_context", None)
    
    def clear(self, session_id: str):
        """Nettoie une session"""
        if session_id in self._store:
            del self._store[session_id]
        if session_id in self._bloc_history:
            del self._bloc_history[session_id]
        if session_id in self._conversation_context:
            del self._conversation_context[session_id]
        if session_id in self._last_response:
            del self._last_response[session_id]
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du store"""
        return {
            "total_sessions": len(self._store),
            "total_bloc_history": len(self._bloc_history),
            "total_contexts": len(self._conversation_context),
            "total_responses": len(self._last_response),
            "most_accessed": max(self._access_count.items(), key=lambda x: x[1]) if self._access_count else None
        }

# Instance globale du store de mémoire
memory_store = OptimizedMemoryStoreV7()

# ============================================================================
# MOTEUR DE DÉTECTION OPTIMISÉ POUR SUPABASE V7
# ============================================================================

class SupabaseDrivenDetectionEngineV7:
    """Moteur de détection basé sur les blocs Supabase - Version 7 avec logique de paiement corrigée"""
    
    def __init__(self):
        # Mots-clés organisés par bloc avec frozenset pour O(1) lookup
        self._init_bloc_keywords()
    
    def _init_bloc_keywords(self):
        """Initialise les mots-clés par bloc selon la logique Supabase V7"""
        self.bloc_keywords = {
            IntentType.BLOC_A: frozenset([
                "paiement", "payé", "payée", "payer", "argent", "facture", "débit", "prélèvement",
                "virement", "chèque", "carte bancaire", "cb", "mastercard", "visa", "pas été payé"
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
                "spécialités", "domaines formation", "c'est quoi vos formations", "quelles sont vos formations"
            ]),
            IntentType.BLOC_L: frozenset([
                "délai dépassé", "retard paiement", "paiement en retard", "délai expiré"
            ]),
            IntentType.BLOC_M: frozenset([
                "après choix", "formation choisie", "inscription", "confirmation", "intéressé par",
                "je voudrais", "je veux", "je choisis", "m'intéresse"
            ]),
            IntentType.BLOC_LEGAL: frozenset([
                "légal", "droit", "juridique", "avocat", "procédure", "recours"
            ]),
            IntentType.BLOC_AGRO: frozenset([
                "agressif", "énervé", "fâché", "colère", "insulte", "grossier", "impoli",
                "nuls", "nul", "merde", "putain", "con", "connard", "salop", "salope"
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

    def _detect_formation_interest(self, message_lower: str, session_id: str) -> bool:
        """Détecte si l'utilisateur exprime un intérêt pour une formation spécifique"""
        interest_indicators = [
            "intéressé par", "je choisis", "je veux", "m'intéresse", 
            "ça m'intéresse", "je prends", "je sélectionne", "je souhaite",
            "je voudrais"
        ]
    
        formation_keywords = [
            "comptabilité", "marketing", "langues", "web", "3d", "vente", 
            "développement", "bureautique", "informatique", "écologie", "bilan",
            "anglais", "français", "espagnol", "allemand", "italien"
        ]
    
        has_interest = any(indicator in message_lower for indicator in interest_indicators)
        has_formation = any(keyword in message_lower for keyword in formation_keywords)
    
        # Vérifier si l'utilisateur a récemment vu les formations
        last_blocs = memory_store.get_last_n_blocs(session_id, 3)
        formations_recently_shown = any("BLOC_K" in bloc for bloc in last_blocs)
    
        return has_interest and has_formation and formations_recently_shown

    def _detect_aggressive_behavior(self, message_lower: str) -> bool:
        """Détecte les comportements agressifs"""
        aggressive_indicators = [
            "nuls", "nul", "merde", "putain", "con", "connard", "salop", "salope",
            "dégage", "va te faire", "ta gueule", "ferme ta gueule", "imbécile",
            "idiot", "stupide", "incompétent", "inutile"
        ]
        
        return any(indicator in message_lower for indicator in aggressive_indicators)

    def _detect_follow_up_context(self, message_lower: str, session_id: str) -> Optional[IntentType]:
        """Détecte les messages de suivi basés sur le contexte conversationnel - AMÉLIORÉ V7"""
    
        # Récupérer le contexte récent
        last_bloc = memory_store.get_last_bloc(session_id)
        last_blocs = memory_store.get_last_n_blocs(session_id, 3)
    
        # NOUVEAU V6: Détection d'agressivité prioritaire
        if self._detect_aggressive_behavior(message_lower):
            return IntentType.BLOC_AGRO
    
        # Si l'utilisateur a vu les formations et exprime un intérêt
        if self._detect_formation_interest(message_lower, session_id):
            return IntentType.BLOC_M
    
        # Si l'utilisateur vient de voir les ambassadeurs et pose des questions
        if last_bloc in ["BLOC D.1", "BLOC D.2"] and any(word in message_lower for word in ["comment", "quand", "où", "combien"]):
            return IntentType.BLOC_E  # Processus ambassadeur
    
        # Si l'utilisateur vient de voir un problème de paiement et donne plus d'infos
        if last_bloc == "BLOC_A" and any(word in message_lower for word in ["depuis", "ça fait", "délai", "attendre"]):
            return IntentType.BLOC_L  # Délai dépassé
        
        # Si l'utilisateur répond à une question de filtrage CPF
        if last_bloc == "BLOC_F1" and any(word in message_lower for word in ["oui", "non", "bloqué", "informé"]):
            return IntentType.BLOC_F2  # Suite du processus CPF
        
        # NOUVEAU V7: Si l'utilisateur répond à une question de filtrage OPCO
        if last_bloc == "BLOC_F3" and any(word in message_lower for word in ["oui", "non", "bloqué", "informé"]):
            return IntentType.BLOC_F2  # Suite du processus OPCO
        
        return None

# ============================================================================
# STRUCTURE DE DÉCISION RAG OPTIMISÉE V6
# ============================================================================

@dataclass
class SupabaseRAGDecisionV7:
    """Structure de décision RAG basée sur Supabase - Version 7"""
    bloc_id: IntentType
    search_query: str
    context_needed: List[str]
    priority_level: str
    should_escalade: bool
    system_instructions: str
    financing_type: Optional[FinancingType] = None
    time_info: Optional[Dict] = None
    session_id: str = "default"
    continuity_context: Optional[str] = None

# ============================================================================
# MOTEUR RAG OPTIMISÉ POUR SUPABASE V7
# ============================================================================

class SupabaseRAGEngineV7:
    """Moteur RAG optimisé pour la logique Supabase - Version 7 avec logique de paiement corrigée"""
    
    def __init__(self):
        self.detection_engine = SupabaseDrivenDetectionEngineV7()
    
    async def analyze_intent(self, message: str, session_id: str = "default") -> SupabaseRAGDecisionV7:
        """Analyse l'intention avec gestion du contexte conversationnel améliorée V7"""
        message_lower = message.lower()
    
        # 1. Vérifier d'abord le contexte conversationnel
        follow_up_bloc = self.detection_engine._detect_follow_up_context(message_lower, session_id)
        if follow_up_bloc:
            logger.info(f"Contexte conversationnel détecté: {follow_up_bloc.value} pour session {session_id}")
            return self._create_contextual_decision(follow_up_bloc, message, session_id)
    
        # 2. Détection du bloc principal (logique existante)
        detected_bloc = self._detect_primary_bloc(message_lower)
    
        # 3. Sauvegarder le contexte après détection
        memory_store.set_conversation_context(session_id, "last_bloc_presented", detected_bloc.value)
        
        # CORRECTION V7: Logique de filtrage de paiement corrigée
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
        """Détecte le bloc principal selon la logique Supabase V7"""
        # Priorité absolue pour l'agressivité
        if self.detection_engine._detect_aggressive_behavior(message_lower):
            return IntentType.BLOC_AGRO
        
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
        
        for bloc_id in priority_order:
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.bloc_keywords[bloc_id]):
                return bloc_id
        
        return IntentType.FALLBACK
    
    # CORRECTION V7: Logique de filtrage de paiement corrigée
    def _should_apply_payment_filtering(self, message_lower: str, session_id: str) -> bool:
        """Détermine si on doit appliquer le filtrage de paiement - CORRIGÉ V7"""
        financing_type = self.detection_engine._detect_financing_type(message_lower)
        time_info = self.detection_engine._extract_time_info(message_lower)
        total_days = self.detection_engine._convert_to_days(time_info)
        
        # Sauvegarder le contexte de paiement
        memory_store.set_payment_context(session_id, financing_type.value, time_info, total_days)
        
        # NOUVEAU V7: Logique corrigée selon la logique n8n
        if financing_type == FinancingType.CPF:
            if total_days > 45 and not memory_store.has_bloc_been_presented(session_id, "BLOC_F1"):
                return True  # Appliquer le filtrage BLOC_F1
            elif total_days <= 45:
                return False  # Rassurer directement (pas de bloc spécial)
        
        elif financing_type == FinancingType.OPCO:
            if total_days > 60 and not memory_store.has_bloc_been_presented(session_id, "BLOC_F3"):
                return True  # Appliquer le filtrage BLOC_F3
        
        return False
    
    # CORRECTION V7: Création de décision de paiement corrigée
    def _create_payment_filtering_decision(self, message: str, session_id: str) -> SupabaseRAGDecisionV7:
        """Crée une décision pour le filtrage de paiement - CORRIGÉ V7"""
        payment_context = memory_store.get_payment_context(session_id)
        financing_type = payment_context.get("financing_type") if payment_context else "unknown"
        total_days = payment_context.get("total_days", 0) if payment_context else 0
        
        # NOUVEAU V7: Logique de blocage corrigée
        if financing_type == "cpf":
            if total_days > 45:
                return SupabaseRAGDecisionV7(
                    bloc_id=IntentType.BLOC_F1,
                    search_query="CPF question dossier bloqué filtrage",
                    context_needed=["paiement", "cpf", "filtrage"],
                    priority_level="CRITICAL",
                    should_escalade=False,
                    system_instructions="""RÈGLE ABSOLUE : Poser d'abord la question de filtrage BLOC F1.
                    Ne pas donner d'informations complètes avant la réponse du client.
                    Focus sur la clarification du problème de paiement CPF.""",
                    financing_type=FinancingType.CPF,
                    session_id=session_id,
                    continuity_context="payment_filtering"
                )
            else:
                # CPF ≤ 45 jours : rassurer directement
                return SupabaseRAGDecisionV7(
                    bloc_id=IntentType.BLOC_C,
                    search_query="CPF rassurance délai normal",
                    context_needed=["paiement", "cpf", "rassurance"],
                    priority_level="HIGH",
                    should_escalade=False,
                    system_instructions="""RÈGLE ABSOLUE : Rassurer le client CPF.
                    Le délai est dans les normes, pas de problème.
                    Utiliser le ton rassurant JAK Company.""",
                    financing_type=FinancingType.CPF,
                    session_id=session_id,
                    continuity_context="cpf_reassurance"
                )
        
        elif financing_type == "opco":
            if total_days > 60:
                return SupabaseRAGDecisionV7(
                    bloc_id=IntentType.BLOC_F3,
                    search_query="OPCO question dossier bloqué filtrage",
                    context_needed=["paiement", "opco", "filtrage"],
                    priority_level="CRITICAL",
                    should_escalade=False,
                    system_instructions="""RÈGLE ABSOLUE : Poser d'abord la question de filtrage BLOC F3.
                    Ne pas donner d'informations complètes avant la réponse du client.
                    Focus sur la clarification du problème de paiement OPCO.""",
                    financing_type=FinancingType.OPCO,
                    session_id=session_id,
                    continuity_context="payment_filtering"
                )
            else:
                # OPCO ≤ 60 jours : rassurer directement
                return SupabaseRAGDecisionV7(
                    bloc_id=IntentType.BLOC_C,
                    search_query="OPCO rassurance délai normal",
                    context_needed=["paiement", "opco", "rassurance"],
                    priority_level="HIGH",
                    should_escalade=False,
                    system_instructions="""RÈGLE ABSOLUE : Rassurer le client OPCO.
                    Le délai est dans les normes, pas de problème.
                    Utiliser le ton rassurant JAK Company.""",
                    financing_type=FinancingType.OPCO,
                    session_id=session_id,
                    continuity_context="opco_reassurance"
                )
        
        # Retour par défaut
        return SupabaseRAGDecisionV7(
            bloc_id=IntentType.BLOC_C,
            search_query="paiement général",
            context_needed=["paiement"],
            priority_level="MEDIUM",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Utiliser le BLOC C général.
            Rassurer le client sur les délais de paiement.""",
            session_id=session_id,
            continuity_context="payment_general"
        )
    
    def _create_ambassador_decision(self, message: str, session_id: str) -> SupabaseRAGDecisionV7:
        """Crée une décision pour les ambassadeurs"""
        bloc_id = IntentType.BLOC_D1 if "devenir" in message.lower() else IntentType.BLOC_D2
        return SupabaseRAGDecisionV7(
            bloc_id=bloc_id,
            search_query=f"ambassadeur {bloc_id.value.lower()}",
            context_needed=["ambassadeur", "affiliation"],
            priority_level="HIGH",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le bloc ambassadeur correspondant.
            Reproduire MOT POUR MOT avec TOUS les emojis.
            Ne pas mélanger avec d'autres blocs.""",
            session_id=session_id,
            continuity_context="ambassador"
        )
    
    def _create_formation_decision(self, message: str, session_id: str) -> SupabaseRAGDecisionV7:
        """Crée une décision pour les formations"""
        return SupabaseRAGDecisionV7(
            bloc_id=IntentType.BLOC_K,
            search_query="formations disponibles catalogue programmes",
            context_needed=["formation", "programme", "catalogue"],
            priority_level="MEDIUM",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le bloc formation.
            Présenter le catalogue complet avec toutes les spécialités.
            Maintenir le ton chaleureux JAK Company.""",
            session_id=session_id,
            continuity_context="formations"
        )
    
    def _create_aggressive_decision(self, message: str, session_id: str) -> SupabaseRAGDecisionV7:
        """Crée une décision pour l'agressivité"""
        return SupabaseRAGDecisionV7(
            bloc_id=IntentType.BLOC_AGRO,
            search_query="agressivité impolitesse recadrage",
            context_needed=["agressivité", "recadrage"],
            priority_level="CRITICAL",
            should_escalade=False,
            system_instructions="""RÈGLE ABSOLUE : Appliquer le BLOC AGRO.
            Recadrer poliment mais fermement.
            Proposer une solution constructive.
            Ne pas escalader automatiquement.""",
            session_id=session_id,
            continuity_context="aggressive"
        )
    
    def _create_escalade_decision(self, message: str, session_id: str) -> SupabaseRAGDecisionV7:
        """Crée une décision pour l'escalade"""
        bloc_id = IntentType.BLOC_61 if "admin" in message.lower() else IntentType.BLOC_62
        return SupabaseRAGDecisionV7(
            bloc_id=bloc_id,
            search_query=f"escalade {bloc_id.value.lower()}",
            context_needed=["escalade", "contact"],
            priority_level="CRITICAL",
            should_escalade=True,
            system_instructions="""RÈGLE ABSOLUE : Appliquer le bloc d'escalade correspondant.
            Rediriger vers le bon interlocuteur.
            Assurer le suivi du dossier.""",
            session_id=session_id,
            continuity_context="escalade"
        )
    
    def _create_default_decision(self, bloc_id: IntentType, message: str, session_id: str) -> SupabaseRAGDecisionV7:
        """Crée une décision par défaut basée sur le bloc détecté"""
        return SupabaseRAGDecisionV7(
            bloc_id=bloc_id,
            search_query=f"{bloc_id.value.lower()} {message[:50]}",
            context_needed=[bloc_id.value.lower()],
            priority_level="MEDIUM",
            should_escalade=False,
            system_instructions=f"""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le {bloc_id.value}.
            Reproduire MOT POUR MOT avec TOUS les emojis.
            Ne pas mélanger avec d'autres blocs.""",
            session_id=session_id,
            continuity_context="default"
        )
    
    def _create_contextual_decision(self, bloc_id: IntentType, message: str, session_id: str) -> SupabaseRAGDecisionV7:
        """Crée une décision basée sur le contexte conversationnel - AMÉLIORÉ V7"""
    
        if bloc_id == IntentType.BLOC_M:
            return SupabaseRAGDecisionV7(
                bloc_id=bloc_id,
                search_query="formation choisie inscription confirmation après choix",
                context_needed=["formation", "inscription", "confirmation"],
                priority_level="HIGH",
                should_escalade=False,
                system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le BLOC M.
                L'utilisateur a choisi une formation après avoir vu le catalogue.
                Reproduire MOT POUR MOT le processus d'inscription avec TOUS les emojis.
                Pas de mélange avec d'autres blocs.
                IMPORTANT : Ne pas escalader automatiquement après le choix.""",
                session_id=session_id,
                continuity_context="formation_choice"
            )
    
        elif bloc_id == IntentType.BLOC_E:
            return SupabaseRAGDecisionV7(
                bloc_id=bloc_id,
                search_query="processus ambassadeur étapes comment ça marche",
                context_needed=["ambassadeur", "processus", "étapes"],
                priority_level="HIGH",
                should_escalade=False,
                system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le BLOC E.
                L'utilisateur pose des questions sur le processus ambassadeur.
                Reproduire MOT POUR MOT les étapes avec TOUS les emojis.""",
                session_id=session_id,
                continuity_context="ambassador_process"
            )
    
        elif bloc_id == IntentType.BLOC_L:
            return SupabaseRAGDecisionV7(
                bloc_id=bloc_id,
                search_query="délai dépassé retard paiement solution",
                context_needed=["délai", "retard", "solution"],
                priority_level="CRITICAL",
                should_escalade=True,
                system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le BLOC L.
                Délai de paiement dépassé, escalade nécessaire.
                Reproduire MOT POUR MOT avec TOUS les emojis.""",
                session_id=session_id,
                continuity_context="payment_delay"
            )
    
        elif bloc_id == IntentType.BLOC_F2:
            return SupabaseRAGDecisionV7(
                bloc_id=bloc_id,
                search_query="CPF dossier bloqué suite réponse filtrage",
                context_needed=["cpf", "dossier", "bloqué", "suite"],
                priority_level="CRITICAL",
                should_escalade=False,
                system_instructions="""RÈGLE ABSOLUE : Utiliser UNIQUEMENT le BLOC F2.
                Suite du processus CPF après réponse au filtrage.
                Reproduire MOT POUR MOT avec TOUS les emojis.""",
                session_id=session_id,
                continuity_context="cpf_followup"
            )
    
        elif bloc_id == IntentType.BLOC_AGRO:
            return SupabaseRAGDecisionV7(
                bloc_id=bloc_id,
                search_query="agressivité impolitesse recadrage",
                context_needed=["agressivité", "recadrage"],
                priority_level="CRITICAL",
                should_escalade=False,
                system_instructions="""RÈGLE ABSOLUE : Appliquer le BLOC AGRO.
                Recadrer poliment mais fermement.
                Proposer une solution constructive.
                Ne pas escalader automatiquement.""",
                session_id=session_id,
                continuity_context="aggressive"
            )
    
        # Retour par défaut
        return self._create_default_decision(bloc_id, message, session_id)

# Instance globale du moteur RAG
rag_engine = SupabaseRAGEngineV7()

# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.get("/")
async def root():
    """Endpoint racine avec informations sur l'API"""
    return {
        "message": "JAK Company RAG V7 API - Payment Logic Fixed",
        "version": "9.0",
        "status": "active",
        "features": [
            "Supabase-driven bloc detection V6",
            "Optimized memory management V6",
            "Context-aware decision making V6",
            "Real-time intent analysis V6",
            "Fixed continuity issues",
            "Enhanced contextual responses V6",
            "Improved fallback handling"
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
            "version": "8.0-Continuity-Fixed-V6"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/optimize_rag")
async def optimize_rag_decision(request: Request):
    """Endpoint principal pour l'optimisation RAG basée sur Supabase V6"""
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
        
        # Analyse de l'intention avec le moteur Supabase V6
        rag_decision = await rag_engine.analyze_intent(message, session_id)
        
        # Marquer le bloc comme présenté si nécessaire
        if not rag_decision.should_escalade:
            memory_store.add_bloc_presented(session_id, rag_decision.bloc_id.value)
        
        # Construction de la réponse optimisée
        response = {
            "status": "success",
            "session_id": session_id,
            "processing_time": round(time.time() - start_time, 3),
            "bloc_id": rag_decision.bloc_id.value,
            "search_query": rag_decision.search_query,
            "context_needed": rag_decision.context_needed,
            "priority_level": rag_decision.priority_level,
            "should_escalade": rag_decision.should_escalade,
            "system_instructions": rag_decision.system_instructions,
            "financing_type": rag_decision.financing_type.value if rag_decision.financing_type else None,
            "time_info": rag_decision.time_info,
            "continuity_context": rag_decision.continuity_context,
            "message": message,
            "timestamp": time.time()
        }
        
        logger.info(f"RAG decision for session {session_id}: {rag_decision.bloc_id.value}")
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