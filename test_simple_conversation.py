#!/usr/bin/env python3
"""
Test simplifié de la logique de conversation
"""

import sys
import os

# Simuler les classes nécessaires pour le test
class MockMemoryStore:
    def __init__(self):
        self.messages = {}
    
    def get(self, session_id):
        return self.messages.get(session_id, [])
    
    def add_message(self, session_id, message, role="user"):
        if session_id not in self.messages:
            self.messages[session_id] = []
        self.messages[session_id].append({
            "role": role,
            "content": message,
            "timestamp": 0
        })
    
    def clear(self, session_id):
        if session_id in self.messages:
            del self.messages[session_id]

class MockKeywordSets:
    def __init__(self):
        self.formation_keywords = frozenset([
            "formation", "cours", "apprendre", "catalogue", "proposez",
            "disponible", "enseigner", "stage", "bureautique", 
            "informatique", "langues", "anglais", "excel"
        ])
        
        self.formation_escalade_keywords = frozenset([
            "oui", "ok", "d'accord", "parfait", "super", "ça m'intéresse",
            "je veux bien", "c'est possible", "comment faire", "plus d'infos",
            "mettre en relation", "équipe commerciale", "contact"
        ])
        
        self.formation_confirmation_keywords = frozenset([
            "oui", "ok", "d'accord", "parfait", "super", "ça m'intéresse",
            "je veux bien", "c'est possible", "comment faire", "plus d'infos",
            "mettre en relation", "équipe commerciale", "contact", "recontacte",
            "recontactez", "recontactez-moi", "recontacte-moi", "appelez-moi",
            "appellez-moi", "appel", "téléphone", "téléphoner"
        ])

class MockRAGEngine:
    def __init__(self):
        self.keyword_sets = MockKeywordSets()
        self.memory_store = MockMemoryStore()
    
    def _has_keywords(self, message_lower, keyword_set):
        return any(keyword in message_lower for keyword in keyword_set)
    
    def _has_formation_been_presented(self, session_id):
        """Vérifie si les formations ont déjà été présentées dans cette conversation"""
        try:
            conversation_context = self.memory_store.get(session_id)
            
            # Chercher si le BLOC K a déjà été présenté
            for msg in conversation_context:
                content = str(msg.get("content", "")).lower()
                # Détection robuste du BLOC K déjà présenté
                if any(phrase in content for phrase in [
                    "formations disponibles", 
                    "+100 formations", 
                    "jak company",
                    "bureautique", "informatique", "langues", "web/3d",
                    "vente & marketing", "développement personnel",
                    "écologie numérique", "bilan compétences"
                ]):
                    return True
            
            return False
            
        except Exception as e:
            print(f"Erreur vérification formations présentées: {str(e)}")
            return False
    
    def _has_bloc_m_been_presented(self, session_id):
        """Vérifie si le BLOC M a déjà été présenté dans cette conversation"""
        try:
            conversation_context = self.memory_store.get(session_id)
            
            # Chercher si le BLOC M a déjà été présenté
            for msg in conversation_context:
                content = str(msg.get("content", "")).lower()
                # Détection robuste du BLOC M déjà présenté
                if any(phrase in content for phrase in [
                    "excellent choix", 
                    "équipe commerciale", 
                    "recontacte", "recontactez",
                    "financement optimal", "planning adapté", "accompagnement perso",
                    "ok pour qu'on te recontacte", "meilleure stratégie pour toi"
                ]):
                    return True
            
            return False
            
        except Exception as e:
            print(f"Erreur vérification BLOC M présenté: {str(e)}")
            return False
    
    def _is_formation_escalade_request(self, message_lower, session_id):
        """Détecte si c'est une demande d'escalade après présentation des formations"""
        try:
            # Vérifier si le message contient des mots-clés d'escalade
            has_escalade_keywords = any(
                keyword in message_lower 
                for keyword in self.keyword_sets.formation_escalade_keywords
            )
            
            if not has_escalade_keywords:
                return False
            
            # Vérifier le contexte de conversation
            conversation_context = self.memory_store.get(session_id)
            
            # Chercher si le BLOC K a été présenté récemment (détection améliorée)
            bloc_k_presented = False
            for msg in conversation_context[-5:]:  # Derniers 5 messages
                content = str(msg.get("content", "")).lower()
                # Détection plus robuste du BLOC K
                if any(phrase in content for phrase in [
                    "formations disponibles", 
                    "+100 formations", 
                    "jak company",
                    "bureautique", "informatique", "langues", "web/3d",
                    "vente & marketing", "développement personnel",
                    "écologie numérique", "bilan compétences"
                ]):
                    bloc_k_presented = True
                    break
            
            return bloc_k_presented
            
        except Exception as e:
            print(f"Erreur détection escalade formation: {str(e)}")
            return False
    
    def _is_formation_confirmation_request(self, message_lower, session_id):
        """Détecte si c'est une confirmation d'escalade après présentation du BLOC M"""
        try:
            # Vérifier si le message contient des mots-clés de confirmation
            has_confirmation_keywords = any(
                keyword in message_lower 
                for keyword in self.keyword_sets.formation_confirmation_keywords
            )
            
            if not has_confirmation_keywords:
                return False
            
            # Vérifier le contexte de conversation
            conversation_context = self.memory_store.get(session_id)
            
            # Chercher si le BLOC M a été présenté récemment (détection améliorée)
            bloc_m_presented = False
            for msg in conversation_context[-5:]:  # Derniers 5 messages
                content = str(msg.get("content", "")).lower()
                # Détection plus robuste du BLOC M
                if any(phrase in content for phrase in [
                    "excellent choix", 
                    "équipe commerciale", 
                    "recontacte", "recontactez",
                    "financement optimal", "planning adapté", "accompagnement perso",
                    "ok pour qu'on te recontacte", "meilleure stratégie pour toi"
                ]):
                    bloc_m_presented = True
                    break
            
            return bloc_m_presented
            
        except Exception as e:
            print(f"Erreur détection confirmation formation: {str(e)}")
            return False
    
    def analyze_intent(self, message, session_id="default"):
        """Analyse l'intention de manière simplifiée"""
        message_lower = message.lower().strip()
        
        # Vérifier d'abord si c'est une confirmation d'escalade après présentation du BLOC M
        if self._is_formation_confirmation_request(message_lower, session_id):
            return {"type": "BLOC_6_2", "description": "Confirmation d'escalade formation"}
        
        # Vérifier ensuite si c'est une demande d'escalade après présentation formations
        elif self._is_formation_escalade_request(message_lower, session_id):
            return {"type": "BLOC_M", "description": "Escalade formation"}
        
        # Formation detection avec logique anti-répétition
        elif self._has_keywords(message_lower, self.keyword_sets.formation_keywords):
            # Vérifier si les formations ont déjà été présentées
            if self._has_formation_been_presented(session_id):
                # Si BLOC K déjà présenté, vérifier si BLOC M a été présenté
                if self._has_bloc_m_been_presented(session_id):
                    # Si BLOC M déjà présenté, escalader directement
                    return {"type": "BLOC_6_2", "description": "Escalade directe (BLOC M déjà présenté)"}
                else:
                    # Si BLOC K présenté mais pas BLOC M, présenter BLOC M
                    return {"type": "BLOC_M", "description": "Escalade formation (BLOC K déjà présenté)"}
            else:
                # Première demande de formation, présenter BLOC K
                return {"type": "BLOC_K", "description": "Première présentation formations"}
        
        # Autre type de demande
        else:
            return {"type": "OTHER", "description": "Autre demande"}

