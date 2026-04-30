# 🎓 UniAnalytics Pro

Tableau de bord analytique pour la gestion des étudiants, des notes et des performances académiques. Construit avec **Streamlit**, **SQLite** et **Plotly**.

---

## Structure du projet

```
unianalytics/
├── app.py              # Point d'entrée Streamlit (UI + navigation)
├── database.py         # Couche d'accès aux données SQLite
├── seed.py             # Génération des données fictives
├── charts.py           # Fonctions de visualisation Plotly
├── requirements.txt    # Dépendances Python
├── .streamlit/
│   └── config.toml     # Thème et configuration serveur
└── README.md
```

---

## Installation

### 1. Cloner / copier le projet

```bash
cd unianalytics
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

> **Note :** `faker` est optionnel. Sans lui, des noms génériques (`Nom1`, `Prenom1`…) sont utilisés.

---

## Lancement

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement sur [http://localhost:8501](http://localhost:8501).

Au **premier lancement**, 25 étudiants fictifs sont générés automatiquement avec leurs notes et sessions d'étude.

---

## Pages disponibles

| Page | Description |
|---|---|
| 📊 Dashboard | KPIs globaux, distribution des notes, corrélations |
| 👥 Étudiants | Liste, recherche, ajout d'étudiants |
| 📝 Notes | Saisie et consultation filtrée des notes |
| 📈 Performances | Moyennes par filière, matière et niveau |
| 🔬 Analyses | Corrélations étude/sommeil/notes (scatter + heatmap) |
| ⚙️ Administration | Régénération et réinitialisation de la base |

---

## Base de données

La base SQLite (`unianalytics_pro.db`) est créée automatiquement dans le répertoire courant. Elle contient trois tables :

- **etudiants** — identité, filière, niveau
- **notes** — note, matière, coefficient, session, année académique
- **sessions_etude** — heures d'étude, sommeil, humeur

Pour **réinitialiser** les données, utilisez la page ⚙️ Administration.

---

## Peupler manuellement (CLI)

```bash
python seed.py
```

---

## Dépendances principales

| Package | Rôle |
|---|---|
| `streamlit` | Framework UI |
| `plotly` | Visualisations interactives |
| `pandas` | Manipulation des données |
| `faker` *(optionnel)* | Noms et dates réalistes |
