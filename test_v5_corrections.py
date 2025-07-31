#!/usr/bin/env python3
"""
Test des corrections V5 - Validation des erreurs identifiées
"""

import asyncio
import json
import sys
import os

# Ajouter le répertoire parent au path pour importer le module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process_optimized_v5 import SupabaseRAGEngineV5, memory_store

class TestV5Corrections:
    """Tests pour valider les corrections de la version 5"""
    
    def __init__(self):
        self.rag_engine = SupabaseRAGEngineV5()
        self.test_results = []
    
    async def run_all_tests(self):
        """Exécute tous les tests de validation"""
        print("🧪 DÉBUT DES TESTS V5 - VALIDATION DES CORRECTIONS")
        print("=" * 60)
        
        # Test 1: Problème d'escalade après choix de formation
        await self.test_formation_choice_escalade()
        
        # Test 2: Problème de délai CPF non respecté
        await self.test_cpf_delay_logic()
        
        # Test 3: Problème d'agressivité non détectée
        await self.test_aggressive_behavior_detection()
        
        # Test 4: Logique de détection contextuelle améliorée
        await self.test_contextual_detection()
        
        # Affichage des résultats
        self.print_results()
    
    async def test_formation_choice_escalade(self):
        """Test 1: Vérifier que l'escalade ne se déclenche pas après choix de formation"""
        print("\n🔍 TEST 1: Formation choice escalade")
        
        # Simuler une conversation
        session_id = "test_formation_choice"
        memory_store.clear(session_id)
        
        # Message 1: Demande de formations
        message1 = "c'est quoi vos formations"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id)
        
        # Message 2: Intérêt pour une formation
        message2 = "je suis intéressé par la comptabilité"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id)
        
        # Message 3: Confirmation
        message3 = "ok"
        decision3 = await self.rag_engine.analyze_intent(message3, session_id)
        
        # Vérifications
        success = True
        if decision1.bloc_id.value != "BLOC K":
            print(f"❌ Erreur: Message 1 devrait être BLOC K, obtenu {decision1.bloc_id.value}")
            success = False
        
        if decision2.bloc_id.value != "BLOC M":
            print(f"❌ Erreur: Message 2 devrait être BLOC M, obtenu {decision2.bloc_id.value}")
            success = False
        
        if decision3.should_escalade:
            print(f"❌ Erreur: Message 3 ne devrait pas escalader, escalade={decision3.should_escalade}")
            success = False
        
        if success:
            print("✅ Test 1 PASSÉ: Pas d'escalade après choix de formation")
        else:
            print("❌ Test 1 ÉCHOUÉ: Problème d'escalade après choix de formation")
        
        self.test_results.append(("Formation choice escalade", success))
    
    async def test_cpf_delay_logic(self):
        """Test 2: Vérifier la logique de délai CPF corrigée"""
        print("\n🔍 TEST 2: CPF delay logic")
        
        # Test 2.1: CPF avec délai > 45 jours (doit appliquer BLOC F1)
        session_id1 = "test_cpf_delay_1"
        memory_store.clear(session_id1)
        
        message1 = "j'ai pas été payé cpf il y a 5 mois"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id1)
        
        # Test 2.2: CPF avec délai <= 45 jours (ne doit pas appliquer BLOC F1)
        session_id2 = "test_cpf_delay_2"
        memory_store.clear(session_id2)
        
        message2 = "j'ai pas été payé cpf il y a 20 jours"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id2)
        
        # Vérifications
        success = True
        
        # Test 2.1: Délai > 45 jours
        if decision1.bloc_id.value != "BLOC F1":
            print(f"❌ Erreur: Délai > 45 jours devrait être BLOC F1, obtenu {decision1.bloc_id.value}")
            success = False
        
        # Test 2.2: Délai <= 45 jours
        if decision2.bloc_id.value == "BLOC F1":
            print(f"❌ Erreur: Délai <= 45 jours ne devrait pas être BLOC F1")
            success = False
        
        if success:
            print("✅ Test 2 PASSÉ: Logique de délai CPF corrigée")
        else:
            print("❌ Test 2 ÉCHOUÉ: Problème avec la logique de délai CPF")
        
        self.test_results.append(("CPF delay logic", success))
    
    async def test_aggressive_behavior_detection(self):
        """Test 3: Vérifier la détection d'agressivité améliorée"""
        print("\n🔍 TEST 3: Aggressive behavior detection")
        
        # Test 3.1: Message agressif explicite
        session_id1 = "test_agro_1"
        memory_store.clear(session_id1)
        
        message1 = "vous êtes nuls"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id1)
        
        # Test 3.2: Message agressif avec insulte
        session_id2 = "test_agro_2"
        memory_store.clear(session_id2)
        
        message2 = "vous êtes des cons"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id2)
        
        # Test 3.3: Message normal (contrôle)
        session_id3 = "test_agro_3"
        memory_store.clear(session_id3)
        
        message3 = "bonjour, comment allez-vous ?"
        decision3 = await self.rag_engine.analyze_intent(message3, session_id3)
        
        # Vérifications
        success = True
        
        # Test 3.1: Message agressif
        if decision1.bloc_id.value != "BLOC AGRO":
            print(f"❌ Erreur: Message agressif devrait être BLOC AGRO, obtenu {decision1.bloc_id.value}")
            success = False
        
        # Test 3.2: Message avec insulte
        if decision2.bloc_id.value != "BLOC AGRO":
            print(f"❌ Erreur: Message avec insulte devrait être BLOC AGRO, obtenu {decision2.bloc_id.value}")
            success = False
        
        # Test 3.3: Message normal
        if decision3.bloc_id.value == "BLOC AGRO":
            print(f"❌ Erreur: Message normal ne devrait pas être BLOC AGRO")
            success = False
        
        if success:
            print("✅ Test 3 PASSÉ: Détection d'agressivité améliorée")
        else:
            print("❌ Test 3 ÉCHOUÉ: Problème avec la détection d'agressivité")
        
        self.test_results.append(("Aggressive behavior detection", success))
    
    async def test_contextual_detection(self):
        """Test 4: Vérifier la détection contextuelle améliorée"""
        print("\n🔍 TEST 4: Contextual detection")
        
        # Test 4.1: Contexte formation -> intérêt
        session_id1 = "test_context_1"
        memory_store.clear(session_id1)
        
        # Simuler avoir vu les formations
        memory_store.set_conversation_context(session_id1, "last_bloc_presented", "BLOC K")
        
        message1 = "je suis intéressé par la comptabilité"
        decision1 = await self.rag_engine.analyze_intent(message1, session_id1)
        
        # Test 4.2: Contexte ambassadeur -> questions
        session_id2 = "test_context_2"
        memory_store.clear(session_id2)
        
        # Simuler avoir vu les ambassadeurs
        memory_store.set_conversation_context(session_id2, "last_bloc_presented", "BLOC D1")
        
        message2 = "comment ça marche pour devenir ambassadeur ?"
        decision2 = await self.rag_engine.analyze_intent(message2, session_id2)
        
        # Vérifications
        success = True
        
        # Test 4.1: Contexte formation
        if decision1.bloc_id.value != "BLOC M":
            print(f"❌ Erreur: Contexte formation devrait être BLOC M, obtenu {decision1.bloc_id.value}")
            success = False
        
        # Test 4.2: Contexte ambassadeur
        if decision2.bloc_id.value != "BLOC E":
            print(f"❌ Erreur: Contexte ambassadeur devrait être BLOC E, obtenu {decision2.bloc_id.value}")
            success = False
        
        if success:
            print("✅ Test 4 PASSÉ: Détection contextuelle améliorée")
        else:
            print("❌ Test 4 ÉCHOUÉ: Problème avec la détection contextuelle")
        
        self.test_results.append(("Contextual detection", success))
    
    def print_results(self):
        """Affiche les résultats des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DES TESTS V5")
        print("=" * 60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, success in self.test_results:
            status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
            print(f"{test_name}: {status}")
            if success:
                passed += 1
        
        print(f"\n📈 Résumé: {passed}/{total} tests passés")
        
        if passed == total:
            print("🎉 TOUS LES TESTS SONT PASSÉS ! Les corrections V5 sont validées.")
        else:
            print("⚠️  Certains tests ont échoué. Vérifiez les corrections.")
        
        print("=" * 60)

async def main():
    """Fonction principale pour exécuter les tests"""
    tester = TestV5Corrections()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())