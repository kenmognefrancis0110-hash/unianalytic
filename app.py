import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os
import random

# Tentative d'import de Faker (optionnel)
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

st.set_page_config(page_title="UniAnalytics Pro", page_icon="📊", layout="wide")

# Style
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #1e3c72; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "/tmp/unianalytics_pro.db"
if not os.path.exists(DB_PATH):
    open(DB_PATH, 'w').close()  # crée le fichier vide

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    conn.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS etudiants (
            id_etudiant INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            sexe TEXT DEFAULT 'M',
            filiere TEXT NOT NULL,
            niveau TEXT NOT NULL,
            age INTEGER NOT NULL,
            annee_inscription INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sessions_etude (
            id_session INTEGER PRIMARY KEY AUTOINCREMENT,
            id_etudiant INTEGER REFERENCES etudiants(id_etudiant) ON DELETE CASCADE,
            date TEXT NOT NULL,
            heures_etude REAL NOT NULL,
            heures_sommeil REAL NOT NULL,
            humeur_index INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS resultats (
            id_resultat INTEGER PRIMARY KEY AUTOINCREMENT,
            id_etudiant INTEGER REFERENCES etudiants(id_etudiant) ON DELETE CASCADE,
            code_matiere TEXT NOT NULL,
            nom_matiere TEXT NOT NULL,
            note_examen REAL NOT NULL,
            taux_presence REAL NOT NULL,
            session TEXT DEFAULT 'S1',
            annee_academique TEXT
        );
        CREATE TABLE IF NOT EXISTS anciens_etudiants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_etudiant INTEGER REFERENCES etudiants(id_etudiant) ON DELETE CASCADE,
            cause TEXT NOT NULL,
            annee_depart INTEGER,
            commentaire TEXT
        );
    """)
    conn.commit()

def load_data(query, params=()):
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erreur SQL: {e}")
        return pd.DataFrame()

def execute_query(query, params=()):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        last_id = cur.lastrowid
        return True, last_id
    except Exception as e:
        return False, str(e)

def seed_database_if_empty():
    df = load_data("SELECT COUNT(*) as nb FROM etudiants")
    if df.empty or df.iloc[0]['nb'] == 0:
        with st.spinner("Génération de données de démonstration..."):
            try:
                if FAKER_AVAILABLE:
                    fake = Faker('fr_FR')
                    filieres = ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"]
                    niveaux = ["L1", "L2", "L3", "M1", "M2"]
                    for i in range(25):
                        matricule = f"CM{2024}{i+1:03d}"
                        nom = fake.last_name()
                        prenom = fake.first_name()
                        sexe = random.choice(["M", "F"])
                        filiere = random.choice(filieres)
                        niveau = random.choice(niveaux)
                        age = random.randint(18, 30)
                        annee = random.randint(2018, 2025)
                        execute_query(
                            "INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, annee_inscription) VALUES (?,?,?,?,?,?,?,?)",
                            (matricule, nom, prenom, sexe, filiere, niveau, age, annee)
                        )
                else:
                    for i in range(25):
                        execute_query(
                            "INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, annee_inscription) VALUES (?,?,?,?,?,?,?,?)",
                            (f"CM{2024}{i+1:03d}", f"Nom{i+1}", f"Prénom{i+1}", "M", "Informatique", "L3", 20, 2024)
                        )
                # Ajout de résultats et sessions
                df_ids = load_data("SELECT id_etudiant FROM etudiants")
                ids = df_ids['id_etudiant'].tolist()
                for _ in range(120):
                    id_etud = random.choice(ids)
                    date = datetime.now().date()
                    heures_etude = round(random.uniform(0.5, 10), 1)
                    heures_sommeil = round(random.uniform(4, 10), 1)
                    humeur = random.randint(1, 5)
                    execute_query(
                        "INSERT INTO sessions_etude (id_etudiant, date, heures_etude, heures_sommeil, humeur_index) VALUES (?,?,?,?,?)",
                        (id_etud, date, heures_etude, heures_sommeil, humeur)
                    )
                    code = f"INF{random.randint(100,999)}"
                    matiere = f"Matière{random.randint(1,10)}"
                    note = round(random.uniform(5, 18), 2)
                    presence = random.randint(50, 100)
                    session = f"S{random.randint(1,6)}"
                    annee_ac = f"202{random.randint(3,5)}-202{random.randint(4,6)}"
                    execute_query(
                        "INSERT INTO resultats (id_etudiant, code_matiere, nom_matiere, note_examen, taux_presence, session, annee_academique) VALUES (?,?,?,?,?,?,?)",
                        (id_etud, code, matiere, note, presence, session, annee_ac)
                    )
                st.success("✅ 25 étudiants fictifs ajoutés avec succès !")
                # On recharge la page pour prendre en compte les nouvelles données
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors du peuplement: {e}")

# Initialisation
init_db()
seed_database_if_empty()

# Sidebar
st.sidebar.title("🎓 UniAnalytics Pro")
menu = st.sidebar.radio("Navigation", ["📊 Tableau de bord", "🔍 Recherche", "➕ Collecte", "📈 Performances", "📉 Analyses avancées", "🗂️ Anciens"])

# --- Tableau de bord ---
if menu == "📊 Tableau de bord":
    st.title("Tableau de bord")
    df_etud = load_data("SELECT * FROM etudiants")
    df_res = load_data("SELECT * FROM resultats")
    if not df_etud.empty and not df_res.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Étudiants", len(df_etud))
        col2.metric("Moyenne générale", f"{df_res['note_examen'].mean():.2f}/20")
        col3.metric("Taux réussite", f"{(df_res['note_examen']>=10).mean()*100:.1f}%")
        fig = px.histogram(df_res, x="note_examen", nbins=20, title="Distribution des notes")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée. Utilisez la collecte pour ajouter des étudiants.")

# --- Recherche ---
elif menu == "🔍 Recherche":
    st.title("Recherche")
    search = st.text_input("Rechercher")
    df = load_data("SELECT * FROM etudiants")
    if search:
        mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        df = df[mask]
    st.dataframe(df)

# --- Collecte ---
elif menu == "➕ Collecte":
    st.title("Collecte de données")
    tab1, tab2, tab3 = st.tabs(["Étudiant", "Session", "Résultat"])
    with tab1:
        with st.form("add_etudiant"):
            nom = st.text_input("Nom")
            prenom = st.text_input("Prénom")
            filiere = st.selectbox("Filière", ["Informatique", "Maths", "Physique", "Economie", "Droit"])
            if st.form_submit_button("Ajouter"):
                df_max = load_data("SELECT MAX(id_etudiant) as max_id FROM etudiants")
                new_id = (df_max.iloc[0]['max_id'] or 0) + 1
                mat = f"CM{2024}{new_id:03d}"
                ok, _ = execute_query(
                    "INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, annee_inscription) VALUES (?,?,?,?,?,?,?,?)",
                    (mat, nom, prenom, "M", filiere, "L1", 20, 2024)
                )
                if ok:
                    st.success("Ajouté")
                    st.rerun()
                else:
                    st.error("Erreur")
    # (les autres onglets similaires, mais simplifiés pour la stabilité)
    st.info("Utilisez l'onglet Étudiant pour commencer.")

# --- Performances ---
elif menu == "📈 Performances":
    st.title("Performance par filière")
    df = load_data("""
        SELECT e.filiere, AVG(r.note_examen) as moyenne
        FROM etudiants e JOIN resultats r ON e.id_etudiant = r.id_etudiant
        GROUP BY e.filiere
    """)
    if not df.empty:
        st.bar_chart(df.set_index("filiere"))
    else:
        st.info("Aucune donnée")

# --- Analyses ---
elif menu == "📉 Analyses avancées":
    st.title("Corrélations")
    df = load_data("SELECT note_examen, taux_presence FROM resultats")
    if not df.empty:
        st.write("Relation note / présence")
        st.scatter_chart(df)

# --- Anciens ---
else:
    st.title("Anciens étudiants")
    df = load_data("SELECT * FROM anciens_etudiants")
    st.dataframe(df)
