from flask import render_template, request, redirect, url_for, jsonify
import os
import random

from app import app
from app import models, utils
from app.models import Participant
from app.portrait_utils import get_portraits_and_folders

# --- Constantes ---

# Le chemin vers le dossier des portraits, situé dans le dossier 'static'.
PORTRAIT_DIR = os.path.join(app.static_folder, 'portraits')
os.makedirs(PORTRAIT_DIR, exist_ok=True) # S'assure que le dossier existe.


# --- Routes principales pour l'affichage des pages ---

@app.route('/')
def index():
    """
    Affiche la page principale de l'application (la vue du Maître de Jeu).
    Cette page permet de gérer les participants, de lancer des rencontres, etc.
    """
    encounters_list = utils.list_encounters()
    return render_template('index.html', 
                             participants=models.initiative_data, 
                             current_turn_index=models.current_turn_index,
                             encounters=encounters_list,
                             all_statuses=models.STATUS_EFFECTS)

@app.route('/view')
def view():
    """
    Affiche la page de vue pour les joueurs, qui ne montre que l'ordre d'initiative
    et les informations publiques des participants.
    """
    return render_template('view.html', 
                           participants=models.initiative_data, 
                           current_turn_index=models.current_turn_index, 
                           all_statuses=models.STATUS_EFFECTS)

@app.route('/portrait_view')
def portrait_view():
    """
    Affiche une vue centrée sur le portrait du participant dont c'est le tour.
    Utile pour un affichage sur un écran secondaire.
    """
    active_participant = None
    if models.initiative_data and 0 <= models.current_turn_index < len(models.initiative_data):
        active_participant = models.initiative_data[models.current_turn_index]
    return render_template('portrait_view.html', participant=active_participant)

@app.route('/select_portrait')
def select_portrait():
    """
    Affiche la modale de sélection de portrait.
    Le paramètre 'target' indique quel champ de formulaire doit être mis à jour.
    """
    target_field = request.args.get('target', 'portrait')
    return render_template('select_portrait.html', target_field=target_field)


# --- Routes pour la gestion des participants ---

@app.route('/add', methods=['POST'])
def add():
    """
    Ajoute un nouveau participant (joueur, monstre ou allié) à la liste d'initiative.
    Les données sont reçues via une requête POST depuis un formulaire.
    """
    name = request.form.get('name')
    is_player_val = request.form.get('is_player')
    portrait_filename = request.form.get('portrait')

    if portrait_filename == "":
        portrait_filename = None

    if is_player_val == 'player':
        role = 'player'
        p_type = 'Joker' # Les joueurs sont toujours de type 'Joker'
    else:
        role = is_player_val
        p_type = request.form.get('type', 'Extra')

    if name:
        new_participant = Participant(
            name=name,
            role=role,
            p_type=p_type,
            is_player=(role == 'player'),
            # L'initiative est aléatoire pour les PNJ, fixe pour les joueurs (sera modifiée plus tard)
            initiative_roll=random.randint(1, 20) if role != 'player' else 10,
            portrait=portrait_filename
        )
        models.initiative_data.append(new_participant)
        models.sort_participants() # Trie la liste après l'ajout.

    return jsonify({'success': True})

@app.route('/participant/<int:p_index>/edit', methods=['POST'])
def edit_participant(p_index):
    """
    Modifie les informations d'un participant existant (nom, initiative, rôle, etc.).
    """
    if 0 <= p_index < len(models.initiative_data):
        participant = models.initiative_data[p_index]
        
        participant.name = request.form.get('name', participant.name)
        try:
            new_initiative = request.form.get('initiative_roll')
            if new_initiative is not None and str(new_initiative).strip():
                participant.initiative_roll = int(new_initiative)
        except (ValueError, TypeError):
            pass # Ignore les valeurs d'initiative non valides.
        
        participant.role = request.form.get('role', participant.role)
        participant.p_type = request.form.get('p_type', participant.p_type)
        
        portrait = request.form.get('portrait')
        if portrait == '':
            participant.portrait = None
        elif portrait is not None:
            participant.portrait = portrait
        
        participant.is_player = (participant.role == 'player')

        models.sort_participants()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Participant not found'}), 404

