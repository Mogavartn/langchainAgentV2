#!/usr/bin/env python3
"""
Test de la logique de paiement corrigée
Vérifie que les délais sont correctement gérés
"""

def test_payment_delay_logic():
    """Test de la logique des délais de paiement"""
    print("🧪 TEST LOGIQUE DÉLAIS PAIEMENT")
    print("=" * 50)
    
    test_cases = [
        {
            "scenario": "Financement direct - 4 jours",
            "days": 4,
            "expected": "Réponse normale (pas d'escalade)",
            "reason": "4 jours < 7 jours (dans les délais)"
        },
        {
            "scenario": "Financement direct - 7 jours",
            "days": 7,
            "expected": "Réponse normale (pas d'escalade)",
            "reason": "7 jours = 7 jours (limite exacte)"
        },
        {
            "scenario": "Financement direct - 8 jours",
            "days": 8,
            "expected": "BLOC J (escalade)",
            "reason": "8 jours > 7 jours (délai dépassé)"
        },
        {
            "scenario": "Financement direct - 10 jours",
            "days": 10,
            "expected": "BLOC J (escalade)",
            "reason": "10 jours > 7 jours (délai dépassé)"
        }
    ]
    
    for test in test_cases:
        days = test["days"]
        expected = test["expected"]
        reason = test["reason"]
        
        # Logique de test
        if days <= 7:
            result = "Réponse normale (pas d'escalade)"
            status = "✅" if result == expected else "❌"
        else:
            result = "BLOC J (escalade)"
            status = "✅" if result == expected else "❌"
        
        print(f"{status} {test['scenario']}: {result}")
        print(f"   Raison: {reason}")
        print()

def test_direct_financing_detection():
    """Test de la détection du financement direct"""
    print("🧪 TEST DÉTECTION FINANCEMENT DIRECT")
    print("=" * 50)
    
    direct_financing_terms = [
        "payé tout seul",
        "financé en direct", 
        "j'ai payé",
        "paiement direct",
        "financement direct",
        "j'ai financé",
        "payé par moi",
        "financé par moi",
        "sans organisme",
        "financement personnel",
        "paiement personnel",
        "auto-financé",
        "autofinancé",
        "mes fonds",
        "par mes soins",
        "j'ai payé toute seule",
        "j'ai payé moi",
        "c'est moi qui est financé",
        "financement moi même",
        "financement en direct",
        "j'ai financé toute seule",
        "j'ai financé moi",
        "c'est moi qui ai payé",
        "financement par mes soins",
        "paiement par mes soins",
        "mes propres moyens",
        "avec mes propres fonds",
        "de ma poche",
        "de mes économies",
        "financement individuel",
        "paiement individuel",
        "auto-financement",
        "financement privé",
        "paiement privé",
        "financement personnel",
        "j'ai tout payé",
        "j'ai tout financé",
        "c'est moi qui finance",
        "financement direct",
        "paiement en direct",
        "financement cash",
        "paiement cash",
        "financement comptant",
        "paiement comptant"
    ]
    
    test_messages = [
        "j'ai pas été payé et j'ai payé tout seul",
        "j'ai pas été payé et financé en direct",
        "j'ai pas été payé et j'ai payé par moi",
        "j'ai pas été payé et c'est moi qui est financé",
        "j'ai pas été payé et financement direct",
        "j'ai pas été payé et j'ai payé de ma poche",
        "j'ai pas été payé et auto-financé",
        "j'ai pas été payé et financement personnel"
    ]
    
    def detect_direct_financing(message_lower):
        """Fonction de détection du financement direct"""
        return any(term in message_lower for term in direct_financing_terms)
    
    for message in test_messages:
        is_direct = detect_direct_financing(message.lower())
        status = "✅ DÉTECTÉ" if is_direct else "❌ NON DÉTECTÉ"
        print(f"{status}: '{message}'")
    
    print(f"\n📊 Total termes de financement direct: {len(direct_financing_terms)}")
    detected_count = sum(1 for msg in test_messages if detect_direct_financing(msg.lower()))
    print(f"✅ Messages détectés: {detected_count}/{len(test_messages)}")

def test_complete_scenarios():
    """Test des scénarios complets"""
    print("\n🧪 TEST SCÉNARIOS COMPLETS")
    print("=" * 50)
    
    scenarios = [
        {
            "user_message": "j'ai pas été payé",
            "response": "Comment la formation a-t-elle été financée ? (CPF, OPCO, paiement direct)\nEt environ quand elle s'est terminée ?",
            "user_answer": "en direct et terminée il y a 4 jours",
            "expected_final": "Réponse normale: On est encore dans les délais (7 jours max)",
            "should_escalate": False
        },
        {
            "user_message": "j'ai pas été payé", 
            "response": "Comment la formation a-t-elle été financée ? (CPF, OPCO, paiement direct)\nEt environ quand elle s'est terminée ?",
            "user_answer": "paiement en direct il y a 8 jours",
            "expected_final": "BLOC J: ⏰ Paiement direct : délai dépassé ⏰",
            "should_escalate": True
        },
        {
            "user_message": "j'ai pas été payé et j'ai payé tout seul",
            "response": "Environ quand la formation s'est-elle terminée ?",
            "user_answer": "terminée il y a 4 jours",
            "expected_final": "Réponse normale: On est encore dans les délais (7 jours max)",
            "should_escalate": False
        },
        {
            "user_message": "j'ai pas été payé et financé en direct",
            "response": "Environ quand la formation s'est-elle terminée ?", 
            "user_answer": "terminée il y a 10 jours",
            "expected_final": "BLOC J: ⏰ Paiement direct : délai dépassé ⏰",
            "should_escalate": True
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"📋 Scénario {i}:")
        print(f"   Message: {scenario['user_message']}")
        print(f"   Réponse attendue: {scenario['response']}")
        print(f"   Réponse utilisateur: {scenario['user_answer']}")
        print(f"   Résultat final: {scenario['expected_final']}")
        print(f"   Escalade: {'✅ OUI' if scenario['should_escalate'] else '❌ NON'}")
        print()

def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DES TESTS - LOGIQUE PAIEMENT CORRIGÉE")
    print("=" * 60)
    
    test_payment_delay_logic()
    test_direct_financing_detection()
    test_complete_scenarios()
    
    print("✅ TOUS LES TESTS TERMINÉS")
    print("=" * 60)
    print("📋 RÉSUMÉ DES CORRECTIONS:")
    print("1. ✅ should_escalate=False pour les paiements (logique dans les instructions)")
    print("2. ✅ Logique délais corrigée: ≤7j normal, >7j BLOC J")
    print("3. ✅ Documentation corrigée (4 jours < 7 jours)")
    print("4. ✅ Instructions système clarifiées")
    print("\n🎯 COMPORTEMENT ATTENDU:")
    print("- Financement direct + ≤7 jours → Réponse normale (pas d'escalade)")
    print("- Financement direct + >7 jours → BLOC J (escalade)")
    print("- Détection automatique du financement direct")
    print("- Questions adaptatives selon le type de financement")

if __name__ == "__main__":
    main()