#!/usr/bin/env python3
"""
Performance Testing Suite for JAK Company RAG API v2.4
Tests the optimized LangChain WhatsApp AI Agent performance
"""

import json
import time
import random
from locust import HttpUser, task, between
from locust.exception import RescheduleTask

class RAGAPIUser(HttpUser):
    """Load testing user for the optimized RAG API"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize test data and session"""
        self.session_id = f"test_session_{random.randint(1000, 9999)}"
        self.test_messages = [
            # Legal detection tests
            "Je veux récupérer mon argent du CPF",
            "Comment décaisser le CPF ?",
            
            # Payment detection tests  
            "Je n'ai pas été payé pour ma formation",
            "Quel est le délai de paiement CPF ?",
            
            # Ambassador tests
            "Comment devenir ambassadeur ?",
            "Quelles sont les étapes pour être partenaire ?",
            
            # Formation tests
            "Quelles formations proposez-vous ?",
            "Avez-vous des formations en bureautique ?",
            
            # Definition tests
            "C'est quoi un ambassadeur ?",
            "Qu'est-ce que l'affiliation ?",
            
            # Contact tests
            "Comment envoyer mes contacts ?",
            "Je veux parler à un humain",
            
            # CPF tests
            "Vous faites encore le CPF ?",
            "Formations CPF disponibles ?",
            
            # Time tests
            "Combien de temps ça prend ?",
            "Quel est le délai moyen ?",
            
            # General tests
            "Bonjour, comment ça marche ?",
            "Pouvez-vous m'aider ?"
        ]
    
    @task(5)
    def test_optimize_rag_endpoint(self):
        """Test the main RAG optimization endpoint with various messages"""
        message = random.choice(self.test_messages)
        
        payload = {
            "message": message,
            "session_id": self.session_id
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/optimize_rag",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Validate response structure
                    required_fields = [
                        "optimized_response", "search_query", "search_strategy",
                        "context_needed", "priority_level", "system_instructions",
                        "response_type", "session_id", "rag_confidence"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        response.failure(f"Missing fields: {missing_fields}")
                        return
                    
                    # Check performance metrics
                    if "performance_metrics" in data:
                        processing_time = data["performance_metrics"].get("processing_time_ms", 0)
                        if processing_time > 100:  # Alert if processing takes > 100ms
                            response.failure(f"Slow processing: {processing_time}ms")
                        
                    # Check optimization features
                    if "optimization_features" in data:
                        features = data["optimization_features"]
                        if not features.get("keyword_sets_optimized", False):
                            response.failure("Keyword optimization not active")
                        if not features.get("ttl_caching_enabled", False):
                            response.failure("TTL caching not active")
                    
                    # Log performance for analysis
                    self.environment.events.request_success.fire(
                        request_type="RAG_PROCESSING",
                        name=f"Intent: {data.get('search_strategy', 'unknown')}",
                        response_time=response_time,
                        response_length=len(response.content)
                    )
                    
                    response.success()
                    
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                except Exception as e:
                    response.failure(f"Response validation error: {str(e)}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") != "healthy":
                        response.failure("Service not healthy")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def test_performance_metrics_endpoint(self):
        """Test the performance metrics endpoint"""
        with self.client.get("/performance_metrics", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("optimization_status") != "Active":
                        response.failure("Optimizations not active")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def test_memory_status_endpoint(self):
        """Test the memory status endpoint"""
        with self.client.get("/memory_status", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "memory_optimization" not in data:
                        response.failure("Memory optimization data missing")
                    else:
                        # Check memory utilization
                        utilization = data["memory_optimization"].get("utilization_percentage", 0)
                        if utilization > 90:
                            response.failure(f"High memory utilization: {utilization}%")
                        else:
                            response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def test_clear_memory_endpoint(self):
        """Test the memory clearing endpoint"""
        test_session = f"test_clear_{random.randint(1000, 9999)}"
        
        with self.client.post(
            f"/clear_memory/{test_session}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") not in ["success", "info"]:
                        response.failure("Memory clear failed")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

class IntensiveRAGUser(HttpUser):
    """High-intensity user for stress testing"""
    
    wait_time = between(0.1, 0.5)  # Very fast requests
    
    def on_start(self):
        self.session_id = f"intensive_session_{random.randint(10000, 99999)}"
        self.message_count = 0
    
    @task
    def rapid_fire_requests(self):
        """Send rapid requests to test caching and performance"""
        messages = [
            "Test message for caching",
            "Another test for performance",
            "Rapid fire test message",
            "Cache performance test"
        ]
        
        message = random.choice(messages)
        self.message_count += 1
        
        payload = {
            "message": f"{message} #{self.message_count}",
            "session_id": self.session_id
        }
        
        with self.client.post(
            "/optimize_rag",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    processing_time = data.get("performance_metrics", {}).get("processing_time_ms", 0)
                    
                    # Expect very fast responses due to caching
                    if processing_time > 50:
                        response.failure(f"Slow response in intensive test: {processing_time}ms")
                    else:
                        response.success()
                        
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

# Performance test scenarios
class CachePerformanceUser(HttpUser):
    """Test caching performance specifically"""
    
    wait_time = between(0.5, 1.0)
    
    def on_start(self):
        self.session_id = f"cache_test_{random.randint(1000, 9999)}"
        # Use same messages repeatedly to test cache hits
        self.repeated_messages = [
            "C'est quoi un ambassadeur ?",
            "Comment devenir ambassadeur ?",
            "Je n'ai pas été payé",
            "Formations disponibles ?"
        ]
    
    @task
    def test_cache_performance(self):
        """Send repeated messages to test cache hit performance"""
        message = random.choice(self.repeated_messages)
        
        payload = {
            "message": message,
            "session_id": self.session_id
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/optimize_rag",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    processing_time = data.get("performance_metrics", {}).get("processing_time_ms", 0)
                    
                    # Cache hits should be very fast
                    if processing_time < 10:
                        # Likely a cache hit
                        self.environment.events.request_success.fire(
                            request_type="CACHE_HIT",
                            name="Cached Response",
                            response_time=response_time,
                            response_length=len(response.content)
                        )
                    
                    response.success()
                    
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

if __name__ == "__main__":
    print("Performance Testing Suite for JAK Company RAG API v2.4")
    print("=" * 60)
    print()
    print("To run the tests:")
    print("1. Start the API server: python process.py")
    print("2. Run load tests: locust -f performance_tests.py --host=http://localhost:8000")
    print("3. Open web UI: http://localhost:8089")
    print()
    print("Test scenarios:")
    print("- RAGAPIUser: General load testing with various message types")
    print("- IntensiveRAGUser: High-intensity stress testing")
    print("- CachePerformanceUser: Cache performance validation")
    print()
    print("Performance targets:")
    print("- Response time: < 100ms for regular requests")
    print("- Cache hits: < 10ms processing time")
    print("- Memory utilization: < 90%")
    print("- Error rate: < 1%")