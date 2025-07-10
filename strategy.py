# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006

import os
import sys
import typing
from pathlib import Path
import pandas as pd
from joblib import load
from Battlesnake.game import Cell, Game
from Battlesnake.heatmap import is_food_contested, flood_fill_space, simulate_future_space, build_heatmap
from Battlesnake.path_fallback import PathSolver
from LightGBM.ml_features import ml_features
from Battlesnake.utils import debug
from Battlesnake.astar.astar import AStar

# Setup
ml_path = Path(__file__).resolve().parent.parent / "LightGBM"
if str(ml_path) not in sys.path:
    sys.path.insert(0, str(ml_path))

# Trainingsmodus aktivieren
os.environ["TRAINING_MODE"] = "1"

# Modellpfad definieren
model_path = ml_path / "insane_model.pkl"
csv_path = ml_path / "training_data.csv"

# Feature-Spalten definieren
columns = [
    "head_x", "head_y", "health", "width", "height", "closest_food_distance",
    "space", "future_space", "safe_up", "safe_down", "safe_left", "safe_right",
    "open_area_up", "open_area_down", "open_area_left", "open_area_right",
    "distance_to_nearest_wall", "tail_distance", "closest_food_is_safe", "is_biggest_snake",
    "needs_food", "closest_enemy_head_dist", "enemy_head_is_adjacent", "enemies_within_2",
    "kill_up", "kill_down", "kill_left", "kill_right",
    "dir_up", "dir_down", "dir_left", "dir_right",
    "center_bonus", "food_contest_count", "num_snakes", "path_distance_to_food"
]

#  ML-Modell laden
try:
    ml_model = load(str(model_path))
    debug(f"[ML] insane_model.pkl erfolgreich geladen von: {model_path}")
except Exception as e:
    ml_model = None
    debug(f"[ML] FEHLER beim Laden von insane_model.pkl: {e}")

def choose_strategy(game_state):
    """
    Wählt die Spielstrategie basierend auf dem aktuellen Zustand.
    - early: für erste Züge
    - emergency: bei niedrigem Gesundheitswert
    - late: Standardfall
    """
    turn = game_state['turn']
    health = game_state['you']['health']
    if turn < 30:
        debug("[Strategy] Frühes Spiel")
        return 'early'
    elif health < 30:
        debug("[Strategy] Niedriger Gesundheitswert")
        return 'emergency'
    else:
        debug("[Strategy] Spätes Spiel")
        return 'late'

def classify_move_quality(proba_dict, actual_move, flood_fill_space_after=None):
    """
    Bewertet die Qualität des Zuges basierend auf der Vorhersage des Modells.
    Gibt qualitative Einschätzung zurück (z. B. "Brillant", "Fehler ❌").
    """
    best_move = max(proba_dict, key=proba_dict.get) if proba_dict else None
    confidence_actual = proba_dict.get(actual_move, 0) if proba_dict else 0
    confidence_best = proba_dict[best_move] if best_move else 0

    if actual_move == best_move and confidence_actual > 0.8:
        return "Brillant !!"
    elif confidence_actual >= 0.6:
        return "Großartig !"
    elif confidence_actual >= 0.4:
        return "Ungenauigkeit ?"
    elif flood_fill_space_after is not None and flood_fill_space_after < 3:
        return "Fehler ??"
    else:
        return "Fehler ❌"

