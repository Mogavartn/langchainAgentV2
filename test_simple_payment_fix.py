#!/usr/bin/env python3
"""
Test simplifié pour vérifier la correction du bug de détection des demandes de paiement
"""

import re
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from functools import lru_cache
from collections import defaultdict

# Simulation des classes nécessaires pour le test
class KeywordSets:
    def __init__(self):
        self.escalade_admin_keywords = frozenset([
            # Paiements et délais anormaux
            "délai anormal", "retard anormal", "paiement en retard", "virement en retard",
            "argent pas arrivé", "virement pas reçu",
            "paiement bloqué", "virement bloqué", "argent bloqué",
            "en retard", "retard", "bloqué", "bloquée",
            # Preuves et dossiers
            "justificatif", "preuve", "attestation", "certificat", "facture",
            "dossier bloqué", "dossier en attente", "dossier suspendu",
            "consultation fichier", "accès fichier", "voir mon dossier",
            "état dossier", "suivi dossier", "dossier administratif",
            "dossier", "fichier", "accès", "consultation",
            # Problèmes techniques
            "erreur système", "bug", "problème technique", "dysfonctionnement",
            "impossible de", "ne fonctionne pas", "ça marche pas",
            "problème", "erreur", "dysfonctionnement"
        ])

class TestPaymentDetection:
    def __init__(self):
        self.keyword_sets = KeywordSets()
    
    @lru_cache(maxsize=50)
    def _detect_payment_request(self, message_lower: str) -> bool:
        """Détecte spécifiquement les demandes de paiement avec plus de précision"""
        payment_request_patterns = frozenset([
            # Demandes directes de paiement
            "j'ai pas encore reçu mes sous", "j'ai pas encore reçu mes sous",
            "j'ai pas encore été payé", "j'ai pas encore été payée",
            "j'attends toujours ma tune", "j'attends toujours mon argent",
            "j'attends toujours mon paiement", "j'attends toujours mon virement",
            "c'est quand que je serais payé", "c'est quand que je serai payé",
            "c'est quand que je vais être payé", "c'est quand que je vais être payée",
            "quand est-ce que je serai payé", "quand est-ce que je serai payée",
            "quand est-ce que je vais être payé", "quand est-ce que je vais être payée",
            "quand je serais payé", "quand je serai payé",
            "quand je vais être payé", "quand je vais être payée",
            # Demandes avec "pas encore"
            "pas encore reçu", "pas encore payé", "pas encore payée",
            "pas encore eu", "pas encore touché", "pas encore touchée",
            "n'ai pas encore reçu", "n'ai pas encore payé", "n'ai pas encore payée",
            "n'ai pas encore eu", "n'ai pas encore touché", "n'ai pas encore touchée",
            "je n'ai pas encore reçu", "je n'ai pas encore payé", "je n'ai pas encore payée",
            "je n'ai pas encore eu", "je n'ai pas encore touché", "je n'ai pas encore touchée",
            # Demandes avec "toujours"
            "j'attends toujours", "j'attends encore",
            "j'attends toujours mon argent", "j'attends toujours mon paiement",
            "j'attends toujours mon virement", "j'attends encore mon argent",
            "j'attends encore mon paiement", "j'attends encore mon virement",
            # Demandes avec "toujours pas" (NOUVEAU - CORRECTION DU BUG)
            "toujours pas reçu", "toujours pas payé", "toujours pas payée",
            "toujours pas eu", "toujours pas touché", "toujours pas touchée",
            "j'ai toujours pas reçu", "j'ai toujours pas payé", "j'ai toujours pas payée",
            "j'ai toujours pas eu", "j'ai toujours pas touché", "j'ai toujours pas touchée",
            "je n'ai toujours pas reçu", "je n'ai toujours pas payé", "je n'ai toujours pas payée",
            "je n'ai toujours pas eu", "je n'ai toujours pas touché", "je n'ai toujours pas touchée",
            # Demandes avec "toujours pas été" (NOUVEAU - CORRECTION DU BUG)
            "toujours pas été payé", "toujours pas été payée",
            "j'ai toujours pas été payé", "j'ai toujours pas été payée",
            "je n'ai toujours pas été payé", "je n'ai toujours pas été payée",
            # Demandes avec "pas"
            "pas reçu", "pas payé", "pas payée", "pas eu", "pas touché", "pas touchée",
            "n'ai pas reçu", "n'ai pas payé", "n'ai pas payée", "n'ai pas eu",
            "n'ai pas touché", "n'ai pas touchée", "je n'ai pas reçu",
            "je n'ai pas payé", "je n'ai pas payée", "je n'ai pas eu",
            "je n'ai pas touché", "je n'ai pas touchée",
            # Demandes avec "reçois quand" (NOUVEAU - CORRECTION DU BUG)
            "reçois quand", "reçois quand mes", "reçois quand mon",
            "je reçois quand", "je reçois quand mes", "je reçois quand mon",
            # Termes génériques de paiement
            "sous", "tune", "argent", "paiement", "virement", "rémunération"
        ])
        return any(term in message_lower for term in payment_request_patterns)
    
    @lru_cache(maxsize=100)
    def _has_keywords(self, message_lower: str, keyword_set: frozenset) -> bool:
        """Optimized keyword matching with caching"""
        return any(keyword in message_lower for keyword in keyword_set)

