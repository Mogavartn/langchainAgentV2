#!/usr/bin/env python3
"""
Script de test simplifié pour identifier les problèmes de reconnaissance des délais
"""

import re

def extract_time_info_simple(message_lower: str) -> dict:
    """Version simplifiée de _extract_time_info pour test"""
    
    # Détection des délais
    time_patterns = {
        'days': r'(\d+)\s*(jour|jours|j)',
        'months': r'(\d+)\s*(mois|moi)',
        'weeks': r'(\d+)\s*(semaine|semaines|sem)'
    }
    
    time_info = {}
    for time_type, pattern in time_patterns.items():
        match = re.search(pattern, message_lower)
        if match:
            time_info[time_type] = int(match.group(1))
    
    # Détection du type de financement
    financing_type = "unknown"
    if any(term in message_lower for term in [
        "payé tout seul", "financé tout seul", "financé en direct",
        "paiement direct", "financement direct", "j'ai payé", 
        "j'ai financé", "payé par moi", "financé par moi",
        "sans organisme", "financement personnel", "paiement personnel",
        "auto-financé", "autofinancé", "mes fonds", "par mes soins"
    ]):
        financing_type = "direct"
    elif any(term in message_lower for term in [
        "opco", "opérateur de compétences", "opérateur compétences",
        "financement opco", "paiement opco", "financé par opco",
        "payé par opco", "opco finance", "opco paie"
    ]):
        financing_type = "opco"
    elif "cpf" in message_lower:
        financing_type = "cpf"
    
    return {
        'time_info': time_info,
        'financing_type': financing_type
    }

