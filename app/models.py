import os

class Participant:
    """
    Représente un participant (joueur ou non-joueur) dans le tracker d'initiative.
    Cette classe contient toutes les informations et la logique métier liées à un personnage,
    comme ses blessures, ses statuts et son initiative.
    """
    def __init__(self, name, role, p_type, is_player, initiative_roll=10, is_critical=False, wounds=0, portrait=None, statuses=None):
        """
        Initialise un nouveau participant.

        Args:
            name (str): Le nom du participant.
            role (str): Le rôle du participant (par exemple, 'Joueur', 'Ennemi').
            p_type (str): Le type de personnage (par exemple, 'Principal', 'Extra').
            is_player (bool): True si le participant est un joueur.
            initiative_roll (int, optional): Le résultat du jet d'initiative. Par défaut à 10.
            is_critical (bool, optional): True si le jet d'initiative était un succès critique. Par défaut à False.
            wounds (int, optional): Le nombre de blessures du participant. Par défaut à 0.
            portrait (str, optional): Le chemin vers l'image du portrait. Par défaut à None.
            statuses (list, optional): Une liste des statuts affectant le participant. Par défaut à [].
        """
        self.name = name
        self.role = role
        self.p_type = p_type
        self.is_player = is_player
        self.initiative_roll = initiative_roll
        self.is_critical = is_critical
        self.wounds = wounds
        self.portrait = portrait
        self.statuses = statuses if statuses is not None else [] # List of dicts {'name': str, 'duration': int|None}

    def __repr__(self):
        """Représentation textuelle de l'objet Participant pour le débogage."""
        return f"Participant({self.name}, Role: {self.role}, Type: {self.p_type}, Player: {self.is_player}, Initiative: {self.initiative_roll}, Wounds: {self.wounds}, Statuses: {self.statuses})"

    def add_wound(self):
        """
        Ajoute une blessure au participant et met à jour ses statuts en conséquence.
        La logique dépend du type de personnage ('Extra' ou non).
        Un 'Extra' est hors de combat après une seule blessure.
        """
        # Supprimer les statuts liés aux blessures pour éviter les doublons avant de réévaluer.
        self.statuses = [s for s in self.statuses if s['name'] not in ['Incapacité', 'Mort']]

        if self.p_type == 'Extra':
            if self.wounds < 1:
                self.wounds = 1
                self.statuses.append({'name': 'Mort', 'duration': None})
        else:
            if self.wounds < 5:
                self.wounds += 1
                if self.wounds >= 5:
                    self.statuses.append({'name': 'Mort', 'duration': None})
                elif self.wounds >= 4:
                    self.statuses.append({'name': 'Incapacité', 'duration': None})

    def remove_wound(self):
        """
        Retire une blessure au participant et met à jour ses statuts.
        Cela retire les éventuels statuts 'Incapacité' ou 'Mort' si le nombre de blessures diminue.
        """
        if self.wounds > 0:
            self.wounds -= 1
            # Toujours supprimer les statuts liés aux blessures pour les réévaluer.
            self.statuses = [s for s in self.statuses if s['name'] not in ['Incapacité', 'Mort']]

            if self.p_type != 'Extra':
                if self.wounds >= 4:
                    self.statuses.append({'name': 'Incapacité', 'duration': None})

    @property
    def status(self):
        """
        Calcule l'état (texte et classe CSS) et le malus du participant
        en fonction de son nombre de blessures.
        Cette propriété est utilisée pour l'affichage dans l'interface web.
        """
        status_info = {'text': '', 'class': '', 'malus': 0}
        if self.p_type == 'Extra':
            if self.wounds >= 1:
                status_info['text'] = 'Hors Combat'
                status_info['class'] = 'status-dead'
        else:
            if self.wounds > 0:
                status_info['malus'] = self.wounds
                status_info['class'] = 'status-wounded'
                status_info['text'] = f"-{self.wounds}"
                if self.wounds >= 5:
                    status_info['text'] = 'Mort'
                    status_info['class'] = 'status-dead'
                elif self.wounds >= 4:
                    status_info['text'] = 'Incapacité'
                    status_info['class'] = 'status-incapacitated'
        return status_info

    def to_dict(self):
        """Convertit l'objet Participant en un dictionnaire pour la sérialisation en JSON."""
        return {
            'name': self.name,
            'role': self.role,
            'p_type': self.p_type,
            'is_player': self.is_player,
            'initiative_roll': self.initiative_roll,
            'is_critical': self.is_critical,
            'wounds': self.wounds,
            'portrait': self.portrait,
            'statuses': self.statuses
        }

    @classmethod
    def from_dict(cls, data):
        """
        Crée un objet Participant à partir d'un dictionnaire.
        Cette méthode assure la rétrocompatibilité avec les anciennes versions des données
        en gérant les changements de noms de clés et de formats de statuts.
        """
        # Ignorer la clé 'status' de l'ancien format pour éviter les erreurs.
        data.pop('status', None)

        # Gérer l'ancien nom de clé 'type' pour la compatibilité.
        if 'type' in data and 'p_type' not in data:
            data['p_type'] = data.pop('type')

        # Assurer que les statuts sont toujours dans le format de dictionnaire.
        statuses_data = data.get('statuses', [])
        if statuses_data and any(isinstance(s, str) for s in statuses_data):
            new_statuses = []
            for s in statuses_data:
                if isinstance(s, str):
                    new_statuses.append({'name': s, 'duration': None})
                elif isinstance(s, dict): # Conserver les dictionnaires déjà corrects.
                    new_statuses.append(s)
            data['statuses'] = new_statuses
        
        return cls(**data)

# --- Données et état de l'application ---
from flask import session
import random
from app import socketio

# Liste des effets de statut possibles qu'un participant peut avoir.
STATUS_EFFECTS = [
    "Secoué",
    "Entravé",
    "Aveuglé",
    "Assourdi",
    "Effrayé",
    "Immobilisé",
    "Inconscient",
    "Incapacité",
    "Mort",
]

# Données en mémoire pour l'état de l'initiative.
# 'initiative_data' contient la liste des participants pour la rencontre en cours.
initiative_data = []
# 'current_turn_index' suit le tour du participant actuel dans la liste triée.
current_turn_index = 0

def update_state():
    """
    Émet un événement WebSocket ('update_data') à tous les clients connectés.
    Cela informe l'interface utilisateur qu'elle doit se mettre à jour avec les dernières données.
    """
    print("State changed. Emitting 'update_data' event.")
    socketio.emit('update_data')

def sort_participants():
    """
    Trie la liste des participants (`initiative_data`) en fonction de leur jet d'initiative.
    Le tri est décroissant par initiative, puis par nom (alphabétique) pour les égalités.
    """
    global initiative_data
    initiative_data.sort(key=lambda p: (p.initiative_roll, p.name), reverse=True)
    update_state()
