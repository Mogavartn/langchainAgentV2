#!/usr/bin/env python3
"""
Test complet pour vérifier la logique de paiement dans le contexte de l'Agent IA
"""

import asyncio
import sys
import os

# Ajouter le répertoire courant au path pour importer process.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simulation des classes nécessaires pour le test
from dataclasses import dataclass
from typing import List, Dict
from functools import lru_cache

@dataclass
class SimpleRAGDecision:
    """Structure simplifiée pour les décisions RAG"""
    search_query: str
    search_strategy: str
    context_needed: List[str]
    priority_level: str
    should_escalate: bool
    system_instructions: str

class KeywordSets:
    def __init__(self):
        self.escalade_admin_keywords = frozenset([
            # Paiements et délais anormaux
            "délai anormal", "retard anormal", "paiement en retard", "virement en retard",
            "argent pas arrivé", "virement pas reçu",
            "paiement bloqué", "virement bloqué", "argent bloqué",
            "en retard", "retard", "bloqué", "bloquée",
            # Preuves et dossiers
            "justificatif", "preuve", "attestation", "certificat", "facture",
            "dossier bloqué", "dossier en attente", "dossier suspendu",
            "consultation fichier", "accès fichier", "voir mon dossier",
            "état dossier", "suivi dossier", "dossier administratif",
            "dossier", "fichier", "accès", "consultation",
            # Problèmes techniques
            "erreur système", "bug", "problème technique", "dysfonctionnement",
            "impossible de", "ne fonctionne pas", "ça marche pas",
            "problème", "erreur", "dysfonctionnement"
        ])

