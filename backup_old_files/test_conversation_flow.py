#!/usr/bin/env python3
"""
Test de la logique de conversation pour éviter les répétitions
"""

import asyncio
import sys
import os

# Ajouter le répertoire parent au path pour importer process
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process import OptimizedRAGEngine, OptimizedMemoryManager, memory_store

async def test_conversation_flow():
    """Test de la logique de conversation pour éviter les répétitions"""
    
    print("🧪 TEST DE LA LOGIQUE DE CONVERSATION")
    print("=" * 50)
    
    # Initialiser le moteur RAG
    rag_engine = OptimizedRAGEngine()
    session_id = "test_conversation_flow"
    
    # Nettoyer la mémoire pour ce test
    memory_store.clear(session_id)
    
    # Test 1: Première demande de formation → BLOC K
    print("\n📋 Test 1: Première demande de formation")
    message1 = "je voudrais faire une formation"
    
    # Ajouter le message à la mémoire
    await OptimizedMemoryManager.add_message(session_id, message1, "user")
    
    # Analyser l'intention
    decision1 = await rag_engine.analyze_intent(message1, session_id)
    
    print(f"Message: {message1}")
    print(f"Décision: {decision1.search_strategy}")
    print(f"Instructions: {decision1.system_instructions[:100]}...")
    
    # Vérifier que c'est bien le BLOC K
    test1_ok = "FORMATION (BLOC K)" in decision1.system_instructions or "formations disponibles" in decision1.system_instructions
    print(f"✅ BLOC K détecté: {test1_ok}")
    
    # Simuler la réponse du bot (BLOC K)
    bloc_k_response = "🎓 **+100 formations disponibles chez JAK Company !** 🎓"
    await OptimizedMemoryManager.add_message(session_id, bloc_k_response, "assistant")
    
    # Test 2: Deuxième demande de formation → BLOC M
    print("\n📋 Test 2: Deuxième demande de formation")
    message2 = "je voudrais faire une formation en anglais pro"
    
    # Ajouter le message à la mémoire
    await OptimizedMemoryManager.add_message(session_id, message2, "user")
    
    # Analyser l'intention
    decision2 = await rag_engine.analyze_intent(message2, session_id)
    
    print(f"Message: {message2}")
    print(f"Décision: {decision2.search_strategy}")
    print(f"Instructions: {decision2.system_instructions[:100]}...")
    
    # Vérifier que c'est bien le BLOC M
    test2_ok = "ESCALADE FORMATION (BLOC M)" in decision2.system_instructions or "excellent choix" in decision2.system_instructions
    print(f"✅ BLOC M détecté: {test2_ok}")
    
    # Simuler la réponse du bot (BLOC M)
    bloc_m_response = "🎯 **Excellent choix !** 🎯"
    await OptimizedMemoryManager.add_message(session_id, bloc_m_response, "assistant")
    
    # Test 3: Confirmation → BLOC 6.2
    print("\n📋 Test 3: Confirmation d'escalade")
    message3 = "oui je veux bien"
    
    # Ajouter le message à la mémoire
    await OptimizedMemoryManager.add_message(session_id, message3, "user")
    
    # Analyser l'intention
    decision3 = await rag_engine.analyze_intent(message3, session_id)
    
    print(f"Message: {message3}")
    print(f"Décision: {decision3.search_strategy}")
    print(f"Instructions: {decision3.system_instructions[:100]}...")
    
    # Vérifier que c'est bien le BLOC 6.2
    test3_ok = "CONFIRMATION ESCALADE FORMATION (BLOC 6.2)" in decision3.system_instructions or "ESCALADE AGENT CO" in decision3.system_instructions
    print(f"✅ BLOC 6.2 détecté: {test3_ok}")
    
    # Test 4: Vérification anti-répétition
    print("\n📋 Test 4: Vérification anti-répétition")
    message4 = "je voudrais faire une formation"
    
    # Ajouter le message à la mémoire
    await OptimizedMemoryManager.add_message(session_id, message4, "user")
    
    # Analyser l'intention
    decision4 = await rag_engine.analyze_intent(message4, session_id)
    
    print(f"Message: {message4}")
    print(f"Décision: {decision4.search_strategy}")
    print(f"Instructions: {decision4.system_instructions[:100]}...")
    
    # Vérifier que ce n'est PAS le BLOC K (car déjà présenté)
    test4_ok = "FORMATION (BLOC K)" not in decision4.system_instructions
    print(f"✅ Pas de répétition BLOC K: {test4_ok}")
    
    # Résumé des tests
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    print(f"Test 1 - BLOC K: {'✅ PASS' if test1_ok else '❌ FAIL'}")
    print(f"Test 2 - BLOC M: {'✅ PASS' if test2_ok else '❌ FAIL'}")
    print(f"Test 3 - BLOC 6.2: {'✅ PASS' if test3_ok else '❌ FAIL'}")
    print(f"Test 4 - Anti-répétition: {'✅ PASS' if test4_ok else '❌ FAIL'}")
    
    # Vérification finale
    all_tests_passed = test1_ok and test2_ok and test3_ok and test4_ok
    print(f"\n🎯 RÉSULTAT FINAL: {'✅ TOUS LES TESTS RÉUSSIS' if all_tests_passed else '❌ CERTAINS TESTS ÉCHOUÉS'}")
    
    return all_tests_passed

if __name__ == "__main__":
    # Exécuter le test
    result = asyncio.run(test_conversation_flow())
    
    if result:
        print("\n🎉 La logique de conversation fonctionne correctement !")
        sys.exit(0)
    else:
        print("\n💥 Des problèmes ont été détectés dans la logique de conversation.")
        sys.exit(1)