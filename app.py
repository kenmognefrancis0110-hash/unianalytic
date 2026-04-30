import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# ==========================================
# CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(page_title="UniAnalytics", page_icon="🎓", layout="wide")

DB_PATH = "unianalytics_streamlit.db"

# ==========================================
# BASE DE DONNÉES
# ==========================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS etudiants (
            id_etudiant INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            sexe TEXT DEFAULT 'M',
            filiere TEXT NOT NULL,
            niveau TEXT NOT NULL,
            age INTEGER NOT NULL,
            annee_inscription INTEGER
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
            session TEXT DEFAULT 'S1'
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
    conn.close()

# Initialize DB on startup
if not os.path.exists(DB_PATH):
    init_db()

# ==========================================
# HELPERS (REQUÊTES)
# ==========================================
def load_data(query, params=()):
    conn = get_db()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        conn.commit()
        last_id = cur.lastrowid
        return True, last_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

# ==========================================
# INTERFACE UTILISATEUR (SIDEBAR)
# ==========================================
st.sidebar.title("🎓 UniAnalytics")
menu = st.sidebar.radio("Navigation", [
    "📊 Tableau de bord", 
    "🔍 Recherche étudiant", 
    "➕ Collecte données", 
    "📈 Performance filières", 
    "🗂️ Anciens étudiants"
])

st.sidebar.markdown("---")
st.sidebar.caption("v1.0.0 · Streamlit Version")

# ==========================================
# PAGES
# ==========================================

# --- PAGE 1: TABLEAU DE BORD ---
if menu == "📊 Tableau de bord":
    st.title("Tableau de bord")
    st.write("Analyse statistique complète — données en temps réel")

    df_etud = load_data("SELECT * FROM etudiants")
    df_res = load_data("SELECT * FROM resultats")

    if not df_etud.empty and not df_res.empty:
        moyenne_gen = df_res["note_examen"].mean()
        taux_reussite = (df_res["note_examen"] >= 10).mean() * 100
        
        moy_etudiant = df_res.groupby("id_etudiant")["note_examen"].mean().reset_index()
        risque = (moy_etudiant["note_examen"] < 10).sum()
        pct_risque = (risque / len(moy_etudiant)) * 100 if len(moy_etudiant) > 0 else 0

        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Étudiants inscrits", len(df_etud))
        col2.metric("Moyenne générale", f"{moyenne_gen:.2f} / 20")
        col3.metric("Taux de réussite", f"{taux_reussite:.1f} %")
        col4.metric("Risque d'abandon", f"{pct_risque:.1f} %")

        st.markdown("---")
        colA, colB = st.columns(2)
        
        with colA:
            st.subheader("Distribution des notes")
            df_hist = pd.cut(df_res["note_examen"], bins=[0, 5, 10, 12, 14, 16, 18, 20]).value_counts().sort_index()
            st.bar_chart(df_hist)

        with colB:
            st.subheader("Performance par Filière")
            df_merge = pd.merge(df_res, df_etud, on="id_etudiant")
            perf_fil = df_merge.groupby("filiere")["note_examen"].mean()
            st.bar_chart(perf_fil)
            
    else:
        st.info("Aucune donnée suffisante pour afficher les statistiques. Veuillez ajouter des étudiants et des notes.")


# --- PAGE 2: RECHERCHE ---
elif menu == "🔍 Recherche étudiant":
    st.title("Recherche d'étudiant")
    
    search_term = st.text_input("Rechercher par nom, prénom ou matricule (ex: CM0001)...")
    
    query = "SELECT * FROM etudiants"
    df = load_data(query)
    
    if not df.empty:
        if search_term:
            df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        
        st.write(f"**{len(df)}** étudiant(s) trouvé(s)")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("La base de données est vide.")


