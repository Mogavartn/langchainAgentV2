import os
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain.memory import ConversationBufferMemory
import json
import re
from dataclasses import dataclass

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JAK Company RAG Optimized API", version="1.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vérification de la clé API OpenAI
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

# Store pour la mémoire des conversations
memory_store: Dict[str, ConversationBufferMemory] = {}

@dataclass
class RAGDecision:
    """Structure pour les décisions RAG"""
    search_query: str
    search_strategy: str  # "semantic", "exact", "hybrid"
    context_needed: List[str]  # ["paiement", "formation", "ambassadeur"]
    priority_level: str  # "high", "medium", "low"
    should_escalate: bool
    system_instructions: str

class RAGDecisionEngine:
    """Moteur de décision intelligent pour le RAG"""
    
    @staticmethod
    def analyze_user_intent(message: str, conversation_history: List = None) -> RAGDecision:
        """Analyse l'intention utilisateur et détermine la stratégie RAG optimale"""
        
        message_lower = message.lower()
        conversation_history = conversation_history or []
        
        logger.info(f"🧠 ANALYSE INTENTION: '{message[:50]}...'")
        
        # === DÉTECTION DES CONTEXTES PRIORITAIRES ===
        
        # 1. CONTEXTE PAIEMENT FORMATION (PRIORITÉ HAUTE)
        if RAGDecisionEngine._detect_payment_context(message_lower):
            return RAGDecision(
                search_query=f"paiement formation délai {message}",
                search_strategy="hybrid",
                context_needed=["paiement", "cpf", "opco", "financement"],
                priority_level="high",
                should_escalate=True,
                system_instructions="""
                CONTEXTE DÉTECTÉ: PAIEMENT FORMATION
                
                Tu dois OBLIGATOIREMENT:
                1. Chercher les informations sur les délais de paiement dans Supabase
                2. Identifier le type de financement (CPF, OPCO, direct)
                3. Appliquer les règles de délais spécifiques
                4. Si délai dépassé → proposer escalade
                5. Reproduire EXACTEMENT les blocs trouvés avec tous les emojis
                
                RÈGLES DÉLAIS:
                - CPF: 45 jours minimum
                - OPCO: 2 mois en moyenne
                - Direct: 7 jours maximum
                """
            )
        
        # 2. CONTEXTE AMBASSADEUR (PRIORITÉ HAUTE)
        elif RAGDecisionEngine._detect_ambassador_context(message_lower, conversation_history):
            return RAGDecision(
                search_query=f"ambassadeur programme affiliation {message}",
                search_strategy="semantic",
                context_needed=["ambassadeur", "commission", "étapes", "affiliation"],
                priority_level="high",
                should_escalate=False,
                system_instructions="""
                CONTEXTE DÉTECTÉ: AMBASSADEUR
                
                Tu dois OBLIGATOIREMENT:
                1. Chercher les informations sur le programme ambassadeur
                2. Si c'est une explication → Bloc ambassadeur_explication
                3. Si c'est pour devenir ambassadeur → Bloc ambassadeur_nouveau (4 étapes)
                4. Si c'est une demande d'étapes → Donner les 4 étapes complètes
                5. Reproduire EXACTEMENT les blocs avec tous les liens et emojis
                
                PRIORITÉ: Détecter si l'utilisateur veut:
                - Une explication du rôle
                - Devenir ambassadeur (donner les 4 étapes)
                - Envoyer des contacts
                """
            )
        
        # 3. CONTEXTE FORMATION (PRIORITÉ MOYENNE)
        elif RAGDecisionEngine._detect_formation_context(message_lower):
            return RAGDecision(
                search_query=f"formation catalogue {message}",
                search_strategy="semantic",
                context_needed=["formation", "cpf", "catalogue", "professionnel"],
                priority_level="medium",
                should_escalate=False,
                system_instructions="""
                CONTEXTE DÉTECTÉ: FORMATION
                
                Tu dois OBLIGATOIREMENT:
                1. Chercher les informations sur les formations disponibles
                2. Identifier le profil utilisateur (pro, particulier, entreprise)
                3. Proposer les formations adaptées
                4. Mentionner que le CPF n'est plus disponible
                5. Diriger vers les bons financements (OPCO, entreprise)
                
                DISTINCTIONS:
                - Formation spécifique → Bloc formation_specifique
                - Question générale → Bloc formations_question_generale  
                - Catalogue complet → Bloc formations_disponibles
                """
            )
        
        # 4. CONTEXTE GÉNÉRAL (PRIORITÉ BASSE)
        else:
            return RAGDecision(
                search_query=message,
                search_strategy="semantic",
                context_needed=["general"],
                priority_level="low",
                should_escalate=False,
                system_instructions="""
                CONTEXTE GÉNÉRAL
                
                Tu dois:
                1. Faire une recherche large dans Supabase
                2. Analyser les résultats pour trouver le contexte approprié
                3. Si aucun résultat pertinent → Proposer une escalade
                4. Maintenir le ton chaleureux de JAK Company
                5. Utiliser les emojis naturellement
                """
            )
    
    @staticmethod
    def _detect_payment_context(message: str) -> bool:
        """Détecte le contexte paiement formation"""
        payment_indicators = [
            "pas été payé", "pas ete paye", "pas payé", "pas paye",
            "rien reçu", "rien recu", "toujours rien",
            "virement", "attends", "attendre", "paiement",
            "argent", "retard", "délai", "delai",
            "promesse", "veux être payé", "veux etre paye",
            "payé pour ma formation", "paye pour ma formation",
            "cpf", "opco", "financement", "finance"
        ]
        
        return any(indicator in message for indicator in payment_indicators)
    
    @staticmethod
    def _detect_ambassador_context(message: str, history: List) -> bool:
        """Détecte le contexte ambassadeur avec analyse historique"""
        ambassador_indicators = [
            "ambassadeur", "commission", "affiliation", "partenaire",
            "gagner argent", "gagner de l'argent", "contacts",
            "comment ça marche", "comment ca marche", "étapes", "etapes",
            "devenir ambassadeur", "programme", "recommander"
        ]
        
        # Vérifier le message actuel
        current_match = any(indicator in message for indicator in ambassador_indicators)
        
        # Vérifier si l'historique contient du contexte ambassadeur
        history_context = False
        if history:
            for msg in history[-3:]:  # 3 derniers messages
                msg_content = str(msg.get('content', '')).lower()
                if any(indicator in msg_content for indicator in ambassador_indicators):
                    history_context = True
                    break
        
        return current_match or history_context
    
    @staticmethod
    def _detect_formation_context(message: str) -> bool:
        """Détecte le contexte formation"""
        formation_indicators = [
            "formation", "formations", "cours", "apprendre",
            "catalogue", "proposez", "disponible", "enseigner",
            "stage", "e-learning", "distanciel", "présentiel",
            "bureautique", "informatique", "langues", "anglais",
            "excel", "word", "powerpoint", "marketing", "vente"
        ]
        
        return any(indicator in message for indicator in formation_indicators)

