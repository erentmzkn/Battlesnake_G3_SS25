# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006

import datetime

DEBUG = True  # Aktiviere Debug

def debug(msg):
    """
    Gibt eine Debug-Nachricht mit Zeitstempel aus, sofern DEBUG aktiviert ist.

    Diese Methode dient zur Laufzeitdiagnose und erleichtert das Nachverfolgen
    von Abläufen im Programm, insbesondere während der Entwicklung und Fehlersuche.

    :param msg: Die auszugebende Debug-Nachricht als Zeichenkette.
    """
    if DEBUG:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
