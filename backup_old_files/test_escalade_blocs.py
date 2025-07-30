#!/usr/bin/env python3
"""
Test des nouveaux blocs d'escalade 6.1 et 6.2
Vérification que les escalades sont bien déclenchées selon les conditions
"""

import asyncio
import sys
import os

# Ajouter le répertoire courant au path pour importer process
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process import OptimizedRAGEngine

async def test_escalade_blocs():
    """Test des blocs d'escalade 6.1 et 6.2"""
    
    print("🧪 TEST DES BLOCS D'ESCALADE 6.1 ET 6.2")
    print("=" * 50)
    
    rag_engine = OptimizedRAGEngine()
    
    # Tests pour BLOC 6.1 - ESCALADE AGENT ADMIN
    print("\n📋 BLOC 6.1 - ESCALADE AGENT ADMIN")
    print("-" * 30)
    
    escalade_admin_tests = [
        {
            "message": "Mon paiement est en retard depuis 2 semaines",
            "expected": "ESCALADE ADMIN (BLOC 6.1)",
            "reason": "Paiement en retard"
        },
        {
            "message": "Je n'ai pas reçu mon virement",
            "expected": "ESCALADE ADMIN (BLOC 6.1)", 
            "reason": "Virement non reçu"
        },
        {
            "message": "Mon dossier est bloqué",
            "expected": "ESCALADE ADMIN (BLOC 6.1)",
            "reason": "Dossier bloqué"
        },
        {
            "message": "J'ai besoin d'un justificatif",
            "expected": "ESCALADE ADMIN (BLOC 6.1)",
            "reason": "Besoin de preuve"
        },
        {
            "message": "Je ne peux pas accéder à mon fichier",
            "expected": "ESCALADE ADMIN (BLOC 6.1)",
            "reason": "Consultation fichier"
        },
        {
            "message": "Il y a un bug dans le système",
            "expected": "ESCALADE ADMIN (BLOC 6.1)",
            "reason": "Problème technique"
        }
    ]
    
    for i, test in enumerate(escalade_admin_tests, 1):
        print(f"\n{i}. Test: {test['reason']}")
        print(f"   Message: '{test['message']}'")
        
        try:
            decision = await rag_engine.analyze_intent(test['message'])
            result = "ESCALADE ADMIN (BLOC 6.1)" if decision.should_escalate and "admin" in decision.context_needed else "AUTRE"
            
            print(f"   Résultat: {result}")
            print(f"   Escalade: {'✅ OUI' if decision.should_escalate else '❌ NON'}")
            print(f"   Contexte: {decision.context_needed}")
            
            if result == test['expected']:
                print(f"   ✅ SUCCÈS")
            else:
                print(f"   ❌ ÉCHEC - Attendu: {test['expected']}")
                
        except Exception as e:
            print(f"   ❌ ERREUR: {str(e)}")
    
    # Tests pour BLOC 6.2 - ESCALADE AGENT CO
    print("\n\n📋 BLOC 6.2 - ESCALADE AGENT CO")
    print("-" * 30)
    
    escalade_co_tests = [
        {
            "message": "Je veux discuter d'un deal stratégique",
            "expected": "ESCALADE CO (BLOC 6.2)",
            "reason": "Deal stratégique"
        },
        {
            "message": "Pouvez-vous m'appeler ?",
            "expected": "ESCALADE CO (BLOC 6.2)",
            "reason": "Besoin d'appel"
        },
        {
            "message": "J'ai besoin d'un accompagnement personnalisé",
            "expected": "ESCALADE CO (BLOC 6.2)",
            "reason": "Accompagnement personnalisé"
        },
        {
            "message": "C'est une situation complexe",
            "expected": "ESCALADE CO (BLOC 6.2)",
            "reason": "Situation complexe"
        },
        {
            "message": "Je veux négocier un partenariat",
            "expected": "ESCALADE CO (BLOC 6.2)",
            "reason": "Partenariat"
        },
        {
            "message": "J'ai besoin d'un conseiller dédié",
            "expected": "ESCALADE CO (BLOC 6.2)",
            "reason": "Conseiller dédié"
        }
    ]
    
    for i, test in enumerate(escalade_co_tests, 1):
        print(f"\n{i}. Test: {test['reason']}")
        print(f"   Message: '{test['message']}'")
        
        try:
            decision = await rag_engine.analyze_intent(test['message'])
            result = "ESCALADE CO (BLOC 6.2)" if decision.should_escalate and "co" in decision.context_needed else "AUTRE"
            
            print(f"   Résultat: {result}")
            print(f"   Escalade: {'✅ OUI' if decision.should_escalate else '❌ NON'}")
            print(f"   Contexte: {decision.context_needed}")
            
            if result == test['expected']:
                print(f"   ✅ SUCCÈS")
            else:
                print(f"   ❌ ÉCHEC - Attendu: {test['expected']}")
                
        except Exception as e:
            print(f"   ❌ ERREUR: {str(e)}")
    
    # Tests de non-escalade (contrôle)
    print("\n\n📋 TESTS DE CONTRÔLE - PAS D'ESCALADE")
    print("-" * 40)
    
    controle_tests = [
        {
            "message": "Bonjour, comment allez-vous ?",
            "expected": "PAS D'ESCALADE",
            "reason": "Salutation normale"
        },
        {
            "message": "Quelles sont vos formations ?",
            "expected": "PAS D'ESCALADE",
            "reason": "Question formation"
        },
        {
            "message": "Comment devenir ambassadeur ?",
            "expected": "PAS D'ESCALADE",
            "reason": "Question ambassadeur"
        }
    ]
    
    for i, test in enumerate(controle_tests, 1):
        print(f"\n{i}. Test: {test['reason']}")
        print(f"   Message: '{test['message']}'")
        
        try:
            decision = await rag_engine.analyze_intent(test['message'])
            result = "PAS D'ESCALADE" if not decision.should_escalate else "ESCALADE"
            
            print(f"   Résultat: {result}")
            print(f"   Escalade: {'❌ OUI' if decision.should_escalate else '✅ NON'}")
            
            if result == test['expected']:
                print(f"   ✅ SUCCÈS")
            else:
                print(f"   ❌ ÉCHEC - Attendu: {test['expected']}")
                
        except Exception as e:
            print(f"   ❌ ERREUR: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 FIN DES TESTS DES BLOCS D'ESCALADE")

if __name__ == "__main__":
    asyncio.run(test_escalade_blocs())