class MemoryManager:
    """Gestionnaire de mémoire optimisé"""
    
    @staticmethod
    def trim_memory(memory: ConversationBufferMemory, max_messages: int = 10):
        """Limite la mémoire pour le RAG (plus restrictif pour performance)"""
        messages = memory.chat_memory.messages
        
        if len(messages) > max_messages:
            memory.chat_memory.messages = messages[-max_messages:]
            logger.info(f"Memory trimmed to {max_messages} messages for RAG optimization")
    
    @staticmethod
    def get_conversation_context(memory: ConversationBufferMemory) -> List[Dict]:
        """Extrait le contexte conversationnel pour le RAG"""
        messages = memory.chat_memory.messages
        context = []
        
        for msg in messages[-5:]:  # 5 derniers messages pour le contexte RAG
            context.append({
                'type': getattr(msg, 'type', 'unknown'),
                'content': str(msg.content)[:200],  # Limiter pour performance
                'timestamp': getattr(msg, 'timestamp', None)
            })
        
        return context

class ResponseOptimizer:
    """Optimise les réponses pour le RAG"""
    
    @staticmethod
    def should_use_rag(decision: RAGDecision, rag_results: List = None) -> bool:
        """Détermine si on doit utiliser les résultats RAG ou escalader"""
        
        # Si résultats RAG pertinents et contexte clair
        if rag_results and len(rag_results) > 0:
            # Vérifier la pertinence des résultats
            relevant_results = [r for r in rag_results if r.get('similarity', 0) > 0.7]
            if relevant_results:
                return True
        
        # Si contexte critique (paiement) sans résultats RAG satisfaisants
        if decision.priority_level == "high" and decision.should_escalate:
            return False  # Escalader plutôt que donner une réponse générique
        
        return len(rag_results) > 0 if rag_results else False
    
    @staticmethod
    def format_rag_response(rag_results: List, decision: RAGDecision, user_message: str) -> str:
        """Formate la réponse basée sur les résultats RAG"""
        
        if not rag_results:
            return ResponseOptimizer._get_fallback_response(decision)
        
        # Prendre le meilleur résultat
        best_result = rag_results[0]
        content = best_result.get('content', '')
        
        # Si c'est un bloc JAK Company complet, le retourner tel quel
        if '✅' in content and '👉' in content and ('https://' in content or 'ESCALADE' in content):
            logger.info("📋 BLOC JAK COMPANY DÉTECTÉ - Reproduction exacte")
            return content
        
        # Sinon, contextualiser la réponse
        if decision.priority_level == "high":
            return f"D'après nos informations :\n\n{content}\n\nSi tu as besoin de plus de précisions, notre équipe peut t'aider ! 😊"
        else:
            return content
    
    @staticmethod
    def _get_fallback_response(decision: RAGDecision) -> str:
        """Réponse de fallback selon le contexte"""
        
        if decision.should_escalate:
            return """Je vais faire suivre ta demande à notre équipe spécialisée qui te recontactera rapidement ! 😊

🕐 Notre équipe est disponible du lundi au vendredi, de 9h à 17h.
On te tiendra informé dès que possible ✅"""
        
        return """Salut ! 👋

Je vais chercher les informations les plus pertinentes pour ta question.
Si je ne trouve pas exactement ce qu'il te faut, notre équipe peut t'aider ! 😊

Peux-tu me préciser un peu plus ce que tu recherches ?"""

