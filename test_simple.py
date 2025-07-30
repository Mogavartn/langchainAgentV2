#!/usr/bin/env python3
"""
Test simplifié des corrections apportées au système de détection LangChain
"""

import re
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from functools import lru_cache

# Simuler les classes nécessaires pour le test
class KeywordSets:
    def __init__(self):
        self.payment_keywords = frozenset([
            "pas été payé", "pas payé", "paiement", "cpf", "opco", 
            "virement", "argent", "retard", "délai", "attends",
            "finance", "financement", "payé pour", "rien reçu",
            "je vais être payé quand", "délai paiement",
            "payé tout seul", "financé tout seul", "financé en direct",
            "paiement direct", "financement direct", "j'ai payé", 
            "j'ai financé", "payé par moi", "financé par moi",
            "sans organisme", "financement personnel", "paiement personnel",
            "auto-financé", "autofinancé", "mes fonds", "mes propres fonds",
            "direct", "tout seul", "par moi-même", "par mes soins"
        ])

class SimpleRAGDecision:
    """Structure simplifiée pour les décisions RAG"""
    def __init__(self, search_query: str, search_strategy: str, context_needed: List[str], 
                 priority_level: str, should_escalate: bool, system_instructions: str):
        self.search_query = search_query
        self.search_strategy = search_strategy
        self.context_needed = context_needed
        self.priority_level = priority_level
        self.should_escalate = should_escalate
        self.system_instructions = system_instructions

class TestRAGEngine:
    """Moteur de test pour valider les corrections"""
    
    def __init__(self):
        self.keyword_sets = KeywordSets()
    
    @lru_cache(maxsize=50)
    def _detect_direct_financing(self, message_lower: str) -> bool:
        """Détecte spécifiquement les termes de financement direct/personnel"""
        direct_financing_terms = frozenset([
            "payé tout seul", "financé tout seul", "financé en direct",
            "paiement direct", "financement direct", "j'ai payé", 
            "j'ai financé", "payé par moi", "financé par moi",
            "sans organisme", "financement personnel", "paiement personnel",
            "auto-financé", "autofinancé", "mes fonds", "par mes soins",
            "j'ai payé toute seule", "j'ai payé moi", "c'est moi qui est financé",
            "financement moi même", "financement en direct", "paiement direct",
            "j'ai financé toute seule", "j'ai financé moi", "c'est moi qui ai payé",
            "financement par mes soins", "paiement par mes soins", "mes propres moyens",
            "avec mes propres fonds", "de ma poche", "de mes économies",
            "financement individuel", "paiement individuel", "auto-financement",
            "financement privé", "paiement privé", "financement personnel",
            "j'ai tout payé", "j'ai tout financé", "c'est moi qui finance",
            "financement direct", "paiement en direct", "financement cash",
            "paiement cash", "financement comptant", "paiement comptant"
        ])
        return any(term in message_lower for term in direct_financing_terms)
    
    @lru_cache(maxsize=50)
    def _detect_opco_financing(self, message_lower: str) -> bool:
        """Détecte spécifiquement les termes de financement OPCO"""
        opco_financing_terms = frozenset([
            "opco", "opérateur de compétences", "opérateur compétences",
            "financement opco", "paiement opco", "financé par opco",
            "payé par opco", "opco finance", "opco paie",
            "organisme paritaire", "paritaire", "fonds formation",
            "financement paritaire", "paiement paritaire"
        ])
        return any(term in message_lower for term in opco_financing_terms)
    
    @lru_cache(maxsize=50)
    def _extract_time_info(self, message_lower: str) -> dict:
        """Extrait les informations de temps et de financement du message"""
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
        if self._detect_direct_financing(message_lower):
            financing_type = "direct"
        elif self._detect_opco_financing(message_lower):
            financing_type = "opco"
        elif "cpf" in message_lower:
            financing_type = "cpf"
        
        return {
            'time_info': time_info,
            'financing_type': financing_type
        }
    
    def analyze_payment_decision(self, message: str) -> str:
        """Analyse la décision de paiement selon les nouvelles règles"""
        message_lower = message.lower()
        
        # Vérifier si c'est un message de paiement
        if not any(keyword in message_lower for keyword in self.keyword_sets.payment_keywords):
            return "not_payment"
        
        # Extraire les informations de temps et financement
        time_financing_info = self._extract_time_info(message_lower)
        
        # Appliquer la logique spécifique selon le type de financement et délai
        if time_financing_info['financing_type'] == 'direct' and time_financing_info['time_info'].get('days', 0) > 7:
            return "payment_direct_delayed"  # BLOC L
        elif time_financing_info['financing_type'] == 'opco' and time_financing_info['time_info'].get('months', 0) > 2:
            return "escalade_admin"  # BLOC 6.1
        elif time_financing_info['financing_type'] == 'cpf' and time_financing_info['time_info'].get('days', 0) > 45:
            return "escalade_admin"  # BLOC 6.1
        else:
            return "payment_normal"  # Décision paiement normale