def move(game_state: typing.Dict) -> typing.Dict:
    """
    Hauptentscheidungsfunktion für den Snake-Zug.
    1. Versuche ML-Vorhersage mit Feature-Vektor
    2. Fallback: A* mit PathSolver
    3. Fallback: Heatmap-basierte Bewertung
    4. Sicherheitsprüfung des Zuges
    5. Logging bei aktiviertem Trainingsmodus
    """
    debug("[move] Wähle nächsten Zug...")

    my_head_dict = game_state['you']['body'][0]
    my_head = Cell(my_head_dict["x"], my_head_dict["y"])
    health = game_state['you']['health']
    width = game_state['board']['width']
    height = game_state['board']['height']

    strategy = choose_strategy(game_state)

    moves = {
        "up": (0, 1),
        "down": (0, -1),
        "left": (-1, 0),
        "right": (1, 0)
    }

    features = ml_features(game_state)
    if features is None:
        debug("[move] Feature-Extraktion fehlgeschlagen → benutze 'up'")
        return {"move": "up"}
    debug(f"[move] Extrahierte Features: {features}")

    best_move = None
    proba_dict = {}
    confidence = 0

    # 1. Heatmap-Primary
    debug("[Heatmap] Versuche Heatmap-basierte Entscheidung...")
    heatmap = build_heatmap(game_state, my_head, health)
    move_scores = {}
    for direction, (dx, dy) in moves.items():
        nx, ny = my_head.x + dx, my_head.y + dy
        if 0 <= nx < width and 0 <= ny < height:
            move_scores[direction] = heatmap[nx][ny]
    if move_scores:
        best_move = max(move_scores, key=lambda k: move_scores[k])
        debug(f"[Heatmap] Heatmap-Zug gewählt: {best_move}")
    else:
        debug("[Heatmap] Kein sicherer Heatmap-Zug gefunden")

    # 2. A*-Fallback
    if best_move is None:
        debug("[A*] Aktiviere A*-Fallback...")
        try:
            game_obj = Game(game_state)
            path_solver = PathSolver(game_obj)
            food_goals = set([Cell(f["x"], f["y"]) for f in game_state["board"]["food"]])
            valid_goals = [goal for goal in food_goals if goal not in path_solver.forbidden_cells]
            if not valid_goals:
                valid_goals = list(path_solver.neighbors(my_head))
            astar_result = path_solver.astar(my_head, valid_goals[0]) if valid_goals else None
            path = list(astar_result) if astar_result else None
            if path:
                next_cell = path[1] if len(path) > 1 else path[0]
                for direction, (dx, dy) in moves.items():
                    if next_cell.x == my_head.x + dx and next_cell.y == my_head.y + dy:
                        best_move = direction
                        debug(f"[A*] A*-Zug gewählt: {best_move}")
                        break
            else:
                debug("[A*] Kein gültiger Pfad gefunden")
        except Exception as ex:
            debug(f"[A*] Fehler: {ex}")

    # 3. ML-Fallback
    if best_move is None:
        debug("[ML] Aktiviere ML-Fallback...")
        try:
            if ml_model:
                features_df = pd.DataFrame([features], columns=pd.Index(columns))
                proba = ml_model.predict_proba(features_df)
                confidence = max(proba[0])
                ml_prediction = ml_model.predict(features_df)[0]
                proba_dict = dict(zip(ml_model.classes_, proba[0]))

                debug(f"[ML] Vorhersage: {ml_prediction}, Wahrscheinlichkeiten: {proba_dict}")

                if ml_prediction in moves and confidence > 0.6:
                    best_move = ml_prediction
                    debug(f"[ML] ML-Zug gewählt: {best_move}")
                else:
                    debug("[ML] ML-Vertrauen zu niedrig")
            else:
                debug("[ML] Kein Modell geladen")
        except Exception as e:
            debug(f"[ML] Vorhersage fehlgeschlagen → {e}")

    # Final fallback
    if best_move is None:
        debug("[Fallback] Kein Algorithmus erfolgreich → benutze 'up'")
        best_move = "up"

    # Sicherheitsprüfung
    def is_safe_move(move, game_state):
        moves_ = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
        my_head = game_state["you"]["body"][0]
        width = game_state["board"]["width"]
        height = game_state["board"]["height"]
        snakes = game_state["board"]["snakes"]
        all_snake_bodies = [coord for snake in snakes for coord in snake["body"]]
        dx, dy = moves_[move]
        nx, ny = my_head["x"] + dx, my_head["y"] + dy
        if not (0 <= nx < width and 0 <= ny < height):
            return False
        if {"x": nx, "y": ny} in all_snake_bodies:
            return False
        return True

    if not is_safe_move(best_move, game_state):
        debug(f"[SAFETY] Zug '{best_move}' ist unsicher → Fallback")
        for move in ["up", "down", "left", "right"]:
            if is_safe_move(move, game_state):
                debug(f"[SAFETY] Sicherer Alternativ-Zug: {move}")
                return {"move": move}
        debug("[SAFETY] Kein sicherer Zug → benutze 'up'")
        return {"move": "up"}

    # Debug-Ausgabe zur Bewertung
    move_quality = classify_move_quality(proba_dict, best_move)
    debug(f"[Move Quality] {move_quality}")

    return {"move": best_move}










