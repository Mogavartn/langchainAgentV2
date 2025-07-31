#!/usr/bin/env python3
"""
Test de débogage pour comprendre les problèmes de mémoire
"""

import asyncio
import sys
import os

# Ajouter le répertoire parent au path pour importer le module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process_optimized_v4 import OptimizedRAGEngine

async def debug_test():
    """Test de débogage"""
    print("🔍 DEBUG TEST - V4")
    print("=" * 30)
    
    rag_engine = OptimizedRAGEngine()
    session_id = "debug_test"
    
    # Test 1: Message initial CPF
    print("\n1. Message initial CPF:")
    message1 = "j'ai pas été payé"
    decision1 = await rag_engine.analyze_intent(message1, session_id)
    print(f"   Message: '{message1}'")
    print(f"   Bloc: {decision1.bloc_type}")
    print(f"   Mémoire: {rag_engine.memory_store._bloc_history[session_id]}")
    
    # Test 2: Réponse CPF
    print("\n2. Réponse CPF:")
    message2 = "cpf il y a 5 mois"
    decision2 = await rag_engine.analyze_intent(message2, session_id)
    print(f"   Message: '{message2}'")
    print(f"   Bloc: {decision2.bloc_type}")
    print(f"   Mémoire: {rag_engine.memory_store._bloc_history[session_id]}")
    
    # Test 3: Réponse "oui"
    print("\n3. Réponse 'oui':")
    message3 = "oui"
    decision3 = await rag_engine.analyze_intent(message3, session_id)
    print(f"   Message: '{message3}'")
    print(f"   Bloc: {decision3.bloc_type}")
    print(f"   Mémoire: {rag_engine.memory_store._bloc_history[session_id]}")
    
    # Test 4: Formation
    print("\n4. Formation:")
    session_id2 = "debug_test_formation"
    message4 = "c'est quoi vos formations ?"
    decision4 = await rag_engine.analyze_intent(message4, session_id2)
    print(f"   Message: '{message4}'")
    print(f"   Bloc: {decision4.bloc_type}")
    print(f"   Mémoire: {rag_engine.memory_store._bloc_history[session_id2]}")
    
    # Test 5: Réponse "ok"
    print("\n5. Réponse 'ok':")
    message5 = "ok"
    decision5 = await rag_engine.analyze_intent(message5, session_id2)
    print(f"   Message: '{message5}'")
    print(f"   Bloc: {decision5.bloc_type}")
    print(f"   Mémoire: {rag_engine.memory_store._bloc_history[session_id2]}")

if __name__ == "__main__":
    asyncio.run(debug_test())