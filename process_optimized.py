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

app = FastAPI(title="JAK Company RAG Optimized API", version="3.0-Clean")

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
    """Types d'intentions détectées"""
    DEFINITION = "definition"
    LEGAL = "legal"
    PAYMENT = "payment"
    FORMATION = "formation"
    FORMATION_ESCALADE = "formation_escalade"
    FORMATION_CONFIRMATION = "formation_confirmation"
    AMBASSADOR = "ambassador"
    CONTACT = "contact"
    CPF = "cpf"
    PROSPECT = "prospect"
    TIME = "time"
    AGGRESSIVE = "aggressive"
    ESCALADE_ADMIN = "escalade_admin"
    ESCALADE_CO = "escalade_co"
    GENERAL = "general"
    FALLBACK = "fallback"

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
        """Ajoute un message à une session"""
        messages = self.get(session_id)
        messages.append({
            "role": role,
            "content": message,
            "timestamp": time.time()
        })
        self.set(session_id, messages)
    
    def add_bloc_presented(self, session_id: str, bloc_type: str):
        """Marque un bloc comme présenté"""
        self._bloc_history[session_id].add(bloc_type)
    
    def has_bloc_been_presented(self, session_id: str, bloc_type: str) -> bool:
        """Vérifie si un bloc a été présenté"""
        return bloc_type in self._bloc_history.get(session_id, set())
    
    def clear(self, session_id: str):
        """Nettoie une session"""
        if session_id in self._store:
            del self._store[session_id]
        if session_id in self._bloc_history:
            del self._bloc_history[session_id]
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du store"""
        return {
            "size": len(self._store),
            "max_size": self._store.maxsize,
            "ttl": self._store.ttl,
            "active_sessions": len(self._bloc_history)
        }

# Initialisation du store de mémoire
memory_store = OptimizedMemoryStore()

# ============================================================================
# MOTEUR DE DÉTECTION OPTIMISÉ
# ============================================================================

class OptimizedDetectionEngine:
    """Moteur de détection optimisé avec cache et patterns améliorés"""
    
    def __init__(self):
        # Mots-clés organisés par catégorie avec frozenset pour O(1) lookup
        self._init_keyword_sets()
    
    def _init_keyword_sets(self):
        """Initialise tous les ensembles de mots-clés"""
        
        # Définitions
        self.definition_keywords = frozenset([
            "c'est quoi", "qu'est-ce que", "définition", "qu'est ce que",
            "c'est quoi un ambassadeur", "définir", "expliquer"
        ])
        
        # Légal/CPF
        self.legal_keywords = frozenset([
            "décaisser le cpf", "récupérer mon argent", "récupérer l'argent", 
            "prendre l'argent", "argent du cpf", "sortir l'argent",
            "avoir mon argent", "toucher l'argent", "retirer l'argent",
            "frauder", "arnaquer", "contourner", "bidouiller",
            "récupérer cpf", "prendre cpf", "décaisser cpf",
            "je veux l'argent", "je veux récupérer", "je veux prendre",
            "je veux l'argent de mon cpf", "je veux récupérer mon argent",
            "je veux prendre l'argent", "je veux l'argent du cpf"
        ])
        
        # Paiements - Patterns optimisés (plus spécifiques)
        self.payment_keywords = frozenset([
            # Demandes de paiement générales
            "reçu mon argent", "reçu mes sous", "reçu l'argent", "reçu les sous",
            "payé", "payée", "payés", "payées",
            "touché", "touchée", "touchés", "touchées",
            "eu", "eue", "eus", "eues",
            
            # Demandes avec "toujours pas" (CORRECTION DU BUG)
            "toujours pas reçu", "toujours pas payé", "toujours pas payée",
            "toujours pas eu", "toujours pas touché", "toujours pas touchée",
            "j'ai toujours pas reçu", "j'ai toujours pas payé", "j'ai toujours pas payée",
            "j'ai toujours pas eu", "j'ai toujours pas touché", "j'ai toujours pas touchée",
            "je n'ai toujours pas reçu", "je n'ai toujours pas payé", "je n'ai toujours pas payée",
            "je n'ai toujours pas eu", "je n'ai toujours pas touché", "je n'ai toujours pas touchée",
            
            # Demandes avec "toujours pas été"
            "toujours pas été payé", "toujours pas été payée",
            "j'ai toujours pas été payé", "j'ai toujours pas été payée",
            "je n'ai toujours pas été payé", "je n'ai toujours pas été payée",
            
            # Demandes avec "reçois quand"
            "reçois quand", "reçois quand mes", "reçois quand mon",
            "je reçois quand", "je reçois quand mes", "je reçois quand mon",
            
            # Demandes d'information sur le paiement
            "quand je reçois", "quand je vais recevoir", "quand est-ce que je reçois",
            "quand est-ce que je vais recevoir", "quand je touche", "quand je vais toucher",
            
            # Mots-clés spécifiques au paiement (éviter les conflits)
            "argent", "sous", "paiement", "virement", "remboursement"
        ])
        
        # Formations (plus spécifiques)
        self.formation_keywords = frozenset([
            "formation", "cours", "apprendre", "catalogue", "proposez",
            "disponible", "enseigner", "stage", "bureautique", 
            "informatique", "langues", "anglais", "excel", "word",
            "powerpoint", "access", "outlook", "photoshop", "illustrator",
            "indesign", "premiere", "after effects", "autocad", "solidworks",
            "catia", "revit", "sketchup", "blender", "maya", "3ds max",
            "unity", "unreal", "godot", "python", "java", "javascript",
            "html", "css", "php", "sql", "mongodb", "node.js", "react",
            "vue.js", "angular", "laravel", "django", "flask", "spring",
            "docker", "kubernetes", "aws", "azure", "gcp", "devops",
            "agile", "scrum", "kanban", "lean", "six sigma", "pmp",
            "prince2", "itil", "cobit", "iso", "cefr", "toeic", "toefl",
            "ielts", "cambridge", "delf", "dalf", "tcf", "tcfq", "tef",
            "bulats", "bright", "linguaskill", "aptis", "duolingo",
            "faire une formation", "je veux faire", "je voudrais faire",
            "formation en", "cours de", "apprendre le", "apprendre la"
        ])
        
        # Escalade formation
        self.formation_escalade_keywords = frozenset([
            "oui", "ok", "d'accord", "parfait", "super", "ça m'intéresse",
            "je veux bien", "c'est possible", "comment faire", "plus d'infos",
            "mettre en relation", "équipe commerciale", "contact"
        ])
        
        # Confirmation formation
        self.formation_confirmation_keywords = frozenset([
            "oui", "ok", "d'accord", "parfait", "super", "ça m'intéresse",
            "je veux bien", "c'est possible", "comment faire", "plus d'infos",
            "mettre en relation", "équipe commerciale", "contact", "recontacte",
            "recontactez", "recontactez-moi", "recontacte-moi", "appelez-moi",
            "appellez-moi", "appel", "téléphone", "téléphoner"
        ])
        
        # Ambassadeur (plus spécifiques)
        self.ambassador_keywords = frozenset([
            "ambassadeur", "ambassadeurs", "ambassadrice", "ambassadrices",
            "devenir ambassadeur", "comment devenir", "programme ambassadeur",
            "rémunération", "commission", "pourcentage", "gain", "gagner",
            "salaire", "revenu", "complément", "activité"
        ])
        
        # Contact
        self.contact_keywords = frozenset([
            "contact", "contacter", "joindre", "joignable", "téléphone",
            "appel", "appeler", "numéro", "email", "mail", "adresse",
            "localisation", "où", "où se trouve", "adresse physique"
        ])
        
        # CPF
        self.cpf_keywords = frozenset([
            "cpf", "compte personnel de formation", "droit formation",
            "heures formation", "crédit formation", "budget formation"
        ])
        
        # Prospect
        self.prospect_keywords = frozenset([
            "prospect", "prospection", "client potentiel", "nouveau client",
            "développer", "développement", "commercial", "vente", "vendre"
        ])
        
        # Temps/Délais
        self.time_keywords = frozenset([
            "délai", "délais", "temps", "attendre", "attente", "quand",
            "combien de temps", "durée", "rapidement", "vite", "urgent",
            "jour", "jours", "semaine", "semaines", "mois", "moi"
        ])
        
        # Agressif
        self.aggressive_keywords = frozenset([
            "merde", "putain", "con", "connard", "salope", "pute",
            "nique", "niquer", "fuck", "shit", "bitch", "asshole",
            "enculé", "enculée", "enculer", "branler", "branleur",
            "pédé", "pédale", "gouine", "tapette", "tarlouze"
        ])
        
        # Escalade admin (nettoyé)
        self.escalade_admin_keywords = frozenset([
            "argent pas arrivé", "virement pas reçu", "erreur technique",
            "bug", "problème technique", "dossier bloqué", "blocage",
            "impossible", "ça marche pas", "ça ne fonctionne pas",
            "bug technique", "problème", "erreur", "technique"
        ])
        
        # Escalade CO
        self.escalade_co_keywords = frozenset([
            "manager", "responsable", "directeur", "patron", "boss",
            "escalade", "escalader", "plus haut", "supérieur", "hiérarchie"
        ])
    
    @lru_cache(maxsize=100)
    def _has_keywords(self, message_lower: str, keyword_set: frozenset) -> bool:
        """Vérifie la présence de mots-clés avec cache"""
        return any(keyword in message_lower for keyword in keyword_set)
    
    @lru_cache(maxsize=50)
    def _detect_financing_type(self, message_lower: str) -> FinancingType:
        """Détecte le type de financement"""
        if any(term in message_lower for term in ["opco", "opérateur de compétences", "financement opco"]):
            return FinancingType.OPCO
        elif any(term in message_lower for term in ["payé tout seul", "financé en direct", "j'ai payé", "payé directement"]):
            return FinancingType.DIRECT
        elif "cpf" in message_lower:
            return FinancingType.CPF
        return FinancingType.UNKNOWN
    
    def _is_payment_related(self, message_lower: str) -> bool:
        """Vérifie si le message est lié à un paiement"""
        payment_indicators = [
            "opco", "cpf", "payé", "argent", "sous", "virement", "remboursement",
            "reçu", "touché", "eu", "paiement", "financement"
        ]
        return any(indicator in message_lower for indicator in payment_indicators)
    
    @lru_cache(maxsize=50)
    def _extract_time_info(self, message_lower: str) -> Dict:
        """Extrait les informations temporelles"""
        time_patterns = {
            'days': r'(\d+)\s*(jour|jours|j)',
            'months': r'(\d+)\s*(mois|moi)',
            'weeks': r'(\d+)\s*(semaine|semaines|sem)'
        }
        
        time_info = {}
        for unit, pattern in time_patterns.items():
            match = re.search(pattern, message_lower)
            if match:
                time_info[unit] = int(match.group(1))
        
        financing_type = self._detect_financing_type(message_lower)
        
        return {
            'time_info': time_info,
            'financing_type': financing_type
        }
    
    def _has_formation_been_presented(self, session_id: str) -> bool:
        """Vérifie si les formations ont été présentées"""
        try:
            conversation_context = memory_store.get(session_id)
            
            for msg in conversation_context:
                content = str(msg.get("content", "")).lower()
                if any(phrase in content for phrase in [
                    "formations disponibles", "+100 formations", "jak company",
                    "bureautique", "informatique", "langues", "web/3d",
                    "vente & marketing", "développement personnel",
                    "écologie numérique", "bilan compétences"
                ]):
                    return True
            return False
        except Exception as e:
            logger.error(f"Erreur vérification formations présentées: {str(e)}")
            return False
    
    def _has_bloc_m_been_presented(self, session_id: str) -> bool:
        """Vérifie si le BLOC M a été présenté"""
        try:
            conversation_context = memory_store.get(session_id)
            
            for msg in conversation_context:
                content = str(msg.get("content", "")).lower()
                if any(phrase in content for phrase in [
                    "excellent choix", "équipe commerciale", "recontacte", "recontactez",
                    "financement optimal", "planning adapté", "accompagnement perso",
                    "ok pour qu'on te recontacte", "meilleure stratégie pour toi"
                ]):
                    return True
            return False
        except Exception as e:
            logger.error(f"Erreur vérification BLOC M présenté: {str(e)}")
            return False

# Initialisation du moteur de détection
detection_engine = OptimizedDetectionEngine()

# ============================================================================
# STRUCTURES DE DÉCISION
# ============================================================================

@dataclass
class RAGDecision:
    """Structure de décision RAG optimisée"""
    intent_type: IntentType
    search_query: str
    search_strategy: str
    context_needed: List[str]
    priority_level: str
    should_escalate: bool
    system_instructions: str
    bloc_type: str
    financing_type: Optional[FinancingType] = None
    time_info: Optional[Dict] = None

# ============================================================================
# MOTEUR RAG OPTIMISÉ
# ============================================================================

class OptimizedRAGEngine:
    """Moteur RAG optimisé avec logique de décision améliorée"""
    
    def __init__(self):
        self.detection_engine = detection_engine
    
    async def analyze_intent(self, message: str, session_id: str = "default") -> RAGDecision:
        """Analyse l'intention du message avec logique optimisée"""
        start_time = time.time()
        message_lower = message.lower()
        
        try:
            # 1. Détection des définitions (priorité haute)
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.definition_keywords):
                if "ambassadeur" in message_lower:
                    return self._create_ambassadeur_definition_decision()
                elif "affiliation" in message_lower:
                    return self._create_affiliation_definition_decision()
                else:
                    return self._create_general_definition_decision(message)
            
            # 2. Détection légal/CPF (priorité haute)
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.legal_keywords):
                return self._create_legal_decision()
            
            # 3. Détection formation avec logique d'escalade (priorité haute)
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.formation_keywords):
                if not self.detection_engine._has_formation_been_presented(session_id):
                    return self._create_formation_decision(message)
            
            # 3.1. Détection escalade formation (après présentation)
            if self.detection_engine._has_formation_been_presented(session_id):
                if self.detection_engine._has_keywords(message_lower, self.detection_engine.formation_escalade_keywords):
                    return self._create_formation_escalade_decision()
                elif self.detection_engine._has_keywords(message_lower, self.detection_engine.formation_confirmation_keywords):
                    if not self.detection_engine._has_bloc_m_been_presented(session_id):
                        return self._create_formation_confirmation_decision()
                    else:
                        return self._create_human_decision()
            
            # 4. Détection ambassadeur
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.ambassador_keywords):
                return self._create_ambassador_decision(message)
            
            # 5. Détection contact
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.contact_keywords):
                return self._create_contact_decision()
            
            # 6. Détection CPF
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.cpf_keywords):
                return self._create_cpf_decision()
            
            # 7. Détection prospect
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.prospect_keywords):
                return self._create_prospect_decision()
            
            # 8. Détection agressif
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.aggressive_keywords):
                return self._create_aggressive_decision()
            
            # 9. Détection escalade admin
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.escalade_admin_keywords):
                return self._create_escalade_admin_decision()
            
            # 10. Détection escalade CO
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.escalade_co_keywords):
                return self._create_escalade_co_decision()
            
            # 11. Détection paiement (après les autres détections pour éviter les conflits)
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.payment_keywords):
                # Vérifier si c'est une demande de paiement spécifique
                if any(phrase in message_lower for phrase in [
                    "toujours pas reçu", "reçois quand", "quand je reçois",
                    "payé directement", "opco", "cpf"
                ]):
                    time_info = self.detection_engine._extract_time_info(message_lower)
                    return self._create_payment_decision(message, time_info)
            
            # 12. Détection temps/délais (en dernier pour éviter les conflits)
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.time_keywords):
                # Vérifier si c'est lié à un paiement
                if self.detection_engine._is_payment_related(message_lower):
                    time_info = self.detection_engine._extract_time_info(message_lower)
                    return self._create_payment_decision(message, time_info)
                else:
                    time_info = self.detection_engine._extract_time_info(message_lower)
                    return self._create_time_decision(time_info)
            
            # 13. Fallback général
            return self._create_fallback_decision(message)
            
        except Exception as e:
            logger.error(f"Erreur dans analyze_intent: {str(e)}")
            return self._create_error_decision(message)
    
    # Méthodes de création de décisions optimisées
    def _create_ambassadeur_definition_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.DEFINITION,
            search_query="ambassadeur JAK company définition rôle",
            search_strategy="exact_match",
            context_needed=["ambassadeur", "définition"],
            priority_level="high",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Explique clairement le rôle d'ambassadeur.",
            bloc_type="BLOC_A"
        )
    
    def _create_affiliation_definition_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.DEFINITION,
            search_query="affiliation JAK company programme",
            search_strategy="exact_match",
            context_needed=["affiliation", "programme"],
            priority_level="high",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Explique le programme d'affiliation.",
            bloc_type="BLOC_B"
        )
    
    def _create_legal_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.LEGAL,
            search_query="CPF légal décaissement conditions",
            search_strategy="semantic_search",
            context_needed=["légal", "CPF", "conditions"],
            priority_level="critical",
            should_escalate=True,
            system_instructions="Tu es un expert légal JAK Company. Explique les conditions légales du CPF.",
            bloc_type="BLOC_C"
        )
    
    def _create_payment_decision(self, message: str, time_info: Dict) -> RAGDecision:
        financing_type = time_info.get('financing_type', FinancingType.UNKNOWN)
        time_data = time_info.get('time_info', {})
        
        # Logique de délais optimisée
        if financing_type == FinancingType.DIRECT:
            days = time_data.get('days', 0)
            if days > 7:
                bloc_type = "BLOC_L"  # Délai dépassé
                should_escalate = True
            else:
                bloc_type = "BLOC_K"  # Délai normal
                should_escalate = False
        elif financing_type == FinancingType.OPCO:
            months = time_data.get('months', 0)
            if months > 2:
                bloc_type = "BLOC_L"  # Délai dépassé
                should_escalate = True
            else:
                bloc_type = "BLOC_K"  # Délai normal
                should_escalate = False
        else:
            bloc_type = "BLOC_F"  # Demande d'infos
            should_escalate = False
        
        return RAGDecision(
            intent_type=IntentType.PAYMENT,
            search_query=f"paiement {financing_type.value} délai conditions",
            search_strategy="semantic_search",
            context_needed=["paiement", "délai", financing_type.value],
            priority_level="high",
            should_escalate=should_escalate,
            system_instructions=f"Tu es un expert JAK Company. Explique les délais de paiement {financing_type.value}.",
            bloc_type=bloc_type,
            financing_type=financing_type,
            time_info=time_info
        )
    
    def _create_formation_decision(self, message: str) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.FORMATION,
            search_query="formations JAK company catalogue",
            search_strategy="semantic_search",
            context_needed=["formation", "catalogue"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Présente le catalogue de formations.",
            bloc_type="BLOC_K"
        )
    
    def _create_formation_escalade_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.FORMATION_ESCALADE,
            search_query="escalade formation équipe commerciale",
            search_strategy="exact_match",
            context_needed=["escalade", "commercial"],
            priority_level="high",
            should_escalate=True,
            system_instructions="Tu es un expert JAK Company. Escalade vers l'équipe commerciale.",
            bloc_type="BLOC_M"
        )
    
    def _create_formation_confirmation_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.FORMATION_CONFIRMATION,
            search_query="confirmation formation contact",
            search_strategy="exact_match",
            context_needed=["confirmation", "contact"],
            priority_level="high",
            should_escalate=True,
            system_instructions="Tu es un expert JAK Company. Confirme la formation et contact.",
            bloc_type="BLOC_M"
        )
    
    def _create_ambassador_decision(self, message: str) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.AMBASSADOR,
            search_query="programme ambassadeur JAK company",
            search_strategy="semantic_search",
            context_needed=["ambassadeur", "programme"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Explique le programme ambassadeur.",
            bloc_type="BLOC_D"
        )
    
    def _create_contact_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.CONTACT,
            search_query="contact JAK company coordonnées",
            search_strategy="exact_match",
            context_needed=["contact", "coordonnées"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Donne les coordonnées de contact.",
            bloc_type="BLOC_E"
        )
    
    def _create_cpf_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.CPF,
            search_query="CPF compte personnel formation",
            search_strategy="semantic_search",
            context_needed=["CPF", "formation"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Explique le CPF.",
            bloc_type="BLOC_F"
        )
    
    def _create_prospect_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.PROSPECT,
            search_query="prospection développement commercial",
            search_strategy="semantic_search",
            context_needed=["prospection", "commercial"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Explique la prospection.",
            bloc_type="BLOC_G"
        )
    
    def _create_time_decision(self, time_info: Dict) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.TIME,
            search_query="délais JAK company temps traitement",
            search_strategy="semantic_search",
            context_needed=["délai", "temps"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Explique les délais.",
            bloc_type="BLOC_J",
            time_info=time_info
        )
    
    def _create_aggressive_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.AGGRESSIVE,
            search_query="gestion client agressif JAK company",
            search_strategy="exact_match",
            context_needed=["gestion", "agressif"],
            priority_level="critical",
            should_escalate=True,
            system_instructions="Tu es un expert JAK Company. Gère la situation avec calme et professionnalisme.",
            bloc_type="BLOC_H"
        )
    
    def _create_escalade_admin_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.ESCALADE_ADMIN,
            search_query="escalade admin problème technique",
            search_strategy="exact_match",
            context_needed=["escalade", "admin"],
            priority_level="critical",
            should_escalate=True,
            system_instructions="Tu es un expert JAK Company. Escalade vers l'administration.",
            bloc_type="BLOC_I"
        )
    
    def _create_escalade_co_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.ESCALADE_CO,
            search_query="escalade CO manager responsable",
            search_strategy="exact_match",
            context_needed=["escalade", "CO"],
            priority_level="high",
            should_escalate=True,
            system_instructions="Tu es un expert JAK Company. Escalade vers le CO.",
            bloc_type="BLOC_N"
        )
    
    def _create_human_decision(self) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.FALLBACK,
            search_query="escalade humaine équipe commerciale",
            search_strategy="exact_match",
            context_needed=["humain", "commercial"],
            priority_level="high",
            should_escalate=True,
            system_instructions="Tu es un expert JAK Company. Escalade vers l'équipe commerciale.",
            bloc_type="BLOC_M"
        )
    
    def _create_general_definition_decision(self, message: str) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.DEFINITION,
            search_query=message,
            search_strategy="semantic_search",
            context_needed=["définition"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Explique clairement le concept demandé.",
            bloc_type="BLOC_GENERAL"
        )
    
    def _create_fallback_decision(self, message: str) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.FALLBACK,
            search_query=message,
            search_strategy="semantic_search",
            context_needed=["général"],
            priority_level="low",
            should_escalate=False,
            system_instructions="Tu es un expert JAK Company. Réponds de manière générale et utile.",
            bloc_type="BLOC_FALLBACK"
        )
    
    def _create_error_decision(self, message: str) -> RAGDecision:
        return RAGDecision(
            intent_type=IntentType.FALLBACK,
            search_query="erreur système JAK company",
            search_strategy="exact_match",
            context_needed=["erreur"],
            priority_level="critical",
            should_escalate=True,
            system_instructions="Tu es un expert JAK Company. Gère l'erreur avec professionnalisme.",
            bloc_type="BLOC_ERROR"
        )