@app.route('/remove/<int:index>', methods=['POST'])
def remove_participant(index):
    """Supprime un participant de la liste d'initiative."""
    if 0 <= index < len(models.initiative_data):
        models.initiative_data.pop(index)

        # Ajuste l'index du tour courant si nécessaire pour éviter les erreurs.
        if models.current_turn_index >= len(models.initiative_data) and len(models.initiative_data) > 0:
            models.current_turn_index = len(models.initiative_data) - 1
        elif index < models.current_turn_index:
            models.current_turn_index -= 1
        models.update_state()
            
    return jsonify({'success': True})


# --- Routes pour la gestion des blessures et statuts ---

@app.route('/add_wound/<int:index>', methods=['POST'])
def add_wound(index):
    """Ajoute une blessure à un participant."""
    if 0 <= index < len(models.initiative_data):
        participant = models.initiative_data[index]
        participant.add_wound()
        models.update_state()
    return jsonify({'success': True})

@app.route('/remove_wound/<int:index>', methods=['POST'])
def remove_wound(index):
    """Retire une blessure à un participant."""
    if 0 <= index < len(models.initiative_data):
        participant = models.initiative_data[index]
        participant.remove_wound()
        models.update_state()
    return jsonify({'success': True})

@app.route('/participant/<int:p_index>/status/add', methods=['POST'])
def add_status(p_index):
    """Ajoute un statut (ex: Secoué, Entravé) à un participant."""
    if 0 <= p_index < len(models.initiative_data):
        participant = models.initiative_data[p_index]
        status_name = request.form.get('status')
        duration_str = request.form.get('duration')

        # Ajoute le statut seulement s'il n'est pas déjà présent.
        if status_name in models.STATUS_EFFECTS and not any(s['name'] == status_name for s in participant.statuses):
            new_status = {'name': status_name, 'duration': None}
            if duration_str and duration_str.isdigit():
                duration = int(duration_str)
                if duration > 0:
                    new_status['duration'] = duration
            
            participant.statuses.append(new_status)
            models.update_state()
    return jsonify({'success': True})

@app.route('/participant/<int:p_index>/status/remove', methods=['POST'])
def remove_status(p_index):
    """Supprime un statut d'un participant."""
    if 0 <= p_index < len(models.initiative_data):
        participant = models.initiative_data[p_index]
        status_to_remove = request.form.get('status')
        participant.statuses = [s for s in participant.statuses if s['name'] != status_to_remove]
        models.update_state()
    return jsonify({'success': True})


# --- Routes pour le déroulement du combat ---

@app.route('/update_initiatives', methods=['POST'])
def update_initiatives():
    """Met à jour en masse les jets d'initiative de tous les participants."""
    for key, value in request.form.items():
        if key.startswith('p_'):
            try:
                index = int(key.split('_')[1])
                initiative_roll = int(value)
                if 0 <= index < len(models.initiative_data):
                    participant = models.initiative_data[index]
                    participant.initiative_roll = initiative_roll
            except (ValueError, IndexError):
                pass
    models.sort_participants()
    return jsonify({'success': True})

@app.route('/next', methods=['POST'])
def next_turn():
    """Passe au tour du prochain participant valide (pas 'Mort')."""
    if not models.initiative_data:
        return jsonify({'success': False, 'message': 'No participants.'})

    # Cherche le prochain participant valide en boucle.
    for i in range(len(models.initiative_data)):
        next_index = (models.current_turn_index + 1 + i) % len(models.initiative_data)
        p = models.initiative_data[next_index]
        if p.status['class'] != 'status-dead':
            models.current_turn_index = next_index
            models.update_state()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'No valid next turn.'})

