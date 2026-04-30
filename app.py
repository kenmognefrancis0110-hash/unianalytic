import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Test", layout="wide")
st.title("Test d'affichage")

# Données factices
df = pd.DataFrame({
    "x": [1, 2, 3, 4],
    "y": [10, 20, 15, 25]
})
fig = px.bar(df, x="x", y="y", title="Test graphique")
st.plotly_chart(fig, use_container_width=True)

st.success("Si vous voyez ce message, l'environnement fonctionne.")