def test_conversation_flow():
    """Test de la logique de conversation pour éviter les répétitions"""
    
    print("🧪 TEST DE LA LOGIQUE DE CONVERSATION")
    print("=" * 50)
    
    # Initialiser le moteur RAG
    rag_engine = MockRAGEngine()
    session_id = "test_conversation_flow"
    
    # Nettoyer la mémoire pour ce test
    rag_engine.memory_store.clear(session_id)
    
    # Test 1: Première demande de formation → BLOC K
    print("\n📋 Test 1: Première demande de formation")
    message1 = "je voudrais faire une formation"
    
    # Ajouter le message à la mémoire
    rag_engine.memory_store.add_message(session_id, message1, "user")
    
    # Analyser l'intention
    decision1 = rag_engine.analyze_intent(message1, session_id)
    
    print(f"Message: {message1}")
    print(f"Décision: {decision1}")
    
    # Vérifier que c'est bien le BLOC K
    test1_ok = decision1["type"] == "BLOC_K"
    print(f"✅ BLOC K détecté: {test1_ok}")
    
    # Simuler la réponse du bot (BLOC K)
    bloc_k_response = "🎓 **+100 formations disponibles chez JAK Company !** 🎓"
    rag_engine.memory_store.add_message(session_id, bloc_k_response, "assistant")
    
    # Test 2: Deuxième demande de formation → BLOC M
    print("\n📋 Test 2: Deuxième demande de formation")
    message2 = "je voudrais faire une formation en anglais pro"
    
    # Ajouter le message à la mémoire
    rag_engine.memory_store.add_message(session_id, message2, "user")
    
    # Analyser l'intention
    decision2 = rag_engine.analyze_intent(message2, session_id)
    
    print(f"Message: {message2}")
    print(f"Décision: {decision2}")
    
    # Vérifier que c'est bien le BLOC M
    test2_ok = decision2["type"] == "BLOC_M"
    print(f"✅ BLOC M détecté: {test2_ok}")
    
    # Simuler la réponse du bot (BLOC M)
    bloc_m_response = "🎯 **Excellent choix !** 🎯"
    rag_engine.memory_store.add_message(session_id, bloc_m_response, "assistant")
    
    # Test 3: Confirmation → BLOC 6.2
    print("\n📋 Test 3: Confirmation d'escalade")
    message3 = "oui je veux bien"
    
    # Ajouter le message à la mémoire
    rag_engine.memory_store.add_message(session_id, message3, "user")
    
    # Analyser l'intention
    decision3 = rag_engine.analyze_intent(message3, session_id)
    
    print(f"Message: {message3}")
    print(f"Décision: {decision3}")
    
    # Vérifier que c'est bien le BLOC 6.2
    test3_ok = decision3["type"] == "BLOC_6_2"
    print(f"✅ BLOC 6.2 détecté: {test3_ok}")
    
    # Test 4: Vérification anti-répétition
    print("\n📋 Test 4: Vérification anti-répétition")
    message4 = "je voudrais faire une formation"
    
    # Ajouter le message à la mémoire
    rag_engine.memory_store.add_message(session_id, message4, "user")
    
    # Analyser l'intention
    decision4 = rag_engine.analyze_intent(message4, session_id)
    
    print(f"Message: {message4}")
    print(f"Décision: {decision4}")
    
    # Vérifier que ce n'est PAS le BLOC K (car déjà présenté)
    test4_ok = decision4["type"] != "BLOC_K"
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
    result = test_conversation_flow()
    
    if result:
        print("\n🎉 La logique de conversation fonctionne correctement !")
        sys.exit(0)
    else:
        print("\n💥 Des problèmes ont été détectés dans la logique de conversation.")
        sys.exit(1)