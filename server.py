# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006

import logging
import os
import typing

from flask import Flask, request



def run_server(handlers: typing.Dict):
    app = Flask(__name__)

    @app.get("/")
    def on_info():
        return handlers["info"]()

    @app.post("/start")
    def on_start():
        game_state = request.get_json()
        handlers["start"](game_state)
        return "ok"

    @app.post("/move")
    def on_move():
        game_state = request.get_json()
        return handlers["move"](game_state)

    @app.post("/end")
    def on_end():
        game_state = request.get_json()
        handlers["end"](game_state)
        return "ok"

    @app.after_request
    def identify_server(response):
        response.headers.set(
            "server", "battlesnake/github/starter-snake-python"
        )
        return response

    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))

    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    print(f"\nBattlesnake active at http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
