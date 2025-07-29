# Guide de Configuration Supabase

## 🎯 Objectif

Ce guide vous aide à configurer la connexion Supabase pour votre système RAG JAK Company, permettant de stocker et rechercher les blocs de contenu dynamiquement.

## 📋 Prérequis

✅ **Installation terminée :**
- [x] Client Supabase Python installé (`supabase==2.3.4`)
- [x] Code d'intégration ajouté dans `process.py`
- [x] Endpoints de test créés

## 🔧 Configuration Requise

### Étape 1: Variables d'Environnement

Créez un fichier `.env` dans le répertoire racine avec :

```bash
# Configuration Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_clé_anon_ici

# Configuration OpenAI (existante)
OPENAI_API_KEY=votre_clé_openai

# Configuration serveur
PORT=8000
```

**Où trouver ces informations :**
1. Connectez-vous à [Supabase](https://supabase.com)
2. Allez dans votre projet
3. Dans Settings > API :
   - `SUPABASE_URL` = Project URL
   - `SUPABASE_KEY` = anon public key

### Étape 2: Structure de Base de Données

Créez une table `content_blocks` avec cette structure :

```sql
CREATE TABLE content_blocks (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    context VARCHAR(100),
    content TEXT NOT NULL,
    tags TEXT[],
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index pour améliorer les performances de recherche
CREATE INDEX idx_content_blocks_category ON content_blocks(category);
CREATE INDEX idx_content_blocks_context ON content_blocks(context);
CREATE INDEX idx_content_blocks_content ON content_blocks USING gin(to_tsvector('french', content));
```

### Étape 3: Données d'Exemple

Insérez quelques blocs de test :

```sql
INSERT INTO content_blocks (category, context, content) VALUES
('PAIEMENT', 'DELAI_DIRECT', 'Le paiement est effectué sous 7 jours après la fin de la formation et réception du dossier complet (émargement + administratif) 🧾'),
('PAIEMENT', 'DELAI_CPF', 'Le paiement se fait à partir de 45 jours, mais uniquement à compter de la réception effective des feuilles d''émargement signées ✍'),
('PAIEMENT', 'DELAI_OPCO', 'Le délai moyen est de 2 mois, mais certains dossiers prennent jusqu''à 6 mois ⏳'),
('AMBASSADEUR', 'DEFINITION', 'Un ambassadeur JAK Company est un partenaire qui recommande nos formations et gagne des commissions 💰'),
('LEGAL', 'BLOC LEGAL', 'Nous ne pouvons pas accepter d''inscription si le but est uniquement de récupérer l''argent du CPF. Notre programme d''affiliation est disponible après une formation sérieuse. 🚫');
```

## 🧪 Tests de Validation

### Test 1: Variables d'Environnement
```bash
python3 test_supabase_connection.py
```

### Test 2: Endpoints API
```bash
# Démarrer le serveur
python3 process.py

# Tester la connexion
curl http://localhost:8000/supabase_status

# Tester la recherche
curl -X POST http://localhost:8000/test_supabase_search \
  -H "Content-Type: application/json" \
  -d '{"query": "paiement", "context_type": "DELAI_DIRECT"}'
```

### Test 3: Intégration RAG
```bash
curl -X POST http://localhost:8000/optimize_rag \
  -H "Content-Type: application/json" \
  -d '{"message": "j'\''ai pas été payé", "session_id": "test"}'
```

## 🎯 Fonctionnalités Implémentées

### ✅ Client Supabase Optimisé
- **Cache TTL** : 15 minutes pour les recherches
- **Gestion d'erreurs** robuste
- **Logs détaillés** pour le debugging

### ✅ Recherche Intelligente
- **Recherche textuelle** avec fallback
- **Filtrage par catégorie** et contexte
- **Recherche sémantique** (si embeddings disponibles)

### ✅ Intégration RAG
- **Enrichissement automatique** des décisions
- **Contexte adaptatif** selon le type de requête
- **Priorisation** des blocs pertinents

### ✅ Endpoints de Test
- `/supabase_status` - Vérifier la connexion
- `/test_supabase_search` - Tester la recherche
- `/performance_metrics` - Métriques incluant Supabase

## 🔍 Types de Recherche Supportés

### 1. Recherche par Contexte de Paiement
```python
# Détecte automatiquement "j'ai payé tout seul"
# → Recherche blocs PAIEMENT avec contexte DELAI_DIRECT
```

### 2. Recherche Ambassadeur
```python
# Détecte "devenir ambassadeur"
# → Recherche blocs AMBASSADEUR avec contexte approprié
```

### 3. Recherche Légale
```python
# Détecte tentatives de récupération CPF
# → Applique bloc LEGAL immédiatement
```

## 🚀 Avantages de l'Intégration

### 🎯 **Performance**
- Cache intelligent TTL
- Requêtes optimisées avec index
- Fallback gracieux si Supabase indisponible

### 🧠 **Intelligence**
- Enrichissement contextuel des réponses
- Adaptation selon le type de financement détecté
- Priorisation automatique des blocs

### 🔧 **Maintenance**
- Blocs modifiables en temps réel
- Logs détaillés pour debugging
- Tests automatisés de validation

## 📊 Monitoring

### Métriques Disponibles
- Statut connexion Supabase
- Performance des recherches
- Taux de cache hit/miss
- Nombre de blocs trouvés par requête

### Logs Structurés
```
🔍 SUPABASE SEARCH: 'paiement formation...' | Context: DELAI_DIRECT
✅ Found 3 blocks for query: paiement...
🚀 CACHE HIT for Supabase search: paiement...
```

## 🔧 Dépannage

### Problème : Variables d'environnement
```bash
# Vérifier le fichier .env
cat .env

# Recharger les variables
source .env
```

### Problème : Connexion Supabase
```bash
# Tester manuellement
python3 test_supabase_connection.py

# Vérifier les logs
tail -f logs/app.log
```

### Problème : Structure de base
- Vérifiez que la table `content_blocks` existe
- Vérifiez les colonnes : `category`, `context`, `content`
- Vérifiez les permissions de lecture

## 🎉 Validation Finale

Si tous les tests passent, vous devriez voir :

```
🎉 SUCCÈS: Tous les tests passés!
✅ Supabase est correctement configuré et fonctionnel
```

Votre système RAG est maintenant connecté à Supabase et peut :
- ✅ Rechercher dynamiquement les blocs de contenu
- ✅ Adapter les réponses selon le contexte
- ✅ Enrichir les décisions avec des données temps réel
- ✅ Gérer gracieusement les erreurs de connexion