# Initialisation du moteur RAG
rag_engine = OptimizedRAGEngine()

# ============================================================================
# ENDPOINTS API OPTIMISÉS
# ============================================================================

@app.get("/")
async def root():
    """Endpoint racine avec informations sur l'API"""
    return {
        "message": "JAK Company RAG Optimized API v3.0",
        "status": "operational",
        "version": "3.0-Clean",
        "endpoints": {
            "optimize_rag": "/optimize_rag",
            "health": "/health",
            "memory_status": "/memory_status",
            "performance_metrics": "/performance_metrics"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de santé de l'API"""
    try:
        # Vérifications de base
        memory_stats = memory_store.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "memory": memory_stats,
            "detection_engine": "operational",
            "rag_engine": "operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/optimize_rag")
async def optimize_rag_decision(request: Request):
    """Endpoint principal optimisé pour l'analyse RAG"""
    start_time = time.time()
    
    try:
        # Récupération des données
        data = await request.json()
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")
        
        if not message:
            return await _create_error_response("validation_error", "Message vide", session_id, time.time() - start_time)
        
        # Ajout du message à la mémoire
        await memory_store.add_message(session_id, message, "user")
        
        # Analyse de l'intention
        decision = await rag_engine.analyze_intent(message, session_id)
        
        # Marquer le bloc comme présenté
        memory_store.add_bloc_presented(session_id, decision.bloc_type)
        
        # Construction de la réponse
        response = {
            "session_id": session_id,
            "intent_type": decision.intent_type.value,
            "search_query": decision.search_query,
            "search_strategy": decision.search_strategy,
            "context_needed": decision.context_needed,
            "priority_level": decision.priority_level,
            "should_escalate": decision.should_escalate,
            "system_instructions": decision.system_instructions,
            "bloc_type": decision.bloc_type,
            "financing_type": decision.financing_type.value if decision.financing_type else None,
            "time_info": decision.time_info,
            "processing_time": round(time.time() - start_time, 3),
            "timestamp": time.time()
        }
        
        logger.info(f"RAG decision for session {session_id}: {decision.intent_type.value} -> {decision.bloc_type}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in optimize_rag: {str(e)}")
        return await _create_error_response("processing_error", str(e), session_id, time.time() - start_time)

async def _create_error_response(error_type: str, message: str, session_id: str, processing_time: float):
    """Création de réponse d'erreur standardisée"""
    return {
        "error": True,
        "error_type": error_type,
        "message": message,
        "session_id": session_id,
        "processing_time": round(processing_time, 3),
        "timestamp": time.time()
    }

@app.post("/clear_memory/{session_id}")
async def clear_memory(session_id: str):
    """Nettoie la mémoire d'une session"""
    try:
        memory_store.clear(session_id)
        return {"status": "success", "message": f"Memory cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}")
        raise HTTPException(status_code=500, detail="Error clearing memory")

@app.get("/memory_status")
async def memory_status():
    """Statut de la mémoire"""
    try:
        stats = memory_store.get_stats()
        return {
            "status": "success",
            "memory_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting memory status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting memory status")

@app.get("/performance_metrics")
async def get_performance_metrics():
    """Métriques de performance"""
    try:
        memory_stats = memory_store.get_stats()
        
        return {
            "status": "success",
            "metrics": {
                "memory_usage": memory_stats,
                "cache_hits": getattr(detection_engine._has_keywords, 'cache_info', lambda: {})(),
                "api_version": "3.0-Clean",
                "optimization_level": "high"
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting performance metrics")

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)