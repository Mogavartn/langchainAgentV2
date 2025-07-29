# Middleware d'Escalade Commerciale - JAK Company

Ce middleware automatise l'ajout du bloc de transition d'escalade commerciale dans vos conversations LangChain.

## 🎯 Objectif

Résoudre les problèmes identifiés dans vos conversations :
- ❌ Éviter la répétition de la liste des formations
- ✅ Proposer automatiquement l'escalade commerciale
- ✅ Utiliser le BLOC 6.2 approprié
- ✅ Garder un ton professionnel et engageant

## 📁 Fichiers

- `escalation_middleware.py` - Le middleware principal
- `langchain_integration.py` - Exemple d'intégration avec LangChain
- `test_middleware.py` - Tests de validation
- `README.md` - Ce fichier

## 🚀 Utilisation

### Installation simple

```python
from escalation_middleware import EscalationMiddleware

# Créer l'instance
middleware = EscalationMiddleware()

# Traiter une réponse
user_message = "je voudrais faire une formation en anglais pro"
bot_response = "Parfait ! Les formations en anglais professionnel sont possibles..."

# Appliquer le middleware
final_response = middleware.process_response(user_message, bot_response)
```

### Intégration avec LangChain

```python
from langchain.chains import LLMChain
from escalation_middleware import EscalationMiddleware

class EscalationAwareChain:
    def __init__(self, llm):
        self.llm = llm
        self.middleware = EscalationMiddleware()
        # ... configuration de votre chaîne
    
    def run(self, user_message: str, context: str = "") -> str:
        # Générer la réponse de base
        base_response = self.base_chain.run({
            "user_message": user_message,
            "context": context
        })
        
        # Appliquer le middleware d'escalade
        return self.middleware.process_response(user_message, base_response)
```

## 🧪 Tests

Exécutez les tests pour valider le fonctionnement :

```bash
python3 test_middleware.py
```

### Résultats attendus

✅ **TEST 1**: Demande formation spécifique → Escalade ajoutée
✅ **TEST 2**: Demande générale → Pas d'escalade (liste des formations)
✅ **TEST 3**: Déjà en escalade → Pas de doublon
✅ **TEST 4**: Autre formation → Escalade ajoutée

## 🔧 Configuration

### Mots-clés de formation

Le middleware détecte automatiquement les demandes de formation via ces mots-clés :
- `formation`, `anglais`, `pro`, `professionnel`
- `bureautique`, `informatique`, `langues`
- `web`, `3d`, `vente`, `marketing`
- `développement personnel`, `écologie numérique`, `bilan compétences`

### Bloc de transition

Le bloc ajouté automatiquement :
```
[BLOC TRANSITION]
Parfait ! Notre équipe commerciale va pouvoir t'accompagner pour cette formation. 

Veux-tu être mis en relation avec eux pour explorer les possibilités ? 😊
```

### Bloc d'escalade (BLOC 6.2)

Disponible via `middleware.get_escalation_block()` :
```
🔁 ESCALADE AGENT CO
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
Nous te répondrons dès que possible.
```

## 🎯 Logique de détection

Le middleware ajoute le bloc de transition si :
1. ✅ L'utilisateur demande une formation spécifique
2. ✅ La réponse n'est pas une liste de formations
3. ✅ La réponse n'est pas déjà une escalade

## 💡 Avantages

- 🚀 **Sans modification BDD** : Fonctionne avec votre système existant
- 🔧 **Facile à intégrer** : Middleware simple à ajouter dans votre pipeline
- 🎯 **Intelligent** : Détecte automatiquement quand escalader
- 🛡️ **Sûr** : Évite les doublons et les escalades inappropriées
- 📈 **Maintenable** : Configuration centralisée et tests inclus

## 🔄 Workflow recommandé

1. **Message utilisateur** → Demande formation spécifique
2. **LLM** → Génère réponse de base (sans liste)
3. **Middleware** → Ajoute bloc de transition si nécessaire
4. **Si oui** → Utiliser BLOC 6.2 pour l'escalade finale

## 📞 Support

Pour toute question ou modification, contactez l'équipe technique JAK Company.