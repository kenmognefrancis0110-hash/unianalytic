"""
charts.py — Fonctions de visualisation Plotly réutilisables pour UniAnalytics Pro.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BLUE_PALETTE = px.colors.sequential.Blues_r
PRIMARY_COLOR = "#1e3c72"


# ──────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────

def histogram_notes(df: pd.DataFrame) -> go.Figure:
    """Histogramme de la distribution des notes."""
    fig = px.histogram(
        df, x="note", nbins=20,
        title="Répartition des notes",
        color_discrete_sequence=[PRIMARY_COLOR],
        labels={"note": "Note /20", "count": "Effectif"},
    )
    fig.update_layout(bargap=0.1, plot_bgcolor="white")
    return fig


def pie_filieres(df: pd.DataFrame) -> go.Figure:
    """Camembert des étudiants par filière."""
    repartition = df["filiere"].value_counts().reset_index()
    repartition.columns = ["Filière", "Effectif"]
    return px.pie(
        repartition, values="Effectif", names="Filière",
        title="Étudiants par filière", hole=0.4,
        color_discrete_sequence=BLUE_PALETTE,
    )


def line_session_perf(df: pd.DataFrame) -> go.Figure:
    """Courbe de la moyenne des notes par session."""
    perf = df.groupby("session")["note"].mean().reset_index()
    return px.line(
        perf, x="session", y="note", markers=True,
        title="Moyenne des notes par session",
        labels={"note": "Note moyenne", "session": "Session"},
    )


def heatmap_correlation(df: pd.DataFrame, cols: list[str], title: str = "Matrice de corrélation") -> go.Figure:
    """Heatmap des corrélations entre colonnes numériques."""
    corr = df[cols].corr()
    return px.imshow(
        corr, text_auto=True, aspect="auto",
        color_continuous_scale="RdBu",
        title=title,
    )


# ──────────────────────────────────────────
# PERFORMANCES
# ──────────────────────────────────────────

def bar_moyenne_filiere(df: pd.DataFrame) -> go.Figure:
    """Barres : moyenne des notes par filière."""
    perf = df.groupby("filiere")["note"].mean().round(2).reset_index()
    perf.columns = ["Filière", "Moyenne"]
    return px.bar(
        perf, x="Filière", y="Moyenne", color="Moyenne",
        title="Moyenne par filière", text="Moyenne",
        color_continuous_scale="Blues",
    )


def bar_moyenne_matiere(df: pd.DataFrame, filiere: str) -> go.Figure:
    """Barres : moyenne des notes par matière pour une filière donnée."""
    df_fil = df[df["filiere"] == filiere]
    mat_perf = df_fil.groupby("matiere")["note"].mean().round(2).sort_values(ascending=False).reset_index()
    return px.bar(
        mat_perf, x="matiere", y="note",
        title=f"Matières — {filiere}",
        color="note", color_continuous_scale="Viridis",
        labels={"matiere": "Matière", "note": "Moyenne"},
    )


def box_notes_niveau(df: pd.DataFrame) -> go.Figure:
    """Box plot des notes par niveau d'étude."""
    return px.box(
        df, x="niveau", y="note", color="niveau",
        title="Distribution des notes par niveau",
        labels={"niveau": "Niveau", "note": "Note /20"},
    )


# ──────────────────────────────────────────
# ANALYSES AVANCÉES
# ──────────────────────────────────────────

def scatter_etude_notes(df: pd.DataFrame) -> go.Figure:
    """Nuage de points : heures d'étude vs notes (tendance LOWESS)."""
    return px.scatter(
        df, x="heures_etude", y="note",
        size="humeur", color="matiere",
        trendline="lowess",
        title="Heures d'étude vs Notes obtenues",
        labels={"heures_etude": "Heures d'étude", "note": "Note /20"},
    )


def scatter_sommeil_notes(df: pd.DataFrame) -> go.Figure:
    """Nuage de points : heures de sommeil vs notes (tendance LOWESS)."""
    return px.scatter(
        df, x="heures_sommeil", y="note",
        color="humeur",
        trendline="lowess",
        title="Sommeil et notes",
        labels={"heures_sommeil": "Heures de sommeil", "note": "Note /20"},
        color_continuous_scale="Viridis",
    )
