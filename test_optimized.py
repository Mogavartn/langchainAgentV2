#!/usr/bin/env python3
"""
Test optimisé pour la nouvelle version du process.py
"""

import asyncio
import json
import time
from typing import Dict, Any

# Import de notre version optimisée
from process_optimized import rag_engine, memory_store, detection_engine

class OptimizedTester:
    """Classe de test optimisée pour valider le nouveau système"""
    
    def __init__(self):
        self.test_results = []
        self.session_id = "test_session"
    
    async def run_test_case(self, message: str, expected_intent: str, expected_bloc: str, test_name: str) -> Dict:
        """Exécute un cas de test"""
        start_time = time.time()
        
        try:
            # Analyse de l'intention
            decision = await rag_engine.analyze_intent(message, self.session_id)
            
            # Vérification des résultats
            success = (
                decision.intent_type.value == expected_intent and
                decision.bloc_type == expected_bloc
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "test_name": test_name,
                "message": message,
                "expected_intent": expected_intent,
                "expected_bloc": expected_bloc,
                "actual_intent": decision.intent_type.value,
                "actual_bloc": decision.bloc_type,
                "success": success,
                "processing_time": round(processing_time, 3),
                "search_query": decision.search_query,
                "should_escalate": decision.should_escalate
            }
            
            self.test_results.append(result)
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}: {decision.intent_type.value} -> {decision.bloc_type}")
            
            return result
            
        except Exception as e:
            result = {
                "test_name": test_name,
                "message": message,
                "error": str(e),
                "success": False,
                "processing_time": round(time.time() - start_time, 3)
            }
            self.test_results.append(result)
            print(f"❌ ERROR {test_name}: {str(e)}")
            return result
    
    async def run_all_tests(self):
        """Exécute tous les tests de validation"""
        print("🚀 DÉMARRAGE DES TESTS OPTIMISÉS")
        print("=" * 50)
        
        # Tests de définitions
        await self.run_test_case(
            "c'est quoi un ambassadeur ?",
            "definition",
            "BLOC_A",
            "Définition Ambassadeur"
        )
        
        await self.run_test_case(
            "qu'est-ce que l'affiliation ?",
            "definition",
            "BLOC_B",
            "Définition Affiliation"
        )
        
        # Tests de paiement (CORRECTION DU BUG)
        await self.run_test_case(
            "j'ai toujours pas reçu mon argent",
            "payment",
            "BLOC_F",
            "Paiement - Toujours pas reçu (CORRECTION)"
        )
        
        await self.run_test_case(
            "je reçois quand mes sous ?",
            "payment",
            "BLOC_F",
            "Paiement - Quand je reçois"
        )
        
        await self.run_test_case(
            "OPCO il y a 20 jours",
            "payment",
            "BLOC_K",
            "Paiement OPCO - Délai normal"
        )
        
        await self.run_test_case(
            "j'ai payé directement il y a 10 jours",
            "payment",
            "BLOC_L",
            "Paiement Direct - Délai dépassé"
        )
        
        # Tests de formation
        await self.run_test_case(
            "je veux faire une formation en anglais",
            "formation",
            "BLOC_K",
            "Formation - Première demande"
        )
        
        # Simuler que les formations ont été présentées
        memory_store.add_bloc_presented(self.session_id, "BLOC_K")
        # Ajouter un message de présentation des formations
        memory_store.add_message(self.session_id, "Voici nos formations disponibles...", "assistant")
        
        await self.run_test_case(
            "oui ça m'intéresse",
            "formation_escalade",
            "BLOC_M",
            "Formation - Escalade après présentation"
        )
        
        # Simuler que le BLOC M a été présenté
        memory_store.add_bloc_presented(self.session_id, "BLOC_M")
        # Ajouter un message de confirmation
        memory_store.add_message(self.session_id, "Excellent choix, notre équipe va vous recontacter...", "assistant")
        
        await self.run_test_case(
            "recontactez-moi",
            "formation_confirmation",
            "BLOC_M",
            "Formation - Confirmation contact"
        )
        
        # Tests d'escalade
        await self.run_test_case(
            "je veux parler au manager",
            "escalade_co",
            "BLOC_N",
            "Escalade CO"
        )
        
        await self.run_test_case(
            "il y a un bug technique",
            "escalade_admin",
            "BLOC_I",
            "Escalade Admin"
        )
        
        # Tests de légal
        await self.run_test_case(
            "comment décaisser le CPF ?",
            "legal",
            "BLOC_C",
            "Question Légal CPF"
        )
        
        # Tests d'ambassadeur
        await self.run_test_case(
            "comment devenir ambassadeur ?",
            "ambassador",
            "BLOC_D",
            "Programme Ambassadeur"
        )
        
        # Tests de contact
        await self.run_test_case(
            "quel est votre numéro de téléphone ?",
            "contact",
            "BLOC_E",
            "Demande Contact"
        )
        
        # Tests de temps/délais
        await self.run_test_case(
            "combien de temps ça prend ?",
            "time",
            "BLOC_J",
            "Question Délais"
        )
        
        # Tests agressifs
        await self.run_test_case(
            "putain de merde",
            "aggressive",
            "BLOC_H",
            "Message Agressif"
        )
        
        # Tests de fallback
        await self.run_test_case(
            "bonjour comment allez-vous ?",
            "fallback",
            "BLOC_FALLBACK",
            "Message Général"
        )
        
        print("\n" + "=" * 50)
        await self.print_summary()
    
    async def print_summary(self):
        """Affiche le résumé des tests"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.get("success", False))
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 RÉSUMÉ DES TESTS")
        print(f"Total: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        # Temps de traitement moyen
        avg_time = sum(result.get("processing_time", 0) for result in self.test_results) / total_tests
        print(f"⏱️ Temps moyen: {avg_time:.3f}s")
        
        # Afficher les échecs
        if failed_tests > 0:
            print(f"\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if not result.get("success", False):
                    print(f"  - {result['test_name']}: {result.get('error', 'Mauvaise détection')}")
        
        # Statistiques de performance
        print(f"\n🚀 PERFORMANCE:")
        memory_stats = memory_store.get_stats()
        print(f"  - Sessions actives: {memory_stats['active_sessions']}")
        print(f"  - Taille mémoire: {memory_stats['size']}/{memory_stats['max_size']}")
        print(f"  - TTL: {memory_stats['ttl']}s")
    
    def save_results(self, filename: str = "test_results_optimized.json"):
        """Sauvegarde les résultats des tests"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans {filename}")

async def main():
    """Fonction principale de test"""
    tester = OptimizedTester()
    await tester.run_all_tests()
    tester.save_results()

if __name__ == "__main__":
    asyncio.run(main())