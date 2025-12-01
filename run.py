import eventlet

# Applique un patch aux bibliothèques standard de Python pour les rendre compatibles
# avec les coroutines de 'eventlet'. C'est essentiel pour que les WebSockets
# et autres opérations asynchrones fonctionnent correctement avec Flask-SocketIO.
eventlet.monkey_patch()

from app import app, socketio
import webbrowser
from threading import Timer

def open_browser():
    """
    Ouvre un nouvel onglet dans le navigateur par défaut à l'adresse de l'application.
    """
    webbrowser.open_new('http://127.0.0.1:5000')

if __name__ == '__main__':
    """
    Point d'entrée de l'application.
    Ce bloc est exécuté lorsque le script est lancé directement (par ex. 'python run.py').
    """
    # Démarre un minuteur qui déclenchera l'ouverture du navigateur après 1 seconde.
    # Cela laisse le temps au serveur de démarrer avant d'essayer d'ouvrir la page.
    Timer(1, open_browser).start()
    
    # Lance le serveur de développement Flask avec le support de SocketIO.
    # 'debug=True' active le mode de débogage pour avoir des messages d'erreur détaillés.
    # 'use_reloader=False' est important car le reloader de Flask peut causer des problèmes
    # avec eventlet et le minuteur.
    # 'host="0.0.0.0"' rend l'application accessible depuis d'autres appareils sur le même réseau.
    socketio.run(app, debug=True, use_reloader=False, host="0.0.0.0")
