import os
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import re
from dataclasses import dataclass
import traceback

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="JAK Company RAG Robust API", version="2.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vérification de la clé API OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key
    logger.info("OpenAI API Key configured")
else:
    logger.warning("OpenAI API Key not found - some features may not work")

# Store pour la mémoire des conversations (simplifié)
memory_store: Dict[str, List] = {}

@dataclass
class SimpleRAGDecision:
    """Structure simplifiée pour les décisions RAG"""
    search_query: str
    search_strategy: str
    context_needed: List[str]
    priority_level: str
    should_escalate: bool
    system_instructions: str

class SimpleRAGEngine:
    """Moteur de décision RAG ultra-simplifié et robuste"""
    
    @staticmethod
    def analyze_intent(message: str, session_id: str = "default") -> SimpleRAGDecision:
        """Analyse l'intention de manière robuste"""
        
        try:
            logger.info(f"🧠 ANALYSE INTENTION: '{message[:50]}...'")
            
            message_lower = message.lower().strip()
            
            # === DÉTECTION PAIEMENT (PRIORITÉ HAUTE) ===
            payment_keywords = [
                "pas été payé", "pas payé", "paiement", "cpf", "opco", 
                "virement", "argent", "retard", "délai", "attends",
                "finance", "financement", "payé pour", "rien reçu"
            ]
            
            if any(keyword in message_lower for keyword in payment_keywords):
                logger.info("🎯 CONTEXTE PAIEMENT DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query=f"paiement formation délai {message}",
                    search_strategy="hybrid",
                    context_needed=["paiement", "cpf", "opco", "financement"],
                    priority_level="high",
                    should_escalate=True,
                    system_instructions="""CONTEXTE DÉTECTÉ: PAIEMENT FORMATION

Tu dois OBLIGATOIREMENT:
1. Chercher les informations sur les délais de paiement dans Supabase
2. Identifier le type de financement (CPF, OPCO, direct)
3. Appliquer les règles de délais spécifiques
4. Si délai dépassé → proposer escalade
5. Reproduire EXACTEMENT les blocs trouvés avec tous les emojis

RÈGLES DÉLAIS:
- CPF: 45 jours minimum
- OPCO: 2 mois en moyenne  
- Direct: 7 jours maximum"""
                )
            
            # === DÉTECTION AMBASSADEUR ===
            ambassador_keywords = [
                "ambassadeur", "commission", "affiliation", "partenaire",
                "gagner argent", "contacts", "étapes", "devenir",
                "programme", "recommander"
            ]
            
            if any(keyword in message_lower for keyword in ambassador_keywords):
                logger.info("🎯 CONTEXTE AMBASSADEUR DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query=f"ambassadeur programme affiliation {message}",
                    search_strategy="semantic",
                    context_needed=["ambassadeur", "commission", "étapes", "affiliation"],
                    priority_level="high",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: AMBASSADEUR

Tu dois OBLIGATOIREMENT:
1. Chercher les informations sur le programme ambassadeur
2. Si c'est une explication → Bloc ambassadeur_explication
3. Si c'est pour devenir ambassadeur → Bloc ambassadeur_nouveau (4 étapes)
4. Si c'est une demande d'étapes → Donner les 4 étapes complètes
5. Reproduire EXACTEMENT les blocs avec tous les liens et emojis"""
                )
            
            # === DÉTECTION FORMATION ===
            formation_keywords = [
                "formation", "cours", "apprendre", "catalogue", "proposez",
                "disponible", "enseigner", "stage", "bureautique", 
                "informatique", "langues", "anglais", "excel"
            ]
            
            if any(keyword in message_lower for keyword in formation_keywords):
                logger.info("🎯 CONTEXTE FORMATION DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query=f"formation catalogue {message}",
                    search_strategy="semantic",
                    context_needed=["formation", "cpf", "catalogue", "professionnel"],
                    priority_level="medium",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: FORMATION

Tu dois OBLIGATOIREMENT:
1. Chercher les informations sur les formations disponibles
2. Identifier le profil utilisateur (pro, particulier, entreprise)
3. Proposer les formations adaptées
4. Mentionner que le CPF n'est plus disponible
5. Diriger vers les bons financements (OPCO, entreprise)"""
                )
            
            # === CONTEXTE GÉNÉRAL ===
            logger.info("🎯 CONTEXTE GÉNÉRAL")
            return SimpleRAGDecision(
                search_query=message,
                search_strategy="semantic",
                context_needed=["general"],
                priority_level="low",
                should_escalate=False,
                system_instructions="""CONTEXTE GÉNÉRAL

Tu dois:
1. Faire une recherche large dans Supabase
2. Analyser les résultats pour trouver le contexte approprié
3. Si aucun résultat pertinent → Proposer une escalade
4. Maintenir le ton chaleureux de JAK Company
5. Utiliser les emojis naturellement"""
            )
            
        except Exception as e:
            logger.error(f"Erreur dans analyze_intent: {str(e)}")
            # Retour de secours
            return SimpleRAGDecision(
                search_query=message,
                search_strategy="semantic",
                context_needed=["general"],
                priority_level="low",
                should_escalate=True,
                system_instructions="Cherche dans Supabase et reproduis les blocs trouvés exactement."
            )

