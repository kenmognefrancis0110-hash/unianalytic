import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os

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
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS moderne (sans sélecteurs obsolètes)
st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton > button {
        background-color: #1e3c72;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #2a4a8a;
        transform: translateY(-2px);
    }
    h1, h2, h3 {
        color: #1e3c72;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BASE DE DONNÉES (connexions séparées)
# ==========================================
DB_PATH = "unianalytics_pro.db"

def get_connection():
    """Retourne une nouvelle connexion SQLite (pas de cache pour éviter les threads)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS etudiants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            sexe TEXT,
            filiere TEXT,
            niveau TEXT,
            age INTEGER,
            date_inscription TEXT
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            etudiant_id INTEGER NOT NULL,
            matiere TEXT NOT NULL,
            note REAL NOT NULL,
            coefficient INTEGER DEFAULT 1,
            session TEXT,
            annee_academique TEXT,
            FOREIGN KEY(etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS sessions_etude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            etudiant_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            heures_etude REAL,
            heures_sommeil REAL,
            humeur INTEGER,
            FOREIGN KEY(etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()

def load_data(query, params=()):
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"Erreur SQL : {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        success = True
        msg = last_id
    except Exception as e:
        success = False
        msg = str(e)
    finally:
        conn.close()
    return success, msg

# ==========================================
# PEUPLEMENT AUTOMATIQUE SANS BOUCLE INFINIE
# ==========================================
def seed_database():
    """Remplit la base avec 25 étudiants fictifs si elle est vide."""
    # Vérification rapide
    df_check = load_data("SELECT COUNT(*) as nb FROM etudiants")
    if not df_check.empty and df_check.iloc[0]['nb'] > 0:
        return  # déjà peuplé

    with st.spinner("🎲 Génération de 25 étudiants fictifs..."):
        filieres = ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"]
        niveaux = ["L1", "L2", "L3", "M1", "M2"]
        matieres = {
            "Informatique": ["Algorithmique", "BD", "Programmation Web", "Réseaux", "IA"],
            "Mathématiques": ["Algèbre", "Analyse", "Probabilités", "Statistiques", "Géométrie"],
            "Physique": ["Mécanique", "Électromagnétisme", "Thermodynamique", "Optique", "Quantique"],
            "Économie": ["Micro", "Macro", "Économétrie", "Finance", "Comptabilité"],
            "Droit": ["Civil", "Pénal", "Contrats", "Administratif", "Histoire"]
        }
        # Génération des étudiants
        etudiants = []
        if FAKER_AVAILABLE:
            fake = Faker('fr_FR')
            for i in range(25):
                matricule = f"CM{datetime.now().year}{i+1:04d}"
                nom = fake.last_name()
                prenom = fake.first_name()
                sexe = random.choice(["M", "F"])
                filiere = random.choice(filieres)
                niveau = random.choice(niveaux)
                age = random.randint(18, 30)
                date_insc = fake.date_between(start_date='-3y', end_date='today').isoformat()
                etudiants.append((matricule, nom, prenom, sexe, filiere, niveau, age, date_insc))
        else:
            for i in range(25):
                matricule = f"CM{datetime.now().year}{i+1:04d}"
                nom = f"Nom{i+1}"
                prenom = f"Prenom{i+1}"
                sexe = random.choice(["M", "F"])
                filiere = random.choice(filieres)
                niveau = random.choice(niveaux)
                age = random.randint(18, 30)
                date_insc = datetime.now().date().isoformat()
                etudiants.append((matricule, nom, prenom, sexe, filiere, niveau, age, date_insc))
        
        for e in etudiants:
            execute_query("""
                INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription)
                VALUES (?,?,?,?,?,?,?,?)
            """, e)
        
        # Récupérer les IDs
        df_ids = load_data("SELECT id, filiere FROM etudiants")
        ids_filieres = df_ids.to_dict('records')
        
        # Ajout des notes et sessions
        for etud in ids_filieres:
            id_et = etud['id']
            fil = etud['filiere']
            mat_list = matieres.get(fil, ["Matière1", "Matière2"])
            for mat in random.sample(mat_list, min(len(mat_list), random.randint(3, 5))):
                note = round(random.uniform(6, 18), 2)
                coeff = random.randint(1, 3)
                session = f"S{random.randint(1, 4)}"
                # Année académique cohérente : ex 2023-2024
                start_annee = random.randint(2021, 2024)
                annee = f"{start_annee}-{start_annee+1}"
                execute_query("""
                    INSERT INTO notes (etudiant_id, matiere, note, coefficient, session, annee_academique)
                    VALUES (?,?,?,?,?,?)
                """, (id_et, mat, note, coeff, session, annee))
            
            nb_sessions = random.randint(5, 12)
            for _ in range(nb_sessions):
                date = datetime.now().date() - timedelta(days=random.randint(0, 300))
                heures_etude = round(random.uniform(0.5, 8), 1)
                heures_sommeil = round(random.uniform(5, 9), 1)
                humeur = random.randint(1, 5)
                execute_query("""
                    INSERT INTO sessions_etude (etudiant_id, date, heures_etude, heures_sommeil, humeur)
                    VALUES (?,?,?,?,?)
                """, (id_et, date.isoformat(), heures_etude, heures_sommeil, humeur))

    st.success("✅ 25 étudiants fictifs ajoutés !")
    # On demande à l'utilisateur de rafraîchir manuellement
    st.info("Cliquez sur 'R' ou rechargez la page pour voir les données.")
    st.stop()  # Arrête l'exécution ici pour éviter un appel récursif

# ==========================================
# INITIALISATION
# ==========================================
if not os.path.exists(DB_PATH):
    init_db()
else:
    init_db()  # garantit les tables existent

# Peuplement (s'arrête après insertion)
if "seeded" not in st.session_state:
    st.session_state.seeded = True
    seed_database()  # s'il y a des données, ne fait rien ; sinon insère et stop

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("🎓 UniAnalytics Pro")
menu = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "👥 Étudiants", "📝 Notes", "📈 Performances", "🔬 Analyses", "⚙️ Admin"]
)

# ==========================================
# PAGE DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 Tableau de bord")
    df_etud = load_data("SELECT * FROM etudiants")
    df_notes = load_data("SELECT * FROM notes")
    df_sessions = load_data("SELECT * FROM sessions_etude")

    if df_etud.empty:
        st.info("Aucune donnée. Rendez-vous dans Admin pour générer des données fictives.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👨‍🎓 Étudiants", len(df_etud))
        if not df_notes.empty:
            moyenne = df_notes['note'].mean()
            taux = (df_notes['note'] >= 10).mean() * 100
            col2.metric("📊 Moyenne", f"{moyenne:.2f}/20")
            col3.metric("✅ Réussite", f"{taux:.1f}%")
        else:
            col2.metric("📊 Moyenne", "N/A")
            col3.metric("✅ Réussite", "N/A")
        col4.metric("📖 Sessions", len(df_sessions))

        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            if not df_notes.empty:
                fig = px.histogram(df_notes, x="note", nbins=20, title="Distribution des notes")
                st.plotly_chart(fig, use_container_width=True)
        with colB:
            if not df_etud.empty:
                rep = df_etud['filiere'].value_counts().reset_index()
                rep.columns = ['Filière', 'Effectif']
                fig = px.pie(rep, values='Effectif', names='Filière', title="Répartition par filière")
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PAGE ÉTUDIANTS
# ==========================================
elif menu == "👥 Étudiants":
    st.title("👥 Gestion des étudiants")
    tab_list, tab_add = st.tabs(["📋 Liste", "➕ Ajouter"])
    with tab_list:
        search = st.text_input("Rechercher")
        df = load_data("SELECT * FROM etudiants")
        if not df.empty:
            if search:
                mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
                df = df[mask]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun étudiant.")
    with tab_add:
        with st.form("add_student"):
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nom")
            prenom = col2.text_input("Prénom")
            filiere = col1.selectbox("Filière", ["Informatique", "Maths", "Physique", "Économie", "Droit"])
            niveau = col2.selectbox("Niveau", ["L1", "L2", "L3", "M1", "M2"])
            age = col1.number_input("Âge", 17, 60, 20)
            if st.form_submit_button("Ajouter"):
                if nom and prenom:
                    max_id = load_data("SELECT MAX(id) as max FROM etudiants")
                    new_id = (max_id.iloc[0]['max'] or 0) + 1
                    mat = f"STU{datetime.now().year}{new_id:04d}"
                    ok, _ = execute_query(
                        "INSERT INTO etudiants (matricule, nom, prenom, filiere, niveau, age, date_inscription) VALUES (?,?,?,?,?,?,?)",
                        (mat, nom, prenom, filiere, niveau, age, datetime.now().date().isoformat())
                    )
                    if ok:
                        st.success("Ajouté")
                        st.rerun()
                    else:
                        st.error("Erreur")
                else:
                    st.warning("Nom et prénom requis")

# ==========================================
# PAGE NOTES
# ==========================================
elif menu == "📝 Notes":
    st.title("📝 Notes")
    tab_add, tab_view = st.tabs(["✏️ Ajouter", "📊 Voir"])
    df_et = load_data("SELECT id, nom, prenom FROM etudiants")
    if df_et.empty:
        st.warning("Ajoutez des étudiants d'abord.")
    else:
        et_dict = {f"{r['nom']} {r['prenom']}": r['id'] for _, r in df_et.iterrows()}
        with tab_add:
            with st.form("add_note"):
                etu = st.selectbox("Étudiant", list(et_dict.keys()))
                mat = st.text_input("Matière")
                note = st.number_input("Note", 0.0, 20.0, 10.0, 0.25)
                coeff = st.number_input("Coefficient", 1, 5, 1)
                session = st.selectbox("Session", ["S1","S2","S3","S4"])
                annee = st.text_input("Année académique", f"{datetime.now().year}-{datetime.now().year+1}")
                if st.form_submit_button("Enregistrer"):
                    if mat:
                        ok, _ = execute_query(
                            "INSERT INTO notes (etudiant_id, matiere, note, coefficient, session, annee_academique) VALUES (?,?,?,?,?,?)",
                            (et_dict[etu], mat, note, coeff, session, annee)
                        )
                        if ok:
                            st.success("Note ajoutée")
                        else:
                            st.error("Erreur")
        with tab_view:
            df_notes = load_data("""
                SELECT e.nom, e.prenom, n.matiere, n.note, n.coefficient, n.session
                FROM notes n JOIN etudiants e ON n.etudiant_id = e.id
            """)
            if not df_notes.empty:
                st.dataframe(df_notes, use_container_width=True)

# ==========================================
# PAGE PERFORMANCES
# ==========================================
elif menu == "📈 Performances":
    st.title("📈 Performances")
    df = load_data("""
        SELECT e.filiere, AVG(n.note) as moyenne
        FROM notes n JOIN etudiants e ON n.etudiant_id = e.id
        GROUP BY e.filiere
    """)
    if not df.empty:
        fig = px.bar(df, x="filiere", y="moyenne", title="Moyenne par filière")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée")

# ==========================================
# PAGE ANALYSES
# ==========================================
elif menu == "🔬 Analyses":
    st.title("🔬 Corrélations")
    df_notes = load_data("SELECT * FROM notes")
    df_sess = load_data("SELECT * FROM sessions_etude")
    if not df_notes.empty and not df_sess.empty:
        merged = pd.merge(df_notes, df_sess, left_on="etudiant_id", right_on="etudiant_id", how="inner")
        if not merged.empty:
            fig = px.scatter(merged, x="heures_etude", y="note", trendline="ols",
                             title="Heures d'étude vs Note")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Données insuffisantes")

# ==========================================
# PAGE ADMIN
# ==========================================
elif menu == "⚙️ Admin":
    st.title("⚙️ Administration")
    if st.button("🔄 Régénérer les 25 étudiants fictifs"):
        # Supprimer tout
        execute_query("DELETE FROM etudiants")
        execute_query("DELETE FROM notes")
        execute_query("DELETE FROM sessions_etude")
        if "seeded" in st.session_state:
            del st.session_state.seeded
        st.success("Base vidée. Rechargement en cours...")
        st.rerun()
