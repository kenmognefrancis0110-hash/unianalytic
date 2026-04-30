import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os

# Tentative d'import de Faker (optionnel, sinon données mock)
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

# Style CSS personnalisé pour un look professionnel
st.markdown("""
<style>
    .main { background-color: #f5f7fb; }
    .stApp { background: linear-gradient(135deg, #f5f7fb 0%, #e9edf2 100%); }
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #1e3c72;
    }
    h1, h2, h3 { color: #1e3c72; font-weight: 600; }
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
    hr { margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BASE DE DONNÉES
# ==========================================
DB_PATH = "unianalytics_pro.db"

def get_connection():
    """Crée une nouvelle connexion SQLite à chaque appel (thread-safe)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Crée les tables si elles n'existent pas."""
    conn = get_connection()
    try:
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
    finally:
        conn.close()

def load_data(query, params=()):
    """Charge des données depuis SQLite."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"❌ Erreur de chargement : {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def execute_query(query, params=()):
    """Exécute une requête d'écriture."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True, cursor.lastrowid
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ==========================================
# PEUPLEMENT AUTOMATIQUE AVEC 25 ÉTUDIANTS
# ==========================================
def seed_database():
    """Remplit la base avec 25 étudiants fictifs, notes et sessions d'étude."""
    df_check = load_data("SELECT COUNT(*) as nb FROM etudiants")
    if not df_check.empty and df_check.iloc[0]['nb'] > 0:
        return  # Base déjà peuplée

    filieres = ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"]
    niveaux = ["L1", "L2", "L3", "M1", "M2"]
    matieres = {
        "Informatique": ["Algorithmique", "Base de données", "Programmation Web", "Réseaux", "IA"],
        "Mathématiques": ["Algèbre", "Analyse", "Probabilités", "Statistiques", "Géométrie"],
        "Physique": ["Mécanique", "Électromagnétisme", "Thermodynamique", "Optique", "Physique quantique"],
        "Économie": ["Microéconomie", "Macroéconomie", "Économétrie", "Finance", "Comptabilité"],
        "Droit": ["Droit civil", "Droit pénal", "Droit des contrats", "Droit administratif", "Histoire du droit"]
    }

    etudiants = []
    if FAKER_AVAILABLE:
        fake = Faker('fr_FR')
        for i in range(25):
            matricule = f"CM{datetime.now().year}{i+1:03d}"
            nom = fake.last_name()
            prenom = fake.first_name()
            sexe = random.choice(["M", "F"])
            filiere = random.choice(filieres)
            niveau = random.choice(niveaux)
            age = random.randint(18, 30)
            date_inscription = fake.date_between(start_date='-3y', end_date='today').isoformat()
            etudiants.append((matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription))
    else:
        for i in range(25):
            matricule = f"CM{datetime.now().year}{i+1:03d}"
            nom = f"Nom{i+1}"
            prenom = f"Prenom{i+1}"
            sexe = random.choice(["M", "F"])
            filiere = random.choice(filieres)
            niveau = random.choice(niveaux)
            age = random.randint(18, 30)
            date_inscription = datetime.now().date().isoformat()
            etudiants.append((matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription))

    with st.spinner("🎲 Génération de 25 étudiants fictifs..."):
        for e in etudiants:
            execute_query("""
                INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription)
                VALUES (?,?,?,?,?,?,?,?)
            """, e)

        df_ids = load_data("SELECT id, filiere FROM etudiants")
        ids_filieres = df_ids.to_dict('records')

        annees_valides = [f"{y}-{y+1}" for y in range(2021, 2026)]  # FIX: années cohérentes

        for etud in ids_filieres:
            id_etud = etud['id']
            fil = etud['filiere']
            mat_list = matieres.get(fil, ["Matière1", "Matière2", "Matière3"])
            for mat in random.sample(mat_list, min(len(mat_list), random.randint(3, 5))):
                note = round(random.uniform(6, 18), 2)
                coeff = random.randint(1, 3)
                session = f"S{random.randint(1, 4)}"
                annee = random.choice(annees_valides)  # FIX: pioche dans une liste valide
                execute_query("""
                    INSERT INTO notes (etudiant_id, matiere, note, coefficient, session, annee_academique)
                    VALUES (?,?,?,?,?,?)
                """, (id_etud, mat, note, coeff, session, annee))

            nb_sessions = random.randint(5, 15)
            for _ in range(nb_sessions):
                date = datetime.now().date() - timedelta(days=random.randint(0, 365))
                heures_etude = round(random.uniform(0.5, 8), 1)
                heures_sommeil = round(random.uniform(5, 9), 1)
                humeur = random.randint(1, 5)
                execute_query("""
                    INSERT INTO sessions_etude (etudiant_id, date, heures_etude, heures_sommeil, humeur)
                    VALUES (?,?,?,?,?)
                """, (id_etud, date, heures_etude, heures_sommeil, humeur))

    # FIX: st.success en dehors du spinner, avant st.rerun()
    st.success("✅ 25 étudiants fictifs ajoutés avec succès !")
    st.rerun()

# ==========================================
# INITIALISATION
# ==========================================
init_db()

if "seeded" not in st.session_state:
    st.session_state.seeded = True  # FIX: mettre à True AVANT seed pour éviter double exécution
    seed_database()

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/graduation-cap.png", width=80)
st.sidebar.title("🎓 UniAnalytics")
st.sidebar.markdown("### Tableau de bord avancé")

menu = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "👥 Étudiants", "📝 Notes", "📈 Performances", "🔬 Analyses", "⚙️ Administration"]
)
st.sidebar.markdown("---")
st.sidebar.caption(f"Version 3.0 · {datetime.now().year}")

