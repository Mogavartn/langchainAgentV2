#!/usr/bin/env python3
"""
Test des corrections apportées au système de détection LangChain
"""

import asyncio
import sys
import os

# Ajouter le répertoire courant au path pour importer process.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process import OptimizedRAGEngine, memory_store

async def test_corrections():
    """Test des corrections apportées"""
    
    print("🧪 TEST DES CORRECTIONS LANGCHAIN")
    print("=" * 50)
    
    # Initialiser le moteur RAG
    rag_engine = OptimizedRAGEngine()
    
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
            "expected_decision": "payment_decision",
            "description": "OPCO 20 jours → Décision paiement normale"
        },
        {
            "message": "OPCO il y a 3 mois", 
            "expected_decision": "escalade_admin",
            "description": "OPCO 3 mois → Escalade admin"
        },
        {
            "message": "j'ai payé tout seul il y a 5 jours",
            "expected_decision": "payment_decision", 
            "description": "Direct 5 jours → Décision paiement normale"
        },
        {
            "message": "paiement direct il y a 10 jours",
            "expected_decision": "payment_direct_delayed",
            "description": "Direct 10 jours → BLOC L (délai dépassé)"
        }
    ]
    
    for i, test_case in enumerate(decision_tests, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Analyser l'intention
        decision = await rag_engine.analyze_intent(test_case['message'], "test_session")
        
        # Identifier le type de décision
        decision_type = "unknown"
        if "BLOC L" in decision.system_instructions:
            decision_type = "payment_direct_delayed"
        elif "ESCALADE AGENT ADMIN" in decision.system_instructions:
            decision_type = "escalade_admin"
        elif "PAIEMENT FORMATION" in decision.system_instructions:
            decision_type = "payment_decision"
        
        print(f"Décision détectée: {decision_type}")
        
        if decision_type == test_case['expected_decision']:
            print("✅ RÉSULTAT: CORRECT")
        else:
            print("❌ RÉSULTAT: INCORRECT")
            print(f"   - Décision attendue: {test_case['expected_decision']}")
            print(f"   - Décision détectée: {decision_type}")
    
    # Tests de détection formation
    print("\n\n3️⃣ TEST DÉTECTION FORMATION")
    print("-" * 30)
    
    # Simuler une conversation avec BLOC K
    session_id = "formation_test"
    memory_store.clear(session_id)
    
    # Ajouter le BLOC K dans l'historique
    memory_store.add_message(session_id, "🎓 +100 formations disponibles chez JAK Company ! 🎓", "assistant")
    
    formation_tests = [
        {
            "message": "j'aimerais faire en anglais pro",
            "expected_decision": "formation_escalade",
            "description": "Choix formation après BLOC K → BLOC M"
        },
        {
            "message": "ok pour qu'on me recontacte",
            "expected_decision": "formation_confirmation", 
            "description": "Confirmation après BLOC M → BLOC 6.2"
        }
    ]
    
    for i, test_case in enumerate(formation_tests, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Analyser l'intention
        decision = await rag_engine.analyze_intent(test_case['message'], session_id)
        
        # Identifier le type de décision
        decision_type = "unknown"
        if "BLOC M" in decision.system_instructions:
            decision_type = "formation_escalade"
        elif "CONFIRMATION ESCALADE FORMATION" in decision.system_instructions:
            decision_type = "formation_confirmation"
        
        print(f"Décision détectée: {decision_type}")
        
        if decision_type == test_case['expected_decision']:
            print("✅ RÉSULTAT: CORRECT")
        else:
            print("❌ RÉSULTAT: INCORRECT")
            print(f"   - Décision attendue: {test_case['expected_decision']}")
            print(f"   - Décision détectée: {decision_type}")
    
    print("\n\n🎯 RÉSUMÉ DES CORRECTIONS")
    print("=" * 50)
    print("✅ Détection OPCO vs Paiement Direct améliorée")
    print("✅ BLOC L pour paiement direct délai dépassé (au lieu de BLOC J)")
    print("✅ BLOC M pour escalade formation ajouté")
    print("✅ Logique de délais corrigée:")
    print("   - Direct: ≤7j normal, >7j BLOC L")
    print("   - OPCO: ≤2 mois normal, >2 mois escalade admin")
    print("   - CPF: ≤45j normal, >45j escalade admin")
    print("✅ Détection automatique des types de financement")
    print("✅ Extraction intelligente des délais")

if __name__ == "__main__":
    asyncio.run(test_corrections())