def test_time_extraction():
    """Test de la méthode _extract_time_info"""
    
    # Cas de test basés sur les conversations fournies
    test_cases = [
        # OPCO - problèmes identifiés
        {
            "message": "OPCO il y a 18 jours",
            "expected": {"financing_type": "opco", "time_info": {"days": 18}},
            "description": "OPCO avec jours - devrait détecter opco et 18 jours"
        },
        {
            "message": "OPCO il y a 6 semaines", 
            "expected": {"financing_type": "opco", "time_info": {"weeks": 6}},
            "description": "OPCO avec semaines - devrait détecter opco et 6 semaines"
        },
        {
            "message": "OPCO il y a 1 mois",
            "expected": {"financing_type": "opco", "time_info": {"months": 1}},
            "description": "OPCO avec mois - devrait détecter opco et 1 mois"
        },
        {
            "message": "OPCO il y a 5 mois",
            "expected": {"financing_type": "opco", "time_info": {"months": 5}},
            "description": "OPCO avec mois - devrait détecter opco et 5 mois"
        },
        
        # CPF - tests
        {
            "message": "CPF il y a 30 jours",
            "expected": {"financing_type": "cpf", "time_info": {"days": 30}},
            "description": "CPF avec jours - devrait détecter cpf et 30 jours"
        },
        {
            "message": "CPF il y a 2 mois",
            "expected": {"financing_type": "cpf", "time_info": {"months": 2}},
            "description": "CPF avec mois - devrait détecter cpf et 2 mois"
        },
        
        # Direct - tests
        {
            "message": "j'ai payé tout seul il y a 10 jours",
            "expected": {"financing_type": "direct", "time_info": {"days": 10}},
            "description": "Direct avec jours - devrait détecter direct et 10 jours"
        },
        {
            "message": "paiement direct il y a 3 semaines",
            "expected": {"financing_type": "direct", "time_info": {"weeks": 3}},
            "description": "Direct avec semaines - devrait détecter direct et 3 semaines"
        },
        
        # Cas complexes
        {
            "message": "j'ai pas été payé OPCO il y a 18 jours",
            "expected": {"financing_type": "opco", "time_info": {"days": 18}},
            "description": "Message complet avec OPCO et jours"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 6 semaines",
            "expected": {"financing_type": "opco", "time_info": {"weeks": 6}},
            "description": "Message complet avec OPCO et semaines"
        }
    ]
    
    print("=== TEST DE RECONNAISSANCE DES DÉLAIS ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Extraire les informations
        result = extract_time_info_simple(test_case['message'].lower())
        
        print(f"Résultat obtenu:")
        print(f"  - Type financement: {result['financing_type']}")
        print(f"  - Info temps: {result['time_info']}")
        
        # Vérifier les résultats
        financing_ok = result['financing_type'] == test_case['expected']['financing_type']
        time_ok = result['time_info'] == test_case['expected']['time_info']
        
        if financing_ok and time_ok:
            print("✅ SUCCÈS")
        else:
            print("❌ ÉCHEC")
            if not financing_ok:
                print(f"  - Type financement attendu: {test_case['expected']['financing_type']}")
            if not time_ok:
                print(f"  - Temps attendu: {test_case['expected']['time_info']}")
        
        print()

def test_payment_logic():
    """Test de la logique de traitement des paiements"""
    
    test_cases = [
        # OPCO - délais dépassés
        {
            "message": "j'ai pas été payé OPCO il y a 18 jours",
            "expected_action": "FILTRAGE",  # Devrait appliquer BLOC F car délai < 2 mois
            "description": "OPCO 18 jours - délai normal, devrait filtrer"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 6 semaines", 
            "expected_action": "FILTRAGE",  # Devrait appliquer BLOC F car délai < 2 mois
            "description": "OPCO 6 semaines - délai normal, devrait filtrer"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 1 mois",
            "expected_action": "FILTRAGE",  # Devrait appliquer BLOC F car délai < 2 mois
            "description": "OPCO 1 mois - délai normal, devrait filtrer"
        },
        {
            "message": "j'ai pas été payé OPCO il y a 5 mois",
            "expected_action": "ESCALADE",  # Devrait escalader car délai > 2 mois
            "description": "OPCO 5 mois - délai dépassé, devrait escalader"
        },
        
        # Direct - délais dépassés
        {
            "message": "j'ai pas été payé j'ai payé tout seul il y a 10 jours",
            "expected_action": "ESCALADE",  # Devrait appliquer BLOC L car > 7 jours
            "description": "Direct 10 jours - délai dépassé, devrait escalader"
        },
        {
            "message": "j'ai pas été payé paiement direct il y a 3 jours",
            "expected_action": "NORMAL",  # Délai normal, réponse normale
            "description": "Direct 3 jours - délai normal, réponse normale"
        }
    ]
    
    print("=== TEST DE LOGIQUE DE PAIEMENT ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        
        # Extraire les informations
        time_financing_info = extract_time_info_simple(test_case['message'].lower())
        
        print(f"Informations extraites:")
        print(f"  - Type financement: {time_financing_info['financing_type']}")
        print(f"  - Info temps: {time_financing_info['time_info']}")
        
        # Appliquer la logique de décision
        action = "UNKNOWN"
        
        if time_financing_info['financing_type'] == 'opco':
            months = time_financing_info['time_info'].get('months', 0)
            weeks = time_financing_info['time_info'].get('weeks', 0)
            days = time_financing_info['time_info'].get('days', 0)
            
            # Convertir en mois pour comparaison
            total_months = months + (weeks * 4 / 12) + (days / 30)
            
            if total_months > 2:
                action = "ESCALADE"
            else:
                action = "FILTRAGE"
                
        elif time_financing_info['financing_type'] == 'direct':
            days = time_financing_info['time_info'].get('days', 0)
            weeks = time_financing_info['time_info'].get('weeks', 0)
            
            # Convertir en jours pour comparaison
            total_days = days + (weeks * 7)
            
            if total_days > 7:
                action = "ESCALADE"
            else:
                action = "NORMAL"
        
        print(f"Action déterminée: {action}")
        
        # Vérifier le résultat
        if action == test_case['expected_action']:
            print("✅ SUCCÈS")
        else:
            print("❌ ÉCHEC")
            print(f"  - Action attendue: {test_case['expected_action']}")
        
        print()

def test_regex_patterns():
    """Test des patterns regex pour la détection des délais"""
    
    print("=== TEST DES PATTERNS REGEX ===\n")
    
    # Patterns actuels
    patterns = {
        'days': r'(\d+)\s*(jour|jours|j)',
        'months': r'(\d+)\s*(mois|moi)',
        'weeks': r'(\d+)\s*(semaine|semaines|sem)'
    }
    
    test_messages = [
        "il y a 18 jours",
        "il y a 6 semaines", 
        "il y a 1 mois",
        "il y a 5 mois",
        "il y a 3 semaines",
        "il y a 10 jours",
        "il y a 2 mois"
    ]
    
    for message in test_messages:
        print(f"Message: '{message}'")
        message_lower = message.lower()
        
        for time_type, pattern in patterns.items():
            match = re.search(pattern, message_lower)
            if match:
                value = int(match.group(1))
                print(f"  - {time_type}: {value}")
            else:
                print(f"  - {time_type}: non détecté")
        
        print()

if __name__ == "__main__":
    print("🔍 DIAGNOSTIC DES PROBLÈMES DE RECONNAISSANCE DES DÉLAIS\n")
    print("=" * 60)
    
    test_regex_patterns()
    print("=" * 60)
    
    test_time_extraction()
    print("=" * 60)
    
    test_payment_logic()
    print("=" * 60)
    
    print("\n📋 RÉSUMÉ DES PROBLÈMES IDENTIFIÉS:")
    print("1. La méthode _extract_time_info semble correcte")
    print("2. Les patterns regex semblent fonctionner")
    print("3. Le problème pourrait être dans la logique de décision")
    print("4. Vérifier si les délais sont correctement comparés")