@app.route('/new_round', methods=['POST'])
def new_round():
    """
    Démarre un nouveau round de combat.
    - Décrémente la durée des statuts.
    - Relance l'initiative pour tous les PNJ.
    - Réinitialise le tour au premier participant.
    """
    models.current_turn_index = 0
    for p in models.initiative_data:
        if p.status['class'] in ['status-dead', 'status-out']:
            continue

        # Décrémente la durée des statuts avec une durée définie.
        active_statuses = []
        for status in p.statuses:
            if isinstance(status, dict) and status.get('duration') is not None:
                status['duration'] -= 1
                if status['duration'] > 0:
                    active_statuses.append(status)
            else:
                active_statuses.append(status) # Conserve les statuts sans durée.
        p.statuses = active_statuses

        # Relance l'initiative pour les PNJ.
        if not p.is_player:
            roll = random.randint(1, 20)
            p.initiative_roll = roll
            p.is_critical = (roll == 20)
        
    models.sort_participants()
    
    # Trouve le premier participant valide pour commencer le round.
    models.current_turn_index = -1
    if models.initiative_data:
        for i, p_data in enumerate(models.initiative_data):
            if p_data.status['class'] not in ['status-dead', 'status-out']:
                models.current_turn_index = i
                break
    models.update_state()
    
    return jsonify({'success': True})

@app.route('/reset_combat', methods=['POST'])
def reset_combat():
    """Réinitialise le combat, ne conservant que les joueurs."""
    models.initiative_data = [p for p in models.initiative_data if p.role == 'player']
    models.current_turn_index = 0
    models.update_state()
    return jsonify({'success': True})

@app.route('/reset', methods=['POST'])
def reset():
    """Réinitialise complètement l'application, supprimant tous les participants."""
    models.initiative_data = []
    models.current_turn_index = 0
    models.update_state()
    return jsonify({'success': True})


# --- Routes pour la sauvegarde et le chargement de données ---

@app.route('/save_players', methods=['POST'])
def save_players_route():
    """Sauvegarde les données des joueurs actuels dans un fichier JSON."""
    utils.save_players(models.initiative_data)
    return jsonify({'success': True})

@app.route('/load_players', methods=['POST'])
def load_players_route():
    """Charge les données des joueurs depuis un fichier JSON."""
    models.initiative_data, _ = utils.load_players(models.initiative_data)
    models.sort_participants()
    return jsonify({'success': True})

@app.route('/save_encounter', methods=['POST'])
def save_encounter_route():
    """Sauvegarde la configuration actuelle des PNJ en tant que rencontre."""
    name = request.form.get('encounter_name')
    if name:
        utils.save_encounter(name, models.initiative_data)
    return jsonify({'success': True})

@app.route('/load_encounter/<filename>', methods=['POST'])
def load_encounter_route(filename):
    """Charge une rencontre de PNJ depuis un fichier JSON."""
    file_path = os.path.join(utils.ENCOUNTERS_DIR, filename)
    models.initiative_data, _ = utils.load_encounter(file_path, models.initiative_data)
    models.sort_participants()
    return jsonify({'success': True})


# --- API interne pour le rafraîchissement dynamique de l'interface ---

@app.route('/api/participants')
def api_participants_list():
    """API pour obtenir la liste complète des participants en format JSON."""
    return jsonify([p.to_dict() for p in models.initiative_data])

@app.route('/api/portraits')
def api_portraits():
    """API pour l'explorateur de fichiers de portraits."""
    rel_path = request.args.get('path', '')
    
    # Sécurité : empêche de remonter dans l'arborescence des fichiers.
    if '..' in rel_path or os.path.isabs(rel_path):
        return jsonify({'error': 'Chemin invalide'}), 400
    
    portraits_data = get_portraits_and_folders(PORTRAIT_DIR, rel_path)
    return jsonify(portraits_data)

@app.route('/api/view_content')
def api_view_content():
    """API qui retourne uniquement le HTML de la table pour la vue joueur."""
    return render_template('_view_table.html', 
                             participants=models.initiative_data, 
                             current_turn_index=models.current_turn_index)

@app.route('/api/portrait_content')
def api_portrait_content():
    """API qui retourne uniquement le HTML de la vue portrait."""
    active_participant = None
    if models.initiative_data and 0 <= models.current_turn_index < len(models.initiative_data):
        active_participant = models.initiative_data[models.current_turn_index]
    return render_template('_portrait.html', participant=active_participant)

@app.route('/api/main_content')
def api_main_content():
    """API qui retourne uniquement le HTML de la table principale pour la vue MJ."""
    return render_template('_main_table.html', 
                             participants=models.initiative_data, 
                             current_turn_index=models.current_turn_index,
                             all_statuses=models.STATUS_EFFECTS)
