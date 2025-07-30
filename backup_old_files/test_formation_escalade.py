#!/usr/bin/env python3
"""
Test de la logique d'escalade de formation
Valide que les conversations suivent le bon flux : K → K+CPF → 6.2
"""

import asyncio
import sys
import os

# Ajouter le répertoire courant au path pour importer process.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process.py import OptimizedRAGEngine, memory_store

async def test_formation_conversation():
    """Test de la conversation de formation avec escalade"""
    
    print("🧪 TEST DE LA LOGIQUE D'ESCALADE FORMATION")
    print("=" * 50)
    
    # Initialiser le moteur RAG
    rag_engine = OptimizedRAGEngine()
    session_id = "test_formation_escalade"
    
    # Nettoyer la session de test
    memory_store.clear(session_id)
    
    # Test 1: Première demande de formation
    print("\n📝 Test 1: Première demande de formation")
    message1 = "je veux faire une formation"
    
    # Simuler l'ajout du message à la mémoire
    memory_store.add_message(session_id, message1, "user")
    
    # Analyser l'intention
    decision1 = await rag_engine.analyze_intent(message1, session_id)
    
    print(f"Message: {message1}")
    print(f"Décision: {decision1.search_strategy} - {decision1.priority_level}")
    print(f"Instructions: {decision1.system_instructions[:100]}...")
    print(f"Escalade requise: {decision1.should_escalate}")
    
    # Simuler la réponse du bot (BLOC K)
    bloc_k_response = "🎓 +100 formations disponibles chez JAK Company ! 🎓"
    memory_store.add_message(session_id, bloc_k_response, "assistant")
    
    # Test 2: Demande spécifique après présentation
    print("\n📝 Test 2: Demande spécifique après présentation")
    message2 = "je voudrais faire une formation en anglais pro"
    
    # Simuler l'ajout du message à la mémoire
    memory_store.add_message(session_id, message2, "user")
    
    # Analyser l'intention
    decision2 = await rag_engine.analyze_intent(message2, session_id)
    
    print(f"Message: {message2}")
    print(f"Décision: {decision2.search_strategy} - {decision2.priority_level}")
    print(f"Instructions: {decision2.system_instructions[:100]}...")
    print(f"Escalade requise: {decision2.should_escalate}")
    
    # Simuler la réponse du bot (BLOC K + CPF)
    bloc_k_cpf_response = "🎓 +100 formations disponibles chez JAK Company ! 🎓 + CPF info"
    memory_store.add_message(session_id, bloc_k_cpf_response, "assistant")
    
    # Test 3: Demande d'escalade
    print("\n📝 Test 3: Demande d'escalade")
    message3 = "ok je veux bien"
    
    # Simuler l'ajout du message à la mémoire
    memory_store.add_message(session_id, message3, "user")
    
    # Analyser l'intention
    decision3 = await rag_engine.analyze_intent(message3, session_id)
    
    print(f"Message: {message3}")
    print(f"Décision: {decision3.search_strategy} - {decision3.priority_level}")
    print(f"Instructions: {decision3.system_instructions[:100]}...")
    print(f"Escalade requise: {decision3.should_escalate}")
    
    # Vérifier que c'est bien une escalade CO
    if "ESCALADE AGENT CO" in decision3.system_instructions:
        print("✅ ESCALADE CO DÉTECTÉE CORRECTEMENT")
    else:
        print("❌ ESCALADE CO NON DÉTECTÉE")
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    # Vérifications finales
    test1_ok = "BLOC K" in decision1.system_instructions or "formations disponibles" in decision1.system_instructions
    test2_ok = "BLOC K" in decision2.system_instructions or "formations disponibles" in decision2.system_instructions
    test3_ok = "ESCALADE AGENT CO" in decision3.system_instructions and decision3.should_escalate
    
    print(f"Test 1 (Première demande): {'✅ PASS' if test1_ok else '❌ FAIL'}")
    print(f"Test 2 (Demande spécifique): {'✅ PASS' if test2_ok else '❌ FAIL'}")
    print(f"Test 3 (Escalade): {'✅ PASS' if test3_ok else '❌ FAIL'}")
    
    if test1_ok and test2_ok and test3_ok:
        print("\n🎉 TOUS LES TESTS PASSENT !")
        print("La logique d'escalade fonctionne correctement.")
    else:
        print("\n⚠️ CERTAINS TESTS ÉCHOUENT")
        print("Vérifiez la logique d'escalade.")

async def test_agent_commercial_detection():
    """Test de la détection des patterns d'agents commerciaux"""
    
    print("\n🧪 TEST DE DÉTECTION AGENTS COMMERCIAUX")
    print("=" * 50)
    
    rag_engine = OptimizedRAGEngine()
    
    # Messages de test pour agents commerciaux
    test_messages = [
        "Je travaille avec un organisme de formation super sérieux...",
        "mise en relation avec une équipe qui gère tout",
        "je peux être rémunéré si ça se met en place",
        "formation personnalisée 100% financée",
        "s'occupent de tout gratuitement et rapidement"
    ]
    
    for i, message in enumerate(test_messages, 1):
        decision = await rag_engine.analyze_intent(message)
        is_agent_pattern = "ESCALADE AGENT CO" in decision.system_instructions
        
        print(f"Test {i}: {'✅' if is_agent_pattern else '❌'} - {message[:50]}...")
    
    print("\n✅ Tests de détection agents commerciaux terminés")

if __name__ == "__main__":
    print("🚀 Démarrage des tests d'escalade formation")
    
    # Exécuter les tests
    asyncio.run(test_formation_conversation())
    asyncio.run(test_agent_commercial_detection())
    
    print("\n✨ Tests terminés !")