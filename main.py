"""
Application Streamlit principale pour gérer les films du CDI d'un lycée.
Sélection multiple, aperçu, export Excel et impression.
"""

import streamlit as st
import pandas as pd
from datetime import datetime  # noqa: F401
from PIL import Image  # noqa: F401
from io import BytesIO  # noqa: F401

# Imports des modules personnalisés
from connexion import get_api_status
from search_movies import search_movies, search_by_filters
from down_poster import (
    download_single_image,
    create_images_zip,
    display_image_from_url
)
from create_worbook import (
    create_simple_excel,
    create_excel_with_images,
    create_csv_export,
    create_printable_html,
    get_export_filename
)

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


# ---------------- FONCTIONS D'AFFICHAGE ----------------
def display_movie_card(movie, index=None):
    """
    Affiche une carte de film avec image et informations
    """
    col1, col2 = st.columns([1, 3])

    # Créer une clé unique basée sur l'API, l'ID et l'index
    api_prefix = st.session_state.selected_api.lower()
    unique_id = f"{api_prefix}_{movie['id']}"
    if index is not None:
        unique_id += f"_{index}"

    with col1:
        if movie["affiche_url"]:
            img = display_image_from_url(movie["affiche_url"])
            if img:
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
        else:
            st.info("📷 Pas d'image disponible")

    with col2:
        st.subheader(movie["titre"])
        col_info1, col_info2 = st.columns(2)

        with col_info1:
            st.write(f"🎬 **Année :** {movie['annee']}")
            st.write(f"⭐ **Note :** {movie['note']}")

        with col_info2:
            st.write(f"📡 **Source :** {movie.get('api_source', 'N/A')}")

        # Résumé avec limitation de caractères
        resume_text = movie["resume"]
        if len(resume_text) > 200:
            resume_text = resume_text[:200] + "…"
        st.write(f"📝 **Résumé :** {resume_text}")

        # Bouton d'ajout à la sélection
        if st.button("➕ Ajouter à la sélection", key=f"add_{unique_id}"):
            if movie not in st.session_state.selected_movies:
                st.session_state.selected_movies.append(movie)
                st.success(f"'{movie['titre']}' ajouté à la sélection !")
                st.rerun()


def display_api_selector():
    """
    Affiche le sélecteur d'API dans la sidebar
    """
    st.header("🔧 Configuration API")

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
    api_status = get_api_status()

    if api_status[st.session_state.selected_api]["configured"]:
        st.success(f"✅ Clé {st.session_state.selected_api} configurée")
    else:
        st.error(f"❌ Clé {st.session_state.selected_api} manquante")

    st.markdown("---")


def display_search_filters():
    """
    Affiche les filtres de recherche avancée
    """
    with st.expander("🔍 Recherche avancée", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            year_filter = st.number_input(
                "Année (optionnel)",
                min_value=1900,
                max_value=2030,
                value=None,
                placeholder="Ex: 2020"
            )

        with col2:
            rating_filter = st.number_input(
                "Note minimale (optionnel)",
                min_value=0.0,
                max_value=10.0,
                value=None,
                step=0.1,
                placeholder="Ex: 7.0"
            )

        return {
            "year": year_filter,
            "min_rating": rating_filter
        }


def export_and_print_section():
    """
    Section d'export et d'impression
    """
    if not st.session_state.selected_movies:
        st.warning("Aucun film sélectionné.")
        return

    df = pd.DataFrame(st.session_state.selected_movies)
    display_columns = ["titre", "annee", "note", "resume", "api_source"]
    df_display = df[display_columns]

    st.subheader("📋 Films sélectionnés")
    st.dataframe(df_display, use_container_width=True)

    # Boutons d'export
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # EXPORT EXCEL SIMPLE
        excel_simple = create_simple_excel(st.session_state.selected_movies)
        if excel_simple:
            st.download_button(
                "📥 Excel simple",
                excel_simple,
                file_name=get_export_filename("excel_simple"),
                mime=("application/vnd.openxmlformats-officedocument"
                      ".spreadsheetml.sheet"),
                help="Tableau Excel sans les images"
            )

    with col2:
        # EXPORT CSV
        csv_data = create_csv_export(st.session_state.selected_movies)
        if csv_data:
            st.download_button(
                "📊 Export CSV",
                csv_data,
                file_name=get_export_filename("csv"),
                mime="text/csv",
                help="Export au format CSV"
            )

    with col3:
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
                            file_name=get_export_filename("excel_images"),
                            mime=("application/vnd.openxmlformats-"
                                  "officedocument.spreadsheetml.sheet"),
                            key="download_excel_images",
                            help="Tableau Excel avec les affiches intégrées"
                        )
                    else:
                        st.error(
                            "Impossible de créer le fichier Excel avec images"
                        )
                except Exception as e:
                    st.error(
                        f"Erreur lors de la création du fichier Excel: "
                        f"{str(e)}"
                    )

    with col4:
        # TÉLÉCHARGEMENT DES IMAGES EN ZIP
        if st.button("🖼️ Préparer ZIP des images"):
            with st.spinner("Création du fichier ZIP..."):
                zip_data = create_images_zip(st.session_state.selected_movies)
                if zip_data:
                    st.download_button(
                        "📦 ZIP des images",
                        data=zip_data,
                        file_name=get_export_filename("zip"),
                        mime="application/zip",
                        key="download_all_images"
                    )
                else:
                    st.error("Impossible de créer le fichier ZIP")

    # VERSION IMPRIMABLE
    st.subheader("🖨️ Version imprimable")
    printable_html = create_printable_html(st.session_state.selected_movies)
    if printable_html:
        st.markdown(printable_html, unsafe_allow_html=True)
        st.info("Utilisez Ctrl+P / Cmd+P pour imprimer le tableau")


