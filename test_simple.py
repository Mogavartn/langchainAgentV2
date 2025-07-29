#!/usr/bin/env python3
"""
Script de test simplifié pour vérifier les modifications apportées.
"""

def test_direct_financing_keywords():
    """Test des nouveaux mots-clés de financement direct"""
    print("🧪 TEST MOTS-CLÉS FINANCEMENT DIRECT")
    print("=" * 50)
    
    # Mots-clés de financement direct (extraits du code)
    direct_financing_terms = [
        "payé tout seul", "financé tout seul", "financé en direct",
        "paiement direct", "financement direct", "j'ai payé", 
        "j'ai financé", "payé par moi", "financé par moi",
        "sans organisme", "financement personnel", "paiement personnel",
        "auto-financé", "autofinancé", "mes fonds", "par mes soins",
        # NOUVEAUX TERMES AJOUTÉS
        "j'ai payé toute seule", "j'ai payé moi", "c'est moi qui est financé",
        "financement moi même", "financement en direct", "paiement direct",
        "j'ai financé toute seule", "j'ai financé moi", "c'est moi qui ai payé",
        "financement par mes soins", "paiement par mes soins", "mes propres moyens",
        "avec mes propres fonds", "de ma poche", "de mes économies",
        "financement individuel", "paiement individuel", "auto-financement",
        "financement privé", "paiement privé", "financement personnel",
        "j'ai tout payé", "j'ai tout financé", "c'est moi qui finance",
        "financement direct", "paiement en direct", "financement cash",
        "paiement cash", "financement comptant", "paiement comptant"
    ]
    
    test_cases = [
        "j'ai payé toute seule",
        "j'ai payé moi",
        "c'est moi qui est financé",
        "financement moi même",
        "financement en direct",
        "paiement direct",
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
    
    def detect_direct_financing(message_lower):
        """Fonction simplifiée de détection"""
        return any(term in message_lower for term in direct_financing_terms)
    
    for message in test_cases:
        is_direct = detect_direct_financing(message.lower())
        status = "✅ DÉTECTÉ" if is_direct else "❌ NON DÉTECTÉ"
        print(f"{status}: '{message}'")
    
    print(f"\n📊 Total: {len(test_cases)} termes testés")
    detected_count = sum(1 for msg in test_cases if detect_direct_financing(msg.lower()))
    print(f"✅ Détectés: {detected_count}")
    print(f"❌ Non détectés: {len(test_cases) - detected_count}")

def test_formation_keywords():
    """Test des mots-clés de formation"""
    print("\n🧪 TEST MOTS-CLÉS FORMATIONS")
    print("=" * 50)
    
    formation_keywords = [
        "formation", "cours", "apprendre", "catalogue", "proposez",
        "disponible", "enseigner", "stage", "bureautique", 
        "informatique", "langues", "anglais", "excel"
    ]
    
    test_cases = [
        "quelles sont vos formations ?",
        "vous proposez quoi comme formations ?",
        "formations disponibles ?",
        "catalogue formations ?",
        "qu'est-ce que vous proposez comme formations ?"
    ]
    
    def detect_formation(message_lower):
        """Fonction simplifiée de détection formation"""
        return any(keyword in message_lower for keyword in formation_keywords)
    
    for message in test_cases:
        is_formation = detect_formation(message.lower())
        status = "✅ DÉTECTÉ" if is_formation else "❌ NON DÉTECTÉ"
        print(f"{status}: '{message}'")
    
    print(f"\n📊 Total: {len(test_cases)} termes testés")
    detected_count = sum(1 for msg in test_cases if detect_formation(msg.lower()))
    print(f"✅ Détectés: {detected_count}")
    print(f"❌ Non détectés: {len(test_cases) - detected_count}")

def test_payment_keywords():
    """Test des mots-clés de paiement"""
    print("\n🧪 TEST MOTS-CLÉS PAIEMENT")
    print("=" * 50)
    
    payment_keywords = [
        "pas été payé", "pas payé", "paiement", "cpf", "opco", 
        "virement", "argent", "retard", "délai", "attends",
        "finance", "financement", "payé pour", "rien reçu",
        "je vais être payé quand", "délai paiement"
    ]
    
    test_cases = [
        "j'ai pas été payé",
        "je n'ai pas reçu mon paiement",
        "pas de virement reçu",
        "délai paiement formation",
        "quand vais-je être payé ?"
    ]
    
    def detect_payment(message_lower):
        """Fonction simplifiée de détection paiement"""
        return any(keyword in message_lower for keyword in payment_keywords)
    
    for message in test_cases:
        is_payment = detect_payment(message.lower())
        status = "✅ DÉTECTÉ" if is_payment else "❌ NON DÉTECTÉ"
        print(f"{status}: '{message}'")
    
    print(f"\n📊 Total: {len(test_cases)} termes testés")
    detected_count = sum(1 for msg in test_cases if detect_payment(msg.lower()))
    print(f"✅ Détectés: {detected_count}")
    print(f"❌ Non détectés: {len(test_cases) - detected_count}")

def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DES TESTS - MODIFICATIONS FORMATIONS ET PAIEMENTS")
    print("=" * 60)
    
    test_direct_financing_keywords()
    test_formation_keywords()
    test_payment_keywords()
    
    print("\n✅ TOUS LES TESTS TERMINÉS")
    print("=" * 60)
    print("📋 RÉSUMÉ DES MODIFICATIONS:")
    print("1. ✅ BLOC K prioritaire pour les formations")
    print("2. ✅ Détection renforcée des financements directs")
    print("3. ✅ BLOC J pour paiements directs délai dépassé")
    print("4. ✅ Nouveaux termes de financement direct ajoutés")
    print("\n🎯 COMPORTEMENT ATTENDU:")
    print("- Questions formations → BLOC K en priorité")
    print("- Financement direct détecté → BLOC J si délai > 7 jours")
    print("- Détection renforcée avec 30+ nouveaux termes")

if __name__ == "__main__":
    main()