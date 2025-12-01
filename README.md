# Web Initiative Tracker

Un gestionnaire d'initiative interactif pour les jeux de rôle sur table, conçu pour fluidifier la gestion des combats.

## Description

Web Initiative Tracker est une application web conçue pour les maîtres de jeu. Elle permet de suivre l'initiative, les points de vie et les états des personnages (joueurs et non-joueurs) sur une interface web simple et claire. Grâce à sa conception en temps réel, toute modification est instantanément visible par tous les participants qui consultent la page (par exemple, sur un écran déporté).

## Fonctionnalités

*   **Suivi de combat en temps réel** : Les changements sont propagés à tous les clients connectés sans rechargement de page.
*   **Gestion des participants** : Ajout, modification et suppression facile des combattants.
*   **Système de tour par tour** : Avancement simple du tour et mise en évidence du participant actif.
*   **Suivi des blessures et états** : Gestion des points de vie et application d'états (ex: Assourdi, Effrayé) avec icônes visuelles.
*   **Affichage des portraits** : Associez une image à chaque participant pour une meilleure immersion.
*   **Persistance des données** : Sauvegardez et chargez des groupes de joueurs ou des configurations de rencontres complètes.

## Technologies utilisées

*   **Backend** : Python
*   **Framework Web** : Flask
*   **Communication temps réel** : Flask-SocketIO
*   **Serveur asynchrone** : Eventlet
*   **Frontend** : HTML, CSS, JavaScript (avec Jinja2 pour le templating)

## Installation et Lancement

Suivez ces étapes pour lancer l'application sur votre machine locale.

### Prérequis

*   Python 3.7 ou une version ultérieure
*   `pip` (l'installeur de paquets Python)

### Instructions

1.  **Cloner le projet** (si vous utilisez git)
    Si vous n'avez pas git, assurez-vous simplement d'avoir tous les fichiers du projet dans un dossier.

2.  **Créer un environnement virtuel** (recommandé)
    Ouvrez un terminal dans le dossier du projet et exécutez :
    ```bash
    # Pour Windows
    python -m venv venv
    venv\Scripts\activate

    # Pour macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Installer les dépendances**
    Avec votre environnement virtuel activé, installez les paquets nécessaires :
    ```bash
    pip install -r requirements.txt
    ```

4.  **Lancer l'application**
    ```bash
    python run.py
    ```

5.  **Accéder à l'application**
    Ouvrez votre navigateur web et allez à l'adresse suivante :
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Structure du projet

Le projet est organisé de la manière suivante :

```
Webtracker/
├── app/                  # Contient le coeur de l'application Flask
│   ├── __init__.py       # Initialise l'application Flask et SocketIO
│   ├── models.py         # Définit la structure des données (classe Participant) et gère l'état du combat en mémoire
│   ├── routes.py         # Gère les routes web, la logique métier et les interactions utilisateur
│   ├── utils.py          # Fonctions utilitaires (sauvegarde/chargement des données JSON)
│   ├── portrait_utils.py # Fonctions pour la gestion des portraits
│   ├── static/           # Fichiers statiques (images, icônes, etc.)
│   └── templates/        # Fichiers de templates HTML (Jinja2)
├── data/                 # Dossier où sont stockées les sauvegardes (joueurs, rencontres)
├── requirements.txt      # Liste des dépendances Python
└── run.py                # Point d'entrée pour démarrer le serveur web
```

## Personnalisation

### Ajout de portraits
Pour ajouter vos propres images de personnages, placez-les dans les sous-dossiers de `app/static/portraits/`.

### Modification du style
Les styles CSS peuvent être modifiés pour personnaliser l'apparence de l'application. Les fichiers pertinents se trouvent dans le dossier `app/static/`.

---
*Développé pour faciliter la vie des maîtres de jeu.*