"""
Application Streamlit pour gérer les films du CDI d'un lycée.
Sélection multiple, aperçu, export Excel et impression.
"""

import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import pandas as pd
from datetime import datetime
import zipfile
import os
import xlsxwriter

# ---------------- CONFIGURATION PAGE ----------------
st.set_page_config(
    page_title="Gestion Films CDI",
    page_icon="🎬",
    layout="wide"
)

# ---------------- CONFIGURATION TMDB ----------------
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w300"  # image plus petite

# ---------------- SESSION STATE ----------------
if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "selected_movies" not in st.session_state:
    st.session_state.selected_movies = []


# ---------------- FONCTIONS API ----------------
def search_movies_tmdb(query: str) -> list:
    if not query or not TMDB_API_KEY:
        return []

    response = requests.get(
        f"{TMDB_BASE_URL}/search/movie",
        params={
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "fr-FR",
            "include_adult": False,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    movies = []
    for movie in data.get("results", [])[:20]:
        movies.append(
            {
                "id": movie["id"],
                "titre": movie.get("title", "N/A"),
                "annee": movie.get("release_date", "")[:4] or "N/A",
                "resume": movie.get("overview", "Résumé non disponible"),
                "affiche_url": (
                    f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}"
                    if movie.get("poster_path")
                    else None
                ),
                "note": movie.get("vote_average", "N/A"),
            }
        )
    return movies


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

                except Exception as e:
                    st.warning(f"Impossible de télécharger l'image pour "
                              f"{movie['titre']}: {str(e)}")
                    continue

    zip_buffer.seek(0)
    return zip_buffer


def create_excel_with_images():
    """Crée un fichier Excel avec les images intégrées"""
    if not st.session_state.selected_movies:
        return None

    excel_buffer = BytesIO()

    # Créer un workbook avec xlsxwriter
    workbook = xlsxwriter.Workbook(excel_buffer, {'in_memory': True})
    worksheet = workbook.add_worksheet("Films CDI")

    # Formats pour l'en-tête et les cellules
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    cell_format = workbook.add_format({
        'text_wrap': True,
        'valign': 'top',
        'border': 1
    })

    # En-têtes des colonnes
    headers = ['Affiche', 'Titre', 'Année', 'Note', 'Résumé']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Définir les largeurs des colonnes
    worksheet.set_column(0, 0, 15)  # Colonne affiche
    worksheet.set_column(1, 1, 25)  # Titre
    worksheet.set_column(2, 2, 8)   # Année
    worksheet.set_column(3, 3, 8)   # Note
    worksheet.set_column(4, 4, 50)  # Résumé

    # Ajouter les données et images
    for row, movie in enumerate(st.session_state.selected_movies, 1):
        # Définir la hauteur de la ligne pour l'image
        worksheet.set_row(row, 120)  # 120 points ≈ 160 pixels

        # Insérer l'image si disponible
        if movie.get("affiche_url"):
            try:
                response = requests.get(movie["affiche_url"], timeout=10)
                response.raise_for_status()

                # Créer un BytesIO pour l'image
                image_buffer = BytesIO(response.content)

                # Insérer l'image dans la cellule
                worksheet.insert_image(row, 0, f"image_{row}.jpg", {
                    'image_data': image_buffer,
                    'x_scale': 0.3,  # Réduire la taille
                    'y_scale': 0.3,
                    'x_offset': 5,
                    'y_offset': 5
                })
            except Exception as e:
                worksheet.write(row, 0, "Image indisponible", cell_format)
        else:
            worksheet.write(row, 0, "Pas d'image", cell_format)

        # Ajouter les autres données
        worksheet.write(row, 1, movie["titre"], cell_format)
        worksheet.write(row, 2, str(movie["annee"]), cell_format)
        worksheet.write(row, 3, str(movie["note"]), cell_format)
        worksheet.write(row, 4, movie["resume"], cell_format)

    workbook.close()
    excel_buffer.seek(0)
    return excel_buffer


# ---------------- AFFICHAGE FILM ----------------
def display_movie_card(movie):
    col1, col2 = st.columns([1, 3])

    with col1:
        if movie["affiche_url"]:
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
                    key=f"img_{movie['id']}",
                    use_container_width=True
                )
        else:
            st.info("📷 Pas d'image disponible")

    with col2:
        st.subheader(movie["titre"])
        st.write(f"🎬 Année : {movie['annee']} | ⭐ {movie['note']}")
        st.write(movie["resume"][:200] + "…")

        if st.button("➕ Ajouter à la sélection", key=f"add_{movie['id']}"):
            if movie not in st.session_state.selected_movies:
                st.session_state.selected_movies.append(movie)


