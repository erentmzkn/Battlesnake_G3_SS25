    # Gruppe 3 – Battlesnake Projekt (SS2025)
    # Mitglieder:
    # Eren Temizkan, 223201982
    # Dominik Ide, 220200046
    # Dogukan Karakoyun, 223202023
    # Alexandra Holsten, 221200813
    # Yuxiao Wu, 223200006

    from Battlesnake.utils import debug
    from Battlesnake.game import Cell
    from Battlesnake.utils import debug
    from collections import deque


    def flood_fill_space(game_state, start):
        """
        Führt eine Flood-Fill-Suche durch, um die Anzahl freier Felder ab dem Startpunkt zu zählen.

        Diese Methode wird genutzt, um zu bewerten, wie viel Platz man in einem bestimmten Gebiet hat.

        :param game_state: Der aktuelle Spielzustand (Board, Snakes, etc.)
        :param start: Cell-Objekt, von dem aus die Suche gestartet wird
        :return: Anzahl erreichbarer freier Felder (int)
        """
        debug("[flood_fill_space] Performing flood fill from start position {}.".format(start))  # for debugging purposes

        width = game_state["board"]["width"]  # Spielfeldbreite
        height = game_state["board"]["height"]  # Spielfeldhöhe
        snakes = [seg for s in game_state["board"]["snakes"] for seg in s["body"]]  # alle Schlangenteile auf dem Feld einsammeln
        blocked = {(s["x"], s["y"]) for s in snakes}  # alle belegten Felder als „blockiert“ merken

        # Füge Wände zu den blockierten Zellen hinzu
        for x in range(width):
            blocked.add((x, 0))  # obere Wand
            blocked.add((x, height - 1))  # untere Wand
        for y in range(height):
            blocked.add((0, y))  # linke Wand
            blocked.add((width - 1, y))  # rechte Wand

        visited = set()  # wo wir schon waren
        count = 0  # wie viele freie Felder gefunden
        queue = deque([(start.x, start.y)])  # Startpunkt in die Queue tun

        while queue:  # solange noch Positionen zum Prüfen
            (x, y) = queue.popleft()  # nächstes Feld herausnehmen

            if (x, y) in visited or (x, y) in blocked:  # wenn schon besucht oder blockiert, dann überspringen
                continue

            visited.add((x, y))  # dieses Feld jetzt als besucht markieren
            count += 1  # einen freien Platz gefunden

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # alle 4 Richtungen durchgehen (links, rechts, runter, hoch)
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:  # nur gültige, noch nicht besuchte Felder
                    queue.append((nx, ny))  # neue Position in die Queue stecken

        return count  # Anzahl freier Felder zurückgeben


    def simulate_future_space(game_state, head_pos, turns=2, visited=None, memo=None):
        """
        Simuliert rekursiv zukünftige Züge und bewertet den Platz in der Zukunft.

        :param game_state: Der aktuelle Spielzustand
        :param head_pos: Aktuelle Kopfposition als Cell
        :param turns: Wie viele Züge voraus simuliert werden sollen
        :param visited: Menge der bereits besuchten Zellen in dieser Rekursion (Cycle Prevention)
        :param memo: Zwischenspeicher für bereits berechnete (head_pos, turns)
        :return: Anzahl erreichbarer Felder nach N Zügen
        """
        if visited is None:
            visited = set()
        if memo is None:
            memo = {}

        key = (head_pos.x, head_pos.y, turns)
        if key in memo:
            return memo[key]

        if turns == 0:
            result = flood_fill_space(game_state, head_pos)
            memo[key] = result
            return result

        width = game_state["board"]["width"]
        height = game_state["board"]["height"]

        visited.add((head_pos.x, head_pos.y))

        best = -1
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = head_pos.x + dx, head_pos.y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                score = simulate_future_space(game_state, Cell(nx, ny), turns - 1, visited.copy(), memo)
                best = max(best, score)

        memo[key] = best if best != -1 else 0
        return memo[key]


    def is_food_contested(food_pos, game_state):
        """
        Prüft, ob ein Futterfeld direkt an einen gegnerischen Kopf angrenzt.

        :param food_pos: Position des Futters (Cell)
        :param game_state: Spielzustand
        :return: True wenn Futterfeld umkämpft ist, sonst False
        """
        for snake in game_state["board"]["snakes"]:  # alle Schlangen durchgehen
            head = snake["body"][0]
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # alle Richtungen rund um den Kopf
                if (head["x"] + dx, head["y"] + dy) == (food_pos.x, food_pos.y):
                    return True  # direkt angrenzend → sehr wahrscheinlich gegessen
        return False


    def apply_food_layer(heatmap, game_state, health):
        """
        Hebt die Attraktivität von Futterfeldern in der Heatmap hervor.

        Wenn die Schlange wenig Leben hat, wird Futter stärker gewichtet.

        :param heatmap: 2D-Heatmap
        :param game_state: Spielzustand
        :param health: Lebenspunkte der eigenen Schlange
        """
        debug("[apply_food_layer] Apply food weight, health = {}".format(health))  # for debugging purposes

        multiplier = 50 if health < 60 else 20  # wenn wenig Leben, dann Futter wichtiger machen
        for food in game_state["board"]["food"]:  # jedes Futterstück
            x, y = food["x"], food["y"]
            if is_food_contested(Cell(x, y), game_state):
                heatmap[x][y] += 5  # weiches Ignorieren: nur wenig Punkte, wenn umkämpft
            else:
                heatmap[x][y] += multiplier  # Feld wärmer machen (wichtiger)


    def apply_snake_penalty_layer(heatmap, game_state):
        """
        Bestraft Zellen, auf denen Schlangen liegen – inkl. Felder um gegnerische Köpfe.

        :param heatmap: Heatmap mit Punktwerten
        :param game_state: Aktueller Spielzustand
        """
        width = game_state["board"]["width"]
        height = game_state["board"]["height"]
        for snake in game_state["board"]["snakes"]:  # alle Schlangen durchgehen
            for segment in snake["body"]:  # jeden Teil der Schlange
                heatmap[segment["x"]][segment["y"]] -= 100  # hier will man nicht sein
            head = snake["body"][0]  # Kopf der Schlange
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Felder um den Kopf herum
                nx, ny = head["x"] + dx, head["y"] + dy
                if 0 <= nx < width and 0 <= ny < height:
                    heatmap[nx][ny] -= 50  # Risiko → Kopf könnte da hin


    def apply_wall_penalty(heatmap, game_state):
        """
        Gibt negativen Wert an Wandfelder und deren direkte Nachbarn.

        So wird vermieden, dass die Schlange sich zu sehr in Ecken drängt.

        :param heatmap: Spielfeldwerte
        :param game_state: Aktueller Zustand
        """
        width = game_state["board"]["width"]
        height = game_state["board"]["height"]
        for x in range(width):  # obere/untere Wand
            heatmap[x][0] -= 20
            heatmap[x][height - 1] -= 20
        for y in range(height):  # linke/rechte Wand
            heatmap[0][y] -= 20
            heatmap[width - 1][y] -= 20

        # zusätzliche Wandnähe leicht bestrafen
        for x in range(width):
            heatmap[x][1] -= 5
            heatmap[x][height - 2] -= 5
        for y in range(height):
            heatmap[1][y] -= 5
            heatmap[width - 2][y] -= 5


    def apply_flood_fill_layer(heatmap, game_state, my_head):
        """
        Nutzt flood_fill, um zu bewerten, wie viel Platz in jede Richtung zur Verfügung steht.

        Je mehr Platz in einer Richtung, desto attraktiver wird sie.

        :param heatmap: Heatmap
        :param game_state: Spielzustand
        :param my_head: Kopfposition (Cell)
        """
        width = game_state["board"]["width"]
        height = game_state["board"]["height"]
        for dx, dy, _ in [(-1, 0, "left"), (1, 0, "right"), (0, -1, "down"), (0, 1, "up")]:
            nx, ny = my_head.x + dx, my_head.y + dy
            if 0 <= nx < width and 0 <= ny < height:
                count = flood_fill_space(game_state, Cell(nx, ny))  # wie viel Platz da?
                heatmap[nx][ny] += min(count, 50)  # max 50 Punkte → größerer Einfluss als vorher


    def apply_tail_priority(heatmap, game_state):
        """
        Gibt dem eigenen Schwanz einen Bonus, weil er meist sicher ist.

        :param heatmap: Heatmap mit Punktwerten
        :param game_state: Aktueller Zustand
        """
        tail = game_state["you"]["body"][-1]  # eigener Schwanz (letztes Körperteil)
        if 0 <= tail["x"] < len(heatmap) and 0 <= tail["y"] < len(heatmap[0]):
            heatmap[tail["x"]][tail["y"]] += 20  # Bonus auf unser Schwanzfeld


    def apply_center_bonus(heatmap, game_state):
        """
        Erhöht die Punktzahl im Zentrum des Spielfelds leicht.

        Zentrale Positionen bieten in der Regel mehr Optionen für zukünftige Bewegungen.

        :param heatmap: Punktwerte des Spielfelds
        :param game_state: Spielzustand
        """
        width = game_state["board"]["width"]
        height = game_state["board"]["height"]
        cx, cy = width // 2, height // 2  # Mittelpunkt

        for x in range(width):
            for y in range(height):
                dist = abs(x - cx) + abs(y - cy)
                heatmap[x][y] += max(0, 10 - dist)  # je näher am Zentrum, desto besser (max +10)


    def build_heatmap(game_state, my_head, health):
        """
        Baut die gesamte Heatmap zusammen, basierend auf mehreren Faktoren.

        Die Heatmap wird später genutzt, um die beste Richtung zu wählen.

        :param game_state: Spielzustand
        :param my_head: Kopfposition der Schlange (Cell)
        :param health: Lebenspunkte (int)
        :return: Fertige 2D-Heatmap
        """
        debug("[build_heatmap] Building the heatmap...")  # for debugging purposes
        width = game_state["board"]["width"]
        height = game_state["board"]["height"]
        heatmap = [[0 for _ in range(height)] for _ in range(width)]  # leeres Spielfeld

        apply_food_layer(heatmap, game_state, health)  # Futter hinzufügen
        apply_snake_penalty_layer(heatmap, game_state)  # Schlangen als Strafe
        apply_wall_penalty(heatmap, game_state)  # Wände abwerten
        apply_flood_fill_layer(heatmap, game_state, my_head)  # Platz berechnen
        apply_tail_priority(heatmap, game_state)  # Schwanz bevorzugen
        apply_center_bonus(heatmap, game_state)  # Zentrum bevorzugen

        return heatmap




