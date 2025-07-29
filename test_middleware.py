from escalation_middleware import EscalationMiddleware

def test_middleware():
    middleware = EscalationMiddleware()
    
    # Test 1: Demande de formation spécifique (doit escalader)
    print("=== TEST 1: Demande formation spécifique ===")
    user_msg = "je voudrais faire une formation en anglais pro"
    bot_response = """Parfait ! 😊 Les formations en anglais professionnel sont tout à fait possibles chez JAK Company.

Cependant, pour le moment, nous ne faisons plus de formations financées par le CPF 🚫. Nous continuons néanmoins à accompagner les professionnels, entreprises, auto-entrepreneurs ou salariés grâce à d'autres dispositifs de financement 💼."""
    
    result = middleware.process_response(user_msg, bot_response)
    print(f"Escalade ajoutée: {'OUI' if '[BLOC TRANSITION]' in result else 'NON'}")
    print(f"Résultat: {result}")
    print()
    
    # Test 2: Demande générale (ne doit pas escalader)
    print("=== TEST 2: Demande générale ===")
    user_msg = "c'est quoi vos formations ?"
    bot_response = """🎓 +100 formations disponibles chez JAK Company ! 🎓
📚 Nos spécialités :
• 💻 Bureautique
• 🖥 Informatique
• 🌍 Langues
• 🎨 Web/3D
• 📈 Vente & Marketing
• 🧠 Développement personnel
• 🌱 Écologie numérique
• 🎯 Bilan compétences ⚙ Sur mesure
Et bien d'autres encore ! ✨
📖 E-learning ou 🏢 Présentiel → Tu choisis ! 😉
Quel domaine t'intéresse ? 👀"""
    
    result = middleware.process_response(user_msg, bot_response)
    print(f"Escalade ajoutée: {'OUI' if '[BLOC TRANSITION]' in result else 'NON'}")
    print(f"Résultat: {result}")
    print()
    
    # Test 3: Déjà en escalade (ne doit pas ajouter de bloc)
    print("=== TEST 3: Déjà en escalade ===")
    user_msg = "je veux une formation"
    bot_response = """Parfait ! Notre équipe commerciale va pouvoir t'accompagner pour cette formation. 

Veux-tu être mis en relation avec eux pour explorer les possibilités ? 😊"""
    
    result = middleware.process_response(user_msg, bot_response)
    print(f"Escalade ajoutée: {'OUI' if '[BLOC TRANSITION]' in result else 'NON'}")
    print(f"Résultat: {result}")
    print()
    
    # Test 4: Autres formations
    print("=== TEST 4: Formation bureautique ===")
    user_msg = "je veux faire une formation en bureautique"
    bot_response = """Excellente idée ! 😊 Les formations en bureautique sont très demandées et nous avons plusieurs programmes adaptés à tous les niveaux.

Nos formations bureautique couvrent Excel, Word, PowerPoint et bien d'autres outils essentiels."""
    
    result = middleware.process_response(user_msg, bot_response)
    print(f"Escalade ajoutée: {'OUI' if '[BLOC TRANSITION]' in result else 'NON'}")
    print(f"Résultat: {result}")

if __name__ == "__main__":
    test_middleware()