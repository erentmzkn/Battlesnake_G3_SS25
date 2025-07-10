# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006

import os
from flask import Flask, request, jsonify
import pandas as pd
import traceback
from joblib import load
from pathlib import Path

from LightGBM.ml_features import ml_features

app = Flask(__name__)

# Modell laden
base_dir = Path(__file__).resolve().parent
model_path = base_dir / "insane_model.pkl"


def load_model(path):
    """
    Lädt ein trainiertes ML-Modell aus der angegebenen Datei.

    Gibt das geladene Modell zurück oder None, falls ein Fehler auftritt.

    :param path: Pfad zur .pkl-Datei mit dem Modell.
    :return: Das geladene Modellobjekt oder None bei Fehler.
    """
    if not path.exists():
        print(f"[WARNUNG] Modell-Datei nicht gefunden: {path}")
        return None
    try:
        model = load(path)
        print(f"[ML] Modell erfolgreich geladen von: {path}")
        return model
    except Exception as e:
        print(f"[ERROR] Modell konnte nicht geladen werden: {e}")
        return None


model = load_model(model_path)


@app.route("/start", methods=["POST"])
def start():
    """
    Wird aufgerufen, wenn ein neues Spiel startet.

    Dient aktuell nur zur Anzeige einer Startmeldung in der Konsole.
    """
    print("[INFO] Spiel gestartet.")
    return "ok"


@app.route("/end", methods=["POST"])
def end():
    """
    Wird aufgerufen, wenn ein Spiel endet.

    Dient aktuell nur zur Anzeige einer Endmeldung in der Konsole.
    """
    print("[INFO] Spiel beendet.")
    return "ok"


@app.route("/move", methods=["POST"])
def move():
    """
    Hauptfunktion zur Entscheidung über den nächsten Zug.

    Wandelt den Game-State in Features um, nutzt das ML-Modell zur Vorhersage
    des besten Zugs und sendet diesen zurück. Falls ein Fehler auftritt oder
    das Modell nicht vorhanden ist, wird ein Fallback-Zug ("up") verwendet.

    :return: JSON-Objekt mit dem gewählten Zug, z. B. {"move": "up"}
    """
    try:
        # Validierung des Request-JSON
        try:
            game_state = request.get_json()
            if not game_state:
                print("[ERROR] Ungültiges JSON im Request erhalten.")
                return jsonify({"move": "up"})
        except Exception as e:
            print(f"[ERROR] Fehler beim Parsen des Request-JSON: {e}")
            return jsonify({"move": "up"})

        # Extrahiere Features
        features = ml_features(game_state)

        if not features or len(features) != 36:
            print(
                "[ERROR] Ungültiger Merkmalsvektor erhalten, Vorhersage wird übersprungen."
            )
            return jsonify({"move": "up"})

        print(f"[DEBUG] Eingabefeatures: {features}")

        # Überprüfe, ob das Modell geladen ist
        if not model:
            print("[ERROR] Kein Modell verfügbar. Beende.")
            return jsonify({"move": "up"})  # Oder ein sicherer Fallback-Zug

        try:
            columns = [
                "head_x", "head_y", "health", "width", "height",
                "closest_food_distance", "space", "future_space", "safe_up",
                "safe_down", "safe_left", "safe_right", "open_area_up",
                "open_area_down", "open_area_left", "open_area_right",
                "distance_to_nearest_wall", "tail_distance",
                "closest_food_is_safe", "is_biggest_snake", "needs_food",
                "closest_enemy_head_dist", "enemy_head_is_adjacent",
                "enemies_within_2", "kill_up", "kill_down", "kill_left",
                "kill_right", "dir_up", "dir_down", "dir_left", "dir_right",
                "center_bonus", "food_contest_count", "num_snakes",
                "path_distance_to_food"
            ]
            # Only use columns for DataFrame creation
            features_df = pd.DataFrame([features],
                                       columns=columns)  # type: ignore
            prediction = model.predict(features_df)[0]
            print(f"[ML] Vorhergesagter Zug: {prediction}")

            # --- Final move safety check ---
            def is_safe_move(move, game_state):
                moves = {
                    "up": (0, 1),
                    "down": (0, -1),
                    "left": (-1, 0),
                    "right": (1, 0)
                }
                my_head = game_state["you"]["body"][0]
                width = game_state["board"]["width"]
                height = game_state["board"]["height"]
                snakes = game_state["board"]["snakes"]
                my_id = game_state["you"]["id"]
                all_snake_bodies = [
                    coord for snake in snakes for coord in snake["body"]
                ]
                dx, dy = moves[move]
                nx, ny = my_head["x"] + dx, my_head["y"] + dy
                # Check wall
                if not (0 <= nx < width and 0 <= ny < height):
                    return False
                # Check self or other snake collision
                if {"x": nx, "y": ny} in all_snake_bodies:
                    return False
                return True

            if not is_safe_move(prediction, game_state):
                print(
                    f"[SAFETY] ML predicted move '{prediction}' is unsafe! Choosing fallback."
                )
                # Try to pick a safe move
                for move in ["up", "down", "left", "right"]:
                    if is_safe_move(move, game_state):
                        print(f"[SAFETY] Fallback safe move: {move}")
                        return jsonify({"move": move})
                print("[SAFETY] No safe moves found. Returning 'up'.")
                return jsonify({"move": "up"})
            # --- End safety check ---
            return jsonify({"move": prediction})
        except Exception as ml_error:
            print(f"[WARNUNG] ML-Vorhersage fehlgeschlagen: {ml_error}")

    except Exception as e:
        print("[ERROR] Fehler im Move-Handler:")
        traceback.print_exc()

    # Fallback-Zug
    fallback_move = "up"
    print(f"[Fallback] Fallback-Zug gewählt: {fallback_move}")
    return jsonify({"move": fallback_move})


if __name__ == "__main__":
    """
    Startet den Battlesnake-Server lokal auf Port 8000.
    Der Debug-Modus ist aktiviert. Dieser kann in der Datei 'utils.py' durch Setzen von DEBUG = False deaktiviert werden.
    """
    print("[INFO] Starte Battlesnake-Server...")
    app.run(host="0.0.0.0", port=8000, debug=True)