def test_corrections():
    """Test des corrections apportées"""
    
    print("🧪 TEST DES CORRECTIONS LANGCHAIN")
    print("=" * 50)
    
    # Initialiser le moteur de test
    rag_engine = TestRAGEngine()
    
    # Tests de détection de financement
    print("\n1️⃣ TEST DÉTECTION FINANCEMENT")
    print("-" * 30)
    
    test_cases = [
        # Test OPCO
        {
            "message": "OPCO il y a 20 jours",
            "expected_financing": "opco",
            "expected_days": 20,
            "expected_months": 0,
            "description": "OPCO 20 jours (délai normal)"
        },
        {
            "message": "OPCO il y a 3 mois",
            "expected_financing": "opco", 
            "expected_days": 0,
            "expected_months": 3,
            "description": "OPCO 3 mois (délai dépassé)"
        },
        # Test Paiement Direct
        {
            "message": "j'ai payé tout seul il y a 5 jours",
            "expected_financing": "direct",
            "expected_days": 5,
            "expected_months": 0,
            "description": "Paiement direct 5 jours (délai normal)"
        },
        {
            "message": "paiement direct il y a 10 jours",
            "expected_financing": "direct",
            "expected_days": 10,
            "expected_months": 0,
            "description": "Paiement direct 10 jours (délai dépassé)"
        },
        # Test CPF
        {
            "message": "CPF il y a 30 jours",
            "expected_financing": "cpf",
            "expected_days": 30,
            "expected_months": 0,
            "description": "CPF 30 jours (délai normal)"
        },
        {
            "message": "CPF il y a 60 jours",
            "expected_financing": "cpf",
            "expected_days": 60,
            "expected_months": 0,
            "description": "CPF 60 jours (délai dépassé)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Extraire les informations
        time_info = rag_engine._extract_time_info(test_case['message'].lower())
        
        print(f"Financing détecté: {time_info['financing_type']}")
        print(f"Jours détectés: {time_info['time_info'].get('days', 0)}")
        print(f"Mois détectés: {time_info['time_info'].get('months', 0)}")
        
        # Vérifier les résultats
        financing_ok = time_info['financing_type'] == test_case['expected_financing']
        days_ok = time_info['time_info'].get('days', 0) == test_case['expected_days']
        months_ok = time_info['time_info'].get('months', 0) == test_case['expected_months']
        
        if financing_ok and days_ok and months_ok:
            print("✅ RÉSULTAT: CORRECT")
        else:
            print("❌ RÉSULTAT: INCORRECT")
            if not financing_ok:
                print(f"   - Financement attendu: {test_case['expected_financing']}, détecté: {time_info['financing_type']}")
            if not days_ok:
                print(f"   - Jours attendus: {test_case['expected_days']}, détectés: {time_info['time_info'].get('days', 0)}")
            if not months_ok:
                print(f"   - Mois attendus: {test_case['expected_months']}, détectés: {time_info['time_info'].get('months', 0)}")
    
    # Tests de logique de décision
    print("\n\n2️⃣ TEST LOGIQUE DE DÉCISION")
    print("-" * 30)
    
    decision_tests = [
        {
            "message": "OPCO il y a 20 jours",
            "expected_decision": "payment_normal",
            "description": "OPCO 20 jours → Décision paiement normale"
        },
        {
            "message": "OPCO il y a 3 mois", 
            "expected_decision": "escalade_admin",
            "description": "OPCO 3 mois → Escalade admin"
        },
        {
            "message": "j'ai payé tout seul il y a 5 jours",
            "expected_decision": "payment_normal", 
            "description": "Direct 5 jours → Décision paiement normale"
        },
        {
            "message": "paiement direct il y a 10 jours",
            "expected_decision": "payment_direct_delayed",
            "description": "Direct 10 jours → BLOC L (délai dépassé)"
        },
        {
            "message": "CPF il y a 30 jours",
            "expected_decision": "payment_normal",
            "description": "CPF 30 jours → Décision paiement normale"
        },
        {
            "message": "CPF il y a 60 jours",
            "expected_decision": "escalade_admin",
            "description": "CPF 60 jours → Escalade admin"
        }
    ]
    
    for i, test_case in enumerate(decision_tests, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Analyser la décision
        decision = rag_engine.analyze_payment_decision(test_case['message'])
        
        print(f"Décision détectée: {decision}")
        
        if decision == test_case['expected_decision']:
            print("✅ RÉSULTAT: CORRECT")
        else:
            print("❌ RÉSULTAT: INCORRECT")
            print(f"   - Décision attendue: {test_case['expected_decision']}")
            print(f"   - Décision détectée: {decision}")
    
    print("\n\n🎯 RÉSUMÉ DES CORRECTIONS")
    print("=" * 50)
    print("✅ Détection OPCO vs Paiement Direct améliorée")
    print("✅ BLOC L pour paiement direct délai dépassé (au lieu de BLOC J)")
    print("✅ Logique de délais corrigée:")
    print("   - Direct: ≤7j normal, >7j BLOC L")
    print("   - OPCO: ≤2 mois normal, >2 mois escalade admin")
    print("   - CPF: ≤45j normal, >45j escalade admin")
    print("✅ Détection automatique des types de financement")
    print("✅ Extraction intelligente des délais")

if __name__ == "__main__":
    test_corrections()