"""
app.py — Point d'entrée principal de UniAnalytics Pro.
Lancer avec : streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import database as db
import seed as seed_module
import charts

# ──────────────────────────────────────────
# CONFIGURATION DE LA PAGE
# ──────────────────────────────────────────
st.set_page_config(
    page_title="UniAnalytics Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fb 0%, #e9edf2 100%); }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #1e3c72;
        margin-bottom: .5rem;
    }
    h1, h2, h3 { color: #1e3c72; font-weight: 600; }
    .stButton > button {
        background-color: #1e3c72;
        color: white;
        border-radius: 8px;
        border: none;
        padding: .5rem 1rem;
        transition: .3s;
    }
    .stButton > button:hover {
        background-color: #2a4a8a;
        transform: translateY(-2px);
    }
    hr { margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# INITIALISATION DB + SEED
# ──────────────────────────────────────────
db.init_db()

if "seeded" not in st.session_state:
    st.session_state.seeded = True
    with st.spinner("🎲 Génération des données fictives..."):
        did_seed = seed_module.seed_if_empty()
    if did_seed:
        st.success("✅ 25 étudiants fictifs ajoutés avec succès !")
        st.rerun()

# ──────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/graduation-cap.png", width=80)
st.sidebar.title("🎓 UniAnalytics Pro")
st.sidebar.markdown("### Navigation")

menu = st.sidebar.radio("", [
    "📊 Dashboard",
    "👥 Étudiants",
    "📝 Notes",
    "📈 Performances",
    "🔬 Analyses",
    "⚙️ Administration",
])
st.sidebar.markdown("---")
st.sidebar.caption(f"👨‍🎓 {db.count_table('etudiants')} étudiant(s) · v3.0 · {datetime.now().year}")

# ══════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ══════════════════════════════════════════
if menu == "📊 Dashboard":
    st.title("📊 Tableau de bord stratégique")
    st.markdown("---")

    df_etud     = db.get_etudiants()
    df_notes    = db.load_data("SELECT * FROM notes")
    df_sessions = db.load_data("SELECT * FROM sessions_etude")

    if df_etud.empty:
        st.info("Aucune donnée. Utilisez **Administration** pour générer des étudiants fictifs.")
        st.stop()

    moyenne_gen   = df_notes["note"].mean() if not df_notes.empty else 0
    taux_reussite = (df_notes["note"] >= 10).mean() * 100 if not df_notes.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "👨‍🎓 Effectif total",     len(df_etud)),
        (c2, "📊 Moyenne générale",    f"{moyenne_gen:.2f} / 20"),
        (c3, "✅ Taux de réussite",    f"{taux_reussite:.1f} %"),
        (c4, "📝 Notes enregistrées", len(df_notes)),
    ]:
        with col:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric(label, value)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    colA, colB = st.columns(2)
    with colA:
        if not df_notes.empty:
            st.plotly_chart(charts.histogram_notes(df_notes), use_container_width=True)
    with colB:
        st.plotly_chart(charts.pie_filieres(df_etud), use_container_width=True)

    if not df_notes.empty and "session" in df_notes.columns:
        st.plotly_chart(charts.line_session_perf(df_notes), use_container_width=True)

    if not df_sessions.empty and not df_notes.empty:
        merged = db.get_sessions_merged_with_notes()
        if len(merged) > 1:
            st.plotly_chart(
                charts.heatmap_correlation(
                    merged,
                    ["note", "heures_etude", "heures_sommeil", "humeur"],
                    "Matrice de corrélation (étude · sommeil · notes)",
                ),
                use_container_width=True,
            )

# ══════════════════════════════════════════
# PAGE 2 — ÉTUDIANTS
# ══════════════════════════════════════════
elif menu == "👥 Étudiants":
    st.title("👥 Gestion des étudiants")
    tab_liste, tab_ajout = st.tabs(["📋 Liste", "➕ Ajouter"])

    with tab_liste:
        search = st.text_input("🔍 Rechercher (nom, prénom ou matricule)")
        df_etud = db.get_etudiants()
        if not df_etud.empty:
            if search:
                mask = df_etud.apply(
                    lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1
                )
                df_etud = df_etud[mask]
            st.dataframe(df_etud, use_container_width=True)
            st.caption(f"{len(df_etud)} résultat(s)")
            with st.expander("⚠️ Zone dangereuse"):
                if st.button("🗑️ Supprimer TOUS les étudiants"):
                    db.delete_all("etudiants")
                    st.warning("Tous les étudiants ont été supprimés.")
                    st.rerun()
        else:
            st.info("Aucun étudiant enregistré.")

    with tab_ajout:
        with st.form("form_add_etudiant", clear_on_submit=True):
            c1, c2  = st.columns(2)
            nom     = c1.text_input("Nom *")
            prenom  = c2.text_input("Prénom *")
            sexe    = c1.selectbox("Sexe", ["M", "F"])
            filiere = c2.selectbox("Filière", ["Informatique", "Mathématiques", "Physique", "Économie", "Droit"])
            niveau  = c1.selectbox("Niveau", ["L1", "L2", "L3", "M1", "M2"])
            age     = c2.number_input("Âge", 17, 60, 20)
            date_ins = st.date_input("Date d'inscription", datetime.now())

            if st.form_submit_button("✅ Enregistrer"):
                if nom and prenom:
                    df_max    = db.load_data("SELECT MAX(id) as max_id FROM etudiants")
                    new_id    = (df_max.iloc[0]["max_id"] or 0) + 1
                    matricule = f"STU{datetime.now().year}{new_id:04d}"
                    ok, msg   = db.add_etudiant(
                        matricule, nom, prenom, sexe, filiere, niveau, age, date_ins.isoformat()
                    )
                    if ok:
                        st.success(f"Étudiant **{prenom} {nom}** ajouté (matricule : `{matricule}`)")
                        st.rerun()
                    else:
                        st.error(f"Erreur : {msg}")
                else:
                    st.warning("Nom et prénom sont obligatoires.")

# ══════════════════════════════════════════
# PAGE 3 — NOTES
# ══════════════════════════════════════════
elif menu == "📝 Notes":
    st.title("📝 Gestion des notes")
    tab_saisie, tab_consult = st.tabs(["✏️ Saisie", "📊 Consultation"])

    with tab_saisie:
        df_etud = db.load_data("SELECT id, nom, prenom FROM etudiants ORDER BY nom")
        if df_etud.empty:
            st.warning("Aucun étudiant. Ajoutez-en d'abord.")
        else:
            etud_dict = {f"{r['nom']} {r['prenom']}": r["id"] for _, r in df_etud.iterrows()}
            with st.form("form_add_note", clear_on_submit=True):
                etudiant = st.selectbox("Étudiant", list(etud_dict))
                matiere  = st.text_input("Matière *")
                c1, c2  = st.columns(2)
                note    = c1.number_input("Note /20", 0.0, 20.0, step=0.25)
                coeff   = c2.number_input("Coefficient", 1, 5, 1)
                session = c1.selectbox("Session", ["S1", "S2", "S3", "S4", "S5", "S6"])
                annee   = c2.text_input("Année académique", f"{datetime.now().year}-{datetime.now().year+1}")

                if st.form_submit_button("✅ Enregistrer la note"):
                    if matiere:
                        ok, _ = db.add_note(etud_dict[etudiant], matiere, note, coeff, session, annee)
                        st.success("Note ajoutée ✅") if ok else st.error("Erreur d'insertion")
                    else:
                        st.warning("La matière est obligatoire.")

    with tab_consult:
        df_notes = db.get_notes_with_names()
        if not df_notes.empty:
            c1, c2   = st.columns(2)
            filieres  = ["Toutes"] + sorted(df_notes["filiere"].unique().tolist())
            f_choice  = c1.selectbox("Filtrer par filière", filieres)
            s_choice  = c2.selectbox("Filtrer par session", ["Toutes"] + sorted(df_notes["session"].unique().tolist()))
            df_show   = df_notes.copy()
            if f_choice != "Toutes":
                df_show = df_show[df_show["filiere"] == f_choice]
            if s_choice != "Toutes":
                df_show = df_show[df_show["session"] == s_choice]
            st.dataframe(df_show, use_container_width=True)
            st.caption(f"{len(df_show)} note(s) · Moyenne filtrée : {df_show['note'].mean():.2f}/20")
        else:
            st.info("Aucune note enregistrée.")

# ══════════════════════════════════════════
# PAGE 4 — PERFORMANCES
# ══════════════════════════════════════════
elif menu == "📈 Performances":
    st.title("📈 Analyse des performances")

    df_merged = db.get_notes_merged_with_etudiants()
    if df_merged.empty:
        st.info("Données insuffisantes.")
        st.stop()

    st.plotly_chart(charts.bar_moyenne_filiere(df_merged), use_container_width=True)

    st.subheader("Performance par matière")
    filiere_choice = st.selectbox("Choisir une filière", sorted(df_merged["filiere"].unique()))
    st.plotly_chart(charts.bar_moyenne_matiere(df_merged, filiere_choice), use_container_width=True)

    st.subheader("Distribution par niveau")
    st.plotly_chart(charts.box_notes_niveau(df_merged), use_container_width=True)

    st.subheader("Récapitulatif par filière")
    recap = (
        df_merged.groupby("filiere")["note"]
        .agg(Effectif="count", Moyenne="mean", Min="min", Max="max")
        .round(2).reset_index()
        .rename(columns={"filiere": "Filière"})
    )
    st.dataframe(recap, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════
# PAGE 5 — ANALYSES AVANCÉES
# ══════════════════════════════════════════
elif menu == "🔬 Analyses":
    st.title("🔬 Analyses avancées")

    df_merged = db.get_sessions_merged_with_notes()
    if df_merged.empty:
        st.info("Aucune correspondance entre notes et sessions d'étude.")
        st.stop()

    st.subheader("📈 Heures d'étude vs Notes")
    st.plotly_chart(charts.scatter_etude_notes(df_merged), use_container_width=True)

    st.subheader("🛌 Sommeil vs Notes")
    st.plotly_chart(charts.scatter_sommeil_notes(df_merged), use_container_width=True)

    st.subheader("📊 Matrice de corrélation complète")
    cols_corr = ["note", "heures_etude", "heures_sommeil", "humeur", "coefficient"]
    st.plotly_chart(
        charts.heatmap_correlation(df_merged, cols_corr, "Corrélations — notes · étude · sommeil · humeur"),
        use_container_width=True,
    )

    st.subheader("📋 Statistiques descriptives")
    st.dataframe(df_merged[cols_corr].describe().round(2), use_container_width=True)

# ══════════════════════════════════════════
# PAGE 6 — ADMINISTRATION
# ══════════════════════════════════════════
elif menu == "⚙️ Administration":
    st.title("⚙️ Administration")

    st.subheader("Statistiques de la base")
    c1, c2, c3 = st.columns(3)
    c1.metric("👨‍🎓 Étudiants",       db.count_table("etudiants"))
    c2.metric("📝 Notes",            db.count_table("notes"))
    c3.metric("📖 Sessions d'étude", db.count_table("sessions_etude"))

    st.markdown("---")
    st.subheader("Actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Régénérer les 25 étudiants fictifs"):
            db.delete_all("sessions_etude")
            db.delete_all("notes")
            db.delete_all("etudiants")
            del st.session_state["seeded"]
            st.success("Base vidée — repeuplement au prochain chargement.")
            st.rerun()
    with col2:
        if st.button("🗑️ Réinitialiser complètement (DROP + CREATE)"):
            db.reset_db()
            del st.session_state["seeded"]
            st.success("Base réinitialisée — repeuplement au prochain chargement.")
            st.rerun()
