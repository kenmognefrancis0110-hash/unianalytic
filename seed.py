"""
seed.py — Génération de données fictives pour UniAnalytics Pro.
Appelé automatiquement au premier lancement si la base est vide.
"""

import random
from datetime import datetime, timedelta

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

from database import (
    load_data, add_etudiant, add_note, add_session_etude, count_table
)

# ──────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────

FILIERES = ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"]
NIVEAUX  = ["L1", "L2", "L3", "M1", "M2"]

MATIERES = {
    "Informatique":  ["Algorithmique", "Base de données", "Programmation Web", "Réseaux", "IA"],
    "Mathématiques": ["Algèbre", "Analyse", "Probabilités", "Statistiques", "Géométrie"],
    "Physique":      ["Mécanique", "Électromagnétisme", "Thermodynamique", "Optique", "Physique quantique"],
    "Économie":      ["Microéconomie", "Macroéconomie", "Économétrie", "Finance", "Comptabilité"],
    "Droit":         ["Droit civil", "Droit pénal", "Droit des contrats", "Droit administratif", "Histoire du droit"],
}

ANNEES_VALIDES = [f"{y}-{y+1}" for y in range(2021, 2026)]


# ──────────────────────────────────────────
# GÉNÉRATION
# ──────────────────────────────────────────

def _generate_etudiants(n: int = 25) -> list[tuple]:
    """Retourne une liste de tuples prêts à insérer dans `etudiants`."""
    rows = []
    year = datetime.now().year

    if FAKER_AVAILABLE:
        fake = Faker("fr_FR")
        for i in range(n):
            rows.append((
                f"CM{year}{i+1:03d}",
                fake.last_name(),
                fake.first_name(),
                random.choice(["M", "F"]),
                random.choice(FILIERES),
                random.choice(NIVEAUX),
                random.randint(18, 30),
                fake.date_between(start_date="-3y", end_date="today").isoformat(),
            ))
    else:
        for i in range(n):
            rows.append((
                f"CM{year}{i+1:03d}",
                f"Nom{i+1}",
                f"Prenom{i+1}",
                random.choice(["M", "F"]),
                random.choice(FILIERES),
                random.choice(NIVEAUX),
                random.randint(18, 30),
                datetime.now().date().isoformat(),
            ))
    return rows


def seed_if_empty(n: int = 25) -> bool:
    """
    Insère n étudiants fictifs si la base est vide.
    Retourne True si un peuplement a eu lieu, False sinon.
    """
    if count_table("etudiants") > 0:
        return False  # Déjà peuplé

    # ── Étudiants ──────────────────────────
    etudiants = _generate_etudiants(n)
    for e in etudiants:
        add_etudiant(*e)

    # ── Notes et sessions ──────────────────
    df_ids = load_data("SELECT id, filiere FROM etudiants")

    for _, row in df_ids.iterrows():
        etud_id = row["id"]
        filiere  = row["filiere"]
        mat_list = MATIERES.get(filiere, ["Matière1", "Matière2", "Matière3"])

        # 3 à 5 matières par étudiant
        for mat in random.sample(mat_list, min(len(mat_list), random.randint(3, 5))):
            add_note(
                etudiant_id      = etud_id,
                matiere          = mat,
                note             = round(random.uniform(6, 18), 2),
                coefficient      = random.randint(1, 3),
                session          = f"S{random.randint(1, 4)}",
                annee_academique = random.choice(ANNEES_VALIDES),
            )

        # 5 à 15 sessions d'étude par étudiant
        for _ in range(random.randint(5, 15)):
            date = datetime.now().date() - timedelta(days=random.randint(0, 365))
            add_session_etude(
                etudiant_id    = etud_id,
                date           = date.isoformat(),
                heures_etude   = round(random.uniform(0.5, 8), 1),
                heures_sommeil = round(random.uniform(5, 9), 1),
                humeur         = random.randint(1, 5),
            )

    return True


# ──────────────────────────────────────────
# CLI (usage direct : python seed.py)
# ──────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    init_db()
    done = seed_if_empty()
    if done:
        print("✅ Base peuplée avec 25 étudiants fictifs.")
    else:
        print("ℹ️  La base contient déjà des données — aucun peuplement effectué.")
