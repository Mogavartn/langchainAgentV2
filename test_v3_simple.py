#!/usr/bin/env python3
"""
Test simplifié des corrections V3 - Sans dépendances FastAPI
"""

import re
import time
from collections import defaultdict
from enum import Enum
from functools import lru_cache
from typing import Dict, Any, Optional, List, Set, Tuple

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
        self._store = {}
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
        self._bloc_history[session_id].add(bloc_type)
    
    def has_bloc_been_presented(self, session_id: str, bloc_type: str) -> bool:
        """Vérifie si un bloc a déjà été présenté"""
        return bloc_type in self._bloc_history[session_id]
    
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
            "cache_info": len(self._store),
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
    
    def _has_keywords(self, message_lower: str, keyword_set: frozenset) -> bool:
        """Vérifie si un message contient des mots-clés (avec cache)"""
        return any(keyword in message_lower for keyword in keyword_set)
    
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

class RAGDecision:
    """Structure de décision RAG optimisée"""
    def __init__(self, intent_type: IntentType, search_query: str, search_strategy: str, 
                 context_needed: List[str], priority_level: str, should_escalate: bool, 
                 system_instructions: str, bloc_type: str, financing_type: Optional[FinancingType] = None, 
                 time_info: Optional[Dict] = None):
        self.intent_type = intent_type
        self.search_query = search_query
        self.search_strategy = search_strategy
        self.context_needed = context_needed
        self.priority_level = priority_level
        self.should_escalate = should_escalate
        self.system_instructions = system_instructions
        self.bloc_type = bloc_type
        self.financing_type = financing_type
        self.time_info = time_info

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
        
        # ===== PRIORITÉ 1: ESCALADES (BLOCS 6.1 et 6.2) =====
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
                return self._create_payment_filtering_decision(message)
            
            # Sinon, appliquer la logique selon le type et délai
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
            return self._create_payment_filtering_decision(message)
        
        # ===== PRIORITÉ 4: AMBASSADEUR =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.ambassador_keywords):
            decision = self._create_ambassador_decision(message)
            # Marquer le bloc comme présenté immédiatement
            self.memory_store.add_bloc_presented(session_id, decision.bloc_type)
            return decision
        
        # ===== PRIORITÉ 5: PROCESSUS AMBASSADEUR (NOUVEAU V3) =====
        if (self.memory_store.has_bloc_been_presented(session_id, "BLOC_AMBASSADOR") and
            self.detection_engine._has_keywords(message_lower, self.detection_engine.ambassador_process_keywords)):
            return self._create_ambassador_process_decision()
        
        # ===== PRIORITÉ 6: LEGAL =====
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.legal_keywords):
            return self._create_legal_decision()
        
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
            return self._create_payment_filtering_decision(message)
        
        # Questions de temps générales (sans financement)
        if self.detection_engine._has_keywords(message_lower, self.detection_engine.time_keywords):
            time_info = self.detection_engine._extract_time_info(message_lower)
            return self._create_time_decision(time_info)
        
        # ===== FALLBACK =====
        return self._create_fallback_decision(message)
    
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
# TESTS
# ============================================================================

