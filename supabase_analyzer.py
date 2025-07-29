#!/usr/bin/env python3
"""
Script d'analyse pour examiner et optimiser la base de données Supabase
Usage: python3 supabase_analyzer.py
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseAnalyzer:
    """Analyseur pour examiner la structure et les données Supabase"""
    
    def __init__(self):
        self.client = None
        self.analysis_results = {}
        
    async def initialize_connection(self) -> bool:
        """Initialise la connexion à Supabase"""
        try:
            from supabase import create_client, Client
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                print("❌ Variables d'environnement SUPABASE_URL et SUPABASE_KEY requises")
                print("📝 Ajoutez-les dans votre fichier .env")
                return False
            
            self.client = create_client(supabase_url, supabase_key)
            print("✅ Connexion Supabase établie")
            return True
            
        except ImportError:
            print("❌ Client Supabase non installé")
            print("📝 Installez avec: pip install supabase")
            return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    async def analyze_database_structure(self) -> Dict[str, Any]:
        """Analyse la structure de la base de données"""
        print("\n🔍 ANALYSE DE LA STRUCTURE DE BASE DE DONNÉES")
        print("=" * 60)
        
        structure_analysis = {
            "tables": [],
            "total_tables": 0,
            "recommendations": []
        }
        
        try:
            # Obtenir la liste des tables (requête PostgreSQL)
            result = self.client.rpc('get_table_info').execute()
            
            if result.data:
                structure_analysis["tables"] = result.data
                structure_analysis["total_tables"] = len(result.data)
                print(f"📊 Nombre de tables trouvées: {len(result.data)}")
                
                for table in result.data:
                    print(f"  📋 Table: {table.get('table_name', 'Unknown')}")
                    
            else:
                print("ℹ️  Utilisation d'une méthode alternative pour l'analyse...")
                # Fallback: essayer d'analyser des tables communes
                common_tables = ['content_blocks', 'users', 'conversations', 'messages', 'blocks']
                
                for table_name in common_tables:
                    try:
                        result = self.client.table(table_name).select("*").limit(1).execute()
                        if result.data is not None:
                            structure_analysis["tables"].append({
                                "table_name": table_name,
                                "accessible": True
                            })
                            print(f"  ✅ Table accessible: {table_name}")
                    except:
                        print(f"  ❌ Table non accessible: {table_name}")
        
        except Exception as e:
            print(f"⚠️  Erreur analyse structure: {e}")
            structure_analysis["error"] = str(e)
        
        self.analysis_results["structure"] = structure_analysis
        return structure_analysis
    
    async def analyze_content_blocks(self) -> Dict[str, Any]:
        """Analyse spécifique de la table content_blocks (supposée)"""
        print("\n📋 ANALYSE DE LA TABLE CONTENT_BLOCKS")
        print("=" * 60)
        
        blocks_analysis = {
            "total_blocks": 0,
            "categories": {},
            "contexts": {},
            "sample_blocks": [],
            "recommendations": []
        }
        
        try:
            # Compter le total
            result = self.client.table("content_blocks").select("*", count="exact").execute()
            
            if result.data is not None:
                blocks_analysis["total_blocks"] = len(result.data)
                print(f"📊 Total des blocs: {len(result.data)}")
                
                # Analyser les catégories
                categories = {}
                contexts = {}
                
                for block in result.data:
                    # Catégories
                    category = block.get('category', 'UNKNOWN')
                    categories[category] = categories.get(category, 0) + 1
                    
                    # Contextes
                    context = block.get('context', 'UNKNOWN')
                    contexts[context] = contexts.get(context, 0) + 1
                
                blocks_analysis["categories"] = categories
                blocks_analysis["contexts"] = contexts
                
                # Échantillon de blocs
                blocks_analysis["sample_blocks"] = result.data[:5]
                
                print(f"📈 Catégories trouvées:")
                for category, count in categories.items():
                    print(f"  • {category}: {count} blocs")
                
                print(f"🏷️  Contextes trouvés:")
                for context, count in contexts.items():
                    print(f"  • {context}: {count} blocs")
                
                # Recommandations
                if len(categories) > 10:
                    blocks_analysis["recommendations"].append("Considérer regrouper certaines catégories")
                
                if 'UNKNOWN' in categories:
                    blocks_analysis["recommendations"].append("Certains blocs n'ont pas de catégorie définie")
            
            else:
                print("❌ Aucun bloc trouvé ou table inaccessible")
        
        except Exception as e:
            print(f"⚠️  Erreur analyse content_blocks: {e}")
            blocks_analysis["error"] = str(e)
        
        self.analysis_results["content_blocks"] = blocks_analysis
        return blocks_analysis
    
    async def analyze_performance_opportunities(self) -> Dict[str, Any]:
        """Analyse les opportunités d'optimisation de performance"""
        print("\n⚡ ANALYSE DES OPPORTUNITÉS DE PERFORMANCE")
        print("=" * 60)
        
        performance_analysis = {
            "indexing_recommendations": [],
            "query_optimizations": [],
            "data_structure_improvements": []
        }
        
        try:
            # Analyser la structure des données pour les index
            if "content_blocks" in self.analysis_results:
                blocks_data = self.analysis_results["content_blocks"]
                
                if blocks_data.get("total_blocks", 0) > 100:
                    performance_analysis["indexing_recommendations"].extend([
                        "Index sur 'category' recommandé pour les requêtes par catégorie",
                        "Index sur 'context' recommandé pour les requêtes par contexte",
                        "Index de recherche textuelle sur 'content' pour la recherche sémantique"
                    ])
                
                # Recommandations basées sur les catégories
                categories = blocks_data.get("categories", {})
                if len(categories) > 5:
                    performance_analysis["query_optimizations"].append(
                        "Utiliser des requêtes avec filtres spécifiques plutôt que des scans complets"
                    )
                
                # Recommandations de structure
                if blocks_data.get("total_blocks", 0) > 1000:
                    performance_analysis["data_structure_improvements"].extend([
                        "Considérer la pagination pour les grandes requêtes",
                        "Implémenter un cache pour les blocs fréquemment utilisés",
                        "Séparer les blocs actifs des blocs archivés"
                    ])
            
            print("🎯 Recommandations d'indexation:")
            for rec in performance_analysis["indexing_recommendations"]:
                print(f"  • {rec}")
            
            print("🚀 Optimisations de requêtes:")
            for rec in performance_analysis["query_optimizations"]:
                print(f"  • {rec}")
            
            print("🏗️  Améliorations de structure:")
            for rec in performance_analysis["data_structure_improvements"]:
                print(f"  • {rec}")
        
        except Exception as e:
            print(f"⚠️  Erreur analyse performance: {e}")
            performance_analysis["error"] = str(e)
        
        self.analysis_results["performance"] = performance_analysis
        return performance_analysis
    
    async def analyze_code_integration_opportunities(self) -> Dict[str, Any]:
        """Analyse les opportunités d'intégration avec le code existant"""
        print("\n🔧 ANALYSE D'INTÉGRATION AVEC LE CODE")
        print("=" * 60)
        
        integration_analysis = {
            "langchain_optimizations": [],
            "n8n_workflow_improvements": [],
            "caching_strategies": []
        }
        
        try:
            # Analyser les données pour l'intégration
            if "content_blocks" in self.analysis_results:
                blocks_data = self.analysis_results["content_blocks"]
                categories = blocks_data.get("categories", {})
                
                # Recommandations LangChain
                if "PAIEMENT" in categories:
                    integration_analysis["langchain_optimizations"].append(
                        "Créer des chaînes spécialisées pour les requêtes de paiement"
                    )
                
                if "AMBASSADEUR" in categories:
                    integration_analysis["langchain_optimizations"].append(
                        "Implémenter un système de templates pour les réponses ambassadeur"
                    )
                
                # Recommandations N8N
                integration_analysis["n8n_workflow_improvements"].extend([
                    "Créer des webhooks spécialisés par catégorie de bloc",
                    "Implémenter un système de fallback pour les blocs non trouvés",
                    "Ajouter des logs structurés pour le debugging"
                ])
                
                # Stratégies de cache
                total_blocks = blocks_data.get("total_blocks", 0)
                if total_blocks > 50:
                    integration_analysis["caching_strategies"].extend([
                        "Cache Redis pour les blocs fréquemment utilisés",
                        "Cache local avec TTL pour les réponses",
                        "Invalidation de cache basée sur les mises à jour"
                    ])
            
            print("🤖 Optimisations LangChain:")
            for rec in integration_analysis["langchain_optimizations"]:
                print(f"  • {rec}")
            
            print("🔄 Améliorations N8N:")
            for rec in integration_analysis["n8n_workflow_improvements"]:
                print(f"  • {rec}")
            
            print("💾 Stratégies de cache:")
            for rec in integration_analysis["caching_strategies"]:
                print(f"  • {rec}")
        
        except Exception as e:
            print(f"⚠️  Erreur analyse intégration: {e}")
            integration_analysis["error"] = str(e)
        
        self.analysis_results["integration"] = integration_analysis
        return integration_analysis
    
    async def generate_optimization_report(self) -> str:
        """Génère un rapport complet d'optimisation"""
        print("\n📊 GÉNÉRATION DU RAPPORT D'OPTIMISATION")
        print("=" * 60)
        
        report_path = "/workspace/supabase_optimization_report.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Rapport généré: {report_path}")
            return report_path
        
        except Exception as e:
            print(f"❌ Erreur génération rapport: {e}")
            return ""
    
    async def run_complete_analysis(self):
        """Lance l'analyse complète"""
        print("🚀 DÉMARRAGE DE L'ANALYSE SUPABASE")
        print("=" * 60)
        
        if not await self.initialize_connection():
            return
        
        # Analyses séquentielles
        await self.analyze_database_structure()
        await self.analyze_content_blocks()
        await self.analyze_performance_opportunities()
        await self.analyze_code_integration_opportunities()
        
        # Génération du rapport
        report_path = await self.generate_optimization_report()
        
        print("\n🎉 ANALYSE TERMINÉE")
        print("=" * 60)
        print(f"📄 Rapport disponible: {report_path}")
        print("🔧 Consultez le rapport pour les recommandations détaillées")

async def main():
    """Fonction principale"""
    analyzer = SupabaseAnalyzer()
    await analyzer.run_complete_analysis()

if __name__ == "__main__":
    asyncio.run(main())