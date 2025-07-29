#!/usr/bin/env python3
"""
Analyseur de données Supabase pour optimisation du code Langchain
Évalue si le code process.py est optimal par rapport à la structure de données
"""

import json
import re
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class OptimizationRecommendation:
    """Structure pour les recommandations d'optimisation"""
    category: str
    priority: str  # high, medium, low
    description: str
    code_impact: str
    implementation_suggestion: str

class SupabaseLangchainAnalyzer:
    """Analyseur pour évaluer l'optimisation du code Langchain vs données Supabase"""
    
    def __init__(self):
        self.supabase_data = None
        self.analysis_results = {}
        self.recommendations = []
        
    def load_supabase_data(self, json_data: str) -> bool:
        """Charge les données JSON de Supabase"""
        try:
            if isinstance(json_data, str):
                self.supabase_data = json.loads(json_data)
            else:
                self.supabase_data = json_data
            print(f"✅ Données Supabase chargées: {len(self.supabase_data)} entrées")
            return True
        except Exception as e:
            print(f"❌ Erreur chargement données: {e}")
            return False
    
    def analyze_data_structure(self) -> Dict[str, Any]:
        """Analyse la structure des données Supabase"""
        if not self.supabase_data:
            return {"error": "Aucune donnée chargée"}
        
        structure_analysis = {
            "total_records": len(self.supabase_data),
            "fields": set(),
            "categories": defaultdict(int),
            "contexts": defaultdict(int),
            "content_types": defaultdict(int),
            "has_embeddings": False,
            "unique_identifiers": set()
        }
        
        # Analyser chaque enregistrement
        for record in self.supabase_data:
            # Collecter tous les champs
            structure_analysis["fields"].update(record.keys())
            
            # Analyser les catégories
            if "category" in record:
                structure_analysis["categories"][record["category"]] += 1
            
            # Analyser les contextes
            if "context" in record:
                structure_analysis["contexts"][record["context"]] += 1
            
            # Détecter les embeddings
            if "embedding" in record or "vector" in record:
                structure_analysis["has_embeddings"] = True
            
            # Analyser les types de contenu
            if "content" in record:
                content_length = len(str(record["content"]))
                if content_length < 100:
                    structure_analysis["content_types"]["short"] += 1
                elif content_length < 500:
                    structure_analysis["content_types"]["medium"] += 1
                else:
                    structure_analysis["content_types"]["long"] += 1
            
            # IDs uniques
            if "id" in record:
                structure_analysis["unique_identifiers"].add(record["id"])
        
        # Convertir sets en listes pour JSON
        structure_analysis["fields"] = list(structure_analysis["fields"])
        structure_analysis["categories"] = dict(structure_analysis["categories"])
        structure_analysis["contexts"] = dict(structure_analysis["contexts"])
        structure_analysis["content_types"] = dict(structure_analysis["content_types"])
        structure_analysis["unique_identifiers"] = len(structure_analysis["unique_identifiers"])
        
        self.analysis_results["structure"] = structure_analysis
        return structure_analysis
    
    def analyze_keyword_coverage(self) -> Dict[str, Any]:
        """Analyse la couverture des mots-clés du code Langchain vs données Supabase"""
        if not self.supabase_data:
            return {"error": "Aucune donnée chargée"}
        
        # Mots-clés du code Langchain (extraits de process.py)
        langchain_keywords = {
            "payment": ["pas été payé", "pas payé", "paiement", "cpf", "opco", "virement", 
                       "argent", "retard", "délai", "attends", "finance", "financement",
                       "payé tout seul", "financé tout seul", "financé en direct",
                       "paiement direct", "financement direct"],
            "ambassador": ["ambassadeur", "commission", "affiliation", "partenaire",
                          "gagner argent", "contacts", "étapes", "devenir", "programme"],
            "formation": ["formation", "cours", "apprendre", "catalogue", "proposez",
                         "disponible", "enseigner", "stage", "bureautique"],
            "legal": ["décaisser le cpf", "récupérer mon argent", "frauder", "arnaquer"],
            "contact": ["comment envoyer", "envoie des contacts", "transmettre contacts"]
        }
        
        coverage_analysis = {
            "keyword_matches": defaultdict(list),
            "missing_keywords": defaultdict(list),
            "supabase_unique_terms": set(),
            "coverage_percentage": {}
        }
        
        # Analyser le contenu Supabase
        all_supabase_content = ""
        for record in self.supabase_data:
            if "content" in record:
                all_supabase_content += " " + str(record["content"]).lower()
            if "category" in record:
                all_supabase_content += " " + str(record["category"]).lower()
            if "context" in record:
                all_supabase_content += " " + str(record["context"]).lower()
        
        # Vérifier la couverture des mots-clés
        for category, keywords in langchain_keywords.items():
            found_keywords = []
            missing_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in all_supabase_content:
                    found_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)
            
            coverage_analysis["keyword_matches"][category] = found_keywords
            coverage_analysis["missing_keywords"][category] = missing_keywords
            coverage_analysis["coverage_percentage"][category] = round(
                (len(found_keywords) / len(keywords)) * 100, 2
            ) if keywords else 0
        
        # Identifier des termes uniques dans Supabase
        supabase_words = set(re.findall(r'\b\w+\b', all_supabase_content.lower()))
        langchain_words = set()
        for keywords in langchain_keywords.values():
            for keyword in keywords:
                langchain_words.update(re.findall(r'\b\w+\b', keyword.lower()))
        
        coverage_analysis["supabase_unique_terms"] = list(supabase_words - langchain_words)[:20]  # Top 20
        
        self.analysis_results["keyword_coverage"] = coverage_analysis
        return coverage_analysis
    
    def analyze_content_mapping(self) -> Dict[str, Any]:
        """Analyse la correspondance entre les blocs Supabase et la logique Langchain"""
        if not self.supabase_data:
            return {"error": "Aucune donnée chargée"}
        
        # Blocs attendus par le code Langchain
        expected_blocks = {
            "AMBASSADEUR_DEFINITION": "Définition ambassadeur",
            "AFFILIATION_DEFINITION": "Définition affiliation", 
            "BLOC_LEGAL": "Recadrage légal",
            "BLOC_PAIEMENT": "Gestion paiements",
            "BLOC_F1": "Question CPF bloqué",
            "BLOC_F2": "Déblocage CPF",
            "BLOC_B": "Programme ambassadeur",
            "BLOC_D": "Devenir ambassadeur",
            "BLOC_E": "Envoi contacts",
            "BLOC_C": "Plus de CPF",
            "BLOC_G": "Contact humain",
            "BLOC_H": "Argumentaire prospect",
            "BLOC_I1": "Argumentaire entreprise",
            "BLOC_I2": "Argumentaire ambassadeur",
            "BLOC_J": "Délais",
            "BLOC_AGRO": "Gestion agressivité"
        }
        
        mapping_analysis = {
            "blocks_found": {},
            "blocks_missing": [],
            "blocks_extra": [],
            "content_quality": {},
            "mapping_score": 0
        }
        
        # Analyser les blocs présents
        supabase_blocks = set()
        for record in self.supabase_data:
            block_id = None
            if "id" in record:
                block_id = record["id"]
            elif "context" in record:
                block_id = record["context"]
            elif "category" in record:
                block_id = record["category"]
            
            if block_id:
                supabase_blocks.add(str(block_id))
                
                # Analyser la qualité du contenu
                content = record.get("content", "")
                mapping_analysis["content_quality"][block_id] = {
                    "length": len(str(content)),
                    "has_emojis": "🙏" in str(content) or "✅" in str(content),
                    "has_links": "http" in str(content) or "www" in str(content),
                    "has_structure": "•" in str(content) or "→" in str(content)
                }
        
        # Identifier les blocs manquants et supplémentaires
        expected_block_names = set(expected_blocks.keys())
        mapping_analysis["blocks_missing"] = list(expected_block_names - supabase_blocks)
        mapping_analysis["blocks_extra"] = list(supabase_blocks - expected_block_names)
        mapping_analysis["blocks_found"] = {
            block: expected_blocks.get(block, "Bloc trouvé") 
            for block in supabase_blocks 
            if block in expected_block_names
        }
        
        # Score de correspondance
        total_expected = len(expected_blocks)
        found_blocks = len(mapping_analysis["blocks_found"])
        mapping_analysis["mapping_score"] = round((found_blocks / total_expected) * 100, 2)
        
        self.analysis_results["content_mapping"] = mapping_analysis
        return mapping_analysis
    
    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Génère des recommandations d'optimisation basées sur l'analyse"""
        recommendations = []
        
        if "structure" in self.analysis_results:
            structure = self.analysis_results["structure"]
            
            # Recommandations basées sur la structure
            if structure["has_embeddings"]:
                recommendations.append(OptimizationRecommendation(
                    category="Performance",
                    priority="high",
                    description="Votre base contient des embeddings - le code Langchain pourrait les utiliser pour une recherche sémantique plus efficace",
                    code_impact="Amélioration significative de la pertinence des réponses",
                    implementation_suggestion="Ajouter une couche de recherche vectorielle dans process.py"
                ))
            
            if len(structure["categories"]) > 10:
                recommendations.append(OptimizationRecommendation(
                    category="Architecture",
                    priority="medium", 
                    description="Nombreuses catégories détectées - optimisation possible du système de décision",
                    code_impact="Réduction de la complexité et amélioration des performances",
                    implementation_suggestion="Créer des groupes de catégories dans les keyword_sets"
                ))
        
        if "keyword_coverage" in self.analysis_results:
            coverage = self.analysis_results["keyword_coverage"]
            
            for category, percentage in coverage["coverage_percentage"].items():
                if percentage < 70:
                    recommendations.append(OptimizationRecommendation(
                        category="Keyword Coverage",
                        priority="high",
                        description=f"Couverture faible pour {category}: {percentage}%",
                        code_impact="Risque de non-détection d'intentions utilisateur",
                        implementation_suggestion=f"Ajouter les mots-clés manquants: {coverage['missing_keywords'][category][:3]}"
                    ))
            
            if coverage["supabase_unique_terms"]:
                recommendations.append(OptimizationRecommendation(
                    category="Keyword Expansion",
                    priority="medium",
                    description="Termes uniques détectés dans Supabase non couverts par Langchain",
                    code_impact="Opportunité d'améliorer la détection d'intentions",
                    implementation_suggestion=f"Considérer l'ajout de: {coverage['supabase_unique_terms'][:5]}"
                ))
        
        if "content_mapping" in self.analysis_results:
            mapping = self.analysis_results["content_mapping"]
            
            if mapping["mapping_score"] < 80:
                recommendations.append(OptimizationRecommendation(
                    category="Content Mapping",
                    priority="high",
                    description=f"Score de correspondance faible: {mapping['mapping_score']}%",
                    code_impact="Risque d'erreurs dans la récupération de contenu",
                    implementation_suggestion=f"Créer les blocs manquants: {mapping['blocks_missing'][:3]}"
                ))
            
            if mapping["blocks_extra"]:
                recommendations.append(OptimizationRecommendation(
                    category="Content Optimization",
                    priority="low",
                    description="Blocs supplémentaires détectés dans Supabase",
                    code_impact="Opportunité d'enrichir les réponses",
                    implementation_suggestion=f"Intégrer les blocs: {mapping['blocks_extra'][:3]}"
                ))
        
        self.recommendations = recommendations
        return recommendations
    
    def generate_code_optimization_suggestions(self) -> Dict[str, Any]:
        """Génère des suggestions spécifiques d'optimisation du code"""
        suggestions = {
            "keyword_sets_updates": {},
            "new_decision_methods": [],
            "performance_improvements": [],
            "integration_opportunities": []
        }
        
        if "keyword_coverage" in self.analysis_results:
            coverage = self.analysis_results["keyword_coverage"]
            
            # Suggestions de mise à jour des keyword_sets
            for category, missing in coverage["missing_keywords"].items():
                if missing:
                    suggestions["keyword_sets_updates"][category] = missing[:5]  # Top 5
        
        if "structure" in self.analysis_results:
            structure = self.analysis_results["structure"]
            
            # Nouvelles méthodes de décision basées sur les catégories Supabase
            for category in structure["categories"]:
                if category not in ["PAIEMENT", "AMBASSADEUR", "FORMATION"]:  # Catégories déjà gérées
                    suggestions["new_decision_methods"].append(f"_create_{category.lower()}_decision")
            
            # Améliorations de performance
            if structure["total_records"] > 100:
                suggestions["performance_improvements"].append("Implémenter un cache spécialisé pour les blocs fréquents")
            
            if structure["has_embeddings"]:
                suggestions["integration_opportunities"].append("Intégrer la recherche vectorielle pour améliorer la pertinence")
        
        return suggestions
    
    def run_complete_analysis(self, json_data: str) -> Dict[str, Any]:
        """Lance l'analyse complète"""
        print("🚀 DÉMARRAGE DE L'ANALYSE LANGCHAIN vs SUPABASE")
        print("=" * 60)
        
        if not self.load_supabase_data(json_data):
            return {"error": "Impossible de charger les données"}
        
        # Analyses séquentielles
        structure_analysis = self.analyze_data_structure()
        keyword_analysis = self.analyze_keyword_coverage()
        mapping_analysis = self.analyze_content_mapping()
        recommendations = self.generate_optimization_recommendations()
        code_suggestions = self.generate_code_optimization_suggestions()
        
        # Résultats consolidés
        complete_results = {
            "analysis_summary": {
                "data_structure": structure_analysis,
                "keyword_coverage": keyword_analysis,
                "content_mapping": mapping_analysis,
                "optimization_score": self._calculate_optimization_score()
            },
            "recommendations": [
                {
                    "category": rec.category,
                    "priority": rec.priority,
                    "description": rec.description,
                    "code_impact": rec.code_impact,
                    "implementation": rec.implementation_suggestion
                } for rec in recommendations
            ],
            "code_suggestions": code_suggestions,
            "conclusion": self._generate_conclusion()
        }
        
        return complete_results
    
    def _calculate_optimization_score(self) -> int:
        """Calcule un score global d'optimisation"""
        scores = []
        
        if "content_mapping" in self.analysis_results:
            scores.append(self.analysis_results["content_mapping"]["mapping_score"])
        
        if "keyword_coverage" in self.analysis_results:
            avg_coverage = sum(self.analysis_results["keyword_coverage"]["coverage_percentage"].values()) / len(self.analysis_results["keyword_coverage"]["coverage_percentage"])
            scores.append(avg_coverage)
        
        return round(sum(scores) / len(scores), 1) if scores else 0
    
    def _generate_conclusion(self) -> str:
        """Génère une conclusion sur l'optimisation"""
        score = self._calculate_optimization_score()
        
        if score >= 80:
            return f"✅ EXCELLENT: Score d'optimisation {score}% - Le code Langchain est bien aligné avec vos données Supabase"
        elif score >= 60:
            return f"⚠️ CORRECT: Score d'optimisation {score}% - Quelques améliorations recommandées"
        else:
            return f"❌ À AMÉLIORER: Score d'optimisation {score}% - Optimisations importantes nécessaires"

# Fonction utilitaire pour l'analyse rapide
def analyze_supabase_langchain_optimization(json_data: str) -> Dict[str, Any]:
    """Fonction rapide pour analyser l'optimisation"""
    analyzer = SupabaseLangchainAnalyzer()
    return analyzer.run_complete_analysis(json_data)

if __name__ == "__main__":
    print("📊 Analyseur Supabase-Langchain prêt")
    print("Usage: analyzer.run_complete_analysis(json_data)")