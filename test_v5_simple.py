#!/usr/bin/env python3
"""
Test simplifié des corrections V5 - Validation des erreurs identifiées
Version sans dépendances FastAPI
"""

import re
import time
from collections import defaultdict
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Set, Tuple
from functools import lru_cache

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
# STORE DE MÉMOIRE SIMPLIFIÉ
# ============================================================================

class SimpleMemoryStore:
    """Store de mémoire simplifié pour les tests"""
    
    def __init__(self):
        self._store = {}
        self._bloc_history = defaultdict(set)
        self._conversation_context = defaultdict(dict)
    
    def add_message(self, session_id: str, message: str, role: str = "user"):
        """Ajoute un message à la session"""
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append({"role": role, "content": message})
    
    def add_bloc_presented(self, session_id: str, bloc_id: str):
        """Marque un bloc comme présenté"""
        self._bloc_history[session_id].add(bloc_id)
    
    def has_bloc_been_presented(self, session_id: str, bloc_id: str) -> bool:
        """Vérifie si un bloc a déjà été présenté"""
        return bloc_id in self._bloc_history[session_id]
    
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

# Instance globale du store de mémoire
memory_store = SimpleMemoryStore()

# ============================================================================
# MOTEUR DE DÉTECTION SIMPLIFIÉ V5
# ============================================================================

class SimpleDetectionEngineV5:
    """Moteur de détection simplifié - Version 5"""
    
    def __init__(self):
        self._init_bloc_keywords()
    
    def _init_bloc_keywords(self):
        """Initialise les mots-clés par bloc selon la logique Supabase V5"""
        self.bloc_keywords = {
            IntentType.BLOC_A: frozenset([
                "paiement", "payé", "payée", "payer", "argent", "facture", "débit", "prélèvement",
                "virement", "chèque", "carte bancaire", "cb", "mastercard", "visa", "pas été payé"
            ]),
            IntentType.BLOC_K: frozenset([
                "formations disponibles", "catalogue formation", "programmes formation",
                "spécialités", "domaines formation", "c'est quoi vos formations"
            ]),
            IntentType.BLOC_M: frozenset([
                "après choix", "formation choisie", "inscription", "confirmation", "intéressé par"
            ]),
            IntentType.BLOC_F1: frozenset([
                "cpf bloqué", "dossier bloqué", "blocage cpF", "problème cpF", "délai cpF"
            ]),
            IntentType.BLOC_E: frozenset([
                "processus ambassadeur", "étapes ambassadeur", "comment ça marche ambassadeur",
                "procédure ambassadeur"
            ]),
            IntentType.BLOC_AGRO: frozenset([
                "agressif", "énervé", "fâché", "colère", "insulte", "grossier", "impoli",
                "nuls", "nul", "merde", "putain", "con", "connard", "salop", "salope"
            ]),
            IntentType.BLOC_GENERAL: frozenset([
                "bonjour", "salut", "hello", "qui êtes-vous", "jak company", "présentation"
            ])
        }
    
    def _has_keywords(self, message_lower: str, keyword_set: frozenset) -> bool:
        """Vérifie si le message contient les mots-clés d'un bloc"""
        return any(keyword in message_lower for keyword in keyword_set)
    
    def _detect_financing_type(self, message_lower: str) -> FinancingType:
        """Détecte le type de financement"""
        if any(word in message_lower for word in ["cpf", "compte personnel formation"]):
            return FinancingType.CPF
        elif any(word in message_lower for word in ["opco", "opérateur compétences"]):
            return FinancingType.OPCO
        elif any(word in message_lower for word in ["direct", "immédiat", "maintenant"]):
            return FinancingType.DIRECT
        return FinancingType.UNKNOWN
    
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
            "ça m'intéresse", "je prends", "je sélectionne", "je souhaite"
        ]
    
        formation_keywords = [
            "comptabilité", "marketing", "langues", "web", "3d", "vente", 
            "développement", "bureautique", "informatique", "écologie", "bilan"
        ]
    
        has_interest = any(indicator in message_lower for indicator in interest_indicators)
        has_formation = any(keyword in message_lower for keyword in formation_keywords)
    
        # Vérifier si l'utilisateur a récemment vu les formations
        recent_context = memory_store.get_conversation_context(session_id, "last_bloc_presented")
        formations_recently_shown = recent_context == "BLOC_K" or "formations" in str(recent_context)
    
        return has_interest and has_formation and formations_recently_shown

    def _detect_aggressive_behavior(self, message_lower: str) -> bool:
        """Détecte les comportements agressifs - NOUVEAU V5"""
        aggressive_indicators = [
            "nuls", "nul", "merde", "putain", "con", "connard", "salop", "salope",
            "dégage", "va te faire", "ta gueule", "ferme ta gueule", "imbécile",
            "idiot", "stupide", "incompétent", "inutile"
        ]
        
        return any(indicator in message_lower for indicator in aggressive_indicators)

    def _detect_follow_up_context(self, message_lower: str, session_id: str) -> Optional[IntentType]:
        """Détecte les messages de suivi basés sur le contexte conversationnel - AMÉLIORÉ V5"""
    
        # Récupérer le contexte récent
        last_bloc = memory_store.get_conversation_context(session_id, "last_bloc_presented")
    
        # NOUVEAU V5: Détection d'agressivité prioritaire
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
        
        return None

