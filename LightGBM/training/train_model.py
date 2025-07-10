# Gruppe 3 – Battlesnake Projekt (SS2025)
# Mitglieder:
# Eren Temizkan, 223201982
# Dominik Ide, 220200046
# Dogukan Karakoyun, 223202023
# Alexandra Holsten, 221200813
# Yuxiao Wu, 223200006

import os
from pathlib import Path
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from joblib import dump
import matplotlib.pyplot as plt
from imblearn.under_sampling import RandomUnderSampler

# Basis-Verzeichnis festlegen
base_dir = Path(__file__).resolve().parent.parent
csv_path = base_dir / "simple_synthetic_data.csv"  # Use our synthetic data
model_path = base_dir / "insane_model.pkl"  # Match the expected model name

# Erwartete Spaltennamen
expected_columns = [
    "head_x",
    "head_y",
    "health",
    "width",
    "height",
    "closest_food_distance",
    "space",
    "future_space",
    "safe_up",
    "safe_down",
    "safe_left",
    "safe_right",
    "open_area_up",
    "open_area_down",
    "open_area_left",
    "open_area_right",
    "distance_to_nearest_wall",
    "tail_distance",
    "closest_food_is_safe",
    "is_biggest_snake",
    "needs_food",
    "closest_enemy_head_dist",
    "enemy_head_is_adjacent",
    "enemies_within_2",
    "kill_up",
    "kill_down",
    "kill_left",
    "kill_right",
    "dir_up",
    "dir_down",
    "dir_left",
    "dir_right",
    "center_bonus",
    "food_contest_count",
    "num_snakes",
    "path_distance_to_food",  # New column
    "move"  # Zielspalte
]

# Überprüfe, ob die CSV-Datei existiert
if not csv_path.exists():
    print(
        "[INFO] 'training_data.csv' nicht gefunden – leere Datei wird erstellt."
    )
    df = pd.DataFrame(columns=pd.Index(expected_columns))
    df.to_csv(csv_path, index=False)
    print("[INFO] Leere Datei erstellt. Bitte zuerst Trainingsdaten sammeln.")
    exit()

# CSV-Datei laden (mit Header-Schutz)
print("[DEBUG] Lade Trainingsdaten...")
try:
    data = pd.read_csv(csv_path)
except Exception as e:
    print(f"[FEHLER] CSV konnte nicht geladen werden: {e}")
    exit()

# Falls die 'move' Spalte nicht gefunden wird, setzen wir automatisch die Spaltenüberschriften
if "move" not in data.columns:
    print(
        "[INFO] Keine Spaltenüberschriften gefunden — werden automatisch gesetzt."
    )
    data = pd.read_csv(csv_path, names=expected_columns)

# Duplikate entfernen
data.drop_duplicates(inplace=True)

if data.empty:
    print("[WARNUNG] Datei ist leer –> Spiele erstmal ein paar Spiele.")
    exit()

print(f"[DEBUG] Zeilen geladen nach Duplikat-Filter: {len(data)}")
print(f"[DEBUG] Spalten: {list(data.columns)}")

# Features und Ziel trennen
if "move" not in data.columns:
    print("[FEHLER] Spalte 'move' fehlt – Trainingsdaten ungültig.")
    exit()

feature_columns = [
    "head_x", "head_y", "health", "width", "height", "closest_food_distance",
    "space", "future_space", "safe_up", "safe_down", "safe_left", "safe_right",
    "open_area_up", "open_area_down", "open_area_left", "open_area_right",
    "distance_to_nearest_wall", "tail_distance", "closest_food_is_safe",
    "is_biggest_snake", "needs_food", "closest_enemy_head_dist",
    "enemy_head_is_adjacent", "enemies_within_2", "kill_up", "kill_down",
    "kill_left", "kill_right", "dir_up", "dir_down", "dir_left", "dir_right",
    "center_bonus", "food_contest_count", "num_snakes", "path_distance_to_food"
]

X = data[feature_columns]
y = data["move"]

# Optional: Überprüfen der Klassenverteilung
print("\nZüge-Verteilung:")
print(y.value_counts())

# Führe Undersampling durch, um die Daten auszubalancieren
print("\n[DEBUG] Führe RandomUnderSampling durch...")
rus = RandomUnderSampler(random_state=42)
try:
    resampled_data = rus.fit_resample(X, y)
    X, y = resampled_data[0], resampled_data[1]
except ValueError as ve:
    print(f"[FEHLER] Undersampling fehlgeschlagen: {ve}")
    exit()

print(f"[DEBUG] Nach Resampling: {len(X)} Beispiele")

# Features normalisieren
print("[DEBUG] Skaliere Features mit StandardScaler...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train-Test-Split
print("[DEBUG] Splitte in Training/Test...")
X_train, X_test, y_train, y_test = train_test_split(X_scaled,
                                                    y,
                                                    test_size=0.1,
                                                    random_state=66)

print(f"\n[DEBUG] Training: {len(X_train)} | Test: {len(X_test)}")

# Modell trainieren
print("\n[INFO] Training läuft...")
clf = LGBMClassifier(n_estimators=400,
                     max_depth=25,
                     class_weight="balanced",
                     random_state=42)
clf.fit(X_train, y_train)
print("[INFO] Training abgeschlossen!\n")

# Modell bewerten
print("[INFO] Klassifikationsübersicht:")
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# Feature-Wichtigkeit plotten
print("[DEBUG] Zeige Featurewichtigkeit...")
importances = clf.feature_importances_
feature_names = X.columns.tolist()

plt.figure(figsize=(10, 8))
plt.barh(feature_names, importances)
plt.xlabel("Wichtigkeit")
plt.title("Featurewichtigkeit des Modells")
plt.tight_layout()

plot_path = base_dir / "feature_importance.png"
plt.savefig(plot_path)
print(f"[INFO] Featurewichtigkeit gespeichert als '{plot_path.name}'.")

# Modell speichern
dump(clf, model_path)
print(f"[INFO] Modell gespeichert als: '{model_path}'")
