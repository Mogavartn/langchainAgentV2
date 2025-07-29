import re
from typing import Dict, Any, Optional

class EscalationMiddleware:
    """
    Middleware pour ajouter automatiquement le bloc de transition d'escalade
    quand l'utilisateur demande une formation spécifique.
    """
    
    def __init__(self):
        self.transition_block = """
[BLOC TRANSITION]
Parfait ! Notre équipe commerciale va pouvoir t'accompagner pour cette formation. 

Veux-tu être mis en relation avec eux pour explorer les possibilités ? 😊
"""
        
        # Mots-clés qui indiquent une demande de formation spécifique
        self.formation_keywords = [
            "formation", "anglais", "pro", "professionnel", "bureautique", 
            "informatique", "langues", "web", "3d", "vente", "marketing",
            "développement personnel", "écologie numérique", "bilan compétences"
        ]
        
        # Patterns pour détecter les réponses de liste (à éviter)
        self.list_patterns = [
            r"Nos spécialités",
            r"\+100 formations",
            r"• 💻",
            r"📚 Nos spécialités"
        ]
    
    def should_escalate(self, user_message: str, bot_response: str) -> bool:
        """
        Détermine si une escalade est nécessaire basée sur le message utilisateur
        et la réponse du bot.
        """
        # Vérifier si l'utilisateur demande une formation spécifique
        user_asks_formation = any(
            keyword in user_message.lower() 
            for keyword in self.formation_keywords
        )
        
        # Vérifier que la réponse n'est pas une liste de formations
        is_list_response = any(
            re.search(pattern, bot_response, re.IGNORECASE)
            for pattern in self.list_patterns
        )
        
        # Vérifier que la réponse n'est pas déjà une escalade
        already_escalating = any(
            phrase in bot_response.lower()
            for phrase in ["équipe commerciale", "mettre en relation", "bloc transition"]
        )
        
        return user_asks_formation and not is_list_response and not already_escalating
    
    def process_response(self, user_message: str, bot_response: str) -> str:
        """
        Traite la réponse du bot et ajoute le bloc de transition si nécessaire.
        """
        if self.should_escalate(user_message, bot_response):
            return bot_response + "\n\n" + self.transition_block
        
        return bot_response
    
    def get_escalation_block(self) -> str:
        """
        Retourne le bloc d'escalade standard (BLOC 6.2).
        """
        return """
🔁 ESCALADE AGENT CO
🕐 Notre équipe traite les demandes du lundi au vendredi, de 9h à 17h (hors pause déjeuner).
Nous te répondrons dès que possible.
"""

# Exemple d'utilisation
if __name__ == "__main__":
    middleware = EscalationMiddleware()
    
    # Test avec votre exemple
    user_message = "je voudrais faire une formation en anglais pro"
    bot_response = """Parfait ! 😊 Les formations en anglais professionnel sont tout à fait possibles chez JAK Company.

Cependant, pour le moment, nous ne faisons plus de formations financées par le CPF 🚫. Nous continuons néanmoins à accompagner les professionnels, entreprises, auto-entrepreneurs ou salariés grâce à d'autres dispositifs de financement 💼."""
    
    result = middleware.process_response(user_message, bot_response)
    print("Résultat avec middleware:")
    print(result)