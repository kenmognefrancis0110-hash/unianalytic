# ==========================================
# app.py - Application complète améliorée
# ==========================================
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import io

# ==========================================
# CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="UniAnalytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #1e3c72; color: white; border-radius: 8px; }
    .stMetric { background-color: white; padding: 10px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "unianalytics_pro.db"

# ==========================================
# BASE DE DONNÉES (améliorée)
# ==========================================
def get_connection():
    return sqlite3.connect(DB_PATH)

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
    conn.close()

if not os.path.exists(DB_PATH):
    init_db()

# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================
@st.cache_data(ttl=3600)
def load_data(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_connection()
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

def export_dataframe(df, filename, format='csv'):
    if format == 'csv':
        return df.to_csv(index=False).encode('utf-8')
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='data')
        return output.getvalue()

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/graduation-cap.png", width=80)
st.sidebar.title("🎓 UniAnalytics")
st.sidebar.markdown("### Tableau de bord avancé")

menu = st.sidebar.radio(
    "Navigation",
    ["📊 Tableau de bord", "🔍 Recherche", "➕ Collecte", "📈 Performances", "📉 Analyses avancées", "🗂️ Anciens", "⚙️ Export"]
)

st.sidebar.markdown("---")
st.sidebar.caption("v2.0.0 · Dashboard interactif")

# ==========================================
# PAGE : TABLEAU DE BORD (enrichi)
# ==========================================
if menu == "📊 Tableau de bord":
    st.title("📊 Tableau de bord stratégique")
    st.markdown("Vue d'ensemble des indicateurs clés de performance")

    # Chargement
    df_etud = load_data("SELECT * FROM etudiants")
    df_res = load_data("SELECT * FROM resultats")
    df_sess = load_data("SELECT * FROM sessions_etude")

    if not df_etud.empty and not df_res.empty:
        # Indicateurs globaux
        total_etudiants = len(df_etud)
        moyenne_generale = df_res["note_examen"].mean()
        taux_reussite = (df_res["note_examen"] >= 10).mean() * 100
        taux_abandon = len(df_sess) / total_etudiants if total_etudiants else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👨‍🎓 Étudiants", total_etudiants)
        col2.metric("📊 Moyenne", f"{moyenne_generale:.2f}/20")
        col3.metric("✅ Taux réussite", f"{taux_reussite:.1f}%")
        col4.metric("⚠️ Risque abandon", f"{taux_abandon:.1f}%")

        st.markdown("---")
        colA, colB = st.columns(2)

        # Distribution des notes avec Plotly
        with colA:
            st.subheader("Distribution des notes")
            fig = px.histogram(df_res, x="note_examen", nbins=20, color_discrete_sequence=['#1e3c72'],
                               labels={"note_examen": "Note /20"}, title="Histogramme des notes")
            fig.update_layout(bargap=0.1)
            st.plotly_chart(fig, use_container_width=True)

        # Boxplot par matière
        with colB:
            st.subheader("Performance par matière")
            top_matiere = df_res.groupby("nom_matiere")["note_examen"].mean().sort_values(ascending=False).head(8)
            fig = px.bar(top_matiere, x=top_matiere.values, y=top_matiere.index, orientation='h',
                         color=top_matiere.values, color_continuous_scale='Blues', title="Moyenne par matière")
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        # Évolution temporelle (si date présente)
        if 'date' in df_sess.columns and not df_sess.empty:
            st.subheader("Évolution des heures d'étude")
            df_sess['date'] = pd.to_datetime(df_sess['date'])
            evol = df_sess.groupby(df_sess['date'].dt.date)['heures_etude'].mean().reset_index()
            fig = px.line(evol, x='date', y='heures_etude', title="Moyenne des heures d'étude par jour",
                          markers=True, labels={"heures_etude": "Heures"})
            st.plotly_chart(fig, use_container_width=True)

        # Radar chart de répartition par filière
        repartition = df_etud["filiere"].value_counts().reset_index()
        repartition.columns = ["Filière", "Effectif"]
        fig_pie = px.pie(repartition, values="Effectif", names="Filière", title="Répartition par filière",
                         hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_pie, use_container_width=True)

    else:
        st.warning("Données insuffisantes pour afficher le tableau de bord. Veuillez ajouter des étudiants et des notes.")

# ==========================================
# PAGE : ANALYSES AVANCÉES (NOUVEAU)
# ==========================================
elif menu == "📉 Analyses avancées":
    st.title("📉 Analyses avancées")
    st.markdown("Corrélations, heatmaps, et prédictions simplifiées")

    df_etud = load_data("SELECT * FROM etudiants")
    df_res = load_data("SELECT * FROM resultats")
    df_sess = load_data("SELECT * FROM sessions_etude")

    if not df_res.empty:
        # Matrice de corrélation entre présence, note, heures d'étude
        merged = pd.merge(df_res, df_sess, on="id_etudiant", how="inner")
        if not merged.empty:
            corr_data = merged[["note_examen", "taux_presence", "heures_etude", "heures_sommeil", "humeur_index"]].corr()
            fig = px.imshow(corr_data, text_auto=True, aspect="auto", color_continuous_scale='RdBu',
                            title="Matrice de corrélation")
            st.plotly_chart(fig, use_container_width=True)

        # Nuage de points note vs présence
        st.subheader("Relation : Note exam vs Taux de présence")
        fig = px.scatter(merged, x="taux_presence", y="note_examen", color="humeur_index",
                         size="heures_etude", hover_data=["code_matiere"],
                         labels={"taux_presence": "Présence (%)", "note_examen": "Note /20"})
        st.plotly_chart(fig, use_container_width=True)

        # Heatmap des notes par filière et niveau
        df_merged = pd.merge(df_res, df_etud, on="id_etudiant")
        pivot = df_merged.pivot_table(index="filiere", columns="niveau", values="note_examen", aggfunc="mean")
        fig = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale='Viridis',
                        title="Moyennes (filière × niveau)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ajoutez des résultats pour voir les analyses avancées.")

