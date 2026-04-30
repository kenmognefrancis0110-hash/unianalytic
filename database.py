"""
database.py — Couche d'accès aux données SQLite pour UniAnalytics Pro.
Importer ce module dans app.py pour centraliser toutes les opérations DB.
"""

import sqlite3
import pandas as pd

DB_PATH = "unianalytics_pro.db"


# ──────────────────────────────────────────
# CONNEXION
# ──────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Crée et retourne une nouvelle connexion SQLite (thread-safe)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ──────────────────────────────────────────
# INITIALISATION
# ──────────────────────────────────────────

def init_db() -> None:
    """Crée toutes les tables si elles n'existent pas encore."""
    conn = get_connection()
    try:
        conn.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS etudiants (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule        TEXT    UNIQUE NOT NULL,
                nom              TEXT    NOT NULL,
                prenom           TEXT    NOT NULL,
                sexe             TEXT,
                filiere          TEXT,
                niveau           TEXT,
                age              INTEGER,
                date_inscription TEXT
            );

            CREATE TABLE IF NOT EXISTS notes (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                etudiant_id      INTEGER NOT NULL,
                matiere          TEXT    NOT NULL,
                note             REAL    NOT NULL,
                coefficient      INTEGER DEFAULT 1,
                session          TEXT,
                annee_academique TEXT,
                FOREIGN KEY(etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sessions_etude (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                etudiant_id     INTEGER NOT NULL,
                date            TEXT    NOT NULL,
                heures_etude    REAL,
                heures_sommeil  REAL,
                humeur          INTEGER,
                FOREIGN KEY(etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
    finally:
        conn.close()


def reset_db() -> None:
    """Supprime toutes les tables puis les recrée."""
    conn = get_connection()
    try:
        conn.executescript("""
            DROP TABLE IF EXISTS sessions_etude;
            DROP TABLE IF EXISTS notes;
            DROP TABLE IF EXISTS etudiants;
        """)
        conn.commit()
    finally:
        conn.close()
    init_db()


# ──────────────────────────────────────────
# LECTURE
# ──────────────────────────────────────────

def load_data(query: str, params: tuple = ()) -> pd.DataFrame:
    """Exécute un SELECT et retourne un DataFrame Pandas."""
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as exc:
        print(f"[DB][load_data] Erreur : {exc}")
        return pd.DataFrame()
    finally:
        conn.close()


def count_table(table: str) -> int:
    """Retourne le nombre de lignes d'une table."""
    df = load_data(f"SELECT COUNT(*) as nb FROM {table}")
    return int(df.iloc[0]["nb"]) if not df.empty else 0


# ──────────────────────────────────────────
# ÉCRITURE
# ──────────────────────────────────────────

def execute_query(query: str, params: tuple = ()):
    """
    Exécute une requête INSERT / UPDATE / DELETE.
    Retourne (True, lastrowid) en cas de succès, (False, message) sinon.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True, cursor.lastrowid
    except Exception as exc:
        return False, str(exc)
    finally:
        conn.close()


def delete_all(table: str) -> None:
    """Vide une table entière."""
    execute_query(f"DELETE FROM {table}")


# ──────────────────────────────────────────
# REQUÊTES MÉTIER
# ──────────────────────────────────────────

def get_etudiants() -> pd.DataFrame:
    return load_data("SELECT * FROM etudiants ORDER BY nom, prenom")


def get_notes_with_names() -> pd.DataFrame:
    return load_data("""
        SELECT e.nom, e.prenom, e.filiere, e.niveau,
               n.matiere, n.note, n.coefficient, n.session, n.annee_academique
        FROM notes n
        JOIN etudiants e ON n.etudiant_id = e.id
        ORDER BY e.nom, n.matiere
    """)


def get_notes_merged_with_etudiants() -> pd.DataFrame:
    """Joint notes + filière/niveau pour les analyses de performance."""
    return load_data("""
        SELECT n.*, e.filiere, e.niveau, e.sexe
        FROM notes n
        JOIN etudiants e ON n.etudiant_id = e.id
    """)


def get_sessions_merged_with_notes() -> pd.DataFrame:
    """Joint sessions d'étude + notes pour les analyses de corrélation."""
    return load_data("""
        SELECT n.note, n.matiere, n.coefficient,
               s.heures_etude, s.heures_sommeil, s.humeur, s.date
        FROM notes n
        JOIN sessions_etude s ON n.etudiant_id = s.etudiant_id
    """)


def add_etudiant(matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription):
    return execute_query("""
        INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription)
        VALUES (?,?,?,?,?,?,?,?)
    """, (matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription))


def add_note(etudiant_id, matiere, note, coefficient, session, annee_academique):
    return execute_query("""
        INSERT INTO notes (etudiant_id, matiere, note, coefficient, session, annee_academique)
        VALUES (?,?,?,?,?,?)
    """, (etudiant_id, matiere, note, coefficient, session, annee_academique))


def add_session_etude(etudiant_id, date, heures_etude, heures_sommeil, humeur):
    return execute_query("""
        INSERT INTO sessions_etude (etudiant_id, date, heures_etude, heures_sommeil, humeur)
        VALUES (?,?,?,?,?)
    """, (etudiant_id, date, heures_etude, heures_sommeil, humeur))
