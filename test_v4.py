#!/usr/bin/env python3
"""
Script de test pour la JAK Company RAG V4 API
Teste toutes les fonctionnalités principales de la V4
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = "test_session_v4"

class V4Tester:
    """Classe de test pour la V4 API"""
    
    def __init__(self):
        self.session = None
        self.results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Teste un endpoint de l'API"""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                async with self.session.get(url) as response:
                    result = await response.json()
            elif method == "POST":
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
            
            return {
                "endpoint": endpoint,
                "method": method,
                "status": response.status,
                "result": result,
                "success": response.status == 200
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": "ERROR",
                "result": str(e),
                "success": False
            }
    
    async def test_health_check(self):
        """Teste l'endpoint de santé"""
        print("🔍 Testing health check...")
        result = await self.test_endpoint("/health")
        self.results.append(result)
        
        if result["success"]:
            print("✅ Health check passed")
            print(f"   - API Status: {result['result'].get('status')}")
            print(f"   - Version: {result['result'].get('version')}")
            print(f"   - Memory Stats: {result['result'].get('memory_stats')}")
        else:
            print("❌ Health check failed")
            print(f"   - Error: {result['result']}")
        
        return result["success"]
    
    async def test_root_endpoint(self):
        """Teste l'endpoint racine"""
        print("\n🔍 Testing root endpoint...")
        result = await self.test_endpoint("/")
        self.results.append(result)
        
        if result["success"]:
            print("✅ Root endpoint passed")
            print(f"   - Message: {result['result'].get('message')}")
            print(f"   - Version: {result['result'].get('version')}")
        else:
            print("❌ Root endpoint failed")
            print(f"   - Error: {result['result']}")
        
        return result["success"]
    
    async def test_rag_optimization(self, message: str, expected_bloc: str = None):
        """Teste l'optimisation RAG"""
        print(f"\n🔍 Testing RAG optimization: '{message[:50]}...'")
        
        data = {
            "message": message,
            "session_id": TEST_SESSION_ID
        }
        
        result = await self.test_endpoint("/optimize_rag", "POST", data)
        self.results.append(result)
        
        if result["success"]:
            rag_result = result["result"]
            bloc_type = rag_result.get("bloc_type")
            processing_time = rag_result.get("processing_time")
            
            print("✅ RAG optimization passed")
            print(f"   - Bloc Type: {bloc_type}")
            print(f"   - Processing Time: {processing_time}s")
            print(f"   - Search Query: {rag_result.get('search_query')}")
            print(f"   - Priority: {rag_result.get('priority_level')}")
            
            if expected_bloc and bloc_type != expected_bloc:
                print(f"⚠️  Warning: Expected {expected_bloc}, got {bloc_type}")
                return False
            return True
        else:
            print("❌ RAG optimization failed")
            print(f"   - Error: {result['result']}")
            return False
    
    async def test_memory_management(self):
        """Teste la gestion de mémoire"""
        print("\n🔍 Testing memory management...")
        
        # Test status mémoire
        status_result = await self.test_endpoint("/memory_status")
        self.results.append(status_result)
        
        if status_result["success"]:
            print("✅ Memory status passed")
            memory_stats = status_result["result"].get("memory_stats", {})
            print(f"   - Total Sessions: {memory_stats.get('total_sessions', 0)}")
            print(f"   - Total Bloc History: {memory_stats.get('total_bloc_history', 0)}")
        
        # Test nettoyage mémoire
        clear_result = await self.test_endpoint(f"/clear_memory/{TEST_SESSION_ID}", "POST")
        self.results.append(clear_result)
        
        if clear_result["success"]:
            print("✅ Memory clear passed")
        else:
            print("❌ Memory clear failed")
        
        return status_result["success"] and clear_result["success"]
    
    async def run_comprehensive_tests(self):
        """Lance tous les tests complets"""
        print("🚀 Starting JAK Company RAG V4 Comprehensive Tests")
        print("=" * 60)
        
        # Tests de base
        health_ok = await self.test_health_check()
        root_ok = await self.test_root_endpoint()
        
        if not health_ok:
            print("❌ Health check failed - stopping tests")
            return False
        
        # Tests RAG avec différents types de messages
        test_cases = [
            # Paiements
            ("J'ai payé ma formation mais je n'ai pas reçu de confirmation", "BLOC A"),
            ("Mon paiement CPF est bloqué depuis 50 jours", "BLOC F1"),
            ("Problème avec OPCO, délai dépassé", "BLOC F3"),
            
            # Ambassadeurs
            ("C'est quoi un ambassadeur ?", "BLOC B.2"),
            ("Comment devenir ambassadeur ?", "BLOC D.1"),
            ("J'ai reçu un mail d'affiliation", "BLOC B.1"),
            
            # Formations
            ("Quelles formations proposez-vous ?", "BLOC K"),
            ("Je suis intéressé par vos programmes", "BLOC H"),
            ("Question sur le CPF", "BLOC C"),
            
            # Contact et escalade
            ("Je veux parler à un humain", "BLOC G"),
            ("C'est inadmissible, je suis énervé !", "BLOC AGRO"),
            ("Je veux escalader vers un administrateur", "BLOC 6.1"),
            
            # Général
            ("Bonjour, qui êtes-vous ?", "BLOC GENERAL"),
            ("Salut, comment ça va ?", "BLOC GENERAL"),
        ]
        
        rag_tests_passed = 0
        for message, expected_bloc in test_cases:
            if await self.test_rag_optimization(message, expected_bloc):
                rag_tests_passed += 1
        
        # Test gestion mémoire
        memory_ok = await self.test_memory_management()
        
        # Résumé des tests
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        
        print(f"✅ Successful Tests: {successful_tests}/{total_tests}")
        print(f"❌ Failed Tests: {total_tests - successful_tests}/{total_tests}")
        print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print(f"\n🔍 RAG Tests: {rag_tests_passed}/{len(test_cases)} passed")
        print(f"💾 Memory Tests: {'✅' if memory_ok else '❌'}")
        print(f"🏥 Health Check: {'✅' if health_ok else '❌'}")
        print(f"🏠 Root Endpoint: {'✅' if root_ok else '❌'}")
        
        # Détails des échecs
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for test in failed_tests:
                print(f"   - {test['method']} {test['endpoint']}: {test['result']}")
        
        return successful_tests == total_tests

async def main():
    """Fonction principale"""
    print("🧪 JAK Company RAG V4 Test Suite")
    print("Make sure the V4 API is running on http://localhost:8000")
    
    async with V4Tester() as tester:
        success = await tester.run_comprehensive_tests()
        
        if success:
            print("\n🎉 ALL TESTS PASSED! V4 is ready for production.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Please check the API and try again.")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)