class MemoryManager:
    """Gestionnaire de mémoire ultra-simplifié"""
    
    @staticmethod
    def add_message(session_id: str, message: str, role: str = "user"):
        """Ajoute un message à la mémoire"""
        try:
            if session_id not in memory_store:
                memory_store[session_id] = []
            
            memory_store[session_id].append({
                "role": role,
                "content": message,
                "timestamp": "now"
            })
            
            # Limiter à 10 messages max
            if len(memory_store[session_id]) > 10:
                memory_store[session_id] = memory_store[session_id][-10:]
                
        except Exception as e:
            logger.error(f"Erreur mémoire: {str(e)}")
    
    @staticmethod
    def get_context(session_id: str) -> List[Dict]:
        """Récupère le contexte de conversation"""
        try:
            return memory_store.get(session_id, [])
        except Exception as e:
            logger.error(f"Erreur récupération contexte: {str(e)}")
            return []

# ENDPOINTS API

@app.get("/")
async def root():
    """Endpoint racine pour vérifier que l'API fonctionne"""
    return {
        "status": "healthy",
        "message": "JAK Company RAG API is running",
        "version": "2.0 Robust"
    }

@app.get("/health")
async def health_check():
    """Endpoint de santé détaillé"""
    return {
        "status": "healthy",
        "version": "2.0 Robust",
        "active_sessions": len(memory_store),
        "features": [
            "Simple RAG Decision Engine",
            "Context-Aware Search",
            "Robust Error Handling",
            "Memory Management",
            "Ultra-Stable Processing"
        ]
    }

