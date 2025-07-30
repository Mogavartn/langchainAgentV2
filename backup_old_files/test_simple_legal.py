#!/usr/bin/env python3
"""
Test simplifié de détection des demandes de récupération d'argent CPF
Teste uniquement la logique de détection des mots-clés
"""

# Définition simplifiée des mots-clés légaux (copiée de process.py)
legal_keywords = frozenset([
    "décaisser le cpf", "récupérer mon argent", "récupérer l'argent", 
    "prendre l'argent", "argent du cpf", "sortir l'argent",
    "avoir mon argent", "toucher l'argent", "retirer l'argent",
    "frauder", "arnaquer", "contourner", "bidouiller",
    "récupérer cpf", "prendre cpf", "décaisser cpf",
    # NOUVELLES VARIANTES POUR CAPTURER TOUTES LES DEMANDES DE RÉCUPÉRATION
    "je veux l'argent", "je veux récupérer", "je veux prendre",
    "je veux l'argent de mon cpf", "je veux récupérer mon argent",
    "je veux prendre l'argent", "je veux l'argent du cpf",
    "je veux récupérer l'argent", "je veux prendre l'argent",
    "récupérer mon argent de mon cpf", "prendre mon argent de mon cpf",
    "récupérer l'argent de mon cpf", "prendre l'argent de mon cpf",
    "récupérer mon argent du cpf", "prendre mon argent du cpf",
    "récupérer l'argent du cpf", "prendre l'argent du cpf",
    "argent de mon cpf", "argent du cpf pour moi",
    "récupération argent cpf", "prise argent cpf",
    "rémunération pour sois-même", "rémunération pour moi",
    "récupération pour sois-même", "récupération pour moi",
    "prendre pour sois-même", "prendre pour moi",
    "argent cpf pour moi", "argent cpf pour sois-même"
])

def has_legal_keywords(message: str) -> bool:
    """Vérifie si un message contient des mots-clés légaux"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in legal_keywords)

def test_legal_detection():
    """Test de détection des demandes légales"""
    
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
        is_legal = has_legal_keywords(message)
        
        # Déterminer si c'est attendu ou non
        expected_legal = i <= 28  # Les 28 premiers messages devraient être détectés comme légaux
        
        status = "✅ LEGAL" if is_legal else "❌ AUTRE"
        expected = "✅ ATTENDU" if expected_legal else "❌ NON ATTENDU"
        
        print(f"{i:2d}. {status} | {expected} | '{message}'")
        
        if is_legal:
            legal_detected += 1
        
        # Vérifier la cohérence
        if expected_legal and not is_legal:
            print(f"    ⚠️  PROBLÈME: Devrait être détecté comme légal mais ne l'est pas!")
        elif not expected_legal and is_legal:
            print(f"    ⚠️  PROBLÈME: Détecté comme légal mais ne devrait pas l'être!")
    
    print("\n" + "=" * 70)
    print(f"📊 RÉSULTATS:")
    print(f"   - Détections légales: {legal_detected}/{total_tests}")
    print(f"   - Taux de détection: {(legal_detected/total_tests)*100:.1f}%")
    print(f"   - Messages attendus comme légaux: 28")
    print(f"   - Messages détectés comme légaux: {legal_detected}")
    
    # Test spécifique des mots-clés
    print(f"\n🔍 TEST DES MOTS-CLÉS LÉGAUX:")
    print(f"   - Nombre de mots-clés légaux: {len(legal_keywords)}")
    
    # Afficher quelques mots-clés pour vérification
    print(f"   - Exemples de mots-clés:")
    for keyword in list(legal_keywords)[:15]:
        print(f"     • {keyword}")
    if len(legal_keywords) > 15:
        print(f"     • ... et {len(legal_keywords) - 15} autres")
    
    # Test spécifique des messages de la conversation
    print(f"\n🎯 TEST DES MESSAGES DE LA CONVERSATION:")
    conversation_messages = [
        "Comment je récupère mon argent de mon CPF ?",
        "je veux l'argent de mon cpf",
        "je veux prendre l'argent de mon cpf"
    ]
    
    for msg in conversation_messages:
        detected = has_legal_keywords(msg)
        print(f"   - '{msg}' → {'✅ DÉTECTÉ' if detected else '❌ NON DÉTECTÉ'}")

if __name__ == "__main__":
    test_legal_detection()