# ---------------- EXPORT & IMPRESSION ----------------
def export_and_print():
    if not st.session_state.selected_movies:
        st.warning("Aucun film sélectionné.")
        return

    df = pd.DataFrame(st.session_state.selected_movies)
    df = df[["titre", "annee", "note", "resume"]]

    st.subheader("📋 Films sélectionnés")
    st.dataframe(df, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        # EXPORT EXCEL SIMPLE (sans images)
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        st.download_button(
            "📥 Excel simple",
            excel_buffer,
            file_name="films_cdi_simple.xlsx",
            mime=("application/vnd.openxmlformats-officedocument"
                  ".spreadsheetml.sheet"),
            help="Tableau Excel sans les images"
        )

    with col2:
        # EXPORT EXCEL AVEC IMAGES
        if st.button("📊 Préparer Excel avec images"):
            with st.spinner("Création du fichier Excel avec images..."):
                try:
                    excel_with_images = create_excel_with_images()
                    if excel_with_images:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            "📥 Excel avec images",
                            data=excel_with_images,
                            file_name=f"films_cdi_avec_images_{timestamp}.xlsx",
                            mime=("application/vnd.openxmlformats-"
                                  "officedocument.spreadsheetml.sheet"),
                            key="download_excel_images",
                            help="Tableau Excel avec les affiches intégrées"
                        )
                    else:
                        st.error("Impossible de créer le fichier Excel avec "
                                 "images")
                except Exception as e:
                    st.error(f"Erreur lors de la création du fichier Excel: "
                            f"{str(e)}")
    
    with col3:
        # TÉLÉCHARGEMENT DES IMAGES EN ZIP
        if st.button("🖼️ Préparer ZIP des images"):
            with st.spinner("Création du fichier ZIP..."):
                zip_data = create_images_zip()
                if zip_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "📦 ZIP des images",
                        data=zip_data,
                        file_name=f"images_films_{timestamp}.zip",
                        mime="application/zip",
                        key="download_all_images"
                    )
                else:
                    st.error("Impossible de créer le fichier ZIP")

    # VERSION IMPRIMABLE
    st.subheader("🖨️ Version imprimable")
    st.markdown(df.to_html(index=False), unsafe_allow_html=True)
    st.info("Utilisez Ctrl+P / Cmd+P pour imprimer le tableau")


# ---------------- BARRE LATERALE ----------------
with st.sidebar:
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
            st.write(f"{i}. {m['titre']} ({m['annee']})")

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

    Cette application utilise l'API TMDB (The Movie Database) pour
    rechercher des informations sur les films.

    🎯 **Objectif :** Faciliter la gestion et l'inventaire des films
    disponibles au Centre de Documentation et d'Information.
    """)


# ---------------- APPLICATION PRINCIPALE ----------------
st.title("🎬 Gestion des Films du CDI")

search = st.text_input(
    "🔍 Rechercher un film",
    placeholder="Ex: Avatar, Inception, Le Parrain..."
)
if st.button("🔍 Rechercher", type="primary") and search:
    with st.spinner("Recherche en cours..."):
        st.session_state.search_results = search_movies_tmdb(search)

# Résultats
if st.session_state.search_results:
    st.subheader(
        f"📋 Résultats de recherche "
        f"({len(st.session_state.search_results)} films)"
    )
    for movie in st.session_state.search_results:
        display_movie_card(movie)
        st.divider()
elif search:
    st.warning("Aucun film trouvé pour cette recherche.")
else:
    st.info("👆 Entrez un titre de film et cliquez sur 'Rechercher' pour "
            "commencer.")
