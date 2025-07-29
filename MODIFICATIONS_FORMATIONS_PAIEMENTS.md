# Modifications - Formations et Paiements

## 1. BLOC K - Formations Disponibles (PRIORITÉ ABSOLUE)

### Problème identifié
Actuellement, certaines questions sur les formations ne déclenchent pas le BLOC K (formations disponibles) et vont directement vers le BLOC C (CPF non disponible).

### Solution implémentée
- **PRIORITÉ ABSOLUE** : Le BLOC K doit TOUJOURS être présenté en premier pour toute question sur les formations
- **Ordre de réponse** : 
  1. BLOC K (formations disponibles) - OBLIGATOIRE
  2. Si question CPF → Bloc C (plus de CPF disponible)
  3. Autres informations selon le contexte

### Texte du BLOC K
```
🎓 **+100 formations disponibles chez JAK Company !** 🎓
📚 **Nos spécialités :**
💻 Bureautique • 🖥 Informatique • 🌍 Langues • 🎨 Web/3D
📈 Vente & Marketing • 🧠 Développement personnel
🌱 Écologie numérique • 🎯 Bilan compétences • ⚙ Sur mesure
**Et bien d'autres encore !** ✨
📖 **E-learning** ou 🏢 **Présentiel** → Tu choisis ! 😉
Quel domaine t'intéresse ? 👀
```

## 2. BLOC J - Paiement Direct Délai Dépassé

### Problème identifié
Le BLOC J n'est pas toujours appliqué quand le délai de 7 jours pour les paiements directs est dépassé.

### Solution implémentée
- **Détection renforcée** des financements directs
- **Application automatique** du BLOC J si financement direct ET délai > 7 jours
- **Escalade immédiate** vers l'équipe admin

### Texte du BLOC J
```
⏰ **Paiement direct : délai dépassé** ⏰
Le délai normal c'est **7 jours max** après la formation ! 📅
Comme c'est dépassé, **j'escalade ton dossier immédiatement** à l'équipe admin ! 🚨
🔁 ESCALADE AGENT ADMIN
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
On va régler ça vite ! 💪
```

## 3. Détection Renforcée des Financements Directs

### Nouveaux termes ajoutés
- "j'ai payé toute seule"
- "j'ai payé moi"
- "c'est moi qui est financé"
- "financement moi même"
- "financement en direct"
- "paiement direct"
- "j'ai financé toute seule"
- "j'ai financé moi"
- "c'est moi qui ai payé"
- "financement par mes soins"
- "paiement par mes soins"
- "mes propres moyens"
- "avec mes propres fonds"
- "de ma poche"
- "de mes économies"
- "financement individuel"
- "paiement individuel"
- "auto-financement"
- "financement privé"
- "paiement privé"
- "financement personnel"
- "j'ai tout payé"
- "j'ai tout financé"
- "c'est moi qui finance"
- "financement direct"
- "paiement en direct"
- "financement cash"
- "paiement cash"
- "financement comptant"
- "paiement comptant"

### Logique de détection
1. **Auto-détection** : Si un de ces termes est détecté → Financement direct confirmé
2. **Question simplifiée** : Demander seulement "Environ quand la formation s'est-elle terminée ?"
3. **Application du BLOC J** : Si délai > 7 jours → BLOC J immédiat

## 4. Ordre de Priorité des Blocs

### Formations
1. **BLOC K** (formations disponibles) - PRIORITÉ ABSOLUE
2. BLOC C (CPF non disponible) - si question CPF spécifique
3. Autres blocs selon le contexte

### Paiements
1. **Détection financement** (direct, CPF, OPCO)
2. **Question de délai** (si nécessaire)
3. **Application du bloc approprié** :
   - Financement direct + > 7 jours → **BLOC J**
   - CPF + > 45 jours → Bloc F1 puis F2
   - OPCO + > 2 mois → Escalade

## 5. Exemples de Comportement Attendu

### Question : "quelles sont vos formations ?"
**Réponse attendue** :
1. BLOC K (formations disponibles) - OBLIGATOIRE
2. Puis informations sur les financements disponibles

### Question : "j'ai pas été payé" + "paiement en direct oui et terminé il y a 8 jours"
**Réponse attendue** :
1. BLOC J (paiement direct délai dépassé) - car 8 jours > 7 jours
2. Escalade immédiate vers l'équipe admin

### Question : "j'ai pas été payé" + "paiement en direct oui et terminé il y a 4 jours"
**Réponse attendue** :
1. Réponse normale : "On est encore dans les délais (7 jours max)"
2. PAS d'escalade car 4 jours < 7 jours

## 6. Tests Recommandés

### Test Formations
- "quelles sont vos formations ?"
- "vous proposez quoi comme formations ?"
- "formations disponibles ?"
- "catalogue formations ?"

### Test Paiements Directs
- "j'ai pas été payé" + "paiement direct oui et terminé il y a 4 jours"
- "j'ai payé toute seule et pas reçu mon paiement"
- "financement direct et formation terminée il y a 10 jours"

### Test Détection Financement
- "j'ai financé moi même"
- "c'est moi qui est financé"
- "financement en direct"
- "j'ai payé de ma poche"