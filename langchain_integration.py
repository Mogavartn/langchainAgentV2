from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI  # ou votre LLM
from escalation_middleware import EscalationMiddleware

class EscalationAwareChain:
    """
    Chaîne LangChain qui intègre automatiquement l'escalade commerciale.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.middleware = EscalationMiddleware()
        
        # Template de base pour les réponses
        self.base_prompt = PromptTemplate(
            input_variables=["user_message", "context"],
            template="""
            Tu es un assistant commercial de JAK Company, spécialisé dans les formations.
            
            Contexte: {context}
            Message utilisateur: {user_message}
            
            Réponds de manière professionnelle et engageante. Si l'utilisateur demande 
            une formation spécifique, ne répète pas la liste complète des formations.
            """
        )
        
        self.base_chain = LLMChain(llm=self.llm, prompt=self.base_prompt)
    
    def run(self, user_message: str, context: str = "") -> str:
        """
        Exécute la chaîne avec gestion automatique de l'escalade.
        """
        # Générer la réponse de base
        base_response = self.base_chain.run({
            "user_message": user_message,
            "context": context
        })
        
        # Appliquer le middleware d'escalade
        final_response = self.middleware.process_response(user_message, base_response)
        
        return final_response

# Exemple d'utilisation avec votre conversation
def test_conversation():
    # Simuler un LLM (remplacez par votre vrai LLM)
    llm = OpenAI(temperature=0.7)
    
    chain = EscalationAwareChain(llm)
    
    # Test avec votre exemple
    user_message = "je voudrais faire une formation en anglais pro"
    
    # Simuler une réponse de base (dans la vraie vie, ce serait généré par le LLM)
    base_response = """Parfait ! 😊 Les formations en anglais professionnel sont tout à fait possibles chez JAK Company.

Cependant, pour le moment, nous ne faisons plus de formations financées par le CPF 🚫. Nous continuons néanmoins à accompagner les professionnels, entreprises, auto-entrepreneurs ou salariés grâce à d'autres dispositifs de financement 💼."""
    
    # Appliquer le middleware
    middleware = EscalationMiddleware()
    result = middleware.process_response(user_message, base_response)
    
    print("=== Test du middleware ===")
    print(f"Message utilisateur: {user_message}")
    print(f"Réponse de base: {base_response}")
    print(f"Réponse finale: {result}")
    print("=" * 50)

if __name__ == "__main__":
    test_conversation()