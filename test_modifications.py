#!/usr/bin/env python3
"""
Script de test pour vérifier les modifications apportées au système de gestion des formations et paiements.
"""

import asyncio
import sys
import os

# Ajouter le répertoire courant au path pour importer process
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process import OptimizedRAGEngine, KEYWORD_SETS

async def test_formation_detection():
    """Test de la détection des questions sur les formations"""
    print("🧪 TEST DÉTECTION FORMATIONS")
    print("=" * 50)
    
    engine = OptimizedRAGEngine()
    
    test_cases = [
        "quelles sont vos formations ?",
        "vous proposez quoi comme formations ?",
        "formations disponibles ?",
        "catalogue formations ?",
        "qu'est-ce que vous proposez comme formations ?"
    ]
    
    for message in test_cases:
        decision = await engine.analyze_intent(message)
        print(f"Message: '{message}'")
        print(f"Type: {decision.search_strategy}")
        print(f"Instructions: {decision.system_instructions[:100]}...")
        print(f"Priorité: {decision.priority_level}")
        print("-" * 30)

async def test_direct_financing_detection():
    """Test de la détection des financements directs"""
    print("\n🧪 TEST DÉTECTION FINANCEMENT DIRECT")
    print("=" * 50)
    
    engine = OptimizedRAGEngine()
    
    test_cases = [
        "j'ai payé toute seule",
        "j'ai payé moi",
        "c'est moi qui est financé",
        "financement moi même",
        "financement en direct",
        "paiement direct",
        "j'ai financé toute seule",
        "j'ai financé moi",
        "c'est moi qui ai payé",
        "financement par mes soins",
        "paiement par mes soins",
        "mes propres moyens",
        "avec mes propres fonds",
        "de ma poche",
        "de mes économies",
        "financement individuel",
        "paiement individuel",
        "auto-financement",
        "financement privé",
        "paiement privé",
        "financement personnel",
        "j'ai tout payé",
        "j'ai tout financé",
        "c'est moi qui finance",
        "financement direct",
        "paiement en direct",
        "financement cash",
        "paiement cash",
        "financement comptant",
        "paiement comptant"
    ]
    
    for message in test_cases:
        is_direct = engine._detect_direct_financing(message.lower())
        status = "✅ DÉTECTÉ" if is_direct else "❌ NON DÉTECTÉ"
        print(f"{status}: '{message}'")

async def test_payment_detection():
    """Test de la détection des questions de paiement"""
    print("\n🧪 TEST DÉTECTION PAIEMENTS")
    print("=" * 50)
    
    engine = OptimizedRAGEngine()
    
    test_cases = [
        "j'ai pas été payé",
        "je n'ai pas reçu mon paiement",
        "pas de virement reçu",
        "délai paiement formation",
        "quand vais-je être payé ?"
    ]
    
    for message in test_cases:
        decision = await engine.analyze_intent(message)
        print(f"Message: '{message}'")
        print(f"Type: {decision.search_strategy}")
        print(f"Priorité: {decision.priority_level}")
        print(f"Escalade: {decision.should_escalate}")
        print("-" * 30)

async def test_keyword_sets():
    """Test des ensembles de mots-clés"""
    print("\n🧪 TEST ENSEMBLES MOTS-CLÉS")
    print("=" * 50)
    
    # Test formation keywords
    formation_test = "quelles formations proposez-vous ?"
    has_formation = any(keyword in formation_test.lower() for keyword in KEYWORD_SETS.formation_keywords)
    print(f"Formation détectée: {has_formation}")
    
    # Test payment keywords
    payment_test = "j'ai payé toute seule"
    has_payment = any(keyword in payment_test.lower() for keyword in KEYWORD_SETS.payment_keywords)
    print(f"Paiement détecté: {has_payment}")
    
    # Test direct financing
    engine = OptimizedRAGEngine()
    is_direct = engine._detect_direct_financing(payment_test.lower())
    print(f"Financement direct détecté: {is_direct}")

async def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DES TESTS - MODIFICATIONS FORMATIONS ET PAIEMENTS")
    print("=" * 60)
    
    await test_formation_detection()
    await test_direct_financing_detection()
    await test_payment_detection()
    await test_keyword_sets()
    
    print("\n✅ TOUS LES TESTS TERMINÉS")
    print("=" * 60)
    print("📋 RÉSUMÉ DES MODIFICATIONS:")
    print("1. ✅ BLOC K prioritaire pour les formations")
    print("2. ✅ Détection renforcée des financements directs")
    print("3. ✅ BLOC J pour paiements directs délai dépassé")
    print("4. ✅ Nouveaux termes de financement direct ajoutés")

if __name__ == "__main__":
    asyncio.run(main())