# --- PAGE 3: COLLECTE ---
elif menu == "➕ Collecte données":
    st.title("Collecte de données")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Nouvel étudiant", "📖 Session d'étude", "📝 Résultat examen", "🎓 Ancien étudiant"])
    
    # 1. Ajouter un étudiant
    with tab1:
        st.subheader("Enregistrer un nouvel étudiant")
        with st.form("form_etudiant", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nom")
            prenom = col2.text_input("Prénom")
            sexe = col1.selectbox("Sexe", ["M", "F"])
            filiere = col2.selectbox("Filière", ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"])
            niveau = col1.selectbox("Niveau", ["L1", "L2", "L3", "M1", "M2"])
            age = col2.number_input("Âge", min_value=17, max_value=60, value=20)
            annee = st.number_input("Année d'inscription", min_value=2000, max_value=2050, value=datetime.now().year)
            
            if st.form_submit_button("Enregistrer l'étudiant"):
                df_ids = load_data("SELECT MAX(id_etudiant) as max_id FROM etudiants")
                new_id = (df_ids["max_id"][0] or 0) + 1
                matricule = f"CM{new_id:04d}"
                
                success, msg = execute_query(
                    "INSERT INTO etudiants (matricule, nom, prenom, sexe, filiere, niveau, age, annee_inscription) VALUES (?,?,?,?,?,?,?,?)",
                    (matricule, nom, prenom, sexe, filiere, niveau, age, annee)
                )
                if success:
                    st.success(f"Étudiant {prenom} {nom} enregistré avec le matricule {matricule}")
                else:
                    st.error(f"Erreur : {msg}")

    # Récupérer la liste pour les selectbox
    df_etudiants = load_data("SELECT id_etudiant, matricule, nom, prenom FROM etudiants")
    etudiants_dict = {f"{row['matricule']} - {row['prenom']} {row['nom']}": row['id_etudiant'] for _, row in df_etudiants.iterrows()}
    
    # 2. Session d'étude
    with tab2:
        st.subheader("Enregistrer une session d'étude")
        if not etudiants_dict:
            st.warning("Ajoutez d'abord un étudiant.")
        else:
            with st.form("form_session", clear_on_submit=True):
                etud_sel = st.selectbox("Étudiant", list(etudiants_dict.keys()))
                date_sess = st.date_input("Date")
                heures = st.number_input("Heures d'étude", min_value=0.0, max_value=24.0, step=0.5)
                sommeil = st.number_input("Heures de sommeil", min_value=0.0, max_value=24.0, step=0.5, value=7.0)
                humeur = st.slider("Humeur (1=Mauvais, 5=Excellent)", 1, 5, 3)
                
                if st.form_submit_button("Enregistrer la session"):
                    id_etud = etudiants_dict[etud_sel]
                    success, msg = execute_query(
                        "INSERT INTO sessions_etude (id_etudiant, date, heures_etude, heures_sommeil, humeur_index) VALUES (?,?,?,?,?)",
                        (id_etud, date_sess, heures, sommeil, humeur)
                    )
                    if success:
                        st.success("Session enregistrée !")
                    else:
                        st.error(msg)

    # 3. Résultat
    with tab3:
        st.subheader("Enregistrer un résultat")
        if not etudiants_dict:
            st.warning("Ajoutez d'abord un étudiant.")
        else:
            with st.form("form_resultat", clear_on_submit=True):
                etud_sel_r = st.selectbox("Étudiant concerné", list(etudiants_dict.keys()))
                code = st.text_input("Code Matière (ex: INF101)")
                nom_mat = st.text_input("Nom de la matière")
                note = st.number_input("Note / 20", min_value=0.0, max_value=20.0, step=0.25)
                presence = st.number_input("Taux de présence (%)", min_value=0, max_value=100, value=100)
                
                if st.form_submit_button("Enregistrer la note"):
                    id_etud_r = etudiants_dict[etud_sel_r]
                    success, msg = execute_query(
                        "INSERT INTO resultats (id_etudiant, code_matiere, nom_matiere, note_examen, taux_presence) VALUES (?,?,?,?,?)",
                        (id_etud_r, code, nom_mat, note, presence)
                    )
                    if success:
                        st.success("Note enregistrée !")
                    else:
                        st.error(msg)

    # 4. Ancien étudiant
    with tab4:
        st.subheader("Archiver un départ")
        if not etudiants_dict:
            st.warning("Ajoutez d'abord un étudiant.")
        else:
            with st.form("form_ancien", clear_on_submit=True):
                etud_sel_a = st.selectbox("Sélectionner l'étudiant à archiver", list(etudiants_dict.keys()))
                cause = st.selectbox("Cause", ["fin_parcours", "abandon", "echec_scolaire"])
                annee_d = st.number_input("Année de départ", min_value=2000, max_value=2050, value=datetime.now().year)
                commentaire = st.text_area("Commentaire")
                
                if st.form_submit_button("Archiver"):
                    id_etud_a = etudiants_dict[etud_sel_a]
                    success, msg = execute_query(
                        "INSERT INTO anciens_etudiants (id_etudiant, cause, annee_depart, commentaire) VALUES (?,?,?,?)",
                        (id_etud_a, cause, annee_d, commentaire)
                    )
                    if success:
                        st.success("Étudiant archivé avec succès.")
                    else:
                        st.error(msg)


# --- PAGE 4: PERFORMANCE ---
elif menu == "📈 Performance filières":
    st.title("Performance par filière")
    
    df = load_data("""
        SELECT e.filiere, 
               COUNT(DISTINCT e.id_etudiant) as nb_etudiants,
               AVG(r.note_examen) as moyenne,
               MAX(r.note_examen) as note_max,
               MIN(r.note_examen) as note_min
        FROM etudiants e
        JOIN resultats r ON e.id_etudiant = r.id_etudiant
        GROUP BY e.filiere
        ORDER BY moyenne DESC
    """)
    
    if not df.empty:
        st.dataframe(df.style.highlight_max(subset=['moyenne'], color='lightgreen'), use_container_width=True)
        
        st.subheader("Moyenne Générale par Filière")
        st.bar_chart(df.set_index("filiere")["moyenne"])
    else:
        st.info("Ajoutez des étudiants et des notes pour voir les performances.")


# --- PAGE 5: ANCIENS ÉTUDIANTS ---
elif menu == "🗂️ Anciens étudiants":
    st.title("Anciens étudiants")
    
    df_anciens = load_data("""
        SELECT ae.id, e.matricule, e.nom, e.prenom, e.filiere, ae.cause, ae.annee_depart, ae.commentaire
        FROM anciens_etudiants ae
        JOIN etudiants e ON ae.id_etudiant = e.id_etudiant
    """)
    
    if not df_anciens.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Anciens", len(df_anciens))
        col2.metric("Diplômés", len(df_anciens[df_anciens['cause'] == 'fin_parcours']))
        col3.metric("Abandons", len(df_anciens[df_anciens['cause'] == 'abandon']))
        col4.metric("Échecs", len(df_anciens[df_anciens['cause'] == 'echec_scolaire']))
        
        st.markdown("---")
        st.dataframe(df_anciens, use_container_width=True)
    else:
        st.info("Aucun ancien étudiant enregistré.")