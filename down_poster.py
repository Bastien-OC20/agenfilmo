"""
Fonctions de téléchargement des affiches de films
"""

import requests
import streamlit as st
from io import BytesIO
from PIL import Image
import zipfile


def download_single_image(movie):
    """
    Télécharge une seule image de film

    Args:
        movie (dict): Informations du film avec affiche_url

    Returns:
        dict: Données de l'image ou None en cas d'erreur
    """
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


def create_images_zip(movies_list):
    """
    Crée un fichier ZIP contenant toutes les images des films

    Args:
        movies_list (list): Liste des films sélectionnés

    Returns:
        BytesIO: Buffer contenant le fichier ZIP ou None
    """
    if not movies_list:
        return None

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for movie in movies_list:
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


def display_image_from_url(image_url, max_size=(150, 220)):
    """
    Affiche une image à partir d'une URL

    Args:
        image_url (str): URL de l'image
        max_size (tuple): Taille maximale (largeur, hauteur)

    Returns:
        PIL.Image: Image redimensionnée ou None
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        img.thumbnail(max_size)
        return img
    except Exception as e:
        st.error(f"Erreur lors du chargement de l'image: {str(e)}")
        return None


def get_image_dimensions(image_url):
    """
    Récupère les dimensions d'une image à partir de son URL

    Args:
        image_url (str): URL de l'image

    Returns:
        tuple: (largeur, hauteur) ou None en cas d'erreur
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        return img.size
    except Exception:
        return None


def validate_image_url(image_url):
    """
    Valide qu'une URL pointe vers une image accessible

    Args:
        image_url (str): URL à valider

    Returns:
        bool: True si l'image est accessible
    """
    try:
        response = requests.head(image_url, timeout=5)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()
        return content_type.startswith('image/')
    except Exception:
        return False
