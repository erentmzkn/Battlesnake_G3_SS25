# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006

import typing


class Cell:
    """
    Repräsentiert eine Zelle auf dem Battlesnake-Spielfeld.

    Kann z. B. aus JSON-Daten erstellt werden und wird für Koordinaten, Distanzen usw. verwendet.

    :ivar x: X-Koordinate der Zelle.
    :ivar y: Y-Koordinate der Zelle.
    """
    __slots__ = ('x', 'y', 'prime_encode')

    def __init__(self, x: int, y: int):
        """
        Erstellt eine neue Cell mit x- und y-Koordinaten.

        Kodiert die Position zusätzlich eindeutig mit Primzahlen.

        :param x: horizontale Position
        :param y: vertikale Position
        """
        self.x = x
        self.y = y
        self.prime_encode = 2 ** self.x * 3 ** self.y

    def __str__(self):
        """String-Darstellung wie (3, 5)"""
        return f'({self.x}, {self.y})'

    def __repr__(self):
        """Detaillierte Darstellung für Debugging"""
        return f'Cell(x={self.x}, y={self.y})'

    def __eq__(self, other):
        """
        Zwei Zellen gelten als gleich, wenn X und Y übereinstimmen.

        :param other: Vergleichszelle
        :return: True oder False
        """
        if not isinstance(other, Cell):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        """
        Hash-Wert auf Basis der Primzahlkodierung.

        Dadurch können Cells effizient in Mengen und Dictionaries verwendet werden.
        """
        return hash(self.prime_encode)

    def distance(self, other: typing.Self) -> int:
        """
        Berechnet die Manhattan-Distanz zu einer anderen Zelle.

        Wird für Bewegungslogik und Distanzen verwendet (keine Diagonalen).

        :param other: Zielzelle
        :return: Anzahl Schritte (int)
        """
        return abs(self.x - other.x) + abs(self.y - other.y)

    @staticmethod
    def from_json(json: typing.Dict):
        """
        Erstellt eine Cell aus einem JSON-Objekt wie {'x': 3, 'y': 5}

        :param json: Dictionary mit 'x' und 'y'
        :return: Neue Cell-Instanz
        """
        return Cell(int(json['x']), int(json['y']))


class Snake:
    """
    Repräsentiert eine Schlange im Spiel.

    Besteht aus einem Body (Liste von Zellen) und einer ID.
    """
    __slots__ = ('game_id', 'body', 'length')

    def __init__(self, game_id: str, body: list[Cell]):
        """
        Erstellt eine neue Snake mit ID und Body.

        :param game_id: Eindeutige ID der Schlange
        :param body: Liste der Zellen, beginnend mit dem Kopf
        """
        self.game_id = game_id
        self.body = body
        self.length = len(self.body)

    def __str__(self):
        """Kurze Darstellung der Schlange"""
        return f'{self.game_id}: {self.body})'

    def __repr__(self):
        """Detaillierte Darstellung für Debugging"""
        return f'Snake(game_id={self.game_id}, body={self.body})'

    def __eq__(self, other):
        """
        Zwei Schlangen gelten als gleich, wenn ID und Körper identisch sind.

        :param other: Vergleichsobjekt
        :return: True oder False
        """
        if not isinstance(other, Snake):
            return False
        return self.game_id == other.game_id and self.body == other.body

    def __hash__(self):
        """
        Hash-Funktion zur Nutzung der Snake in Mengen/Dictionaries.
        """
        return hash((self.game_id, self.body))

    def update_from_json(self, json: typing.Dict):
        """
        Aktualisiert die Schlange basierend auf dem JSON-State des neuen Zugs.

        Fügt neue Kopfposition ein und entfernt ggf. das letzte Element,
        falls die Länge gleich bleibt (kein Fressen passiert).

        :param json: JSON-Daten für die Schlange im neuen Zug
        """
        self.body.insert(0, Cell.from_json(json['head']))

        if int(json['length']) == self.length:
            self.body.pop(-1)
        else:
            self.length = len(self.body)

    @staticmethod
    def from_json(json: typing.Dict):
        """
        Erstellt eine neue Snake aus JSON-Daten.

        :param json: Dictionary mit 'id' und 'body'
        :return: Snake-Instanz
        """
        game_id: str = json['id']
        body: list[Cell] = [Cell.from_json(cell_obj) for cell_obj in json['body']]
        return Snake(game_id, body)


class Game:
    """
    Hält den Gesamtzustand des Spiels (Feldgröße, eigene Schlange, Gegner usw.)

    Wird bei jedem Zug aktualisiert.
    """
    __slots__ = ('turn', 'width', 'height', 'snakes', 'you', 'ownfood', 'hazards')

    def __init__(self, game_state: typing.Dict):
        """
        Erstellt ein neues Game-Objekt aus dem vollständigen Spielzustand.

        :param game_state: Komplette JSON-Daten des aktuellen Spiels
        """
        self.turn: int = int(game_state['turn'])
        self.width: int = int(game_state['board']['width'])
        self.height: int = int(game_state['board']['height'])
        self.snakes: list[Snake] = [Snake.from_json(snake_obj) for snake_obj in game_state['board']['snakes']]
        self.you: Snake = next(x for x in self.snakes if x.game_id == game_state['you']['id'])
        self.ownfood: list[Cell] = [Cell.from_json(food_obj) for food_obj in game_state['board']['food']]
        self.hazards: list[Cell] = [Cell.from_json(hazard_obj) for hazard_obj in game_state['board']['hazards']]

    def __str__(self):
        """Zeigt nur Turn und die Liste der Schlangen"""
        return f"Turn {self.turn}: {self.snakes}"

    def update(self, game_state: typing.Dict) -> None:
        """
        Aktualisiert das Game-Objekt basierend auf dem neuen Game-State.

        Bewegt Schlangen, aktualisiert Futterpositionen und entfernt tote Gegner.

        :param game_state: Neuer JSON-Zustand des Spiels
        """
        self.turn = int(game_state['turn'])
        if self.turn == 0:
            return  # Runde 0 → nichts machen

        self.ownfood = [Cell.from_json(food_obj) for food_obj in game_state['board']['food']]

        sn_ids: list[str] = [sn['id'] for sn in game_state['board']['snakes']]
        to_delete: list[Snake] = []

        for snake in self.snakes:
            if snake.game_id in sn_ids:
                snake.update_from_json(game_state['board']['snakes'][sn_ids.index(snake.game_id)])
            else:
                to_delete.append(snake)

        for snake in to_delete:
            self.snakes.remove(snake)

