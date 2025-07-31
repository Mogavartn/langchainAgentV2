#!/usr/bin/env python3
"""
Test des corrections V4 - AgentIA JAK Company
Valide tous les problèmes identifiés et corrigés dans la version V4
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Ajouter le répertoire parent au path pour importer le module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process_optimized_v4 import OptimizedRAGEngine

class TestV4Corrections:
    """Tests pour valider les corrections V4"""
    
    def __init__(self):
        self.rag_engine = OptimizedRAGEngine()
        self.test_results = []
    
    async def run_all_tests(self):
        """Exécute tous les tests de correction V4"""
        print("🧪 TESTS V4 - CORRECTIONS JAK COMPANY")
        print("=" * 50)
        
        # Test 1: Détection agressivité
        await self.test_aggressive_detection()
        
        # Test 2: CPF "oui" → BLOC F2
        await self.test_cpf_oui_response()
        
        # Test 3: Paiement direct ≤ 7 jours
        await self.test_payment_direct_normal()
        
        # Test 4: Formation "ok" → BLOC 6.2
        await self.test_formation_ok_response()
        
        # Test 5: Paiement direct > 7 jours (vérification)
        await self.test_payment_direct_delayed()
        
        # Test 6: CPF > 45 jours (vérification)
        await self.test_cpf_delayed()
        
        # Test 7: Ambassadeur (vérification)
        await self.test_ambassador_flow()
        
        # Test 8: Formation (vérification)
        await self.test_formation_flow()
        
        # Affichage des résultats
        self.print_results()
    
    async def test_aggressive_detection(self):
        """Test 1: Détection de l'agressivité"""
        print("\n🔍 Test 1: Détection agressivité")
        
        test_cases = [
            "Vous êtes nuls !",
            "C'est de la merde",
            "Vous êtes débiles",
            "Je vous emmerde",
            "C'est nul"
        ]
        
        for message in test_cases:
            decision = await self.rag_engine.analyze_intent(message, "test_aggressive")
            
            if decision.bloc_type == "BLOC_AGRO":
                print(f"✅ '{message}' → BLOC_AGRO")
                self.test_results.append({
                    "test": "aggressive_detection",
                    "message": message,
                    "result": "PASS",
                    "bloc": decision.bloc_type
                })
            else:
                print(f"❌ '{message}' → {decision.bloc_type} (attendu: BLOC_AGRO)")
                self.test_results.append({
                    "test": "aggressive_detection",
                    "message": message,
                    "result": "FAIL",
                    "bloc": decision.bloc_type,
                    "expected": "BLOC_AGRO"
                })
    
    async def test_cpf_oui_response(self):
        """Test 2: CPF 'oui' → BLOC F2"""
        print("\n🔍 Test 2: CPF 'oui' → BLOC F2")
        
        # Simuler le contexte CPF
        session_id = "test_cpf_oui"
        
        # Message initial CPF
        initial_message = "j'ai pas été payé"
        decision1 = await self.rag_engine.analyze_intent(initial_message, session_id)
        
        # Réponse avec CPF > 45 jours
        cpf_message = "cpf il y a 5 mois"
        decision2 = await self.rag_engine.analyze_intent(cpf_message, session_id)
        
        # Réponse "oui"
        oui_message = "oui"
        decision3 = await self.rag_engine.analyze_intent(oui_message, session_id)
        
        if decision3.bloc_type == "BLOC_F2":
            print(f"✅ CPF flow: '{initial_message}' → '{cpf_message}' → '{oui_message}' → BLOC_F2")
            self.test_results.append({
                "test": "cpf_oui_response",
                "result": "PASS",
                "bloc": decision3.bloc_type
            })
        else:
            print(f"❌ CPF flow: '{initial_message}' → '{cpf_message}' → '{oui_message}' → {decision3.bloc_type} (attendu: BLOC_F2)")
            self.test_results.append({
                "test": "cpf_oui_response",
                "result": "FAIL",
                "bloc": decision3.bloc_type,
                "expected": "BLOC_F2"
            })
    
    async def test_payment_direct_normal(self):
        """Test 3: Paiement direct ≤ 7 jours"""
        print("\n🔍 Test 3: Paiement direct ≤ 7 jours")
        
        test_cases = [
            "j'ai payé tout seul il y a 3 jours",
            "j'ai financé en direct il y a 5 jours",
            "paiement direct il y a 1 semaine"
        ]
        
        for message in test_cases:
            decision = await self.rag_engine.analyze_intent(message, "test_direct_normal")
            
            if decision.bloc_type == "BLOC_DIRECT_NORMAL":
                print(f"✅ '{message}' → BLOC_DIRECT_NORMAL")
                self.test_results.append({
                    "test": "payment_direct_normal",
                    "message": message,
                    "result": "PASS",
                    "bloc": decision.bloc_type
                })
            else:
                print(f"❌ '{message}' → {decision.bloc_type} (attendu: BLOC_DIRECT_NORMAL)")
                self.test_results.append({
                    "test": "payment_direct_normal",
                    "message": message,
                    "result": "FAIL",
                    "bloc": decision.bloc_type,
                    "expected": "BLOC_DIRECT_NORMAL"
                })
    
    async def test_formation_ok_response(self):
        """Test 4: Formation 'ok' → BLOC 6.2"""
        print("\n🔍 Test 4: Formation 'ok' → BLOC 6.2")
        
        # Simuler le contexte formation
        session_id = "test_formation_ok"
        
        # Message initial formation
        initial_message = "c'est quoi vos formations ?"
        decision1 = await self.rag_engine.analyze_intent(initial_message, session_id)
        
        # Réponse "ok"
        ok_message = "ok"
        decision2 = await self.rag_engine.analyze_intent(ok_message, session_id)
        
        if decision2.bloc_type == "BLOC_6.2":
            print(f"✅ Formation flow: '{initial_message}' → '{ok_message}' → BLOC_6.2")
            self.test_results.append({
                "test": "formation_ok_response",
                "result": "PASS",
                "bloc": decision2.bloc_type
            })
        else:
            print(f"❌ Formation flow: '{initial_message}' → '{ok_message}' → {decision2.bloc_type} (attendu: BLOC_6.2)")
            self.test_results.append({
                "test": "formation_ok_response",
                "result": "FAIL",
                "bloc": decision2.bloc_type,
                "expected": "BLOC_6.2"
            })
    
    async def test_payment_direct_delayed(self):
        """Test 5: Paiement direct > 7 jours (vérification)"""
        print("\n🔍 Test 5: Paiement direct > 7 jours")
        
        test_cases = [
            "j'ai payé tout seul il y a 10 jours",
            "j'ai financé en direct il y a 2 semaines",
            "paiement direct il y a 1 mois"
        ]
        
        for message in test_cases:
            decision = await self.rag_engine.analyze_intent(message, "test_direct_delayed")
            
            if decision.bloc_type == "BLOC_J":
                print(f"✅ '{message}' → BLOC_J")
                self.test_results.append({
                    "test": "payment_direct_delayed",
                    "message": message,
                    "result": "PASS",
                    "bloc": decision.bloc_type
                })
            else:
                print(f"❌ '{message}' → {decision.bloc_type} (attendu: BLOC_J)")
                self.test_results.append({
                    "test": "payment_direct_delayed",
                    "message": message,
                    "result": "FAIL",
                    "bloc": decision.bloc_type,
                    "expected": "BLOC_J"
                })
    
    async def test_cpf_delayed(self):
        """Test 6: CPF > 45 jours (vérification)"""
        print("\n🔍 Test 6: CPF > 45 jours")
        
        test_cases = [
            "cpf il y a 3 mois",
            "cpf il y a 16 semaines",
            "cpf il y a 60 jours"
        ]
        
        for message in test_cases:
            decision = await self.rag_engine.analyze_intent(message, "test_cpf_delayed")
            
            if decision.bloc_type == "BLOC_F1":
                print(f"✅ '{message}' → BLOC_F1")
                self.test_results.append({
                    "test": "cpf_delayed",
                    "message": message,
                    "result": "PASS",
                    "bloc": decision.bloc_type
                })
            else:
                print(f"❌ '{message}' → {decision.bloc_type} (attendu: BLOC_F1)")
                self.test_results.append({
                    "test": "cpf_delayed",
                    "message": message,
                    "result": "FAIL",
                    "bloc": decision.bloc_type,
                    "expected": "BLOC_F1"
                })
    
    async def test_ambassador_flow(self):
        """Test 7: Ambassadeur (vérification)"""
        print("\n🔍 Test 7: Ambassadeur flow")
        
        # Simuler le contexte ambassadeur
        session_id = "test_ambassador"
        
        # Message initial ambassadeur
        initial_message = "c'est quoi un ambassadeur ?"
        decision1 = await self.rag_engine.analyze_intent(initial_message, session_id)
        
        # Réponse "oui"
        oui_message = "oui"
        decision2 = await self.rag_engine.analyze_intent(oui_message, session_id)
        
        if (decision1.bloc_type == "BLOC_AMBASSADOR" and 
            decision2.bloc_type == "BLOC_AMBASSADOR_PROCESS"):
            print(f"✅ Ambassadeur flow: '{initial_message}' → '{oui_message}' → BLOC_AMBASSADOR_PROCESS")
            self.test_results.append({
                "test": "ambassador_flow",
                "result": "PASS",
                "bloc1": decision1.bloc_type,
                "bloc2": decision2.bloc_type
            })
        else:
            print(f"❌ Ambassadeur flow: '{initial_message}' → '{oui_message}' → {decision2.bloc_type}")
            self.test_results.append({
                "test": "ambassador_flow",
                "result": "FAIL",
                "bloc1": decision1.bloc_type,
                "bloc2": decision2.bloc_type,
                "expected": "BLOC_AMBASSADOR_PROCESS"
            })
    
    async def test_formation_flow(self):
        """Test 8: Formation (vérification)"""
        print("\n🔍 Test 8: Formation flow")
        
        # Simuler le contexte formation
        session_id = "test_formation"
        
        # Message initial formation
        initial_message = "c'est quoi vos formations ?"
        decision1 = await self.rag_engine.analyze_intent(initial_message, session_id)
        
        if decision1.bloc_type == "BLOC_K":
            print(f"✅ Formation flow: '{initial_message}' → BLOC_K")
            self.test_results.append({
                "test": "formation_flow",
                "result": "PASS",
                "bloc": decision1.bloc_type
            })
        else:
            print(f"❌ Formation flow: '{initial_message}' → {decision1.bloc_type} (attendu: BLOC_K)")
            self.test_results.append({
                "test": "formation_flow",
                "result": "FAIL",
                "bloc": decision1.bloc_type,
                "expected": "BLOC_K"
            })
    
    def print_results(self):
        """Affiche les résultats des tests"""
        print("\n" + "=" * 50)
        print("📊 RÉSULTATS DES TESTS V4")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["result"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"Tests réussis: {passed_tests} ✅")
        print(f"Tests échoués: {failed_tests} ❌")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if result["result"] == "FAIL":
                    print(f"  - {result['test']}: {result.get('bloc', 'N/A')} (attendu: {result.get('expected', 'N/A')})")
        
        print(f"\n🎯 TAUX DE RÉUSSITE: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 TOUS LES TESTS V4 SONT PASSÉS !")
        else:
            print("⚠️  CERTAINS TESTS V4 ONT ÉCHOUÉ")

async def main():
    """Fonction principale"""
    tester = TestV4Corrections()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())