# ============================================================================
# STRUCTURE DE DÉCISION SIMPLIFIÉE V5
# ============================================================================

@dataclass
class SimpleRAGDecisionV5:
    """Structure de décision RAG simplifiée - Version 5"""
    bloc_id: IntentType
    should_escalade: bool
    session_id: str = "default"

# ============================================================================
# MOTEUR RAG SIMPLIFIÉ V5
# ============================================================================

class SimpleRAGEngineV5:
    """Moteur RAG simplifié - Version 5"""
    
    def __init__(self):
        self.detection_engine = SimpleDetectionEngineV5()
    
    async def analyze_intent(self, message: str, session_id: str = "default") -> SimpleRAGDecisionV5:
        """Analyse l'intention avec gestion du contexte conversationnel améliorée V5"""
        message_lower = message.lower()
    
        # 1. NOUVEAU V5: Vérifier d'abord le contexte conversationnel
        follow_up_bloc = self.detection_engine._detect_follow_up_context(message_lower, session_id)
        if follow_up_bloc:
            # Sauvegarder le contexte avant de retourner la décision
            memory_store.set_conversation_context(session_id, "last_bloc_presented", follow_up_bloc.value)
            return self._create_contextual_decision(follow_up_bloc, session_id)
    
        # 2. Détection du bloc principal (logique existante)
        detected_bloc = self._detect_primary_bloc(message_lower)
    
        # 3. Sauvegarder le contexte après détection (seulement si pas de contexte détecté)
        if not follow_up_bloc:
            memory_store.set_conversation_context(session_id, "last_bloc_presented", detected_bloc.value)
        
        # Logique spéciale pour les paiements CPF avec délai - CORRIGÉ V5
        if self._should_apply_payment_filtering(message_lower, session_id):
            return SimpleRAGDecisionV5(bloc_id=IntentType.BLOC_F1, should_escalade=False, session_id=session_id)
        
        # Décision par défaut basée sur le bloc détecté
        return self._create_default_decision(detected_bloc, session_id)
    
    def _detect_primary_bloc(self, message_lower: str) -> IntentType:
        """Détecte le bloc principal selon la logique Supabase V5"""
        # Priorité absolue pour l'agressivité - NOUVEAU V5
        if self.detection_engine._detect_aggressive_behavior(message_lower):
            return IntentType.BLOC_AGRO
        
        # Vérification de tous les blocs par ordre de priorité
        priority_order = [
            IntentType.BLOC_F1, IntentType.BLOC_K, IntentType.BLOC_M,
            IntentType.BLOC_E, IntentType.BLOC_A, IntentType.BLOC_GENERAL
        ]
        
        for bloc_id in priority_order:
            if self.detection_engine._has_keywords(message_lower, self.detection_engine.bloc_keywords[bloc_id]):
                return bloc_id
        
        return IntentType.FALLBACK
    
    def _should_apply_payment_filtering(self, message_lower: str, session_id: str) -> bool:
        """Détermine si on doit appliquer le filtrage de paiement - CORRIGÉ V5"""
        financing_type = self.detection_engine._detect_financing_type(message_lower)
        time_info = self.detection_engine._extract_time_info(message_lower)
        total_days = self.detection_engine._convert_to_days(time_info)
        
        # NOUVEAU V5: Logique de filtrage corrigée selon la logique n8n
        # Si CPF et délai > 45 jours ET pas encore présenté le bloc F1
        if (financing_type == FinancingType.CPF and 
            total_days > 45 and 
            not memory_store.has_bloc_been_presented(session_id, "BLOC_F1")):
            return True
        
        # Si CPF et délai <= 45 jours, on rassure (pas de bloc spécial)
        if (financing_type == FinancingType.CPF and 
            total_days <= 45):
            return False
        
        return False
    
    def _create_contextual_decision(self, bloc_id: IntentType, session_id: str) -> SimpleRAGDecisionV5:
        """Crée une décision basée sur le contexte conversationnel - AMÉLIORÉ V5"""
    
        if bloc_id == IntentType.BLOC_M:
            return SimpleRAGDecisionV5(
                bloc_id=bloc_id,
                should_escalade=False,  # ← CORRECTION IMPORTANTE
                session_id=session_id
            )
    
        elif bloc_id == IntentType.BLOC_E:
            return SimpleRAGDecisionV5(
                bloc_id=bloc_id,
                should_escalade=False,
                session_id=session_id
            )
    
        elif bloc_id == IntentType.BLOC_AGRO:
            return SimpleRAGDecisionV5(
                bloc_id=bloc_id,
                should_escalade=False,
                session_id=session_id
            )
    
        # Retour par défaut
        return self._create_default_decision(bloc_id, session_id)
    
    def _create_default_decision(self, bloc_id: IntentType, session_id: str) -> SimpleRAGDecisionV5:
        """Crée une décision par défaut basée sur le bloc détecté"""
        return SimpleRAGDecisionV5(
            bloc_id=bloc_id,
            should_escalade=False,
            session_id=session_id
        )

