# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006

from typing import Iterable
from Battlesnake.astar.astar import AStar
from Battlesnake.game import Game, Cell
from Battlesnake.heatmap import flood_fill_space

class PathSolver(AStar):
    def __init__(self, game: Game):
        """
        Initialisiert den PathSolver mit dem aktuellen Spielzustand.

        :param game: Das aktuelle Game-Objekt
        """
        self.game = game
        self.forbidden_cells: set[Cell] = set()  # Zellen, in die wir lieber nicht gehen sollten, z. B. weil dort Schlangen sind

    def heuristic_cost_estimate(self, current: Cell, goal: Cell) -> float:
        """
        Schätzt die Entfernung vom aktuellen Punkt zum Ziel mit der Manhattan-Distanz.

        :param current: Startzelle
        :param goal: Zielzelle
        :return: Geschätzter Abstand als float
        """
        return float(current.distance(goal))

    def distance_between(self, n1: Cell, n2: Cell) -> float:
        """
        Gibt die Kosten zwischen zwei benachbarten Zellen zurück.
        Vermeidet verbotene Zellen, indem dort unendlich hohe Kosten gesetzt werden.

        :param n1: Erste Zelle
        :param n2: Zweite Zelle
        :return: Entfernungskosten
        """
        if n1 in self.forbidden_cells or n2 in self.forbidden_cells:
            return float("inf")
        return 1  # Normalerweise kostet jeder Schritt gleich viel

    def neighbors(self, node: Cell) -> Iterable[Cell]:
        """
        Gibt alle gültigen Nachbarzellen der übergebenen Zelle zurück.

        :param node: Aktuelle Zelle
        :return: Liste von benachbarten Zellen
        """
        neighbors: list[Cell] = []
        if node.x > 0:
            neighbors.append(Cell(node.x - 1, node.y))  # links
        if node.x < self.game.width - 1:
            neighbors.append(Cell(node.x + 1, node.y))  # rechts
        if node.y > 0:
            neighbors.append(Cell(node.x, node.y - 1))  # unten
        if node.y < self.game.height - 1:
            neighbors.append(Cell(node.x, node.y + 1))  # oben
        return neighbors


def next_step(game: Game) -> Cell | None:
    """
    Berechnet den besten nächsten Schritt für unsere Schlange, basierend auf A* Pfadfindung.
    Bewertet erreichbare Futtersorten, verbotene Felder und den Raum, der nach dem Zug verfügbar ist.

    :param game: Aktuelles Game-Objekt
    :return: Nächste Zelle, in die sich die Schlange bewegen sollte (oder None)
    """
    path_solver = PathSolver(game)

    # Mögliche gültige Food-Zellen bestimmen
    goals: set[Cell] = set()
    for food in game.ownfood:
        is_valid_food = True
        for snake in game.snakes:
            if snake == game.you:
                continue
            snake_head = snake.body[0]
            if food.distance(snake_head) == 1:
                # Gegner ist näher oder genauso lang => besser vermeiden
                if food.distance(game.you.body[0]) > 1 or snake.length >= game.you.length:
                    is_valid_food = False
                    break
        if is_valid_food:
            goals.add(food)

    #  Verbotene Felder sammeln
    your_head = game.you.body[0]
    forbidden_cells: set[Cell] = set()

    # Berücksichtige Wände als verbotene Zellen
    width, height = game.width, game.height
    for x in range(width):
        forbidden_cells.add(Cell(x, 0))  # obere Wand
        forbidden_cells.add(Cell(x, height - 1))  # untere Wand
    for y in range(height):
        forbidden_cells.add(Cell(0, y))  # linke Wand
        forbidden_cells.add(Cell(width - 1, y))  # rechte Wand

    for snake in game.snakes:
        if snake == game.you:
            continue

        is_by_food = False
        snake_head = snake.body[0]

        # Direkte Nachbarn vom Kopf der anderen Schlangen
        for cell in path_solver.neighbors(snake_head):
            if cell == snake.body[1]:  # Verhindert rückwärts gehen
                continue
            if cell in game.ownfood:
                is_by_food = True  # Wenn Kopf in der Nähe von Futter ist
            if snake.length >= game.you.length and cell.distance(your_head) < 2:
                forbidden_cells.add(cell)

        # Der restliche Körper der Schlange
        for i, cell in enumerate(snake.body):
            move_time = snake.length - i + 1 if is_by_food else snake.length - i
            if move_time >= cell.distance(your_head):
                forbidden_cells.add(cell)

    # Auch die eigenen Körperteile als gefährlich markieren
    for i, cell in enumerate(game.you.body):
        if i == 0:
            continue  # Kopf auslassen
        move_time = game.you.length - i + 1
        if move_time >= cell.distance(your_head):
            forbidden_cells.add(cell)

    path_solver.forbidden_cells = forbidden_cells

    # Schritt 3: Versuche Pfade zu gültigen Zielen zu berechnen
    paths: list[tuple[Cell, int, int]] = []
    for goal in goals:
        path = path_solver.astar(your_head, goal)
        if path is None:
            continue
        path = list(path)  # Convert to list for indexing
        length = len(path)
        first_step = path[1] if length > 1 else path[0]
        area = flood_fill_space(game, first_step)
        paths.append((first_step, length, area))  # Startfeld, Pfadlänge und Platz speichern

    # Schritt 4: Entscheide über den nächsten Schritt
    next_cell: Cell | None = None

    if not paths:
        # Kein Pfad gefunden → suche alternatives sicheres Feld mit größtem Freiraum
        max_area = 0
        for cell in path_solver.neighbors(your_head):
            if cell in forbidden_cells:
                continue
            area = flood_fill_space(game, cell)  # Wie viel Platz haben wir dort?
            if area > max_area:
                max_area = area
                next_cell = cell
    else:
        # Wähle den Pfad mit bester Kombination aus Länge und Freiraum
        # Priorität auf kürzere Pfade, aber Raum beachten
        paths.sort(key=lambda x: (x[1], -x[2]))
        next_cell = paths[0][0]

        # Falls gewählter Schritt wenig Platz bietet, prüfe Alternativen
        for candidate in paths[1:]:
            if flood_fill_space(game, next_cell) < 10 and candidate[2] > paths[0][2]:
                next_cell = candidate[0]
                break

    return next_cell