@app.post("/optimize_rag")
async def optimize_rag_decision(request: Request):
    """Point d'entrée principal - VERSION ULTRA ROBUSTE"""
    
    session_id = "default_session"
    user_message = "message par défaut"
    
    try:
        # === PARSING SÉCURISÉ ===
        try:
            body = await request.json()
            logger.info(f"Body reçu: {body}")
        except Exception as e:
            logger.error(f"Erreur parsing JSON: {str(e)}")
            return {
                "optimized_response": "Erreur de format JSON",
                "search_query": "error",
                "search_strategy": "fallback",
                "context_needed": ["error"],
                "priority_level": "high",
                "system_instructions": "Erreur de parsing",
                "escalade_required": True,
                "response_type": "json_error",
                "session_id": "error_session",
                "rag_confidence": 0
            }

        # === EXTRACTION SÉCURISÉE DES DONNÉES ===
        try:
            user_message = str(body.get("message", "")).strip()
            session_id = str(body.get("session_id", "default_session"))
            
            if not user_message:
                user_message = "message vide"
                
            logger.info(f"[{session_id}] Message: '{user_message[:50]}...'")
            
        except Exception as e:
            logger.error(f"Erreur extraction données: {str(e)}")
            user_message = "erreur extraction"
            session_id = "error_session"

        # === GESTION MÉMOIRE SÉCURISÉE ===
        try:
            MemoryManager.add_message(session_id, user_message, "user")
            conversation_context = MemoryManager.get_context(session_id)
        except Exception as e:
            logger.error(f"Erreur mémoire: {str(e)}")
            conversation_context = []

        # === ANALYSE D'INTENTION SÉCURISÉE ===
        try:
            decision = SimpleRAGEngine.analyze_intent(user_message, session_id)
            logger.info(f"[{session_id}] DÉCISION RAG: {decision.search_strategy} - {decision.priority_level}")
        except Exception as e:
            logger.error(f"Erreur analyse intention: {str(e)}")
            # Décision de fallback
            decision = SimpleRAGDecision(
                search_query=user_message,
                search_strategy="semantic",
                context_needed=["general"],
                priority_level="low",
                should_escalate=True,
                system_instructions="Erreur d'analyse - cherche dans Supabase"
            )

        # === CONSTRUCTION RÉPONSE SÉCURISÉE ===
        try:
            response_data = {
                "optimized_response": "Réponse optimisée générée",
                "search_query": decision.search_query,
                "search_strategy": decision.search_strategy,
                "context_needed": decision.context_needed,
                "priority_level": decision.priority_level,
                "system_instructions": decision.system_instructions,
                "escalade_required": decision.should_escalate,
                "response_type": "rag_optimized_robust",
                "session_id": session_id,
                "rag_confidence": 8,  # Confiance élevée
                "conversation_length": len(conversation_context)
            }
            
            # Ajouter la réponse à la mémoire
            MemoryManager.add_message(session_id, "RAG decision made", "assistant")
            
            logger.info(f"[{session_id}] RAG Response généré avec succès: {decision.search_strategy}")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Erreur construction réponse: {str(e)}")
            return {
                "optimized_response": "Erreur construction réponse",
                "search_query": user_message,
                "search_strategy": "fallback",
                "context_needed": ["error"],
                "priority_level": "high",
                "system_instructions": "Erreur système - escalade requise",
                "escalade_required": True,
                "response_type": "construction_error",
                "session_id": session_id,
                "rag_confidence": 0
            }

    except Exception as e:
        # === GESTION D'ERREUR GLOBALE ===
        logger.error(f"ERREUR GLOBALE: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        
        # Réponse de fallback ultra-robuste
        return {
            "optimized_response": "Erreur système détectée",
            "search_query": user_message,
            "search_strategy": "fallback",
            "context_needed": ["error"],
            "priority_level": "high", 
            "system_instructions": "Erreur critique - escalade immédiate requise",
            "escalade_required": True,
            "response_type": "global_error_fallback",
            "session_id": session_id,
            "rag_confidence": 0,
            "error_details": str(e)[:100]  # Limiter la taille de l'erreur
        }

@app.post("/clear_memory/{session_id}")
async def clear_memory(session_id: str):
    """Efface la mémoire d'une session"""
    try:
        if session_id in memory_store:
            del memory_store[session_id]
            return {"status": "success", "message": f"Memory cleared for {session_id}"}
        return {"status": "info", "message": f"No memory found for {session_id}"}
    except Exception as e:
        logger.error(f"Erreur clear memory: {str(e)}")
        return {"status": "error", "message": "Erreur lors de l'effacement mémoire"}

@app.get("/memory_status")
async def memory_status():
    """Statut de la mémoire"""
    try:
        return {
            "active_sessions": len(memory_store),
            "sessions": list(memory_store.keys()),
            "total_messages": sum(len(messages) for messages in memory_store.values())
        }
    except Exception as e:
        logger.error(f"Erreur memory status: {str(e)}")
        return {"error": "Erreur récupération statut mémoire"}

if __name__ == "__main__":
    import uvicorn
    try:
        logger.info("🚀 Démarrage JAK Company RAG API Robust")
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    except Exception as e:
        logger.error(f"Erreur démarrage serveur: {str(e)}")
        print(f"ERREUR CRITIQUE: {str(e)}")