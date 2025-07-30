#!/usr/bin/env python3
"""
Test pour vérifier la correction du bug de détection des demandes de paiement
"""

import asyncio
import sys
import os

# Ajouter le répertoire courant au path pour importer process.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process import OptimizedRAGEngine

async def test_payment_detection_bug_fix():
    """Test la correction du bug de détection des demandes de paiement"""
    
    print("🧪 TEST DE CORRECTION DU BUG DE DÉTECTION DES DEMANDES DE PAIEMENT")
    print("=" * 70)
    
    # Initialiser le moteur RAG
    rag_engine = OptimizedRAGEngine()
    
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
    
    print("\n🔍 RÉSULTATS DE LA DÉTECTION :")
    print("-" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Message: '{message}'")
        
        # Tester la détection de paiement
        is_payment_request = rag_engine._detect_payment_request(message.lower())
        print(f"   → Détection paiement: {'✅ OUI' if is_payment_request else '❌ NON'}")
        
        # Tester la détection d'escalade admin
        has_escalade_admin = rag_engine._has_keywords(message.lower(), rag_engine.keyword_sets.escalade_admin_keywords)
        print(f"   → Détection escalade admin: {'✅ OUI' if has_escalade_admin else '❌ NON'}")
        
        # Analyser l'intention complète
        decision = await rag_engine.analyze_intent(message, f"test_session_{i}")
        print(f"   → Décision finale: {decision.search_strategy}")
        print(f"   → Instructions système: {decision.system_instructions[:100]}...")
        
        # Vérifier la cohérence
        if is_payment_request and not has_escalade_admin:
            print(f"   ✅ CORRECT: Détection paiement sans escalade admin")
        elif has_escalade_admin and not is_payment_request:
            print(f"   ⚠️  ATTENTION: Escalade admin sans détection paiement")
        else:
            print(f"   ❌ PROBLÈME: Conflit de détection")
    
    print("\n" + "=" * 70)
    print("🎯 RÉSULTAT ATTENDU :")
    print("Tous les messages doivent être détectés comme des demandes de paiement")
    print("et déclencher le BLOC F (demande d'informations) au lieu de l'escalade admin.")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_payment_detection_bug_fix())