# ==========================================
# PAGE : PERFORMANCES (améliorée)
# ==========================================
elif menu == "📈 Performances":
    st.title("📈 Performance détaillée par filière")
    df = load_data("""
        SELECT e.filiere, e.niveau,
               COUNT(DISTINCT e.id_etudiant) as nb_etudiants,
               ROUND(AVG(r.note_examen),2) as moyenne,
               ROUND(MAX(r.note_examen),2) as max_note,
               ROUND(MIN(r.note_examen),2) as min_note,
               ROUND((SUM(CASE WHEN r.note_examen >= 10 THEN 1 ELSE 0 END) * 100.0 / COUNT(r.note_examen)),1) as taux_reussite
        FROM etudiants e
        JOIN resultats r ON e.id_etudiant = r.id_etudiant
        GROUP BY e.filiere, e.niveau
        ORDER BY moyenne DESC
    """)
    if not df.empty:
        st.dataframe(df.style.background_gradient(subset=["moyenne"], cmap="Blues"), use_container_width=True)
        fig = px.bar(df, x="filiere", y="moyenne", color="niveau", barmode="group",
                     title="Moyenne par filière et niveau", labels={"moyenne": "Note moyenne"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée de performance disponible.")

# ==========================================
# PAGE : EXPORT (NOUVEAU)
# ==========================================
elif menu == "⚙️ Export":
    st.title("📀 Export de données")
    tables = ["etudiants", "resultats", "sessions_etude", "anciens_etudiants"]
    selected = st.selectbox("Choisir une table", tables)
    df = load_data(f"SELECT * FROM {selected}")
    if not df.empty:
        format_export = st.radio("Format", ["csv", "excel"])
        if st.button("Télécharger"):
            data = export_dataframe(df, f"{selected}.{format_export}", format_export)
            st.download_button(label="📥 Cliquer pour télécharger", data=data,
                               file_name=f"{selected}_{datetime.now().strftime('%Y%m%d')}.{format_export}",
                               mime="application/octet-stream")
    else:
        st.warning("Table vide.")
