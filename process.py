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

app = FastAPI(title="JAK Company RAG Robust API", version="2.3")

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
        """Analyse l'intention de manière robuste avec détection optimisée"""
        
        try:
            logger.info(f"🧠 ANALYSE INTENTION: '{message[:50]}...'")
            
            message_lower = message.lower().strip()
            
            # === NOUVEAUX BLOCS : DÉFINITIONS AMBASSADEUR/AFFILIATION ===
            definition_keywords = [
                "c'est quoi", "qu'est-ce que", "définition", "qu'est ce que",
                "c'est quoi un ambassadeur", "définir", "expliquer"
            ]
            
            if any(keyword in message_lower for keyword in definition_keywords):
                if "ambassadeur" in message_lower:
                    logger.info("🎯 DÉFINITION AMBASSADEUR DÉTECTÉE")
                    return SimpleRAGDecision(
                        search_query="définition ambassadeur partenaire argent commission",
                        search_strategy="semantic",
                        context_needed=["ambassadeur", "definition", "explication"],
                        priority_level="medium",
                        should_escalate=False,
                        system_instructions="""CONTEXTE DÉTECTÉ: DÉFINITION AMBASSADEUR
Tu dois OBLIGATOIREMENT:
1. Chercher le bloc AMBASSADEUR_DEFINITION dans Supabase
2. Reproduire EXACTEMENT le bloc avec tous les emojis
3. Ne pas improviser ou résumer
4. Proposer ensuite d'approfondir avec "devenir ambassadeur"
5. Maintenir le ton chaleureux JAK Company
6. JAMAIS de salutations répétées - contenu direct"""
                    )
                elif "affiliation" in message_lower and ("mail" in message_lower or "reçu" in message_lower):
                    logger.info("🎯 DÉFINITION AFFILIATION DÉTECTÉE")
                    return SimpleRAGDecision(
                        search_query="affiliation programme mail définition",
                        search_strategy="semantic", 
                        context_needed=["affiliation", "definition", "programme"],
                        priority_level="medium",
                        should_escalate=False,
                        system_instructions="""CONTEXTE DÉTECTÉ: DÉFINITION AFFILIATION
Tu dois OBLIGATOIREMENT:
1. Chercher le bloc AFFILIATION_DEFINITION dans Supabase
2. Reproduire EXACTEMENT le bloc avec tous les emojis
3. Poser la question de clarification (formation terminée vs ambassadeur)
4. Ne pas combiner avec d'autres blocs
5. Maintenir le ton WhatsApp chaleureux
6. JAMAIS de salutations répétées - contenu direct"""
                    )
            
            # === DÉTECTION BLOC LEGAL - PRIORITÉ CRITIQUE ===
            legal_keywords = [
                "décaisser le cpf", "récupérer mon argent", "récupérer l'argent", 
                "prendre l'argent", "argent du cpf", "sortir l'argent",
                "avoir mon argent", "toucher l'argent", "retirer l'argent",
                "frauder", "arnaquer", "contourner", "bidouiller",
                "récupérer cpf", "prendre cpf", "décaisser cpf"
            ]
            
            if any(keyword in message_lower for keyword in legal_keywords):
                logger.info("🚨 CONTEXTE LEGAL DÉTECTÉ - RECADRAGE OBLIGATOIRE")
                return SimpleRAGDecision(
                    search_query="legal fraude cpf récupérer argent règles",
                    search_strategy="semantic",
                    context_needed=["legal", "recadrage", "cpf", "fraude"],
                    priority_level="high",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: RECADRAGE LEGAL OBLIGATOIRE

Tu dois OBLIGATOIREMENT:
1. Chercher le BLOC LEGAL dans Supabase avec category="Recadrage" et context="BLOC LEGAL"
2. Reproduire EXACTEMENT le message de recadrage avec tous les emojis
3. Expliquer: pas d'inscription si but = récupération argent CPF
4. Orienter vers programme affiliation après formation sérieuse
5. Maintenir un ton ferme mais pédagogique
6. NE PAS négocier ou discuter - application stricte des règles
7. JAMAIS de salutations répétées - recadrage direct"""
                )
            
            # === DÉTECTION PAIEMENT (PRIORITÉ HAUTE) - AVEC BLOC F1 RENFORCÉ ===
            payment_keywords = [
                "pas été payé", "pas payé", "paiement", "cpf", "opco", 
                "virement", "argent", "retard", "délai", "attends",
                "finance", "financement", "payé pour", "rien reçu",
                "je vais être payé quand", "délai paiement"
            ]
            
            if any(keyword in message_lower for keyword in payment_keywords):
                logger.info("💰 CONTEXTE PAIEMENT DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query=f"paiement formation délai cpf opco {message}",
                    search_strategy="hybrid",
                    context_needed=["paiement", "cpf", "opco", "financement", "délai"],
                    priority_level="high",
                    should_escalate=True,
                    system_instructions="""CONTEXTE DÉTECTÉ: PAIEMENT FORMATION
RÈGLE ABSOLUE - FILTRAGE PAIEMENT OBLIGATOIRE:

ÉTAPE 1 - QUESTIONS DE FILTRAGE OBLIGATOIRES :
1. "Comment la formation a été financée ?" (CPF, OPCO, direct)
2. "Environ quand elle s'est terminée ?"

ÉTAPE 2 - LOGIQUE CONDITIONNELLE STRICTE :
- Si CPF ET > 45 jours → OBLIGATOIRE : Poser d'abord la question du Bloc F1
- Bloc F1 = "Question CPF Bloqué. Juste avant que je transmette ta demande 🙏
Est-ce que tu as déjà été informé par l'équipe que ton dossier CPF faisait partie des quelques cas bloqués par la Caisse des Dépôts ?
👉 Si oui, je te donne directement toutes les infos liées à ce blocage.
Sinon, je fais remonter ta demande à notre équipe pour vérification ✅"
- Si réponse OUI → Appliquer Bloc F2 (déblocage CPF)
- Si réponse NON → Escalade admin car délai anormal

ÉTAPE 3 - DÉLAIS DE RÉFÉRENCE :
- Direct: ≤7j normal, >7j ESCALADE
- CPF: ≤45j normal, >45j → QUESTION F1 OBLIGATOIRE puis F2 si bloqué, si non bloqué ESCALADE ADMIN.
- OPCO: ≤2 mois normal, >2 mois ESCALADE

INTERDICTION ABSOLUE : Passer directement au Bloc F2 sans poser la question F1.
OBLIGATION : Toujours demander "Est-ce que ton CPF est bloqué ?" avant F2.

Reproduire les blocs EXACTEMENT avec tous les emojis.
JAMAIS de salutations répétées - questions directes."""
                )
            
            # === DÉTECTION AMBASSADEUR ===
            ambassador_keywords = [
                "ambassadeur", "commission", "affiliation", "partenaire",
                "gagner argent", "contacts", "étapes", "devenir",
                "programme", "recommander", "comment je deviens",
                "comment devenir ambassadeur"
            ]
            
            if any(keyword in message_lower for keyword in ambassador_keywords):
                # Éviter les conflits avec les définitions
                if not any(def_kw in message_lower for def_kw in definition_keywords):
                    logger.info("🎯 CONTEXTE AMBASSADEUR DÉTECTÉ")
                    return SimpleRAGDecision(
                        search_query=f"ambassadeur programme affiliation étapes {message}",
                        search_strategy="semantic",
                        context_needed=["ambassadeur", "commission", "étapes", "affiliation", "programme"],
                        priority_level="high",
                        should_escalate=False,
                        system_instructions="""CONTEXTE DÉTECTÉ: AMBASSADEUR
Tu dois OBLIGATOIREMENT:
1. Identifier le type de demande ambassadeur:
   - Découverte programme → Bloc B
   - Devenir ambassadeur → Bloc D 
   - Envoi contacts → Bloc E
   - Suivi paiement → Appliquer FILTRAGE PAIEMENT
2. Chercher le bloc approprié dans Supabase
3. Reproduire EXACTEMENT avec tous les emojis et liens
4. Si demande "4 étapes" → donner les étapes complètes du Bloc D
5. Ne jamais combiner plusieurs blocs
6. Maintenir le ton WhatsApp avec emojis naturels
7. JAMAIS de salutations répétées - contenu direct"""
                    )
            
            # === DÉTECTION ENVOI CONTACTS ===
            contact_keywords = [
                "comment envoyer", "envoie des contacts", "transmettre contacts",
                "formulaire", "liste contacts", "comment je vous envoie"
            ]
            
            if any(keyword in message_lower for keyword in contact_keywords):
                logger.info("📋 CONTEXTE ENVOI CONTACTS DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query="envoyer contacts formulaire nom prénom téléphone",
                    search_strategy="semantic",
                    context_needed=["contacts", "formulaire", "transmission"],
                    priority_level="medium",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: ENVOI CONTACTS
Tu dois OBLIGATOIREMENT:
1. Chercher le Bloc E dans Supabase
2. Reproduire EXACTEMENT avec le lien formulaire
3. Mentionner: nom, prénom, contact (tel/email)
4. Bonus SIRET pour les pros
5. Maintenir le ton encourageant et simple
6. JAMAIS de salutations répétées - contenu direct"""
                )
            
            # === DÉTECTION FORMATION ===
            formation_keywords = [
                "formation", "cours", "apprendre", "catalogue", "proposez",
                "disponible", "enseigner", "stage", "bureautique", 
                "informatique", "langues", "anglais", "excel"
            ]
            
            if any(keyword in message_lower for keyword in formation_keywords):
                logger.info("📚 CONTEXTE FORMATION DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query=f"formation catalogue cpf opco {message}",
                    search_strategy="semantic",
                    context_needed=["formation", "cpf", "catalogue", "professionnel"],
                    priority_level="medium",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: FORMATION
Tu dois OBLIGATOIREMENT:
1. Si question CPF → Bloc C (plus de CPF disponible)
2. Chercher les informations formations dans Supabase
3. Identifier le profil (pro, particulier, entreprise)
4. Orienter vers les bons financements (OPCO, entreprise)
5. Proposer contact humain si besoin (Bloc G)
6. JAMAIS de salutations répétées - contenu direct"""
                )
            
            # === DÉTECTION PARLER À UN HUMAIN ===
            human_keywords = [
                "parler humain", "contact humain", "équipe", "quelqu'un",
                "agent", "conseiller", "je veux parler"
            ]
            
            if any(keyword in message_lower for keyword in human_keywords):
                logger.info("👥 CONTEXTE CONTACT HUMAIN DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query="parler humain contact équipe",
                    search_strategy="semantic",
                    context_needed=["humain", "contact", "escalade"],
                    priority_level="medium",
                    should_escalate=True,
                    system_instructions="""CONTEXTE DÉTECTÉ: CONTACT HUMAIN
Tu dois OBLIGATOIREMENT:
1. Chercher le Bloc G dans Supabase
2. Reproduire EXACTEMENT avec les horaires
3. Proposer d'abord de répondre directement
4. Mentionner les horaires: 9h-17h, lun-ven
5. Escalader si vraiment nécessaire
6. JAMAIS de salutations répétées - contenu direct"""
                )
            
            # === DÉTECTION CPF ===
            cpf_keywords = [
                "cpf", "compte personnel", "vous faites encore le cpf",
                "formations cpf", "financement cpf"
            ]
            
            if any(keyword in message_lower for keyword in cpf_keywords):
                logger.info("🎓 CONTEXTE CPF DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query="cpf formation financement opco",
                    search_strategy="semantic",
                    context_needed=["cpf", "financement", "alternatives"],
                    priority_level="medium",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: CPF
Tu dois OBLIGATOIREMENT:
1. Chercher le Bloc C dans Supabase
2. Reproduire EXACTEMENT: plus de CPF pour le moment
3. Proposer alternatives pour pros (OPCO, entreprise)
4. Donner les liens réseaux sociaux pour être tenu au courant
5. Proposer d'expliquer pour les pros
6. JAMAIS de salutations répétées - contenu direct"""
                )
            
            # === DÉTECTION ARGUMENTAIRE/PROSPECT ===
            prospect_keywords = [
                "que dire à un prospect", "argumentaire", "comment présenter",
                "offres", "comprendre", "expliquer à quelqu'un"
            ]
            
            if any(keyword in message_lower for keyword in prospect_keywords):
                logger.info("💼 CONTEXTE PROSPECT/ARGUMENTAIRE DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query="argumentaire prospect entreprise formation",
                    search_strategy="semantic",
                    context_needed=["prospect", "argumentaire", "présentation"],
                    priority_level="medium",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: ARGUMENTAIRE PROSPECT
Tu dois OBLIGATOIREMENT:
1. Identifier le type d'argumentaire:
   - Que dire à un prospect → Bloc H
   - Argumentaire entreprise → Bloc I1 
   - Argumentaire ambassadeur → Bloc I2
2. Reproduire le bloc approprié EXACTEMENT
3. Maintenir le ton professionnel mais accessible
4. JAMAIS de salutations répétées - contenu direct"""
                )
            
            # === DÉTECTION COMBIEN DE TEMPS ===
            time_keywords = [
                "combien de temps", "délai", "ça prend combien", "durée",
                "quand", "temps nécessaire"
            ]
            
            if any(keyword in message_lower for keyword in time_keywords):
                logger.info("⏰ CONTEXTE DÉLAI/TEMPS DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query="délai temps paiement formation mois",
                    search_strategy="semantic",
                    context_needed=["délai", "temps", "durée"],
                    priority_level="medium",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: DÉLAI/TEMPS
Tu dois OBLIGATOIREMENT:
1. Chercher le Bloc J dans Supabase
2. Reproduire EXACTEMENT: 3-6 mois en moyenne
3. Expliquer les facteurs (financement, réactivité, traitement)
4. Donner les exemples de délais par type
5. Conseiller d'envoyer plusieurs contacts au début
6. JAMAIS de salutations répétées - contenu direct"""
                )
            
            # === DÉTECTION AGRESSIVITÉ ===
            aggressive_keywords = [
                "merde", "putain", "con", "salaud", "nul", "arnaque",
                "escroquerie", "voleur", "marre", "insulte"
            ]
            
            if any(keyword in message_lower for keyword in aggressive_keywords):
                logger.info("😤 CONTEXTE AGRO DÉTECTÉ")
                return SimpleRAGDecision(
                    search_query="gestion agressivité calme",
                    search_strategy="semantic",
                    context_needed=["agro", "apaisement"],
                    priority_level="high",
                    should_escalate=False,
                    system_instructions="""CONTEXTE DÉTECTÉ: GESTION AGRO
Tu dois OBLIGATOIREMENT:
1. Appliquer le Bloc AGRO immédiatement
2. Reproduire EXACTEMENT avec le poème/chanson d'amour
3. Maintenir un ton humoristique mais ferme
4. Ne pas alimenter le conflit
5. Rediriger vers une conversation constructive
6. JAMAIS de salutations répétées - gestion directe"""
                )
            
            # === CONTEXTE GÉNÉRAL ===
            logger.info("🔄 CONTEXTE GÉNÉRAL")
            return SimpleRAGDecision(
                search_query=message,
                search_strategy="semantic",
                context_needed=["general"],
                priority_level="low",
                should_escalate=False,
                system_instructions="""CONTEXTE GÉNÉRAL
Tu dois:
1. Faire une recherche large dans Supabase Vector Store 2
2. Analyser les résultats pour identifier le bon bloc
3. Identifier le profil utilisateur (ambassadeur, apprenant, prospect)
4. Si aucun bloc pertinent → Appliquer les règles:
   - Tentative récupération argent CPF → BLOC LEGAL immédiat
   - Problème paiement → FILTRAGE PAIEMENT obligatoire avec séquence F→F1→F2
   - Demande spécifique → Bloc approprié
   - Aucune correspondance → Escalade avec Bloc G
5. Maintenir TOUJOURS le ton WhatsApp chaleureux avec emojis
6. Reproduire les blocs EXACTEMENT sans modification
7. JAMAIS de salutations répétées - contenu direct

RÈGLES ABSOLUES:
- Jamais d'improvisation
- Un seul bloc par réponse
- Respect total du contenu avec emojis
- Filtrage paiement prioritaire avec séquence F1 obligatoire
- Bloc Legal priorité absolue pour récupération argent CPF
- Identification profil avant réponse"""
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
                system_instructions="Erreur système - cherche dans Supabase et reproduis les blocs trouvés exactement. Si problème paiement détecté, applique le filtrage obligatoire avec séquence F1. Si récupération argent CPF détectée, applique le BLOC LEGAL immédiatement."
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
        "version": "2.3 Optimized with reinforced F1 block sequence"
    }