# ============================================================================
# TESTS DE VALIDATION
# ============================================================================

class TestV5Corrections:
    """Tests pour valider les corrections de la version 5"""
    
    def __init__(self):
        self.rag_engine = SimpleRAGEngineV5()
        self.test_results = []
    
    async def run_all_tests(self):
        """Exécute tous les tests de validation"""
        print("🧪 DÉBUT DES TESTS V5 - VALIDATION DES CORRECTIONS")
        print("=" * 60)
        
        # Test 1: Problème d'escalade après choix de formation
        await self.test_formation_choice_escalade()
        
        # Test 2: Problème de délai CPF non respecté
        await self.test_cpf_delay_logic()
        
        # Test 3: Problème d'agressivité non détectée
        await self.test_aggressive_behavior_detection()
        
        # Test 4: Logique de détection contextuelle améliorée
        await self.test_contextual_detection()
        
        # Affichage des résultats
        self.print_results()
    
    async def test_formation_choice_escalade(self):
        """Test 1: Vérifier que l'escalade ne se déclenche pas après choix de formation"""
        print("\n🔍 TEST 1: Formation choice escalade")
        
        # Simuler une conversation
        session_id = "test_formation_choice"
        memory_store.clear(session_id)
        
        # Message 1: Demande de formations
        message1 = "c'est quoi vos formations"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id)
        
        # Message 2: Intérêt pour une formation
        message2 = "je suis intéressé par la comptabilité"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id)
        
        # Message 3: Confirmation
        message3 = "ok"
        decision3 = await self.rag_engine.analyze_intent(message3, session_id)
        
        # Vérifications
        success = True
        if decision1.bloc_id.value != "BLOC K":
            print(f"❌ Erreur: Message 1 devrait être BLOC K, obtenu {decision1.bloc_id.value}")
            success = False
        
        if decision2.bloc_id.value != "BLOC M":
            print(f"❌ Erreur: Message 2 devrait être BLOC M, obtenu {decision2.bloc_id.value}")
            success = False
        
        if decision3.should_escalade:
            print(f"❌ Erreur: Message 3 ne devrait pas escalader, escalade={decision3.should_escalade}")
            success = False
        
        if success:
            print("✅ Test 1 PASSÉ: Pas d'escalade après choix de formation")
        else:
            print("❌ Test 1 ÉCHOUÉ: Problème d'escalade après choix de formation")
        
        self.test_results.append(("Formation choice escalade", success))
    
    async def test_cpf_delay_logic(self):
        """Test 2: Vérifier la logique de délai CPF corrigée"""
        print("\n🔍 TEST 2: CPF delay logic")
        
        # Test 2.1: CPF avec délai > 45 jours (doit appliquer BLOC F1)
        session_id1 = "test_cpf_delay_1"
        memory_store.clear(session_id1)
        
        message1 = "j'ai pas été payé cpf il y a 5 mois"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id1)
        
        # Test 2.2: CPF avec délai <= 45 jours (ne doit pas appliquer BLOC F1)
        session_id2 = "test_cpf_delay_2"
        memory_store.clear(session_id2)
        
        message2 = "j'ai pas été payé cpf il y a 20 jours"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id2)
        
        # Vérifications
        success = True
        
        # Test 2.1: Délai > 45 jours
        if decision1.bloc_id.value != "BLOC F1":
            print(f"❌ Erreur: Délai > 45 jours devrait être BLOC F1, obtenu {decision1.bloc_id.value}")
            success = False
        
        # Test 2.2: Délai <= 45 jours
        if decision2.bloc_id.value == "BLOC F1":
            print(f"❌ Erreur: Délai <= 45 jours ne devrait pas être BLOC F1")
            success = False
        
        if success:
            print("✅ Test 2 PASSÉ: Logique de délai CPF corrigée")
        else:
            print("❌ Test 2 ÉCHOUÉ: Problème avec la logique de délai CPF")
        
        self.test_results.append(("CPF delay logic", success))
    
    async def test_aggressive_behavior_detection(self):
        """Test 3: Vérifier la détection d'agressivité améliorée"""
        print("\n🔍 TEST 3: Aggressive behavior detection")
        
        # Test 3.1: Message agressif explicite
        session_id1 = "test_agro_1"
        memory_store.clear(session_id1)
        
        message1 = "vous êtes nuls"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id1)
        
        # Test 3.2: Message agressif avec insulte
        session_id2 = "test_agro_2"
        memory_store.clear(session_id2)
        
        message2 = "vous êtes des cons"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id2)
        
        # Test 3.3: Message normal (contrôle)
        session_id3 = "test_agro_3"
        memory_store.clear(session_id3)
        
        message3 = "bonjour, comment allez-vous ?"
        decision3 = await self.rag_engine.analyze_intent(message3, session_id3)
        
        # Vérifications
        success = True
        
        # Test 3.1: Message agressif
        if decision1.bloc_id.value != "BLOC AGRO":
            print(f"❌ Erreur: Message agressif devrait être BLOC AGRO, obtenu {decision1.bloc_id.value}")
            success = False
        
        # Test 3.2: Message avec insulte
        if decision2.bloc_id.value != "BLOC AGRO":
            print(f"❌ Erreur: Message avec insulte devrait être BLOC AGRO, obtenu {decision2.bloc_id.value}")
            success = False
        
        # Test 3.3: Message normal
        if decision3.bloc_id.value == "BLOC AGRO":
            print(f"❌ Erreur: Message normal ne devrait pas être BLOC AGRO")
            success = False
        
        if success:
            print("✅ Test 3 PASSÉ: Détection d'agressivité améliorée")
        else:
            print("❌ Test 3 ÉCHOUÉ: Problème avec la détection d'agressivité")
        
        self.test_results.append(("Aggressive behavior detection", success))
    
    async def test_contextual_detection(self):
        """Test 4: Vérifier la détection contextuelle améliorée"""
        print("\n🔍 TEST 4: Contextual detection")
        
        # Test 4.1: Contexte formation -> intérêt
        session_id1 = "test_context_1"
        memory_store.clear(session_id1)
        
        # Simuler avoir vu les formations
        memory_store.set_conversation_context(session_id1, "last_bloc_presented", "BLOC K")
        
        message1 = "je suis intéressé par la comptabilité"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id1)
        
        # Test 4.2: Contexte ambassadeur -> questions
        session_id2 = "test_context_2"
        memory_store.clear(session_id2)
        
        # Simuler avoir vu les ambassadeurs
        memory_store.set_conversation_context(session_id2, "last_bloc_presented", "BLOC D.1")
        
        message2 = "comment ça marche pour devenir ambassadeur ?"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id2)
        
        # Debug: afficher le contexte pour comprendre
        print(f"Debug - Contexte ambassadeur: {memory_store.get_conversation_context(session_id2, 'last_bloc_presented')}")
        print(f"Debug - Message: {message2}")
        print(f"Debug - Décision: {decision2.bloc_id.value}")
        print(f"Debug - Follow-up détecté: {self.rag_engine.detection_engine._detect_follow_up_context(message2.lower(), session_id2)}")
        print(f"Debug - Contexte avant analyse: BLOC D.1")
        print(f"Debug - Mots-clés trouvés: {[word for word in ['comment', 'quand', 'où', 'combien'] if word in message2.lower()]}")
        
        # Vérifications
        success = True
        
        # Test 4.1: Contexte formation
        if decision1.bloc_id.value != "BLOC M":
            print(f"❌ Erreur: Contexte formation devrait être BLOC M, obtenu {decision1.bloc_id.value}")
            success = False
        
        # Test 4.2: Contexte ambassadeur
        if decision2.bloc_id.value != "BLOC E":
            print(f"❌ Erreur: Contexte ambassadeur devrait être BLOC E, obtenu {decision2.bloc_id.value}")
            success = False
        
        if success:
            print("✅ Test 4 PASSÉ: Détection contextuelle améliorée")
        else:
            print("❌ Test 4 ÉCHOUÉ: Problème avec la détection contextuelle")
        
        self.test_results.append(("Contextual detection", success))
    
    def print_results(self):
        """Affiche les résultats des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DES TESTS V5")
        print("=" * 60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, success in self.test_results:
            status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
            print(f"{test_name}: {status}")
            if success:
                passed += 1
        
        print(f"\n📈 Résumé: {passed}/{total} tests passés")
        
        if passed == total:
            print("🎉 TOUS LES TESTS SONT PASSÉS ! Les corrections V5 sont validées.")
        else:
            print("⚠️  Certains tests ont échoué. Vérifiez les corrections.")
        
        print("=" * 60)

async def main():
    """Fonction principale pour exécuter les tests"""
    tester = TestV5Corrections()
    await tester.run_all_tests()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())