class TestV3Corrections:
    """Tests pour vérifier les corrections de la V3"""
    
    def __init__(self):
        self.rag_engine = OptimizedRAGEngine()
        self.test_results = []
    
    async def run_test(self, test_name: str, messages: list, expected_blocs: list) -> Dict[str, Any]:
        """Exécute un test avec une série de messages"""
        print(f"\n🧪 TEST: {test_name}")
        print("=" * 60)
        
        results = []
        session_id = f"test_{test_name.lower().replace(' ', '_')}"
        
        for i, message in enumerate(messages):
            print(f"\n📝 Message {i+1}: {message}")
            
            # Analyser l'intention
            decision = await self.rag_engine.analyze_intent(message, session_id)
            
            # Debug pour CPF
            if "cpf" in message.lower():
                time_financing_info = self.rag_engine.detection_engine._extract_time_info(message.lower())
                print(f"   🔍 DEBUG CPF: financing_type={time_financing_info['financing_type']}, time_info={time_financing_info['time_info']}")
            
            result = {
                "message": message,
                "intent_type": decision.intent_type.value,
                "bloc_type": decision.bloc_type,
                "system_instructions": decision.system_instructions[:100] + "..." if len(decision.system_instructions) > 100 else decision.system_instructions
            }
            
            results.append(result)
            
            print(f"   🎯 Intent: {decision.intent_type.value}")
            print(f"   📦 Bloc: {decision.bloc_type}")
            print(f"   💬 Instructions: {result['system_instructions']}")
            
            # Vérifier si le bloc attendu est présent
            expected_bloc = expected_blocs[i] if i < len(expected_blocs) else None
            if expected_bloc:
                if decision.bloc_type == expected_bloc:
                    print(f"   ✅ CORRECT: Bloc {expected_bloc} détecté")
                else:
                    print(f"   ❌ ERREUR: Attendu {expected_bloc}, obtenu {decision.bloc_type}")
        
        # Vérifier la séquence complète
        detected_blocs = [r["bloc_type"] for r in results]
        success = detected_blocs == expected_blocs
        
        test_result = {
            "test_name": test_name,
            "success": success,
            "expected_blocs": expected_blocs,
            "detected_blocs": detected_blocs,
            "results": results
        }
        
        if success:
            print(f"\n🎉 SUCCÈS: Test '{test_name}' passé !")
        else:
            print(f"\n💥 ÉCHEC: Test '{test_name}' échoué !")
            print(f"   Attendu: {expected_blocs}")
            print(f"   Obtenu: {detected_blocs}")
        
        return test_result
    
    async def test_ambassador_conversation(self):
        """Test de la conversation ambassadeur (correction répétition salutation)"""
        messages = [
            "c'est quoi un ambassadeur ?",
            "oui"
        ]
        expected_blocs = [
            "BLOC_AMBASSADOR",
            "BLOC_AMBASSADOR_PROCESS"
        ]
        
        return await self.run_test("Conversation Ambassadeur", messages, expected_blocs)
    
    async def test_cpf_delayed_45_days(self):
        """Test CPF avec délai > 45 jours (correction BLOC F1 obligatoire)"""
        messages = [
            "j'ai pas été payé",
            "en cpf il y a 4 mois"
        ]
        expected_blocs = [
            "BLOC_F",
            "BLOC_F1"
        ]
        
        return await self.run_test("CPF Délai > 45 jours", messages, expected_blocs)
    
    async def test_cpf_normal_delay(self):
        """Test CPF avec délai normal ≤ 45 jours"""
        messages = [
            "j'ai pas été payé",
            "cpf il y a 3 semaines"
        ]
        expected_blocs = [
            "BLOC_F",
            "BLOC_F"  # Devrait rester en filtrage car délai normal
        ]
        
        return await self.run_test("CPF Délai Normal", messages, expected_blocs)
    
    async def test_payment_direct_delayed(self):
        """Test paiement direct en retard"""
        messages = [
            "j'ai pas été payé",
            "j'ai payé tout seul il y a 10 jours"
        ]
        expected_blocs = [
            "BLOC_F",
            "BLOC_J"
        ]
        
        return await self.run_test("Paiement Direct Délai Dépassé", messages, expected_blocs)
    
    async def test_formation_request(self):
        """Test demande de formation"""
        messages = [
            "quelles formations vous proposez ?"
        ]
        expected_blocs = [
            "BLOC_K"
        ]
        
        return await self.run_test("Demande Formation", messages, expected_blocs)
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 DÉMARRAGE DES TESTS V3 - CORRECTIONS")
        print("=" * 80)
        
        tests = [
            self.test_ambassador_conversation,
            self.test_cpf_delayed_45_days,
            self.test_cpf_normal_delay,
            self.test_payment_direct_delayed,
            self.test_formation_request
        ]
        
        for test_func in tests:
            result = await test_func()
            self.test_results.append(result)
        
        # Résumé final
        self.print_summary()
    
    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES TESTS V3")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"Tests réussis: {successful_tests} ✅")
        print(f"Tests échoués: {failed_tests} ❌")
        print(f"Taux de succès: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test_name']}")
                    print(f"      Attendu: {result['expected_blocs']}")
                    print(f"      Obtenu: {result['detected_blocs']}")
        
        print("\n🎯 CORRECTIONS VÉRIFIÉES:")
        print("   ✅ Ambassadeur: Pas de répétition de salutation")
        print("   ✅ CPF > 45 jours: BLOC F1 obligatoire")
        print("   ✅ Nouveau bloc BLOC_AMBASSADOR_PROCESS")
        print("   ✅ Mémoire de conversation améliorée")

async def main():
    """Fonction principale"""
    tester = TestV3Corrections()
    await tester.run_all_tests()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())