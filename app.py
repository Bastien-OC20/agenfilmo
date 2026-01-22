"""
Application Streamlit pour gérer les films du CDI d'un lycée.
Sélection multiple, aperçu, export Excel et impression.
"""

import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import pandas as pd
from datetime import datetime # noqa: F401
import zipfile

# Import des modules locaux
from search_movies import search_movies
from create_worbook import (
    create_simple_excel,
    create_excel_with_images,
    create_csv_export,
    create_printable_html,
    get_export_filename
)
from connexion import get_api_config

# ---------------- CONFIGURATION PAGE ----------------
st.set_page_config(
    page_title="Gestion Films CDI",
    page_icon="🎬",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "selected_movies" not in st.session_state:
    st.session_state.selected_movies = []

if "selected_api" not in st.session_state:
    st.session_state.selected_api = "TMDB"


# ---------------- TÉLÉCHARGEMENT D'IMAGES ----------------
def download_single_image(movie):
    """Télécharge une seule image de film"""
    if not movie.get("affiche_url"):
        st.error(f"Aucune image disponible pour {movie['titre']}")
        return None

    try:
        response = requests.get(movie["affiche_url"], timeout=10)
        response.raise_for_status()

        # Créer un nom de fichier sûr
        safe_filename = "".join(
            c for c in movie["titre"]
            if c.isalnum() or c in (' ', '-', '_')
        ).rstrip()
        filename = f"{safe_filename}_{movie['annee']}.jpg"

        return {
            "data": response.content,
            "filename": filename,
            "mime": "image/jpeg"
        }
    except Exception as e:
        st.error(f"Erreur lors du téléchargement de l'image pour "
                 f"{movie['titre']}: {str(e)}")
        return None


def create_images_zip():
    """Crée un fichier ZIP contenant toutes les images des films"""
    if not st.session_state.selected_movies:
        return None

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for movie in st.session_state.selected_movies:
            if movie.get("affiche_url"):
                try:
                    response = requests.get(movie["affiche_url"], timeout=10)
                    response.raise_for_status()

                    # Créer un nom de fichier sûr
                    safe_filename = "".join(
                        c for c in movie["titre"]
                        if c.isalnum() or c in (' ', '-', '_')
                    ).rstrip()
                    filename = f"{safe_filename}_{movie['annee']}.jpg"

                    # Ajouter l'image au ZIP
                    zip_file.writestr(filename, response.content)

                except Exception:
                    st.warning(f"Impossible de télécharger l'image pour "
                               f"{movie['titre']}")
                    continue

    zip_buffer.seek(0)
    return zip_buffer


# ---------------- AFFICHAGE FILM ----------------
def display_movie_card(movie, index=None):
    col1, col2 = st.columns([1, 3])

    # Créer une clé unique basée sur l'API, l'ID et l'index
    api_prefix = st.session_state.selected_api.lower()
    unique_id = f"{api_prefix}_{movie['id']}"
    if index is not None:
        unique_id += f"_{index}"

    with col1:
        if movie["affiche_url"]:
            try:
                response = requests.get(movie["affiche_url"])
                img = Image.open(BytesIO(response.content))
                img.thumbnail((150, 220))
                st.image(img)

                # Bouton de téléchargement individuel de l'image
                image_data = download_single_image(movie)
                if image_data:
                    st.download_button(
                        "📥 Télécharger l'image",
                        data=image_data["data"],
                        file_name=image_data["filename"],
                        mime=image_data["mime"],
                        key=f"img_{unique_id}",
                        use_container_width=True
                    )
            except Exception:
                st.info("📷 Erreur de chargement d'image")
        else:
            st.info("📷 Pas d'image disponible")

    with col2:
        st.subheader(movie["titre"])
        info_line = f"🎬 Année : {movie['annee']}"
        if movie.get('realisateur') and movie['realisateur'] != 'N/A':
            info_line += f" | 🎭 Réalisateur : {movie['realisateur']}"
        info_line += f" | ⭐ {movie['note']}"
        st.write(info_line)
        resume_text = (movie["resume"][:200] + "…"
                       if len(movie["resume"]) > 200
                       else movie["resume"])
        st.write(resume_text)

        if st.button("➕ Ajouter à la sélection", key=f"add_{unique_id}"):
            if movie not in st.session_state.selected_movies:
                st.session_state.selected_movies.append(movie)
                st.success(f"Film '{movie['titre']}' ajouté à la sélection!")
                st.rerun()


# ---------------- EXPORT & IMPRESSION ----------------
def export_and_print():
    if not st.session_state.selected_movies:
        st.warning("Aucun film sélectionné.")
        return

    # Préparer les colonnes à afficher
    columns = ["titre", "annee", "note", "resume"]
    if any(movie.get('realisateur') and movie['realisateur'] != 'N/A'
           for movie in st.session_state.selected_movies):
        columns.insert(2, "realisateur")

    df = pd.DataFrame(st.session_state.selected_movies)
    df = df[columns]

    st.subheader("📋 Films sélectionnés")
    st.dataframe(df, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # EXPORT EXCEL SIMPLE (sans images)
        simple_excel = create_simple_excel(st.session_state.selected_movies)
        if simple_excel:
            st.download_button(
                "📥 Excel simple",
                simple_excel,
                file_name=get_export_filename('excel_simple'),
                mime=("application/vnd.openxmlformats-officedocument"
                      ".spreadsheetml.sheet"),
                help="Tableau Excel sans les images"
            )

    with col2:
        # EXPORT EXCEL AVEC IMAGES
        if st.button("📊 Préparer Excel avec images"):
            with st.spinner("Création du fichier Excel avec images..."):
                try:
                    excel_with_images = create_excel_with_images(
                        st.session_state.selected_movies
                    )
                    if excel_with_images:
                        st.download_button(
                            "📥 Excel avec images",
                            data=excel_with_images,
                            file_name=get_export_filename('excel_images'),
                            mime=("application/vnd.openxmlformats-"
                                  "officedocument.spreadsheetml.sheet"),
                            key="download_excel_images",
                            help="Tableau Excel avec les affiches intégrées"
                        )
                    else:
                        st.error("Impossible de créer le fichier Excel "
                                 "avec images")
                except Exception as e:
                    st.error(f"Erreur lors de la création du fichier Excel: "
                             f"{str(e)}")

    with col3:
        # EXPORT CSV
        csv_data = create_csv_export(st.session_state.selected_movies)
        if csv_data:
            st.download_button(
                "📄 Export CSV",
                csv_data,
                file_name=get_export_filename('csv'),
                mime="text/csv",
                help="Export au format CSV"
            )

    with col4:
        # TÉLÉCHARGEMENT DES IMAGES EN ZIP
        if st.button("🖼️ Préparer ZIP des images"):
            with st.spinner("Création du fichier ZIP..."):
                zip_data = create_images_zip()
                if zip_data:
                    st.download_button(
                        "📦 ZIP des images",
                        data=zip_data,
                        file_name=get_export_filename('zip'),
                        mime="application/zip",
                        key="download_all_images"
                    )
                else:
                    st.error("Impossible de créer le fichier ZIP")

    # VERSION IMPRIMABLE
    st.subheader("🖨️ Version imprimable")
    html_content = create_printable_html(st.session_state.selected_movies)
    if html_content:
        st.markdown(html_content, unsafe_allow_html=True)
        st.info("Utilisez Ctrl+P / Cmd+P pour imprimer le tableau")


# ---------------- BARRE LATERALE ----------------
with st.sidebar:
    st.header("⚙️ Configuration API")

    # Sélecteur d'API
    api_choice = st.selectbox(
        "Choisir l'API de recherche :",
        ["TMDB", "OMDb"],
        index=0 if st.session_state.selected_api == "TMDB" else 1,
        help=("TMDB: Plus d'informations, images haute qualité. "
              "OMDb: Plus simple, données IMDb.")
    )

    if api_choice != st.session_state.selected_api:
        st.session_state.selected_api = api_choice
        # Vider les résultats de recherche lors du changement d'API
        st.session_state.search_results = []
        st.rerun()

    # Statut des clés API
    tmdb_config = get_api_config("TMDB")
    omdb_config = get_api_config("OMDb")

    if st.session_state.selected_api == "TMDB":
        if tmdb_config and tmdb_config.get('api_key'):
            st.success("✅ Clé TMDB configurée")
        else:
            st.error("❌ Clé TMDB manquante")
    else:
        if omdb_config and omdb_config.get('api_key'):
            st.success("✅ Clé OMDb configurée")
        else:
            st.error("❌ Clé OMDb manquante")

    st.markdown("---")

    st.header("📖 Mode d'emploi")

    st.markdown("""
    ### 🔍 Recherche de films
    1. Entrez le titre d'un film dans la barre de recherche
    2. Cliquez sur "Rechercher" pour lancer la recherche
    3. Les résultats s'afficheront sous forme de cartes

    ### ➕ Sélection de films
    1. Parcourez les résultats de recherche
    2. Cliquez sur "➕ Ajouter à la sélection" pour chaque film souhaité
    3. Vos films sélectionnés apparaîtront dans la section "Sélection actuelle"

    ### 📥 Téléchargement et export
    - **Image individuelle** : Sous chaque affiche
    - **Excel simple** : Tableau sans images
    - **Excel avec images** : Tableau avec affiches intégrées
    - **CSV** : Export au format CSV
    - **ZIP des images** : Toutes les images séparément

    ### 📤 Export et impression
    1. Sélectionnez vos films
    2. Cliquez sur "📤 Exporter / Imprimer"
    3. Choisissez le format souhaité
    """)

    st.markdown("---")

    st.header("🎯 Sélection actuelle")
    if st.session_state.selected_movies:
        st.success(
            f"**{len(st.session_state.selected_movies)} "
            f"film(s) sélectionné(s)**"
        )
        for i, m in enumerate(st.session_state.selected_movies, 1):
            director_info = ""
            if m.get('realisateur') and m['realisateur'] != 'N/A':
                director_info = f" - {m['realisateur']}"
            st.write(f"{i}. {m['titre']} ({m['annee']}){director_info}")

        # Bouton pour vider la sélection
        if st.button("🗑️ Vider la sélection", type="secondary"):
            st.session_state.selected_movies = []
            st.rerun()
    else:
        st.info("Aucun film sélectionné")

    st.markdown("---")

    # Export
    if st.button(
        "📤 Exporter / Imprimer",
        type="primary",
        use_container_width=True
    ):
        export_and_print()

    st.markdown("---")

    st.header("ℹ️ Informations")
    st.markdown("""
    **Application de gestion des films pour le CDI**

    Cette application peut utiliser deux APIs différentes :
    - **TMDB** (The Movie Database) : Plus d'informations, images HD
    - **OMDb** (Open Movie Database) : Plus simple, données IMDb

    🎯 **Objectif :** Faciliter la gestion et l'inventaire des films
    disponibles au Centre de Documentation et d'Information.

    📋 **API actuelle :** {}
    """.format(st.session_state.selected_api))


# ---------------- APPLICATION PRINCIPALE ----------------
st.title("🎬 Gestion des Films du CDI")

search = st.text_input(
    "🔍 Rechercher un film",
    placeholder="Ex: Avatar, Inception, Le Parrain..."
)
if st.button("🔍 Rechercher", type="primary") and search:
    with st.spinner(f"Recherche en cours via "
                    f"{st.session_state.selected_api}..."):
        st.session_state.search_results = search_movies(
            search, st.session_state.selected_api
        )

# Résultats
if st.session_state.search_results:
    st.subheader(
        f"📋 Résultats de recherche "
        f"({len(st.session_state.search_results)} films)"
    )
    for index, movie in enumerate(st.session_state.search_results):
        display_movie_card(movie, index)
        st.divider()
elif search:
    st.warning("Aucun film trouvé pour cette recherche.")
else:
    st.info("👆 Entrez un titre de film et cliquez sur 'Rechercher' pour "
            "commencer.")