# ==========================================
# PAGE 1 : DASHBOARD
# ==========================================
if menu == "📊 Dashboard":
    st.title("📊 Tableau de bord stratégique")
    st.markdown("---")

    df_etud = load_data("SELECT * FROM etudiants")
    df_notes = load_data("SELECT * FROM notes")
    df_sessions = load_data("SELECT * FROM sessions_etude")

    if df_etud.empty:
        st.info("Aucune donnée pour le moment. Utilisez l'onglet Administration pour ajouter des étudiants.")
    else:
        moyenne_gen = df_notes["note"].mean() if not df_notes.empty else 0
        taux_reussite = (df_notes["note"] >= 10).mean() * 100 if not df_notes.empty else 0
        nb_etudiants = len(df_etud)
        nb_notes = len(df_notes)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("👨‍🎓 Effectif total", nb_etudiants)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("📊 Moyenne générale", f"{moyenne_gen:.2f}/20")
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("✅ Taux de réussite", f"{taux_reussite:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)
        with col4:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("📝 Notes enregistrées", nb_notes)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        colA, colB = st.columns(2)
        with colA:
            st.subheader("Distribution des notes")
            if not df_notes.empty:
                fig = px.histogram(df_notes, x="note", nbins=20,
                                   title="Répartition des notes",
                                   color_discrete_sequence=["#1e3c72"])
                fig.update_layout(bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune note disponible")

        with colB:
            st.subheader("Répartition par filière")
            repartition = df_etud["filiere"].value_counts().reset_index()
            repartition.columns = ["Filière", "Effectif"]
            fig = px.pie(repartition, values="Effectif", names="Filière",
                         title="Étudiants par filière", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig, use_container_width=True)

        if not df_notes.empty and "session" in df_notes.columns:
            st.subheader("Performance par session")
            perf_session = df_notes.groupby("session")["note"].mean().reset_index()
            fig = px.line(perf_session, x="session", y="note", markers=True,
                          title="Moyenne des notes par session",
                          labels={"note": "Note moyenne"})
            st.plotly_chart(fig, use_container_width=True)

        if not df_sessions.empty and not df_notes.empty:
            st.subheader("📊 Corrélations (étude, sommeil, notes)")
            merged = pd.merge(df_notes, df_sessions, on="etudiant_id", how="inner")
            if not merged.empty and len(merged) > 1:
                corr_data = merged[["note", "heures_etude", "heures_sommeil", "humeur"]].corr()
                fig = px.imshow(corr_data, text_auto=True, aspect="auto",
                                color_continuous_scale="RdBu",
                                title="Matrice de corrélation")
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PAGE 2 : ÉTUDIANTS
# ==========================================
elif menu == "👥 Étudiants":
    st.title("👥 Gestion des étudiants")
    tab_liste, tab_ajout = st.tabs(["📋 Liste des étudiants", "➕ Ajouter un étudiant"])

    with tab_liste:
        st.subheader("Recherche")
        search = st.text_input("Rechercher par nom, prénom ou matricule")
        df_etud = load_data("SELECT * FROM etudiants")
        if not df_etud.empty:
            if search:
                mask = df_etud.apply(
                    lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1
                )
                df_etud = df_etud[mask]
            st.dataframe(df_etud, use_container_width=True)
            if st.button("🗑️ Supprimer tous les étudiants (danger)"):
                execute_query("DELETE FROM etudiants")
                st.warning("Tous les étudiants ont été supprimés.")
                st.rerun()
        else:
            st.info("Aucun étudiant enregistré.")

    with tab_ajout:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nom*")
            prenom = col2.text_input("Prénom*")
            sexe = col1.selectbox("Sexe", ["M", "F"])
            filiere = col2.selectbox("Filière", ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"])
            niveau = col1.selectbox("Niveau", ["L1", "L2", "L3", "M1", "M2"])
            age = col2.number_input("Âge", min_value=17, max_value=60, value=20)
            date_insc = st.date_input("Date d'inscription", datetime.now())
            submitted = st.form_submit_button("Enregistrer l'étudiant")
            if submitted:
                if nom and prenom:
                    df_max = load_data("SELECT MAX(id) as max_id FROM etudiants")
                    new_id = (df_max.iloc[0]['max_id'] or 0) + 1
                    matricule = f"STU{datetime.now().year}{new_id:04d}"
                    ok, msg = execute_query("""
                        INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, date_inscription)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (matricule, nom, prenom, sexe, filiere, niveau, age, date_insc.isoformat()))
                    if ok:
                        st.success(f"Étudiant {prenom} {nom} ajouté (matricule : {matricule})")
                        st.rerun()
                    else:
                        st.error(f"Erreur : {msg}")
                else:
                    st.warning("Nom et prénom sont obligatoires.")

# ==========================================
# PAGE 3 : NOTES
# ==========================================
elif menu == "📝 Notes":
    st.title("📝 Gestion des notes")
    tab_saisie, tab_consult = st.tabs(["✏️ Saisie de notes", "📊 Consultation"])

    with tab_saisie:
        df_etud = load_data("SELECT id, nom, prenom FROM etudiants")
        if df_etud.empty:
            st.warning("Veuillez d'abord ajouter des étudiants.")
        else:
            etud_dict = {f"{row['nom']} {row['prenom']}": row['id'] for _, row in df_etud.iterrows()}
            with st.form("add_note_form"):
                etudiant = st.selectbox("Étudiant", list(etud_dict.keys()))
                matiere = st.text_input("Matière")
                note = st.number_input("Note /20", 0.0, 20.0, step=0.25)
                coeff = st.number_input("Coefficient", 1, 5, 1)
                session = st.selectbox("Session", ["S1", "S2", "S3", "S4", "S5", "S6"])
                annee = st.text_input("Année académique (ex: 2024-2025)",
                                      f"{datetime.now().year}-{datetime.now().year + 1}")
                if st.form_submit_button("Enregistrer la note"):
                    if matiere:
                        ok, _ = execute_query("""
                            INSERT INTO notes (etudiant_id, matiere, note, coefficient, session, annee_academique)
                            VALUES (?,?,?,?,?,?)
                        """, (etud_dict[etudiant], matiere, note, coeff, session, annee))
                        if ok:
                            st.success("Note ajoutée ✅")
                        else:
                            st.error("Erreur d'insertion")
                    else:
                        st.warning("Matière requise")

    with tab_consult:
        df_notes = load_data("""
            SELECT e.nom, e.prenom, n.matiere, n.note, n.coefficient, n.session, n.annee_academique
            FROM notes n
            JOIN etudiants e ON n.etudiant_id = e.id
            ORDER BY e.nom, n.matiere
        """)
        if not df_notes.empty:
            st.dataframe(df_notes, use_container_width=True)
        else:
            st.info("Aucune note enregistrée.")

# ==========================================
# PAGE 4 : PERFORMANCES
# ==========================================
elif menu == "📈 Performances":
    st.title("📈 Analyse des performances")

    df_notes = load_data("SELECT * FROM notes")
    df_etud = load_data("SELECT id, filiere, niveau FROM etudiants")

    if df_notes.empty or df_etud.empty:
        st.info("Données insuffisantes pour générer les performances.")
    else:
        merged = pd.merge(df_notes, df_etud, left_on="etudiant_id", right_on="id")

        perf_fil = merged.groupby("filiere")["note"].agg(["mean", "count"]).reset_index()
        perf_fil.columns = ["Filière", "Moyenne", "Effectif"]
        perf_fil["Moyenne"] = perf_fil["Moyenne"].round(2)
        fig = px.bar(perf_fil, x="Filière", y="Moyenne", color="Moyenne",
                     title="Moyenne par filière", text="Moyenne",
                     color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Performance par matière")
        filiere_choice = st.selectbox("Choisir une filière", sorted(merged["filiere"].unique()))
        df_fil = merged[merged["filiere"] == filiere_choice]
        mat_perf = df_fil.groupby("matiere")["note"].mean().sort_values(ascending=False).reset_index()
        mat_perf["note"] = mat_perf["note"].round(2)
        fig2 = px.bar(mat_perf, x="matiere", y="note",
                      title=f"Matières - {filiere_choice}",
                      color="note", color_continuous_scale="Viridis")
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Notes par niveau")
        box = px.box(merged, x="niveau", y="note", color="niveau",
                     title="Distribution des notes par niveau")
        st.plotly_chart(box, use_container_width=True)

# ==========================================
# PAGE 5 : ANALYSES AVANCÉES
# ==========================================
elif menu == "🔬 Analyses":
    st.title("🔬 Analyses avancées")

    df_notes = load_data("SELECT * FROM notes")
    df_sessions = load_data("SELECT * FROM sessions_etude")

    if df_notes.empty or df_sessions.empty:
        st.info("Besoin de notes et de sessions d'étude pour les analyses.")
    else:
        merged = pd.merge(df_notes, df_sessions, on="etudiant_id", how="inner")
        if merged.empty:
            st.warning("Aucune correspondance entre notes et sessions d'étude.")
        else:
            st.subheader("📈 Relation entre heures d'étude et notes")
            # FIX: trendline="ols" remplacé par "lowess" (ne nécessite pas statsmodels)
            fig = px.scatter(merged, x="heures_etude", y="note", size="humeur",
                             color="matiere", trendline="lowess",
                             title="Heures d'étude vs Notes obtenues",
                             labels={"heures_etude": "Heures d'étude", "note": "Note /20"})
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("🛌 Impact du sommeil sur les performances")
            fig2 = px.scatter(merged, x="heures_sommeil", y="note", color="humeur",
                              trendline="lowess",
                              title="Sommeil et notes",
                              labels={"heures_sommeil": "Heures de sommeil", "note": "Note /20"})
            st.plotly_chart(fig2, use_container_width=True)

            st.subheader("📊 Matrice de corrélation complète")
            cols_corr = ["note", "heures_etude", "heures_sommeil", "humeur", "coefficient"]
            corr_data = merged[cols_corr].corr()
            fig3 = px.imshow(corr_data, text_auto=True, aspect="auto",
                             color_continuous_scale="RdBu",
                             title="Corrélations (notes, étude, sommeil, humeur)")
            st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# PAGE 6 : ADMINISTRATION
# ==========================================
elif menu == "⚙️ Administration":
    st.title("⚙️ Administration")
    st.markdown("Outils de gestion de la base de données.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Régénérer les données fictives (25 étudiants)"):
            execute_query("DELETE FROM etudiants")
            execute_query("DELETE FROM notes")
            execute_query("DELETE FROM sessions_etude")
            del st.session_state["seeded"]  # FIX: supprime la clé pour forcer le re-seed
            st.success("Base vidée. Repeuplement en cours...")
            st.rerun()
    with col2:
        if st.button("🗑️ Réinitialiser complètement (toutes les tables)"):
            execute_query("DROP TABLE IF EXISTS etudiants")
            execute_query("DROP TABLE IF EXISTS notes")
            execute_query("DROP TABLE IF EXISTS sessions_etude")
            init_db()
            del st.session_state["seeded"]  # FIX: idem
            st.success("Base réinitialisée.")
            st.rerun()

    st.markdown("---")
    st.subheader("Statistiques de la base")
    df_et = load_data("SELECT COUNT(*) as nb FROM etudiants")
    df_no = load_data("SELECT COUNT(*) as nb FROM notes")
    df_se = load_data("SELECT COUNT(*) as nb FROM sessions_etude")
    if not df_et.empty:
        st.write(f"👨‍🎓 Étudiants : **{df_et.iloc[0]['nb']}**")
        st.write(f"📝 Notes : **{df_no.iloc[0]['nb']}**")
        st.write(f"📖 Sessions d'étude : **{df_se.iloc[0]['nb']}**")
