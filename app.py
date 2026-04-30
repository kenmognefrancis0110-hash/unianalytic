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

# ==========================================
# CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="UniAnalytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé (facultatif)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #1e3c72; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# BASE DE DONNÉES (dans /tmp pour Streamlit Cloud)
# ==========================================
DB_PATH = "/tmp/unianalytics_pro.db"

# Création du fichier DB s'il n'existe pas
if not os.path.exists(DB_PATH):
    open(DB_PATH, 'w').close()

@st.cache_resource
def get_connection():
    """Retourne une connexion SQLite mise en cache."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Initialise les tables si elles n'existent pas."""
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
    """Exécute une requête SELECT et retourne un DataFrame."""
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erreur SQL : {e}")
        return pd.DataFrame()

def execute_query(query, params=()):
    """Exécute une requête d'écriture (INSERT, UPDATE, DELETE)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return True, cur.lastrowid
    except Exception as e:
        return False, str(e)

# ==========================================
# PEUPLEMENT AUTOMATIQUE SI BASE VIDE
# ==========================================
def seed_database_if_empty():
    """Ajoute 25 étudiants fictifs et des données associées si la table est vide."""
    df_check = load_data("SELECT COUNT(*) as nb FROM etudiants")
    if df_check.empty or df_check.iloc[0]['nb'] == 0:
        with st.spinner("Génération de données de démonstration..."):
            try:
                # Génération des étudiants
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
                
                # Récupération des IDs des étudiants créés
                df_ids = load_data("SELECT id_etudiant FROM etudiants")
                ids = df_ids['id_etudiant'].tolist()
                
                # Ajout de sessions d'étude et résultats (120 entrées)
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
                    
                    code_matiere = f"INF{random.randint(100, 999)}"
                    nom_matiere = f"Matière {random.randint(1, 10)}"
                    note = round(random.uniform(5, 18), 2)
                    presence = random.randint(50, 100)
                    session = f"S{random.randint(1, 6)}"
                    annee_acad = f"{random.randint(2020, 2025)}-{random.randint(2021, 2026)}"
                    execute_query(
                        "INSERT INTO resultats (id_etudiant, code_matiere, nom_matiere, note_examen, taux_presence, session, annee_academique) VALUES (?,?,?,?,?,?,?)",
                        (id_etud, code_matiere, nom_matiere, note, presence, session, annee_acad)
                    )
                
                st.success("✅ 25 étudiants fictifs ajoutés avec succès !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors du peuplement : {e}")

# ==========================================
# INITIALISATION DE L'APPLICATION
# ==========================================
init_db()
seed_database_if_empty()

# ==========================================
# SIDEBAR DE NAVIGATION
# ==========================================
st.sidebar.title("🎓 UniAnalytics Pro")
menu = st.sidebar.radio(
    "Navigation",
    ["📊 Tableau de bord", "🔍 Recherche", "➕ Collecte", "📈 Performances", "📉 Analyses avancées", "🗂️ Anciens"]
)
st.sidebar.markdown("---")
st.sidebar.caption("v2.0 · Données fictives intégrées")

# ==========================================
# PAGE 1 : TABLEAU DE BORD
# ==========================================
if menu == "📊 Tableau de bord":
    st.title("📊 Tableau de bord stratégique")
    df_etud = load_data("SELECT * FROM etudiants")
    df_res = load_data("SELECT * FROM resultats")
    df_sess = load_data("SELECT * FROM sessions_etude")
    
    if not df_etud.empty and not df_res.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👨‍🎓 Étudiants", len(df_etud))
        col2.metric("📊 Moyenne générale", f"{df_res['note_examen'].mean():.2f}/20")
        col3.metric("✅ Taux réussite", f"{(df_res['note_examen'] >= 10).mean() * 100:.1f}%")
        col4.metric("📈 Sessions/étudiant", f"{len(df_sess) / len(df_etud):.1f}")
        
        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            fig = px.histogram(df_res, x="note_examen", nbins=20, title="Distribution des notes")
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            top_fil = df_etud['filiere'].value_counts().reset_index()
            top_fil.columns = ['Filière', 'Effectif']
            fig = px.pie(top_fil, values='Effectif', names='Filière', title="Répartition par filière")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible. Commencez par ajouter des étudiants via l'onglet 'Collecte'.")

# ==========================================
# PAGE 2 : RECHERCHE
# ==========================================
elif menu == "🔍 Recherche":
    st.title("🔍 Recherche d'étudiant")
    search_term = st.text_input("Rechercher par nom, prénom ou matricule")
    df = load_data("SELECT * FROM etudiants")
    if not df.empty:
        if search_term:
            mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
            df = df[mask]
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Aucun étudiant en base.")

# ==========================================
# PAGE 3 : COLLECTE DE DONNÉES
# ==========================================
elif menu == "➕ Collecte":
    st.title("➕ Collecte de données")
    df_etud = load_data("SELECT id_etudiant, matricule, nom, prenom FROM etudiants")
    
    tab1, tab2, tab3 = st.tabs(["👤 Nouvel étudiant", "📖 Session d'étude", "📝 Résultat examen"])
    
    # Onglet 1 : Ajouter un étudiant
    with tab1:
        with st.form("form_etudiant", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nom")
            prenom = col2.text_input("Prénom")
            sexe = col1.selectbox("Sexe", ["M", "F"])
            filiere = col2.selectbox("Filière", ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"])
            niveau = col1.selectbox("Niveau", ["L1", "L2", "L3", "M1", "M2"])
            age = col2.number_input("Âge", min_value=17, max_value=60, value=20)
            annee = st.number_input("Année d'inscription", min_value=2000, max_value=2030, value=datetime.now().year)
            if st.form_submit_button("Enregistrer"):
                df_max = load_data("SELECT MAX(id_etudiant) as max_id FROM etudiants")
                new_id = (df_max.iloc[0]['max_id'] or 0) + 1
                matricule = f"CM{2024}{new_id:03d}"
                ok, msg = execute_query(
                    "INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, annee_inscription) VALUES (?,?,?,?,?,?,?,?)",
                    (matricule, nom, prenom, sexe, filiere, niveau, age, annee)
                )
                if ok:
                    st.success(f"Étudiant {prenom} {nom} ajouté (matricule {matricule})")
                    st.rerun()
                else:
                    st.error(f"Erreur : {msg}")
    
    if not df_etud.empty:
        etud_dict = {f"{row['matricule']} - {row['prenom']} {row['nom']}": row['id_etudiant'] for _, row in df_etud.iterrows()}
        
        # Onglet 2 : Session d'étude
        with tab2:
            with st.form("form_session", clear_on_submit=True):
                etud = st.selectbox("Étudiant", list(etud_dict.keys()))
                date = st.date_input("Date")
                heures = st.number_input("Heures d'étude", 0.0, 24.0, 2.0, 0.5)
                sommeil = st.number_input("Heures de sommeil", 0.0, 24.0, 7.0, 0.5)
                humeur = st.slider("Humeur (1=très mauvais, 5=excellent)", 1, 5, 3)
                if st.form_submit_button("Enregistrer"):
                    ok, msg = execute_query(
                        "INSERT INTO sessions_etude (id_etudiant, date, heures_etude, heures_sommeil, humeur_index) VALUES (?,?,?,?,?)",
                        (etud_dict[etud], date, heures, sommeil, humeur)
                    )
                    if ok:
                        st.success("Session enregistrée")
                        st.rerun()
                    else:
                        st.error(msg)
        
        # Onglet 3 : Résultat examen
        with tab3:
            with st.form("form_resultat", clear_on_submit=True):
                etud_r = st.selectbox("Étudiant", list(etud_dict.keys()), key="r")
                code = st.text_input("Code matière (ex: INF101)")
                matiere = st.text_input("Nom matière")
                note = st.number_input("Note /20", 0.0, 20.0, 10.0, 0.25)
                presence = st.number_input("Taux de présence (%)", 0, 100, 100)
                session = st.selectbox("Session", ["S1", "S2", "S3", "S4", "S5", "S6"])
                annee_ac = st.text_input("Année académique (ex: 2024-2025)", f"{datetime.now().year}-{datetime.now().year+1}")
                if st.form_submit_button("Enregistrer"):
                    ok, msg = execute_query(
                        "INSERT INTO resultats (id_etudiant, code_matiere, nom_matiere, note_examen, taux_presence, session, annee_academique) VALUES (?,?,?,?,?,?,?)",
                        (etud_dict[etud_r], code, matiere, note, presence, session, annee_ac)
                    )
                    if ok:
                        st.success("Résultat enregistré")
                        st.rerun()
                    else:
                        st.error(msg)
    else:
        st.warning("⚠️ Aucun étudiant enregistré. Commencez par en ajouter un dans l'onglet 'Nouvel étudiant'.")

# ==========================================
# PAGE 4 : PERFORMANCES
# ==========================================
elif menu == "📈 Performances":
    st.title("📈 Performance par filière")
    df = load_data("""
        SELECT e.filiere, 
               COUNT(DISTINCT e.id_etudiant) as nb,
               ROUND(AVG(r.note_examen),2) as moyenne,
               ROUND((SUM(CASE WHEN r.note_examen>=10 THEN 1 ELSE 0 END)*100.0/COUNT(r.note_examen)),1) as taux_reussite
        FROM etudiants e
        JOIN resultats r ON e.id_etudiant = r.id_etudiant
        GROUP BY e.filiere
        ORDER BY moyenne DESC
    """)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        fig = px.bar(df, x="filiere", y="moyenne", color="taux_reussite", title="Moyenne par filière")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune performance à afficher. Ajoutez des résultats d'examen.")

# ==========================================
# PAGE 5 : ANALYSES AVANCÉES
# ==========================================
elif menu == "📉 Analyses avancées":
    st.title("📉 Analyses avancées")
    df_res = load_data("SELECT * FROM resultats")
    df_sess = load_data("SELECT * FROM sessions_etude")
    if not df_res.empty and not df_sess.empty:
        merged = pd.merge(df_res, df_sess, on="id_etudiant", how="inner")
        if not merged.empty:
            # Matrice de corrélation
            corr_data = merged[["note_examen", "taux_presence", "heures_etude", "heures_sommeil", "humeur_index"]].corr()
            fig1 = px.imshow(corr_data, text_auto=True, aspect="auto", title="Matrice de corrélation", color_continuous_scale="RdBu")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Nuage de points note vs présence
            fig2 = px.scatter(merged, x="taux_presence", y="note_examen", color="humeur_index", size="heures_etude",
                              title="Note vs présence (taille = heures d'étude)", labels={"taux_presence": "Présence (%)"})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Données insuffisantes pour les analyses (fusion vide).")
    else:
        st.info("Ajoutez des sessions d'étude et des résultats pour voir les corrélations.")

# ==========================================
# PAGE 6 : ANCIENS ÉTUDIANTS
# ==========================================
elif menu == "🗂️ Anciens":
    st.title("🗂️ Anciens étudiants")
    df_anciens = load_data("""
        SELECT ae.id, e.matricule, e.nom, e.prenom, e.filiere, ae.cause, ae.annee_depart, ae.commentaire
        FROM anciens_etudiants ae
        JOIN etudiants e ON ae.id_etudiant = e.id_etudiant
    """)
    if not df_anciens.empty:
        st.dataframe(df_anciens, use_container_width=True)
    else:
        st.info("Aucun ancien étudiant enregistré pour le moment.")
