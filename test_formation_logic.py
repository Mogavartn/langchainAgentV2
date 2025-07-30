#!/usr/bin/env python3
"""
Script de test pour vérifier la logique des formations
Teste le scénario complet : BLOC K → BLOC M → BLOC 6.2
"""

import asyncio
import aiohttp
import json

async def test_formation_logic():
    """Teste la logique complète des formations"""
    
    # URL de l'API
    base_url = "http://localhost:8000"
    
    # Messages de test selon le scénario
    test_messages = [
        "quelles sont vos formations ?",  # Devrait déclencher BLOC K
        "l'anglais m'intérresse",        # Devrait déclencher BLOC M
        "je veux bien être mis en contact oui",  # Devrait déclencher BLOC 6.2
        "ok"  # Devrait déclencher BLOC 6.2 (confirmation)
    ]
    
    print("🧪 TEST DE LA LOGIQUE DES FORMATIONS")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Vérifier que l'API fonctionne
        print("\n1️⃣ Test de connectivité...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    print("✅ API accessible")
                else:
                    print("❌ API non accessible")
                    return
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return
        
        # Test 2: Tester la logique des formations
        print("\n2️⃣ Test de la logique des formations...")
        
        test_data = {
            "messages": test_messages,
            "session_id": "test_formation_session"
        }
        
        try:
            async with session.post(f"{base_url}/test_formation_logic", json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Test de logique exécuté avec succès")
                    
                    # Analyser les résultats
                    print("\n📊 RÉSULTATS DU TEST:")
                    print("-" * 30)
                    
                    for i, test_result in enumerate(result["test_results"]):
                        print(f"\nMessage {i+1}: '{test_result['message']}'")
                        print(f"  → Type de décision: {test_result['decision_type']}")
                        print(f"  → BLOC K présenté: {test_result['bloc_k_presented']}")
                        print(f"  → BLOC M présenté: {test_result['bloc_m_presented']}")
                        print(f"  → Escalade requise: {test_result['should_escalate']}")
                    
                    print(f"\n🎯 ÉTAT FINAL:")
                    print(f"  → BLOC K présenté: {result['final_state']['bloc_k_presented']}")
                    print(f"  → BLOC M présenté: {result['final_state']['bloc_m_presented']}")
                    
                    # Vérifier que la logique est correcte
                    print("\n🔍 VÉRIFICATION DE LA LOGIQUE:")
                    
                    # Message 1: Devrait présenter BLOC K
                    if "FORMATION" in result["test_results"][0]["decision_type"]:
                        print("✅ Message 1: BLOC K correctement détecté")
                    else:
                        print("❌ Message 1: BLOC K non détecté")
                    
                    # Message 2: Devrait présenter BLOC M
                    if "ESCALADE FORMATION" in result["test_results"][1]["decision_type"]:
                        print("✅ Message 2: BLOC M correctement détecté")
                    else:
                        print("❌ Message 2: BLOC M non détecté")
                    
                    # Message 3: Devrait présenter BLOC 6.2
                    if "CONFIRMATION ESCALADE" in result["test_results"][2]["decision_type"]:
                        print("✅ Message 3: BLOC 6.2 correctement détecté")
                    else:
                        print("❌ Message 3: BLOC 6.2 non détecté")
                    
                    # Message 4: Devrait présenter BLOC 6.2
                    if "CONFIRMATION ESCALADE" in result["test_results"][3]["decision_type"]:
                        print("✅ Message 4: BLOC 6.2 correctement détecté")
                    else:
                        print("❌ Message 4: BLOC 6.2 non détecté")
                    
                    # Vérifier l'état final
                    if result['final_state']['bloc_k_presented'] and result['final_state']['bloc_m_presented']:
                        print("✅ État final: Tous les blocs correctement enregistrés")
                    else:
                        print("❌ État final: Blocs manquants")
                    
                else:
                    print(f"❌ Erreur lors du test: {response.status}")
                    error_text = await response.text()
                    print(f"Erreur: {error_text}")
                    
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
        
        # Test 3: Test individuel de chaque message
        print("\n3️⃣ Test individuel des messages...")
        
        session_id = "test_individual_session"
        
        for i, message in enumerate(test_messages):
            print(f"\n--- Test message {i+1}: '{message}' ---")
            
            try:
                test_data = {
                    "message": message,
                    "session_id": session_id
                }
                
                async with session.post(f"{base_url}/optimize_rag", json=test_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        decision_type = result.get("system_instructions", "")
                        if "FORMATION (BLOC K)" in decision_type:
                            print(f"✅ BLOC K détecté")
                        elif "ESCALADE FORMATION (BLOC M)" in decision_type:
                            print(f"✅ BLOC M détecté")
                        elif "CONFIRMATION ESCALADE FORMATION (BLOC 6.2)" in decision_type:
                            print(f"✅ BLOC 6.2 détecté")
                        else:
                            print(f"❓ Autre type: {decision_type[:50]}...")
                        
                        print(f"   Escalade: {result.get('escalade_required', False)}")
                        
                    else:
                        print(f"❌ Erreur: {response.status}")
                        
            except Exception as e:
                print(f"❌ Erreur: {e}")

async def test_specific_scenarios():
    """Teste des scénarios spécifiques"""
    
    print("\n🎯 TESTS DE SCÉNARIOS SPÉCIFIQUES")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Scénario 1: Demande de formation pour la première fois
    print("\n📚 Scénario 1: Première demande de formation")
    
    async with aiohttp.ClientSession() as session:
        test_data = {
            "message": "quelles sont vos formations ?",
            "session_id": "scenario1"
        }
        
        try:
            async with session.post(f"{base_url}/optimize_rag", json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "FORMATION (BLOC K)" in result.get("system_instructions", ""):
                        print("✅ BLOC K correctement détecté pour première demande")
                    else:
                        print("❌ BLOC K non détecté")
                else:
                    print(f"❌ Erreur: {response.status}")
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        # Scénario 2: Intérêt après présentation des formations
        print("\n🎯 Scénario 2: Intérêt après présentation")
        
        # D'abord présenter les formations
        test_data = {
            "message": "quelles sont vos formations ?",
            "session_id": "scenario2"
        }
        
        try:
            async with session.post(f"{base_url}/optimize_rag", json=test_data) as response:
                pass  # On ignore la réponse, on veut juste que le BLOC K soit enregistré
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        # Ensuite tester l'intérêt
        test_data = {
            "message": "l'anglais m'intérresse",
            "session_id": "scenario2"
        }
        
        try:
            async with session.post(f"{base_url}/optimize_rag", json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "ESCALADE FORMATION (BLOC M)" in result.get("system_instructions", ""):
                        print("✅ BLOC M correctement détecté après intérêt")
                    else:
                        print("❌ BLOC M non détecté")
                else:
                    print(f"❌ Erreur: {response.status}")
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        # Scénario 3: Confirmation après BLOC M
        print("\n✅ Scénario 3: Confirmation après BLOC M")
        
        # D'abord présenter les formations et l'intérêt
        for message in ["quelles sont vos formations ?", "l'anglais m'intérresse"]:
            test_data = {
                "message": message,
                "session_id": "scenario3"
            }
            try:
                async with session.post(f"{base_url}/optimize_rag", json=test_data) as response:
                    pass
            except Exception as e:
                print(f"❌ Erreur: {e}")
        
        # Ensuite tester la confirmation
        test_data = {
            "message": "je veux bien être mis en contact oui",
            "session_id": "scenario3"
        }
        
        try:
            async with session.post(f"{base_url}/optimize_rag", json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "CONFIRMATION ESCALADE FORMATION (BLOC 6.2)" in result.get("system_instructions", ""):
                        print("✅ BLOC 6.2 correctement détecté pour confirmation")
                    else:
                        print("❌ BLOC 6.2 non détecté")
                else:
                    print(f"❌ Erreur: {response.status}")
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de la logique des formations")
    
    # Exécuter les tests
    asyncio.run(test_formation_logic())
    asyncio.run(test_specific_scenarios())
    
    print("\n🎉 Tests terminés !")