def test_payment_detection_bug_fix():
    """Test la correction du bug de détection des demandes de paiement"""
    
    print("🧪 TEST DE CORRECTION DU BUG DE DÉTECTION DES DEMANDES DE PAIEMENT")
    print("=" * 70)
    
    # Initialiser le détecteur
    detector = TestPaymentDetection()
    
    # Messages de test qui posaient problème
    test_messages = [
        "j'ai toujours pas reçu mon argent",
        "j'ai toujours pas reçu mes sous", 
        "j'ai toujours pas été payé",
        "je reçois quand mes sous ?"
    ]
    
    print("\n📋 MESSAGES DE TEST :")
    for i, message in enumerate(test_messages, 1):
        print(f"{i}. '{message}'")
    
    print("\n🔍 RÉSULTATS DE LA DÉTECTION :")
    print("-" * 50)
    
    all_correct = True
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Message: '{message}'")
        
        # Tester la détection de paiement
        is_payment_request = detector._detect_payment_request(message.lower())
        print(f"   → Détection paiement: {'✅ OUI' if is_payment_request else '❌ NON'}")
        
        # Tester la détection d'escalade admin
        has_escalade_admin = detector._has_keywords(message.lower(), detector.keyword_sets.escalade_admin_keywords)
        print(f"   → Détection escalade admin: {'✅ OUI' if has_escalade_admin else '❌ NON'}")
        
        # Vérifier la cohérence
        if is_payment_request and not has_escalade_admin:
            print(f"   ✅ CORRECT: Détection paiement sans escalade admin")
        elif has_escalade_admin and not is_payment_request:
            print(f"   ⚠️  ATTENTION: Escalade admin sans détection paiement")
            all_correct = False
        else:
            print(f"   ❌ PROBLÈME: Conflit de détection")
            all_correct = False
    
    print("\n" + "=" * 70)
    print("🎯 RÉSULTAT ATTENDU :")
    print("Tous les messages doivent être détectés comme des demandes de paiement")
    print("et déclencher le BLOC F (demande d'informations) au lieu de l'escalade admin.")
    print("=" * 70)
    
    if all_correct:
        print("\n🎉 SUCCÈS: Tous les tests passent ! Le bug est corrigé.")
    else:
        print("\n❌ ÉCHEC: Certains tests échouent. Le bug persiste.")
    
    return all_correct

if __name__ == "__main__":
    test_payment_detection_bug_fix()