# ---------------- BARRE LATÉRALE ----------------
with st.sidebar:
    # Configuration API
    display_api_selector()

    # Mode d'emploi
    st.header("📖 Mode d'emploi")
    st.markdown("""
    ### 🔍 Recherche de films
    1. Sélectionnez votre API (TMDB ou OMDb)
    2. Entrez le titre d'un film
    3. Utilisez les filtres avancés si nécessaire
    4. Cliquez sur "Rechercher"

    ### ➕ Sélection de films
    1. Parcourez les résultats
    2. Cliquez sur "➕ Ajouter à la sélection"
    3. Vos films apparaîtront dans "Sélection actuelle"

    ### 📥 Export et téléchargement
    - **Image individuelle** : Sous chaque affiche
    - **Excel simple** : Tableau sans images
    - **Excel avec images** : Affiches intégrées
    - **CSV** : Format tableur universel
    - **ZIP des images** : Toutes les images séparément
    """)

    st.markdown("---")

    # Sélection actuelle
    st.header("🎯 Sélection actuelle")
    if st.session_state.selected_movies:
        count = len(st.session_state.selected_movies)
        st.success(f"**{count} film(s) sélectionné(s)**")

        # Liste des films sélectionnés
        for i, movie in enumerate(st.session_state.selected_movies, 1):
            st.write(f"{i}. {movie['titre']} ({movie['annee']})")

        # Bouton pour vider la sélection
        if st.button("🗑️ Vider la sélection", type="secondary"):
            st.session_state.selected_movies = []
            st.success("Sélection vidée !")
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
        # Déclencher l'affichage de la section export dans le main
        st.session_state.show_export = True

    st.markdown("---")

    # Informations
    st.header("ℹ️ Informations")
    st.markdown(f"""
    **Application de gestion des films pour le CDI**

    Cette application utilise deux APIs :
    - **TMDB** : Films internationaux, descriptions détaillées
    - **OMDb** : Base de données IMDb, informations anglophones

    🎯 **Objectif :** Faciliter la gestion et l'inventaire des films
    disponibles au Centre de Documentation et d'Information.

    📋 **API actuelle :** {st.session_state.selected_api}
    """)


# ---------------- APPLICATION PRINCIPALE ----------------
st.title("🎬 Gestion des Films du CDI")

# Barre de recherche
search = st.text_input(
    "🔍 Rechercher un film",
    placeholder="Ex: Avatar, Inception, Le Parrain..."
)

# Filtres de recherche avancée
filters = display_search_filters()

# Bouton de recherche
if st.button("🔍 Rechercher", type="primary") and search:
    spinner_text = f"Recherche en cours via {st.session_state.selected_api}..."
    with st.spinner(spinner_text):
        # Application des filtres si définis
        active_filters = {k: v for k, v in filters.items() if v is not None}

        if active_filters:
            st.session_state.search_results = search_by_filters(
                search, st.session_state.selected_api, active_filters
            )
            filter_text = ', '.join([
                f'{k}={v}' for k, v in active_filters.items()
            ])
            st.info(f"Filtres appliqués: {filter_text}")
        else:
            st.session_state.search_results = search_movies(
                search, st.session_state.selected_api
            )

# Affichage des résultats
if st.session_state.search_results:
    st.subheader(
        f"📋 Résultats de recherche "
        f"({len(st.session_state.search_results)} films via "
        f"{st.session_state.selected_api})"
    )

    for index, movie in enumerate(st.session_state.search_results):
        display_movie_card(movie, index)
        st.divider()

elif search:
    st.warning("Aucun film trouvé pour cette recherche.")
else:
    st.info("👆 Entrez un titre de film et cliquez sur 'Rechercher' "
            "pour commencer.")

# Section export (si déclenchée depuis la sidebar)
if st.session_state.get('show_export', False):
    st.markdown("---")
    export_and_print_section()
    # Réinitialiser le flag
    st.session_state.show_export = False