@app.get("/health")
async def health_check():
    """Endpoint de santé détaillé"""
    return {
        "status": "healthy",
        "version": "2.3 Optimized",
        "active_sessions": len(memory_store),
        "features": [
            "Enhanced RAG Decision Engine",
            "Reinforced F1 Block Sequence (CPF > 45 days)",
            "Legal Block Detection (CPF Recovery)",
            "New Ambassadeur/Affiliation Definition Blocks",
            "Supabase Metadata Filtering",
            "Context-Aware Search",
            "Anti-Repetition System",
            "Robust Error Handling",
            "Memory Management", 
            "Ultra-Stable Processing", 
            "Payment Filtering Priority"
        ]
    }

@app.post("/optimize_rag")
async def optimize_rag_decision(request: Request):
    """Point d'entrée principal - VERSION ULTRA ROBUSTE avec séquence F1 renforcée"""
    
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
                system_instructions="Erreur d'analyse - cherche dans Supabase et applique les règles JAK Company. Si récupération argent CPF détectée, applique BLOC LEGAL. Si paiement CPF >45j, applique séquence F→F1→F2."
            )
        
        # === CONSTRUCTION RÉPONSE SÉCURISÉE ===
        try:
            response_data = {
                "optimized_response": "Réponse optimisée générée avec séquence F1 renforcée",
                "search_query": decision.search_query,
                "search_strategy": decision.search_strategy,
                "context_needed": decision.context_needed,
                "priority_level": decision.priority_level,
                "system_instructions": decision.system_instructions,
                "escalade_required": decision.should_escalate,
                "response_type": "rag_optimized_robust_v2.3",
                "session_id": session_id,
                "rag_confidence": 9, # Confiance très élevée avec séquence F1 renforcée
                "conversation_length": len(conversation_context),
                "new_blocks_supported": ["AMBASSADEUR_DEFINITION", "AFFILIATION_DEFINITION", "BLOC_LEGAL"],
                "metadata_filtering_enabled": True,
                "anti_repetition_enabled": True,
                "f1_sequence_reinforced": True
            }
            
            # Ajouter la réponse à la mémoire
            MemoryManager.add_message(session_id, "RAG decision made with reinforced F1 sequence", "assistant")
            
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
            "error_details": str(e)[:100] # Limiter la taille de l'erreur
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
        logger.info("🚀 Démarrage JAK Company RAG API Robust v2.3 avec séquence F1 renforcée")
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    except Exception as e:
        logger.error(f"Erreur démarrage serveur: {str(e)}")
        print(f"ERREUR CRITIQUE: {str(e)}")