class TestPaymentLogic:
    def __init__(self):
        self.keyword_sets = KeywordSets()
    
    @lru_cache(maxsize=50)
    def _detect_payment_request(self, message_lower: str) -> bool:
        """Détecte spécifiquement les demandes de paiement avec plus de précision"""
        payment_request_patterns = frozenset([
            # Demandes directes de paiement
            "j'ai pas encore reçu mes sous", "j'ai pas encore reçu mes sous",
            "j'ai pas encore été payé", "j'ai pas encore été payée",
            "j'attends toujours ma tune", "j'attends toujours mon argent",
            "j'attends toujours mon paiement", "j'attends toujours mon virement",
            "c'est quand que je serais payé", "c'est quand que je serai payé",
            "c'est quand que je vais être payé", "c'est quand que je vais être payée",
            "quand est-ce que je serai payé", "quand est-ce que je serai payée",
            "quand est-ce que je vais être payé", "quand est-ce que je vais être payée",
            "quand je serais payé", "quand je serai payé",
            "quand je vais être payé", "quand je vais être payée",
            # Demandes avec "pas encore"
            "pas encore reçu", "pas encore payé", "pas encore payée",
            "pas encore eu", "pas encore touché", "pas encore touchée",
            "n'ai pas encore reçu", "n'ai pas encore payé", "n'ai pas encore payée",
            "n'ai pas encore eu", "n'ai pas encore touché", "n'ai pas encore touchée",
            "je n'ai pas encore reçu", "je n'ai pas encore payé", "je n'ai pas encore payée",
            "je n'ai pas encore eu", "je n'ai pas encore touché", "je n'ai pas encore touchée",
            # Demandes avec "toujours"
            "j'attends toujours", "j'attends encore",
            "j'attends toujours mon argent", "j'attends toujours mon paiement",
            "j'attends toujours mon virement", "j'attends encore mon argent",
            "j'attends encore mon paiement", "j'attends encore mon virement",
            # Demandes avec "toujours pas" (NOUVEAU - CORRECTION DU BUG)
            "toujours pas reçu", "toujours pas payé", "toujours pas payée",
            "toujours pas eu", "toujours pas touché", "toujours pas touchée",
            "j'ai toujours pas reçu", "j'ai toujours pas payé", "j'ai toujours pas payée",
            "j'ai toujours pas eu", "j'ai toujours pas touché", "j'ai toujours pas touchée",
            "je n'ai toujours pas reçu", "je n'ai toujours pas payé", "je n'ai toujours pas payée",
            "je n'ai toujours pas eu", "je n'ai toujours pas touché", "je n'ai toujours pas touchée",
            # Demandes avec "toujours pas été" (NOUVEAU - CORRECTION DU BUG)
            "toujours pas été payé", "toujours pas été payée",
            "j'ai toujours pas été payé", "j'ai toujours pas été payée",
            "je n'ai toujours pas été payé", "je n'ai toujours pas été payée",
            # Demandes avec "pas"
            "pas reçu", "pas payé", "pas payée", "pas eu", "pas touché", "pas touchée",
            "n'ai pas reçu", "n'ai pas payé", "n'ai pas payée", "n'ai pas eu",
            "n'ai pas touché", "n'ai pas touchée", "je n'ai pas reçu",
            "je n'ai pas payé", "je n'ai pas payée", "je n'ai pas eu",
            "je n'ai pas touché", "je n'ai pas touchée",
            # Demandes avec "reçois quand" (NOUVEAU - CORRECTION DU BUG)
            "reçois quand", "reçois quand mes", "reçois quand mon",
            "je reçois quand", "je reçois quand mes", "je reçois quand mon",
            # Termes génériques de paiement
            "sous", "tune", "argent", "paiement", "virement", "rémunération"
        ])
        return any(term in message_lower for term in payment_request_patterns)
    
    @lru_cache(maxsize=100)
    def _has_keywords(self, message_lower: str, keyword_set: frozenset) -> bool:
        """Optimized keyword matching with caching"""
        return any(keyword in message_lower for keyword in keyword_set)
    
    @lru_cache(maxsize=50)
    def _extract_time_info(self, message_lower: str) -> dict:
        """Extrait les informations de temps et de financement du message"""
        import re
        
        # Détection des délais
        time_patterns = {
            'days': r'(\d+)\s*(jour|jours|j)',
            'months': r'(\d+)\s*(mois|moi)',
            'weeks': r'(\d+)\s*(semaine|semaines|sem)'
        }
        
        time_info = {}
        for time_type, pattern in time_patterns.items():
            match = re.search(pattern, message_lower)
            if match:
                time_info[time_type] = int(match.group(1))
        
        # Détection du type de financement
        financing_type = "unknown"
        if "cpf" in message_lower:
            financing_type = "cpf"
        elif "opco" in message_lower:
            financing_type = "opco"
        elif any(term in message_lower for term in ["direct", "payé", "financé", "moi-même"]):
            financing_type = "direct"
        
        return {
            'time_info': time_info,
            'financing_type': financing_type
        }
    
    def _create_payment_filtering_decision(self, message: str) -> SimpleRAGDecision:
        """Crée une décision pour le BLOC F (demande d'informations)"""
        return SimpleRAGDecision(
            search_query="demande informations paiement",
            search_strategy="payment_filtering",
            context_needed=["financing_type", "formation_end_date"],
            priority_level="high",
            should_escalate=False,
            system_instructions="""Tu es un assistant spécialisé dans les questions de paiement de formation.

L'utilisateur demande des informations sur son paiement mais tu n'as pas assez d'informations pour l'aider efficacement.

Pour que je puisse t'aider au mieux, est-ce que tu peux me préciser :

● Comment la formation a-t-elle été financée ? (CPF, OPCO, paiement direct)
● Et environ quand elle s'est terminée ?

Une fois que j'aurai ces informations, je pourrai te donner une réponse précise sur les délais de paiement."""
        )
    
    def _create_escalade_admin_decision(self) -> SimpleRAGDecision:
        """Crée une décision pour l'escalade admin (BLOC 6.1)"""
        return SimpleRAGDecision(
            search_query="escalade admin paiement",
            search_strategy="escalade_admin",
            context_needed=["payment_issue"],
            priority_level="critical",
            should_escalate=True,
            system_instructions="""🔁 ESCALADE AGENT ADMIN
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On te tiendra informé dès qu'on a du nouveau ✅"""
        )
    
    async def analyze_intent(self, message: str, session_id: str = "default") -> SimpleRAGDecision:
        """Analyse l'intention de manière robuste et optimisée"""
        
        try:
            message_lower = message.lower().strip()
            
            # NOUVELLES DÉTECTIONS POUR BLOCS 6.1 ET 6.2 (PRIORITÉ HAUTE)
            # Escalade Admin (BLOC 6.1) - Priorité haute
            if self._has_keywords(message_lower, self.keyword_sets.escalade_admin_keywords):
                return self._create_escalade_admin_decision()
            
            # Payment detection (high priority) - RENFORCÉE
            elif self._detect_payment_request(message_lower):
                # Extraire les informations de temps et financement
                time_financing_info = self._extract_time_info(message_lower)
                
                # Vérifier si on a déjà les informations nécessaires
                has_financing_info = time_financing_info['financing_type'] != 'unknown'
                has_time_info = bool(time_financing_info['time_info'])
                
                # Si on n'a pas les informations nécessaires, appliquer le BLOC F
                if not has_financing_info or not has_time_info:
                    return self._create_payment_filtering_decision(message)
                # Sinon, appliquer la logique spécifique selon le type de financement et délai
                elif time_financing_info['financing_type'] == 'direct' and time_financing_info['time_info'].get('days', 0) > 7:
                    return self._create_escalade_admin_decision()
                elif time_financing_info['financing_type'] == 'opco' and time_financing_info['time_info'].get('months', 0) > 2:
                    return self._create_escalade_admin_decision()
                elif time_financing_info['financing_type'] == 'cpf' and time_financing_info['time_info'].get('days', 0) > 45:
                    return self._create_escalade_admin_decision()
                else:
                    return self._create_payment_filtering_decision(message)
            
            # Fallback
            else:
                return SimpleRAGDecision(
                    search_query="general",
                    search_strategy="general",
                    context_needed=[],
                    priority_level="normal",
                    should_escalate=False,
                    system_instructions="Réponse générale"
                )
        
        except Exception as e:
            return SimpleRAGDecision(
                search_query="error",
                search_strategy="fallback",
                context_needed=[],
                priority_level="normal",
                should_escalate=False,
                system_instructions="Erreur de traitement"
            )