# ENDPOINTS API

@app.post("/optimize_rag")
async def optimize_rag_decision(request: Request):
    """Point d'entrée principal pour l'optimisation RAG"""
    try:
        # Parsing du JSON
        try:
            body = await request.json()
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        # Extraction des données
        user_message = body.get("message", body.get("chatInput", ""))
        wa_id = body.get("wa_id", body.get("session_id", "default_session"))
        rag_results = body.get("rag_results", [])
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        logger.info(f"[{wa_id}] RAG OPTIMIZATION: '{user_message[:50]}...'")

        # Gestion de la mémoire
        if wa_id not in memory_store:
            memory_store[wa_id] = ConversationBufferMemory(
                memory_key="history",
                return_messages=True
            )

        memory = memory_store[wa_id]
        MemoryManager.trim_memory(memory, max_messages=10)
        
        # Obtenir le contexte conversationnel
        conversation_context = MemoryManager.get_conversation_context(memory)
        
        # Analyse de l'intention avec le moteur de décision
        decision = RAGDecisionEngine.analyze_user_intent(user_message, conversation_context)
        
        logger.info(f"[{wa_id}] DÉCISION RAG: {decision.search_strategy} - {decision.priority_level}")
        
        # Ajouter le message utilisateur à la mémoire
        memory.chat_memory.add_user_message(user_message)
        
        # Déterminer si utiliser RAG ou escalader
        use_rag = ResponseOptimizer.should_use_rag(decision, rag_results)
        
        if use_rag and rag_results:
            # Utiliser les résultats RAG
            final_response = ResponseOptimizer.format_rag_response(rag_results, decision, user_message)
            response_type = "rag_optimized"
            escalade_required = decision.should_escalate
        else:
            # Utiliser une réponse optimisée
            final_response = ResponseOptimizer._get_fallback_response(decision)
            response_type = "rag_fallback"
            escalade_required = True

        # Ajouter la réponse à la mémoire
        memory.chat_memory.add_ai_message(final_response)
        
        # Optimiser la mémoire après ajout
        MemoryManager.trim_memory(memory, max_messages=10)

        # Construire la réponse
        response_data = {
            "optimized_response": final_response,
            "search_query": decision.search_query,
            "search_strategy": decision.search_strategy,
            "context_needed": decision.context_needed,
            "priority_level": decision.priority_level,
            "system_instructions": decision.system_instructions,
            "escalade_required": escalade_required,
            "response_type": response_type,
            "session_id": wa_id,
            "rag_confidence": len(rag_results) if rag_results else 0
        }

        logger.info(f"[{wa_id}] RAG Response: {response_type}, escalade={escalade_required}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG Optimization error: {str(e)}")
        
        # Retourner une réponse de fallback
        return {
            "optimized_response": """Salut ! 😊

Je rencontre un petit problème technique. Notre équipe va regarder ça et te recontacter rapidement !

🕐 Horaires : Lundi-Vendredi, 9h-17h""",
            "search_query": "technical_error",
            "search_strategy": "fallback",
            "context_needed": ["technical"],
            "priority_level": "high",
            "escalade_required": True,
            "response_type": "error_fallback",
            "session_id": "error_session",
            "rag_confidence": 0
        }

@app.get("/health")
async def health_check():
    """Endpoint de santé"""
    return {
        "status": "healthy",
        "version": "1.0 RAG Optimized",
        "features": [
            "RAG Decision Engine",
            "Context-Aware Search",
            "Optimized Memory Management",
            "Intelligent Response Formatting",
            "Multi-Strategy Search Support"
        ]
    }

@app.post("/clear_memory/{wa_id}")
async def clear_memory(wa_id: str):
    """Efface la mémoire d'une session"""
    try:
        if wa_id in memory_store:
            del memory_store[wa_id]
            return {"status": "success", "message": f"Memory cleared for {wa_id}"}
        return {"status": "info", "message": f"No memory found for {wa_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)