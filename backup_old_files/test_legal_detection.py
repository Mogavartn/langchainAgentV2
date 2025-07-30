#!/usr/bin/env python3
"""
Test de détection des demandes de récupération d'argent CPF
Vérifie que toutes les variantes renvoient au BLOC LEGAL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process import OptimizedRAGEngine, KEYWORD_SETS
import asyncio

async def test_legal_detection():
    """Test de détection des demandes légales"""
    
    rag_engine = OptimizedRAGEngine()
    
    # Liste des messages de test pour récupération d'argent CPF
    test_messages = [
        # Messages de la conversation fournie
        "Comment je récupère mon argent de mon CPF ?",
        "je veux l'argent de mon cpf",
        "je veux prendre l'argent de mon cpf",
        
        # Nouvelles variantes ajoutées
        "je veux récupérer mon argent",
        "je veux prendre l'argent",
        "je veux l'argent du cpf",
        "récupérer mon argent de mon cpf",
        "prendre mon argent de mon cpf",
        "récupérer l'argent de mon cpf",
        "prendre l'argent de mon cpf",
        "argent de mon cpf",
        "argent du cpf pour moi",
        "récupération argent cpf",
        "prise argent cpf",
        "rémunération pour sois-même",
        "rémunération pour moi",
        "récupération pour sois-même",
        "prendre pour sois-même",
        "argent cpf pour moi",
        
        # Variantes avec différentes formulations
        "comment récupérer l'argent de mon cpf",
        "comment prendre l'argent de mon cpf",
        "je souhaite récupérer mon argent cpf",
        "je souhaite prendre l'argent cpf",
        "donnez-moi l'argent de mon cpf",
        "je veux toucher l'argent de mon cpf",
        "je veux avoir l'argent de mon cpf",
        "je veux sortir l'argent de mon cpf",
        "je veux retirer l'argent de mon cpf",
        
        # Messages qui ne devraient PAS déclencher le bloc légal
        "comment devenir ambassadeur",
        "formation cpf disponible",
        "paiement formation",
        "délai paiement",
        "contact humain"
    ]
    
    print("🧪 TEST DE DÉTECTION DES DEMANDES DE RÉCUPÉRATION D'ARGENT CPF")
    print("=" * 70)
    
    legal_detected = 0
    total_tests = len(test_messages)
    
    for i, message in enumerate(test_messages, 1):
        try:
            decision = await rag_engine.analyze_intent(message, f"test_session_{i}")
            
            # Vérifier si c'est une détection légale
            is_legal = "legal" in decision.context_needed or "recadrage" in decision.context_needed
            
            # Vérifier si le message contient des mots-clés légaux
            message_lower = message.lower()
            has_legal_keywords = any(keyword in message_lower for keyword in KEYWORD_SETS.legal_keywords)
            
            status = "✅ LEGAL" if is_legal else "❌ AUTRE"
            expected = "✅ ATTENDU" if has_legal_keywords else "❌ NON ATTENDU"
            
            print(f"{i:2d}. {status} | {expected} | '{message}'")
            
            if is_legal:
                legal_detected += 1
                print(f"    📋 Décision: {decision.search_strategy} - {decision.priority_level}")
                print(f"    🎯 Contexte: {decision.context_needed}")
            
            # Vérifier la cohérence
            if has_legal_keywords and not is_legal:
                print(f"    ⚠️  PROBLÈME: Mots-clés légaux détectés mais pas de décision légale!")
            elif not has_legal_keywords and is_legal:
                print(f"    ⚠️  PROBLÈME: Décision légale sans mots-clés légaux!")
                
        except Exception as e:
            print(f"{i:2d}. ❌ ERREUR | '{message}' - {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"📊 RÉSULTATS:")
    print(f"   - Détections légales: {legal_detected}/{total_tests}")
    print(f"   - Taux de détection: {(legal_detected/total_tests)*100:.1f}%")
    
    # Test spécifique des mots-clés
    print(f"\n🔍 TEST DES MOTS-CLÉS LÉGAUX:")
    print(f"   - Nombre de mots-clés légaux: {len(KEYWORD_SETS.legal_keywords)}")
    
    # Afficher quelques mots-clés pour vérification
    print(f"   - Exemples de mots-clés:")
    for keyword in list(KEYWORD_SETS.legal_keywords)[:10]:
        print(f"     • {keyword}")
    if len(KEYWORD_SETS.legal_keywords) > 10:
        print(f"     • ... et {len(KEYWORD_SETS.legal_keywords) - 10} autres")

if __name__ == "__main__":
    asyncio.run(test_legal_detection())