async def test_complete_payment_logic():
    """Test la logique complète de paiement"""
    
    print("🧪 TEST COMPLET DE LA LOGIQUE DE PAIEMENT")
    print("=" * 70)
    
    # Initialiser le moteur de test
    payment_logic = TestPaymentLogic()
    
    # Messages de test qui posaient problème
    test_messages = [
        "j'ai toujours pas reçu mon argent",
        "j'ai toujours pas reçu mes sous", 
        "j'ai toujours pas été payé",
        "je reçois quand mes sous ?"
    ]
    
    print("\n📋 MESSAGES DE TEST :")
    for i, message in enumerate(test_messages, 1):
        print(f"{i}. '{message}'")
    
    print("\n🔍 RÉSULTATS DE L'ANALYSE COMPLÈTE :")
    print("-" * 50)
    
    all_correct = True
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Message: '{message}'")
        
        # Analyser l'intention complète
        decision = await payment_logic.analyze_intent(message, f"test_session_{i}")
        
        print(f"   → Stratégie: {decision.search_strategy}")
        print(f"   → Priorité: {decision.priority_level}")
        print(f"   → Escalade: {'✅ OUI' if decision.should_escalate else '❌ NON'}")
        print(f"   → Instructions: {decision.system_instructions[:100]}...")
        
        # Vérifier que c'est bien le BLOC F qui est appliqué
        if decision.search_strategy == "payment_filtering":
            print(f"   ✅ CORRECT: BLOC F appliqué (demande d'informations)")
        elif decision.search_strategy == "escalade_admin":
            print(f"   ❌ PROBLÈME: Escalade admin appliquée au lieu du BLOC F")
            all_correct = False
        else:
            print(f"   ⚠️  ATTENTION: Autre stratégie appliquée")
            all_correct = False
    
    print("\n" + "=" * 70)
    print("🎯 RÉSULTAT ATTENDU :")
    print("Tous les messages doivent déclencher le BLOC F (payment_filtering)")
    print("et demander des informations au lieu de l'escalade admin.")
    print("=" * 70)
    
    if all_correct:
        print("\n🎉 SUCCÈS: Tous les tests passent ! Le bug est corrigé.")
        print("✅ La logique de paiement fonctionne maintenant correctement.")
    else:
        print("\n❌ ÉCHEC: Certains tests échouent. Le bug persiste.")
    
    return all_correct

if __name__ == "__main__":
    asyncio.run(test_complete_payment_logic())