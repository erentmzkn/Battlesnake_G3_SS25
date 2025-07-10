# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006


from Battlesnake.utils import debug
from Battlesnake.strategy import choose_strategy, move
from Battlesnake.server import run_server

import typing
import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'LightGBM'))
if base_dir not in sys.path:
    sys.path.append(base_dir)


def info() -> typing.Dict:
    """
    Gibt Meta-Daten des Snakes zurück.
    """
    debug("[info] Sending Battlesnake metadata.")
    return {
        #----------------customization----------------
        "apiversion": "1",
        "author": "erentmzkn",
        "color": "#7B1E1E",
        "head": "mlh-gene",
        "tail": "mystic",
        #----------------customization----------------
    }

def start(game_state: typing.Dict):
    """
    Wird beim Start des Spiels aufgerufen. Kann für Debugging genutzt werden.
    """
    debug("Game started and debug function")
    debug("[start] Game started.")

def end(game_state: typing.Dict):
    """
    Wird am Ende des Spiels aufgerufen.
    """
    debug("[end] Game ended.")

if __name__ == "__main__":
    print("main.py is running")
    run_server({
        "info": info,
        "start": start,
        "move": move,
        "end": end
    })









