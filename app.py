import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(page_title="UniAnalytics", layout="wide")
st.markdown("<h1 style='text-align: center;'>📊 UniAnalytics</h1>", unsafe_allow_html=True)

# Base de données locale (dans le répertoire de l'app)
DB_FILE = "unianalytics.db"

@st.cache_resource
def get_db():
    """Retourne une connexion à la base SQLite."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    """Crée les tables si elles n'existent pas."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etudiants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE,
            nom TEXT,
            prenom TEXT,
            filiere TEXT,
            niveau TEXT,
            date_inscription TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            etudiant_id INTEGER,
            matiere TEXT,
            note REAL,
            coeff INTEGER,
            FOREIGN KEY(etudiant_id) REFERENCES etudiants(id)
        )
    """)
    conn.commit()

# Initialisation au premier chargement
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================
def load_data(query, params=()):
    try:
        conn = get_db()
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erreur chargement : {e}")
        return pd.DataFrame()

def exec_query(query, params=()):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True, cursor.lastrowid
    except Exception as e:
        return False, str(e)

# ==========================================
# SIDEBAR
# ==========================================
menu = st.sidebar.radio("Navigation", ["📊 Tableau de bord", "👥 Gestion étudiants", "📝 Saisie notes", "📈 Visualisations"])

# ==========================================
# PAGE TABLEAU DE BORD
# ==========================================
if menu == "📊 Tableau de bord":
    st.subheader("Indicateurs clés")
    df_etud = load_data("SELECT * FROM etudiants")
    df_notes = load_data("SELECT * FROM notes")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("👨‍🎓 Étudiants", len(df_etud))
    if not df_notes.empty:
        moyenne = df_notes["note"].mean()
        col2.metric("📊 Moyenne générale", f"{moyenne:.2f}/20")
        col3.metric("📝 Nombre de notes", len(df_notes))
    else:
        col2.metric("📊 Moyenne générale", "N/A")
        col3.metric("📝 Nombre de notes", 0)

# ==========================================
# PAGE GESTION ÉTUDIANTS
# ==========================================
elif menu == "👥 Gestion étudiants":
    st.subheader("➕ Ajouter un étudiant")
    with st.form("add_student"):
        col1, col2 = st.columns(2)
        nom = col1.text_input("Nom")
        prenom = col2.text_input("Prénom")
        filiere = st.selectbox("Filière", ["Informatique", "Maths", "Physique", "Économie", "Droit"])
        niveau = st.selectbox("Niveau", ["L1", "L2", "L3", "M1", "M2"])
        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            if nom and prenom:
                # Génération d'un matricule simple
                date_str = datetime.now().strftime("%Y%m%d%H%M%S")
                matricule = f"STU_{date_str}"
                ok, msg = exec_query(
                    "INSERT INTO etudiants (matricule, nom, prenom, filiere, niveau, date_inscription) VALUES (?,?,?,?,?,?)",
                    (matricule, nom, prenom, filiere, niveau, datetime.now().date().isoformat())
                )
                if ok:
                    st.success(f"Étudiant {prenom} {nom} ajouté (matricule {matricule})")
                else:
                    st.error(f"Erreur : {msg}")
            else:
                st.warning("Veuillez remplir le nom et le prénom.")
    
    st.subheader("📋 Liste des étudiants")
    df_etud = load_data("SELECT id, matricule, nom, prenom, filiere, niveau FROM etudiants")
    if not df_etud.empty:
        st.dataframe(df_etud, use_container_width=True)
    else:
        st.info("Aucun étudiant pour le moment.")

# ==========================================
# PAGE SAISIE NOTES
# ==========================================
elif menu == "📝 Saisie notes":
    st.subheader("Ajouter une note")
    df_etud = load_data("SELECT id, nom, prenom FROM etudiants")
    if df_etud.empty:
        st.warning("Veuillez d'abord ajouter des étudiants.")
    else:
        etudiant_dict = {f"{row['nom']} {row['prenom']}": row['id'] for _, row in df_etud.iterrows()}
        with st.form("add_note"):
            etudiant = st.selectbox("Étudiant", list(etudiant_dict.keys()))
            matiere = st.text_input("Matière")
            note = st.number_input("Note /20", 0.0, 20.0, step=0.25)
            coeff = st.number_input("Coefficient", 1, 5, 1)
            if st.form_submit_button("Enregistrer"):
                if matiere:
                    ok, _ = exec_query(
                        "INSERT INTO notes (etudiant_id, matiere, note, coeff) VALUES (?,?,?,?)",
                        (etudiant_dict[etudiant], matiere, note, coeff)
                    )
                    if ok:
                        st.success("Note ajoutée")
                    else:
                        st.error("Erreur d'enregistrement")
                else:
                    st.warning("Veuillez entrer une matière")
    
    st.subheader("📊 Relevé des notes")
    df_notes = load_data("""
        SELECT e.nom, e.prenom, n.matiere, n.note, n.coeff
        FROM notes n
        JOIN etudiants e ON n.etudiant_id = e.id
        ORDER BY e.nom, n.matiere
    """)
    if not df_notes.empty:
        st.dataframe(df_notes, use_container_width=True)
    else:
        st.info("Aucune note saisie.")

# ==========================================
# PAGE VISUALISATIONS
# ==========================================
elif menu == "📈 Visualisations":
    st.subheader("Distribution des notes")
    df_notes = load_data("SELECT note FROM notes")
    if not df_notes.empty:
        fig = px.histogram(df_notes, x="note", nbins=20, title="Histogramme des notes")
        st.plotly_chart(fig, use_container_width=True)
        
        # Moyenne par matière
        df_matiere = load_data("SELECT matiere, AVG(note) as moyenne FROM notes GROUP BY matiere")
        if not df_matiere.empty:
            fig2 = px.bar(df_matiere, x="matiere", y="moyenne", title="Moyenne par matière")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Aucune note à afficher.")
