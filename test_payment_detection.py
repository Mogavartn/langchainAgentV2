#!/usr/bin/env python3
"""
Script de test pour vérifier la détection des paiements
"""

import requests
import json

# URL de l'API (ajustez selon votre configuration)
API_URL = "http://localhost:8000"

def test_payment_detection():
    """Test de la détection des paiements"""
    
    # Messages de test basés sur vos exemples
    test_messages = [
        "j'ai pas encore reçu mes sous",
        "j'ai pas encore été payé",
        "j'attends toujours ma tune",
        "c'est quand que je serais payé ?",
        "quand est-ce que je vais être payé ?",
        "j'ai pas reçu mon argent",
        "pas encore reçu mon paiement",
        "j'attends toujours mon virement",
        "quand je serai payé ?",
        "c'est quand mon argent ?"
    ]
    
    print("🧪 TEST DE DÉTECTION DES PAIEMENTS")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Message: '{message}'")
        
        try:
            # Appel à l'API
            response = requests.post(
                f"{API_URL}/test_payment_logic",
                json={
                    "messages": [message],
                    "session_id": f"test_session_{i}"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data["test_results"][0]
                
                print(f"   ✅ Détection paiement: {result['payment_detected']}")
                print(f"   📊 Type de décision: {result['decision_type']}")
                print(f"   💰 Financement direct: {result['direct_financing']}")
                print(f"   🏢 Financement OPCO: {result['opco_financing']}")
                print(f"   ⏰ Type financement: {result['financing_type']}")
                print(f"   📅 Info temps: {result['time_info']}")
                print(f"   🚨 Escalade: {result['should_escalate']}")
                
                # Vérifier si c'est le bon bloc
                if "FILTRAGE PAIEMENT" in result['decision_type']:
                    print(f"   🎯 BLOC F détecté ✓")
                elif "PAIEMENT DIRECT DÉLAI DÉPASSÉ" in result['decision_type']:
                    print(f"   🎯 BLOC L détecté ✓")
                elif "ESCALADE AGENT ADMIN" in result['decision_type']:
                    print(f"   🎯 BLOC 6.1 détecté ✓")
                else:
                    print(f"   ⚠️  Bloc non identifié")
                    
            else:
                print(f"   ❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Test terminé")

def test_specific_cases():
    """Test des cas spécifiques mentionnés"""
    
    print("\n🎯 TEST DES CAS SPÉCIFIQUES")
    print("=" * 50)
    
    # Cas 1: "j'ai pas encore reçu mes sous" - devrait donner BLOC F
    print("\n1. Test: 'j'ai pas encore reçu mes sous'")
    test_single_message("j'ai pas encore reçu mes sous", "test_case_1")
    
    # Cas 2: "j'ai pas encore été payé" - devrait donner BLOC F
    print("\n2. Test: 'j'ai pas encore été payé'")
    test_single_message("j'ai pas encore été payé", "test_case_2")
    
    # Cas 3: "j'ai payé tout seul" + "il y a 10 jours" - devrait donner BLOC L
    print("\n3. Test: 'j'ai payé tout seul et la formation s'est terminée il y a 10 jours'")
    test_single_message("j'ai payé tout seul et la formation s'est terminée il y a 10 jours", "test_case_3")

def test_single_message(message, session_id):
    """Test d'un message spécifique"""
    try:
        response = requests.post(
            f"{API_URL}/test_payment_logic",
            json={
                "messages": [message],
                "session_id": session_id
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data["test_results"][0]
            
            print(f"   Message: '{message}'")
            print(f"   Décision: {result['decision_type']}")
            print(f"   Détection paiement: {result['payment_detected']}")
            print(f"   Financement direct: {result['direct_financing']}")
            print(f"   Type financement: {result['financing_type']}")
            print(f"   Info temps: {result['time_info']}")
            print(f"   Escalade: {result['should_escalate']}")
            
            # Vérification du bloc attendu
            if "FILTRAGE PAIEMENT" in result['decision_type']:
                print(f"   ✅ BLOC F correctement détecté")
            elif "PAIEMENT DIRECT DÉLAI DÉPASSÉ" in result['decision_type']:
                print(f"   ✅ BLOC L correctement détecté")
            elif "ESCALADE AGENT ADMIN" in result['decision_type']:
                print(f"   ✅ BLOC 6.1 correctement détecté")
            else:
                print(f"   ⚠️  Bloc inattendu détecté")
                
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de détection des paiements")
    print("Assurez-vous que l'API est démarrée sur", API_URL)
    
    try:
        # Test de base
        test_payment_detection()
        
        # Test des cas spécifiques
        test_specific_cases()
        
        print("\n🎉 Tous les tests sont terminés !")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur générale: {str(e)}")