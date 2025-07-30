#!/usr/bin/env python3
"""
Script de test pour identifier les problèmes de reconnaissance des délais
dans le système de paiement OPCO, CPF et direct.
"""

import re
import sys
import os

# Ajouter le répertoire courant au path pour importer process.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process import OptimizedRAGEngine

def test_time_extraction():
    """Test de la méthode _extract_time_info"""
    
    # Initialiser le moteur RAG
    rag_engine = OptimizedRAGEngine()
    
    # Cas de test basés sur les conversations fournies
    test_cases = [
        # OPCO - problèmes identifiés
        {
            "message": "OPCO il y a 18 jours",
            "expected": {"financing_type": "opco", "time_info": {"days": 18}},
            "description": "OPCO avec jours - devrait détecter opco et 18 jours"
        },
        {
            "message": "OPCO il y a 6 semaines", 
            "expected": {"financing_type": "opco", "time_info": {"weeks": 6}},
            "description": "OPCO avec semaines - devrait détecter opco et 6 semaines"
        },
        {
            "message": "OPCO il y a 1 mois",
            "expected": {"financing_type": "opco", "time_info": {"months": 1}},
            "description": "OPCO avec mois - devrait détecter opco et 1 mois"
        },
        {
            "message": "OPCO il y a 5 mois",
            "expected": {"financing_type": "opco", "time_info": {"months": 5}},
            "description": "OPCO avec mois - devrait détecter opco et 5 mois"
        },
        
        # CPF - tests
        {
            "message": "CPF il y a 30 jours",
            "expected": {"financing_type": "cpf", "time_info": {"days": 30}},
            "description": "CPF avec jours - devrait détecter cpf et 30 jours"
        },
        {
            "message": "CPF il y a 2 mois",
            "expected": {"financing_type": "cpf", "time_info": {"months": 2}},
            "description": "CPF avec mois - devrait détecter cpf et 2 mois"
        },
        
        # Direct - tests
        {
            "message": "j'ai payé tout seul il y a 10 jours",
            "expected": {"financing_type": "direct", "time_info": {"days": 10}},
            "description": "Direct avec jours - devrait détecter direct et 10 jours"
        },
        {
            "message": "paiement direct il y a 3 semaines",
            "expected": {"financing_type": "direct", "time_info": {"weeks": 3}},
            "description": "Direct avec semaines - devrait détecter direct et 3 semaines"
        },
        
        # Cas complexes
        {
            "message": "j'ai pas été payé OPCO il y a 18 jours",
            "expected": {"financing_type": "opco", "time_info": {"days": 18}},
            "description": "Message complet avec OPCO et jours"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 6 semaines",
            "expected": {"financing_type": "opco", "time_info": {"weeks": 6}},
            "description": "Message complet avec OPCO et semaines"
        }
    ]
    
    print("=== TEST DE RECONNAISSANCE DES DÉLAIS ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Extraire les informations
        result = rag_engine._extract_time_info(test_case['message'].lower())
        
        print(f"Résultat obtenu:")
        print(f"  - Type financement: {result['financing_type']}")
        print(f"  - Info temps: {result['time_info']}")
        
        # Vérifier les résultats
        financing_ok = result['financing_type'] == test_case['expected']['financing_type']
        time_ok = result['time_info'] == test_case['expected']['time_info']
        
        if financing_ok and time_ok:
            print("✅ SUCCÈS")
        else:
            print("❌ ÉCHEC")
            if not financing_ok:
                print(f"  - Type financement attendu: {test_case['expected']['financing_type']}")
            if not time_ok:
                print(f"  - Temps attendu: {test_case['expected']['time_info']}")
        
        print()

def test_payment_logic():
    """Test de la logique de traitement des paiements"""
    
    rag_engine = OptimizedRAGEngine()
    
    test_cases = [
        # OPCO - délais dépassés
        {
            "message": "j'ai pas été payé OPCO il y a 18 jours",
            "expected_decision": "FILTRAGE PAIEMENT",  # Devrait appliquer BLOC F car délai < 2 mois
            "description": "OPCO 18 jours - délai normal, devrait filtrer"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 6 semaines", 
            "expected_decision": "FILTRAGE PAIEMENT",  # Devrait appliquer BLOC F car délai < 2 mois
            "description": "OPCO 6 semaines - délai normal, devrait filtrer"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 1 mois",
            "expected_decision": "FILTRAGE PAIEMENT",  # Devrait appliquer BLOC F car délai < 2 mois
            "description": "OPCO 1 mois - délai normal, devrait filtrer"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 5 mois",
            "expected_decision": "ESCALADE ADMIN",  # Devrait escalader car délai > 2 mois
            "description": "OPCO 5 mois - délai dépassé, devrait escalader"
        },
        
        # Direct - délais dépassés
        {
            "message": "j'ai pas été payé j'ai payé tout seul il y a 10 jours",
            "expected_decision": "PAIEMENT DIRECT DÉLAI DÉPASSÉ",  # Devrait appliquer BLOC L car > 7 jours
            "description": "Direct 10 jours - délai dépassé, devrait appliquer BLOC L"
        },
        {
            "message": "j'ai pas été payé paiement direct il y a 3 jours",
            "expected_decision": "PAIEMENT",  # Délai normal, réponse normale
            "description": "Direct 3 jours - délai normal, réponse normale"
        }
    ]
    
    print("=== TEST DE LOGIQUE DE PAIEMENT ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Analyser l'intention
        decision = rag_engine.analyze_intent(test_case['message'], "test_session")
        
        # Extraire le type de décision
        decision_type = "UNKNOWN"
        if "FILTRAGE PAIEMENT" in decision.system_instructions:
            decision_type = "FILTRAGE PAIEMENT"
        elif "ESCALADE AGENT ADMIN" in decision.system_instructions:
            decision_type = "ESCALADE ADMIN"
        elif "PAIEMENT DIRECT DÉLAI DÉPASSÉ" in decision.system_instructions:
            decision_type = "PAIEMENT DIRECT DÉLAI DÉPASSÉ"
        elif "PAIEMENT FORMATION" in decision.system_instructions:
            decision_type = "PAIEMENT"
        
        print(f"Décision obtenue: {decision_type}")
        print(f"Escalade requise: {decision.should_escalate}")
        
        # Vérifier le résultat
        if decision_type == test_case['expected_decision']:
            print("✅ SUCCÈS")
        else:
            print("❌ ÉCHEC")
            print(f"  - Décision attendue: {test_case['expected_decision']}")
        
        print()

def test_regex_patterns():
    """Test des patterns regex pour la détection des délais"""
    
    print("=== TEST DES PATTERNS REGEX ===\n")
    
    # Patterns actuels
    patterns = {
        'days': r'(\d+)\s*(jour|jours|j)',
        'months': r'(\d+)\s*(mois|moi)',
        'weeks': r'(\d+)\s*(semaine|semaines|sem)'
    }
    
    test_messages = [
        "il y a 18 jours",
        "il y a 6 semaines", 
        "il y a 1 mois",
        "il y a 5 mois",
        "il y a 3 semaines",
        "il y a 10 jours",
        "il y a 2 mois"
    ]
    
    for message in test_messages:
        print(f"Message: '{message}'")
        message_lower = message.lower()
        
        for time_type, pattern in patterns.items():
            match = re.search(pattern, message_lower)
            if match:
                value = int(match.group(1))
                print(f"  - {time_type}: {value}")
            else:
                print(f"  - {time_type}: non détecté")
        
        print()

if __name__ == "__main__":
    print("🔍 DIAGNOSTIC DES PROBLÈMES DE RECONNAISSANCE DES DÉLAIS\n")
    print("=" * 60)
    
    test_regex_patterns()
    print("=" * 60)
    
    test_time_extraction()
    print("=" * 60)
    
    test_payment_logic()
    print("=" * 60)
    
    print("\n📋 RÉSUMÉ DES PROBLÈMES IDENTIFIÉS:")
    print("1. La méthode _extract_time_info semble correcte")
    print("2. Les patterns regex semblent fonctionner")
    print("3. Le problème pourrait être dans la logique de décision")
    print("4. Vérifier si les délais sont correctement comparés")