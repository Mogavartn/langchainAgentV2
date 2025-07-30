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

app = FastAPI(title="JAK Company RAG V4 API", version="6.0-Corrected")

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
    PAYMENT_FILTERING = "payment_filtering"
    FORMATION = "formation"
    FORMATION_ESCALADE = "formation_escalade"
    FORMATION_CONFIRMATION = "formation_confirmation"
    AMBASSADOR = "ambassador"
    AMBASSADOR_PROCESS = "ambassador_process"
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
        print(f"DEBUG: Adding bloc {bloc_type} to session {session_id}")
        self._bloc_history[session_id].add(bloc_type)
        print(f"DEBUG: Bloc history for {session_id}: {self._bloc_history[session_id]}")
        print(f"DEBUG: Stack trace: {__import__('traceback').format_stack()[-3:]}")
    
    def has_bloc_been_presented(self, session_id: str, bloc_type: str) -> bool:
        """Vérifie si un bloc a déjà été présenté"""
        result = bloc_type in self._bloc_history[session_id]
        print(f"DEBUG: Checking if {bloc_type} in session {session_id}: {result}")
        print(f"DEBUG: Available blocs: {self._bloc_history[session_id]}")
        return result
    
    def set_conversation_context(self, session_id: str, context_key: str, value: Any):
        """Définit le contexte de conversation"""
        self._conversation_context[session_id][context_key] = value
    
    def get_conversation_context(self, session_id: str, context_key: str, default: Any = None) -> Any:
        """Récupère le contexte de conversation"""
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
            "total_conversation_contexts": len(self._conversation_context),
            "cache_info": self._store.currsize,
            "access_counts": dict(self._access_count)
        }

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
        
        # ===== PAYMENT KEYWORDS (CORRIGÉS) =====
        self.payment_keywords = frozenset([
            # Demandes de paiement générales
            "paiement", "payé", "payée", "payer", "payement", "virement", "argent", "sous", "thune",
            "remboursement", "remboursé", "remboursée", "rembourser",
            "commission", "commissions", "rémunération", "rémunéré", "rémunérée",
            
            # Demandes avec "pas encore"
            "pas encore reçu", "pas encore payé", "pas encore payée", "pas encore eu",
            "pas encore touché", "pas encore touchée", "pas encore versé", "pas encore versée",
            "n'ai pas encore reçu", "n'ai pas encore payé", "n'ai pas encore payée",
            "n'ai pas encore eu", "n'ai pas encore touché", "n'ai pas encore touchée",
            "je n'ai pas encore reçu", "je n'ai pas encore payé", "je n'ai pas encore payée",
            "je n'ai pas encore eu", "je n'ai pas encore touché", "je n'ai pas encore touchée",
            
            # Demandes avec "toujours pas" (CORRECTION DU BUG)
            "toujours pas reçu", "toujours pas payé", "toujours pas payée",
            "toujours pas eu", "toujours pas touché", "toujours pas touchée",
            "j'ai toujours pas reçu", "j'ai toujours pas payé", "j'ai toujours pas payée",
            "j'ai toujours pas eu", "j'ai toujours pas touché", "j'ai toujours pas touchée",
            "je n'ai toujours pas reçu", "je n'ai toujours pas payé", "je n'ai toujours pas payée",
            "je n'ai toujours pas eu", "je n'ai toujours pas touché", "je n'ai toujours pas touchée",
            
            # Demandes avec "toujours pas été" (CORRECTION DU BUG)
            "toujours pas été payé", "toujours pas été payée",
            "j'ai toujours pas été payé", "j'ai toujours pas été payée",
            "je n'ai toujours pas été payé", "je n'ai toujours pas été payée",
            
            # Demandes avec "reçois quand" (CORRECTION DU BUG)
            "reçois quand", "reçois quand mes", "reçois quand mon",
            "je reçois quand", "je reçois quand mes", "je reçois quand mon",
            
            # Demandes simples
            "pas reçu", "pas payé", "pas payée", "pas eu", "pas touché", "pas touchée",
            "n'ai pas reçu", "n'ai pas payé", "n'ai pas payée", "n'ai pas eu",
            "n'ai pas touché", "n'ai pas touchée",
            "je n'ai pas reçu", "je n'ai pas payé", "je n'ai pas payée",
            "je n'ai pas eu", "je n'ai pas touché", "je n'ai pas touchée",
            
            # Questions de délai
            "quand je reçois", "quand je vais recevoir", "quand je serai payé",
            "quand je serai payée", "quand je vais être payé", "quand je vais être payée",
            "délai paiement", "délai virement", "délai remboursement",
            "combien de temps", "en combien de temps", "dans combien de temps"
        ])
        
        # ===== FINANCING TYPE KEYWORDS =====
        self.direct_financing_keywords = frozenset([
            # Financement direct (AMÉLIORÉ)
            "j'ai payé", "j'ai financé", "j'ai tout payé", "j'ai tout financé",
            "c'est moi qui ai payé", "c'est moi qui ai financé", "c'est moi qui finance",
            "financement direct", "paiement direct", "financement en direct", "paiement en direct",
            "financement cash", "paiement cash", "financement comptant", "paiement comptant",
            "financement privé", "paiement privé", "financement personnel", "paiement personnel",
            "financement individuel", "paiement individuel", "auto-financement",
            "financement par mes soins", "paiement par mes soins",
            "mes propres moyens", "avec mes propres fonds", "de ma poche", "de mes économies",
            "j'ai payé toute seule", "j'ai payé moi", "j'ai financé toute seule", "j'ai financé moi",
            "c'est moi qui est financé", "financement moi même", "j'ai tout payé", "j'ai tout financé"
        ])
        
        self.cpf_keywords = frozenset([
            "cpf", "compte personnel formation", "compte personnel de formation",
            "financement cpf", "paiement cpf", "formation cpf", "en cpf", "par cpf",
            "via cpf", "avec cpf", "c'est du cpf", "c'est un cpf", "c'est une cpf"
        ])
        
        self.opco_keywords = frozenset([
            "opco", "opérateur de compétences", "financement opco", "paiement opco",
            "formation opco", "fonds formation"
        ])
        
        # ===== FORMATION KEYWORDS =====
        self.formation_keywords = frozenset([
            "formation", "formations", "former", "se former", "formation disponible",
            "formations disponibles", "catalogue formation", "catalogue formations",
            "quelles formations", "quelles sont vos formations", "vous proposez quoi",
            "formations proposées", "types de formation", "domaines formation",
            "spécialités", "spécialité", "domaine", "domaines"
        ])
        
        # ===== AGGRESSIVE KEYWORDS (NOUVEAU V4) =====
        self.aggressive_keywords = frozenset([
            "nuls", "nul", "nulle", "nulles", "incompétents", "incompétent", "incompétente",
            "débiles", "débile", "idiots", "idiot", "idiote", "stupides", "stupide",
            "merde", "putain", "con", "connard", "connasse", "salop", "salope",
            "dégage", "dégagez", "cassez-vous", "casse-toi", "va te faire", "allez vous faire",
            "je vous emmerde", "je t'emmerde", "emmerde", "emmerder", "chier", "chiant",
            "ras le bol", "ras le cul", "j'en ai marre", "j'en ai assez", "ça me saoule",
            "c'est nul", "c'est de la merde", "c'est de la connerie", "c'est débile",
            "vous êtes nuls", "vous êtes débiles", "vous êtes incompétents"
        ])
        
        # ===== AMBASSADOR KEYWORDS =====
        self.ambassador_keywords = frozenset([
            "ambassadeur", "ambassadeurs", "ambassadrice", "ambassadrices",
            "devenir ambassadeur", "comment devenir ambassadeur", "ambassadeur c'est quoi",
            "c'est quoi un ambassadeur", "ambassadeur définition", "rôle ambassadeur"
        ])
        
        # ===== AMBASSADOR PROCESS KEYWORDS (NOUVEAU) =====
        self.ambassador_process_keywords = frozenset([
            "oui", "ok", "d'accord", "je veux", "je veux bien", "ça m'intéresse",
            "comment faire", "comment procéder", "étapes", "processus", "démarrage"
        ])
        
        # ===== ESCALADE ADMIN KEYWORDS (CORRIGÉS) =====
        self.escalade_admin_keywords = frozenset([
            # Problèmes techniques et dossiers
            "délai anormal", "retard anormal", "paiement en retard", "virement en retard",
            "paiement bloqué", "virement bloqué", "argent bloqué",
            "dossier bloqué", "dossier en attente", "dossier suspendu",
            "consultation fichier", "accès fichier", "voir mon dossier",
            "état dossier", "suivi dossier", "dossier administratif",
            "erreur système", "bug", "problème technique", "dysfonctionnement",
            "impossible de", "ne fonctionne pas", "ça marche pas",
            
            # Justificatifs et preuves
            "justificatif", "preuve", "attestation", "certificat", "facture",
            "dossier", "fichier", "accès", "consultation"
        ])
        
        # ===== ESCALADE CO KEYWORDS =====
        self.escalade_co_keywords = frozenset([
            # Deals stratégiques
            "deal", "partenariat", "collaboration", "projet spécial",
            "offre spéciale", "tarif préférentiel", "accord commercial",
            "négociation", "proposition commerciale", "devis spécial",
            
            # Besoin d'appel
            "appel téléphonique", "appeler", "téléphoner", "discussion téléphonique",
            "parler au téléphone", "échange téléphonique", "conversation téléphonique",
            
            # Accompagnement humain
            "accompagnement", "suivi personnalisé", "conseil personnalisé",
            "assistance personnalisée", "aide personnalisée", "support personnalisé",
            "conseiller dédié", "accompagnateur", "mentor", "coach",
            
            # Situations complexes
            "situation complexe", "cas particulier", "dossier complexe",
            "problème spécifique", "demande spéciale", "besoin particulier",
            "parler à quelqu'un", "parler à un humain", "discuter avec quelqu'un"
        ])
        
        # ===== LEGAL KEYWORDS =====
        self.legal_keywords = frozenset([
            "récupérer", "récupération", "récupérer argent", "récupérer mon argent",
            "récupérer mes sous", "récupérer ma thune", "récupérer mon paiement",
            "récupérer mon virement", "récupérer mon remboursement",
            "récupérer cpf", "récupérer mon cpf", "récupérer mes droits cpf",
            "récupérer formation", "récupérer ma formation"
        ])
        
        # ===== TIME KEYWORDS =====
        self.time_keywords = frozenset([
            "il y a", "depuis", "ça fait", "terminé", "terminée", "finie", "fini",
            "jour", "jours", "semaine", "semaines", "mois", "mois", "année", "années",
            "hier", "aujourd'hui", "demain", "cette semaine", "ce mois", "cette année"
        ])
    
    @lru_cache(maxsize=100)
    def _has_keywords(self, message_lower: str, keyword_set: frozenset) -> bool:
        """Vérifie si un message contient des mots-clés (avec cache)"""
        return any(keyword in message_lower for keyword in keyword_set)
    
    @lru_cache(maxsize=50)
    def _detect_financing_type(self, message_lower: str) -> FinancingType:
        """Détecte le type de financement (avec cache)"""
        if self._has_keywords(message_lower, self.direct_financing_keywords):
            return FinancingType.DIRECT
        elif self._has_keywords(message_lower, self.cpf_keywords):
            return FinancingType.CPF
        elif self._has_keywords(message_lower, self.opco_keywords):
            return FinancingType.OPCO
        return FinancingType.UNKNOWN
    
    def _is_payment_related(self, message_lower: str) -> bool:
        """Vérifie si le message concerne un paiement"""
        return self._has_keywords(message_lower, self.payment_keywords)
    
    @lru_cache(maxsize=50)
    def _extract_time_info(self, message_lower: str) -> Dict:
        """Extrait les informations de temps et financement (avec cache)"""
        time_info = {}
        financing_type = self._detect_financing_type(message_lower)
        
        # Extraction des délais
        time_patterns = [
            (r'(\d+)\s*jour', 'days'),
            (r'(\d+)\s*semaine', 'weeks'),
            (r'(\d+)\s*mois', 'months'),
            (r'(\d+)\s*année', 'years')
        ]
        
        for pattern, key in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                time_info[key] = int(match.group(1))
                break
        
        # Si pas de délai trouvé mais qu'on a un type de financement, on peut quand même traiter
        if financing_type != FinancingType.UNKNOWN and not time_info:
            # Essayer de détecter des délais approximatifs
            if "semaine" in message_lower:
                time_info['weeks'] = 1
            elif "mois" in message_lower:
                time_info['months'] = 1
            elif "jour" in message_lower:
                time_info['days'] = 1
        
        return {
            'time_info': time_info,
            'financing_type': financing_type
        }
    
    def _convert_to_days(self, time_info: Dict) -> int:
        """Convertit les informations de temps en jours"""
        total_days = 0
        
        if 'days' in time_info:
            total_days += time_info['days']
        if 'weeks' in time_info:
            total_days += time_info['weeks'] * 7
        if 'months' in time_info:
            total_days += time_info['months'] * 30  # Approximation
        if 'years' in time_info:
            total_days += time_info['years'] * 365  # Approximation
        
        return total_days

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
        self.detection_engine = OptimizedDetectionEngine()
        self.memory_store = OptimizedMemoryStore()
    
    async def analyze_intent(self, message: str, session_id: str = "default") -> RAGDecision:
        """Analyse l'intention du message avec logique optimisée"""
        message_lower = message.lower().strip()
        
        # Ajouter le message à la mémoire
        self.memory_store.add_message(session_id, message)
        
        # ===== PRIORITÉ 1: AGRESSIVITÉ (BLOC AGRO) =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.aggressive_keywords):
            return self._create_aggressive_decision()
        
        # ===== PRIORITÉ 2: ESCALADES (BLOCS 6.1 et 6.2) =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.escalade_admin_keywords):
            return self._create_escalade_admin_decision()
        
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.escalade_co_keywords):
            return self._create_escalade_co_decision()
        
        # ===== PRIORITÉ 2: FORMATIONS (BLOC K) =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.formation_keywords):
            return self._create_formation_decision(message)
        
        # ===== PRIORITÉ 3: PAIEMENTS =====
        if self.detection_engine._is_payment_related(message_lower):
            time_financing_info = self.detection_engine._extract_time_info(message_lower)
            
            # Vérifier si on a les informations nécessaires
            has_financing_info = time_financing_info['financing_type'] != FinancingType.UNKNOWN
            has_time_info = bool(time_financing_info['time_info'])
            
            # Si pas d'infos suffisantes → BLOC F (filtrage)
            if not has_financing_info or not has_time_info:
                decision = self._create_payment_filtering_decision(message)
                # Marquer le bloc comme présenté immédiatement
                self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
                return decision
            
            # Sinon, appliquer la logique selon le type et délai
            financing_type = time_financing_info['financing_type']
            time_info = time_financing_info['time_info']
            
            # Paiement direct > 7 jours → BLOC J + Escalade Admin
            if (financing_type == FinancingType.DIRECT and 
                self.detection_engine._convert_to_days(time_info) > 7):
                return self._create_payment_direct_delayed_decision()
            
            # Paiement direct ≤ 7 jours → Réponse normale (NOUVEAU V4)
            if (financing_type == FinancingType.DIRECT and 
                self.detection_engine._convert_to_days(time_info) <= 7):
                decision = self._create_payment_direct_normal_decision()
                # Marquer le bloc comme présenté immédiatement
                self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
                return decision
            
            # OPCO > 2 mois → Escalade Admin
            if (financing_type == FinancingType.OPCO and 
                self.detection_engine._convert_to_days(time_info) > 60): # 60 jours pour 2 mois
                decision = self._create_escalade_admin_decision()
                # Marquer le bloc comme présenté immédiatement
                self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
                return decision
            
            # CPF > 45 jours → BLOC F1 OBLIGATOIRE (CORRECTION V3)
            if (financing_type == FinancingType.CPF and 
                self.detection_engine._convert_to_days(time_info) > 45):
                decision = self._create_cpf_delayed_decision()
                # Marquer le bloc comme présenté immédiatement
                self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
                return decision
            
            # Autres cas → BLOC F
            decision = self._create_payment_filtering_decision(message)
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 4: AMBASSADEUR =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.ambassador_keywords):
            decision = self._create_ambassador_decision(message)
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 5: FORMATIONS (BLOC K) =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.formation_keywords):
            decision = self._create_formation_decision(message)
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 5: PROCESSUS AMBASSADEUR (NOUVEAU V3) =====
        if (self.memory_store.has_bloc_been_presented(session_id, "BLOC_AMBASSADOR") and
            self.detection_engine._has_keywords(message_lower, self.detection_engine.ambassador_process_keywords)):
            decision = self._create_ambassador_process_decision()
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 6: RÉPONSE CPF BLOC F1 (NOUVEAU V4) =====
        if (self.memory_store.has_bloc_been_presented(session_id, "BLOC_F1") and
            message_lower.strip() in ["oui", "yes", "oui.", "yes."]):
            decision = self._create_cpf_blocked_decision()
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 7: RÉPONSE FORMATION (NOUVEAU V4) =====
        if (self.memory_store.has_bloc_been_presented(session_id, "BLOC_K") and
            message_lower.strip() in ["ok", "ok.", "d'accord", "d'accord.", "oui", "oui.", "yes", "yes."]):
            decision = self._create_formation_confirmation_decision()
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 6: LEGAL =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.legal_keywords):
            decision = self._create_legal_decision()
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 7: TEMPS (SEULEMENT SI PAS DE PAIEMENT) =====
        # Vérifier d'abord si c'est un paiement avec financement
        time_financing_info = self.detection_engine._extract_time_info(message_lower)
        if (time_financing_info['financing_type'] != FinancingType.UNKNOWN and 
            self.detection_engine._has_keywords(message_lower, self.detection_engine.time_keywords)):
            # C'est un paiement avec financement, traiter comme paiement
            financing_type = time_financing_info['financing_type']
            time_info = time_financing_info['time_info']
            
            # Paiement direct > 7 jours → BLOC J + Escalade Admin
            if (financing_type == FinancingType.DIRECT and 
                self.detection_engine._convert_to_days(time_info) > 7):
                return self._create_payment_direct_delayed_decision()
            
            # OPCO > 2 mois → Escalade Admin
            if (financing_type == FinancingType.OPCO and 
                self.detection_engine._convert_to_days(time_info) > 60): # 60 jours pour 2 mois
                return self._create_escalade_admin_decision()
            
            # CPF > 45 jours → BLOC F1 OBLIGATOIRE (CORRECTION V3)
            if (financing_type == FinancingType.CPF and 
                self.detection_engine._convert_to_days(time_info) > 45):
                return self._create_cpf_delayed_decision()
            
            # Autres cas → BLOC F
            decision = self._create_payment_filtering_decision(message)
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # Questions de temps générales (sans financement)
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.time_keywords):
            time_info = self.detection_engine._extract_time_info(message_lower)
            decision = self._create_time_decision(time_info)
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== FALLBACK =====
        decision = self._create_fallback_decision(message)
        # Marquer le bloc comme présenté immédiatement
        self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
        return decision
    
    # ===== MÉTHODES DE CRÉATION DE DÉCISIONS =====
    
    def _create_formation_decision(self, message: str) -> RAGDecision:
        """Décision pour les formations (BLOC K)"""
        return RAGDecision(
            intent_type=IntentType.FORMATION,
            search_query="formations disponibles JAK Company",
            search_strategy="formation_catalog",
            context_needed=["formations", "spécialités", "modalités"],
            priority_level="high",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: DEMANDE FORMATION (BLOC K)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC K :
🎓 +100 formations disponibles chez JAK Company ! 🎓
📚 Nos spécialités :
• 💻 Bureautique • 🖥 Informatique • 🌍 Langues • 🎨 Web/3D
• 📈 Vente & Marketing • 🧠 Développement personnel
• 🌱 Écologie numérique • 🎯 Bilan compétences • ⚙ Sur mesure
Et bien d'autres encore ! ✨
📖 E-learning ou 🏢 Présentiel → Tu choisis ! 😉
Quel domaine t'intéresse ? 👀""",
            bloc_type="BLOC_K"
        )
    
    def _create_formation_confirmation_decision(self) -> RAGDecision:
        """Décision pour confirmation formation (BLOC 6.2) - NOUVEAU V4"""
        return RAGDecision(
            intent_type=IntentType.FORMATION_CONFIRMATION,
            search_query="escalade formation confirmation",
            search_strategy="formation_escalade",
            context_needed=["formation", "escalade", "commercial"],
            priority_level="high",
            should_escalate=True,
            system_instructions="""CONTEXTE DÉTECTÉ: CONFIRMATION FORMATION (BLOC 6.2)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC 6.2 :
🔁 ESCALADE AGENT CO
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
Nous te répondrons dès que possible.""",
            bloc_type="BLOC_6.2"
        )
    
    def _create_payment_filtering_decision(self, message: str) -> RAGDecision:
        """Décision pour le filtrage des paiements (BLOC F)"""
        return RAGDecision(
            intent_type=IntentType.PAYMENT_FILTERING,
            search_query="délais paiement formation",
            search_strategy="payment_delays",
            context_needed=["délais", "financement", "types_paiement"],
            priority_level="high",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: FILTRAGE PAIEMENT (BLOC F)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC F :
Pour que je puisse t'aider au mieux, est-ce que tu peux me préciser :
● Comment la formation a-t-elle été financée ? (CPF, OPCO, paiement direct)
● Et environ quand elle s'est terminée ?
Une fois que j'aurai ces informations, je pourrai te donner une réponse précise sur les délais de paiement.""",
            bloc_type="BLOC_F"
        )
    
    def _create_payment_direct_delayed_decision(self) -> RAGDecision:
        """Décision pour paiement direct en retard (BLOC J)"""
        return RAGDecision(
            intent_type=IntentType.ESCALADE_ADMIN,
            search_query="paiement direct délai dépassé",
            search_strategy="escalade_admin",
            context_needed=["délais", "escalade"],
            priority_level="critical",
            should_escalate=True,
            system_instructions="""CONTEXTE DÉTECTÉ: PAIEMENT DIRECT DÉLAI DÉPASSÉ (BLOC J)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC J :
⏰ Paiement direct : délai dépassé ⏰
Le délai normal c'est 7 jours max après la formation ! 📅
Comme c'est dépassé, j'escalade ton dossier immédiatement à l'équipe admin ! 🚨
🔁 ESCALADE AGENT ADMIN
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On va régler ça vite ! 💪""",
            bloc_type="BLOC_J"
        )
    
    def _create_payment_direct_normal_decision(self) -> RAGDecision:
        """Décision pour paiement direct normal (≤ 7 jours) - NOUVEAU V4"""
        return RAGDecision(
            intent_type=IntentType.PAYMENT,
            search_query="paiement direct délai normal",
            search_strategy="payment_normal",
            context_needed=["délais", "paiement"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: PAIEMENT DIRECT DÉLAI NORMAL
OBLIGATION ABSOLUE - APPLIQUER LA RÉPONSE NORMALE :
Merci pour ces précisions ! 😊
Pour un paiement direct, le délai normal est de 7 jours maximum après la formation.
Comme tu es encore dans les délais normaux, il n'y a pas de souci à signaler.
Si tu as d'autres questions ou si tu souhaites un suivi, n'hésite pas à me le dire ! 😊""",
            bloc_type="BLOC_DIRECT_NORMAL"
        )
    
    def _create_cpf_delayed_decision(self) -> RAGDecision:
        """Décision pour CPF en retard (BLOC F1) - CORRECTION V3"""
        return RAGDecision(
            intent_type=IntentType.PAYMENT,
            search_query="CPF délai dépassé",
            search_strategy="cpf_delayed",
            context_needed=["cpf", "délais", "blocage"],
            priority_level="high",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: CPF DÉLAI DÉPASSÉ (BLOC F1)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC F1 :
D'après les informations que tu m'as données, comme la formation a été financée par le CPF et qu'elle s'est terminée il y a plus de 45 jours, cela dépasse le délai normal de 45 jours pour le paiement.

⚠️ Il est donc possible que le dossier soit bloqué ou qu'il nécessite une vérification !

Juste avant que je transmette ta demande 🙏
Est-ce que tu as déjà été informé par l'équipe que ton dossier CPF faisait partie des quelques cas
bloqués par la Caisse des Dépôts ?
👉 Si oui, je te donne directement toutes les infos liées à ce blocage.
Sinon, je fais remonter ta demande à notre équipe pour vérification ✅""",
            bloc_type="BLOC_F1"
        )
    
    def _create_cpf_blocked_decision(self) -> RAGDecision:
        """Décision pour CPF bloqué (BLOC F2) - NOUVEAU V4"""
        return RAGDecision(
            intent_type=IntentType.PAYMENT,
            search_query="CPF bloqué Caisse des Dépôts",
            search_strategy="cpf_blocked",
            context_needed=["cpf", "blocage", "caisse_dépôts"],
            priority_level="high",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: CPF BLOQUÉ (BLOC F2)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC F2 :
Ce dossier fait partie des quelques cas bloqués depuis la réforme CPF de février 2025.
✅ Tous les éléments nécessaires ont bien été transmis à l'organisme de contrôle 📄 🔍
❌ Mais la Caisse des Dépôts met souvent plusieurs semaines (parfois jusqu'à 2 mois) pour
redemander un document après en avoir reçu un autre.
👉 On accompagne au maximum le centre de formation pour que tout rentre dans l'ordre.
🙏 On est aussi impactés financièrement, car chaque formation a un coût pour nous.
💪 On garde confiance et on espère une issue favorable très bientôt.
🗣 Et on s'engage à revenir vers toi dès qu'on a du nouveau. Merci pour ta patience 🙏""",
            bloc_type="BLOC_F2"
        )
    
    def _create_ambassador_decision(self, message: str) -> RAGDecision:
        """Décision pour ambassadeur"""
        return RAGDecision(
            intent_type=IntentType.AMBASSADOR,
            search_query="devenir ambassadeur JAK Company",
            search_strategy="ambassador_info",
            context_needed=["ambassadeur", "commission", "processus"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: AMBASSADEUR
Un Ambassadeur, c'est quelqu'un qui veut gagner de l'argent simplement 💸
Mais surtout, c'est notre partenaire de terrain 🤝
Il parle de nos formations autour de lui (amis, entourage, réseau pro...) 👥
Et dès qu'une personne s'inscrit grâce à lui 👉 il touche une commission 🤑
Pas besoin d'être expert, il suffit d'en parler et de partager les bons contacts 🔥
Tu veux en savoir plus sur comment devenir ambassadeur ? 😊""",
            bloc_type="BLOC_AMBASSADOR"
        )
    
    def _create_ambassador_process_decision(self) -> RAGDecision:
        """Décision pour le processus ambassadeur (NOUVEAU V3) - SANS SALUTATION"""
        return RAGDecision(
            intent_type=IntentType.AMBASSADOR_PROCESS,
            search_query="processus ambassadeur étapes",
            search_strategy="ambassador_process",
            context_needed=["processus", "étapes", "inscription"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: PROCESSUS AMBASSADEUR
Tu veux devenir ambassadeur et commencer à gagner de l'argent avec nous ? C'est super simple 👇
✅ Étape 1 : Tu t'abonnes à nos réseaux
👉 Insta : https://hi.switchy.io/InstagramWeiWei
👉 Snap : https://hi.switchy.io/SnapChatWeiWei
✅ Étape 2 : Tu nous envoies une liste de contacts intéressés (nom, prénom, téléphone ou email).
➕ Si c'est une entreprise ou un pro, le SIRET est un petit bonus 😉
🔗 Formulaire ici : https://mrqz.to/AffiliationPromotion
✅ Étape 3 : Si un dossier est validé, tu touches une commission jusqu'à 60% 🤑
Et tu peux même être payé sur ton compte perso (jusqu'à 3000 €/an et 3 virements)

Tu veux qu'on t'aide à démarrer ou tu envoies ta première liste ? 📲""",
            bloc_type="BLOC_AMBASSADOR_PROCESS"
        )
    
    def _create_legal_decision(self) -> RAGDecision:
        """Décision pour questions légales"""
        return RAGDecision(
            intent_type=IntentType.LEGAL,
            search_query="récupération CPF formation",
            search_strategy="legal_info",
            context_needed=["cpf", "récupération", "droits"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: RÉCUPÉRATION CPF (BLOC LEGAL)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC LEGAL :
Je comprends ta préoccupation concernant la récupération de tes droits CPF. 
Cependant, il est important de préciser que les droits CPF ne sont pas "récupérables" 
au sens où tu l'entends. Les droits CPF sont des droits à formation, pas de l'argent 
que tu peux retirer ou récupérer.""",
            bloc_type="BLOC_LEGAL"
        )
    
    def _create_escalade_admin_decision(self) -> RAGDecision:
        """Décision pour escalade admin (BLOC 6.1)"""
        return RAGDecision(
            intent_type=IntentType.ESCALADE_ADMIN,
            search_query="escalade admin problème technique",
            search_strategy="escalade_admin",
            context_needed=["escalade", "admin", "problème"],
            priority_level="critical",
            should_escalate=True,
            system_instructions="""CONTEXTE DÉTECTÉ: ESCALADE ADMIN (BLOC 6.1)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC 6.1 :
🔁 ESCALADE AGENT ADMIN
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé dès qu'on a du nouveau ✅""",
            bloc_type="BLOC_6.1"
        )
    
    def _create_escalade_co_decision(self) -> RAGDecision:
        """Décision pour escalade CO (BLOC 6.2)"""
        return RAGDecision(
            intent_type=IntentType.ESCALADE_CO,
            search_query="escalade commercial accompagnement",
            search_strategy="escalade_co",
            context_needed=["escalade", "commercial", "accompagnement"],
            priority_level="high",
            should_escalate=True,
            system_instructions="""CONTEXTE DÉTECTÉ: ESCALADE CO (BLOC 6.2)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC 6.2 :
🔁 ESCALADE AGENT CO
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
Nous te répondrons dès que possible.""",
            bloc_type="BLOC_6.2"
        )
    
    def _create_time_decision(self, time_info: Dict) -> RAGDecision:
        """Décision pour questions de temps"""
        return RAGDecision(
            intent_type=IntentType.TIME,
            search_query="délais formation paiement",
            search_strategy="time_info",
            context_needed=["délais", "temps", "formation"],
            priority_level="medium",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: QUESTION DÉLAI
Je vais t'aider à comprendre les délais selon ton type de financement.
Peux-tu me préciser comment ta formation a été financée ? (CPF, OPCO, paiement direct)""",
            bloc_type="BLOC_TIME"
        )
    
    def _create_aggressive_decision(self) -> RAGDecision:
        """Décision pour messages agressifs (BLOC AGRO)"""
        return RAGDecision(
            intent_type=IntentType.AGGRESSIVE,
            search_query="gestion agressivité client",
            search_strategy="aggressive_handling",
            context_needed=["agressivité", "calme", "apaisement"],
            priority_level="critical",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: AGRESSIVITÉ (BLOC AGRO)
OBLIGATION ABSOLUE - APPLIQUER LE BLOC AGRO :
Être impoli ne fera pas avancer la situation plus vite. Bien au contraire. 
Souhaites-tu que je te propose un poème ou une chanson d'amour pour apaiser ton cœur ? 💌""",
            bloc_type="BLOC_AGRO"
        )
    
    def _create_fallback_decision(self, message: str) -> RAGDecision:
        """Décision de fallback"""
        return RAGDecision(
            intent_type=IntentType.FALLBACK,
            search_query=message,
            search_strategy="general_search",
            context_needed=["général"],
            priority_level="low",
            should_escalate=False,
            system_instructions="""CONTEXTE DÉTECTÉ: QUESTION GÉNÉRALE
Je suis là pour t'aider ! Peux-tu me préciser ta question concernant nos formations, 
nos services ou nos processus ? 😊""",
            bloc_type="BLOC_GENERAL"
        )

# ============================================================================
# INSTANCE GLOBALE RAG ENGINE
# ============================================================================

# Instance globale du moteur RAG pour partager la mémoire entre les requêtes
rag_engine_global = OptimizedRAGEngine()

# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.get("/")
async def root():
    """Endpoint racine avec informations sur l'API"""
    return {
        "message": "JAK Company RAG V4 API",
        "version": "6.0-Corrected",
        "status": "operational",
        "fixes": [
            "✅ Correction CPF > 45 jours → BLOC F1 obligatoire",
            "✅ Correction ambassadeur → Pas de répétition de salutation",
            "✅ Nouveau bloc BLOC_AMBASSADOR_PROCESS",
            "✅ Amélioration de la mémoire de conversation",
            "✅ NOUVEAU V4: Détection agressivité → BLOC AGRO",
            "✅ NOUVEAU V4: CPF 'oui' → BLOC F2 obligatoire",
            "✅ NOUVEAU V4: Paiement direct ≤ 7 jours → Réponse normale",
            "✅ NOUVEAU V4: Formation 'ok' → BLOC 6.2 obligatoire"
        ],
        "features": [
            "Détection optimisée des intentions",
            "Gestion des paiements corrigée",
            "Escalades automatiques (BLOCS 6.1 et 6.2)",
            "Formations avec BLOC K prioritaire",
            "Ambassadeur avec processus complet",
            "Mémoire optimisée avec TTL",
            "Détection agressivité avec BLOC AGRO",
            "Gestion CPF avec BLOC F1 et F2",
            "Paiement direct avec délais corrects",
            "Formation avec escalade automatique"
        ],
        "endpoints": {
            "POST /optimize_rag": "Analyse d'intention optimisée",
            "GET /health": "Statut de santé",
            "GET /memory_status": "Statut de la mémoire",
            "POST /clear_memory/{session_id}": "Nettoyer une session"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de santé de l'API"""
    try:
        # Vérifier les composants critiques
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "6.0-Corrected",
            "components": {
                "rag_engine": "operational",
                "detection_engine": "operational",
                "memory_store": "operational"
            },
            "memory_stats": rag_engine_global.memory_store.get_stats()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/optimize_rag")
async def optimize_rag_decision(request: Request):
    """Endpoint principal pour l'analyse RAG optimisée"""
    start_time = time.time()
    
    try:
        # Récupérer les données de la requête
        body = await request.json()
        message = body.get("message", "").strip()
        session_id = body.get("session_id", "default")
        
        if not message:
            return await _create_error_response("empty_message", "Message vide", session_id, time.time() - start_time)
        
        # Analyser l'intention
        decision = await rag_engine_global.analyze_intent(message, session_id)
        
        # Construire la réponse
        response = {
            "success": True,
            "session_id": session_id,
            "intent_type": decision.intent_type.value,
            "bloc_type": decision.bloc_type,
            "search_query": decision.search_query,
            "search_strategy": decision.search_strategy,
            "context_needed": decision.context_needed,
            "priority_level": decision.priority_level,
            "should_escalate": decision.should_escalate,
            "system_instructions": decision.system_instructions,
            "processing_time": time.time() - start_time,
            "memory_stats": rag_engine_global.memory_store.get_stats()
        }
        
        logger.info(f"RAG analysis completed for session {session_id}: {decision.intent_type.value}")
        return response
        
    except Exception as e:
        logger.error(f"Error in RAG analysis: {e}")
        return await _create_error_response("processing_error", str(e), session_id, time.time() - start_time)

async def _create_error_response(error_type: str, message: str, session_id: str, processing_time: float):
    """Crée une réponse d'erreur standardisée"""
    return {
        "success": False,
        "error_type": error_type,
        "error_message": message,
        "session_id": session_id,
        "processing_time": processing_time,
        "timestamp": time.time()
    }

@app.post("/clear_memory/{session_id}")
async def clear_memory(session_id: str):
    """Nettoie la mémoire d'une session"""
    try:
        rag_engine_global.memory_store.clear(session_id)
        return {"success": True, "message": f"Memory cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory_status")
async def memory_status():
    """Retourne le statut de la mémoire"""
    try:
        stats = rag_engine_global.memory_store.get_stats()
        return {
            "success": True,
            "memory_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DÉMARRAGE DE L'APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)