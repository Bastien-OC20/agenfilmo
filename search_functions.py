"""
Fonctions générales pour les APIs de recherche de films
"""

import requests
import streamlit as st
from connexion import get_api_config


def make_api_request(url, params, timeout=10):
    """
    Effectue une requête API avec gestion d'erreur

    Args:
        url (str): URL de l'API
        params (dict): Paramètres de la requête
        timeout (int): Timeout en secondes

    Returns:
        dict: Réponse JSON ou None en cas d'erreur
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la requête API: {str(e)}")
        return None
    except ValueError as e:
        st.error(f"Erreur de parsing JSON: {str(e)}")
        return None


def check_api_availability(api_name):
    """
    Vérifie si une API est disponible et configurée

    Args:
        api_name (str): Nom de l'API ('TMDB' ou 'OMDb')

    Returns:
        bool: True si l'API est disponible
    """
    config = get_api_config(api_name)
    if not config or not config.get('api_key'):
        st.warning(f"Clé API {api_name} non configurée")
        return False
    return True


def get_movie_details_tmdb(movie_id):
    """
    Récupère les détails complets d'un film TMDB incluant les crédits

    Args:
        movie_id (int): ID du film TMDB

    Returns:
        dict: Détails du film avec réalisateur
    """
    config = get_api_config("TMDB")
    if not config:
        return None

    # Récupérer les crédits pour avoir le réalisateur
    credits_url = f"{config['base_url']}/movie/{movie_id}/credits"
    credits_params = {
        "api_key": config['api_key'],
        "language": "fr-FR"
    }

    credits_data = make_api_request(credits_url, credits_params)
    director = "N/A"

    if credits_data and 'crew' in credits_data:
        # Chercher le réalisateur dans l'équipe technique
        for person in credits_data['crew']:
            if person.get('job') == 'Director':
                director = person.get('name', 'N/A')
                break

    return director


def format_movie_data(movie_data, api_name):
    """
    Formate les données de film selon un format uniforme

    Args:
        movie_data (dict): Données brutes du film
        api_name (str): Nom de l'API source

    Returns:
        dict: Données formatées
    """
    if api_name == "TMDB":
        # Récupérer le réalisateur si on a l'ID du film
        director = "N/A"
        if movie_data.get("id"):
            director = get_movie_details_tmdb(movie_data["id"]) or "N/A"

        return {
            "id": movie_data["id"],
            "titre": movie_data.get("title", "N/A"),
            "annee": movie_data.get("release_date", "")[:4] or "N/A",
            "resume": movie_data.get("overview", "Résumé non disponible"),
            "affiche_url": (
                f"{tmdb_config['image_base_url']}"
                f"{movie_data['poster_path']}"
                if (movie_data.get("poster_path") and
                    (tmdb_config := get_api_config('TMDB')) is not None and
                    tmdb_config.get('image_base_url'))
                else None
            ),
            "note": movie_data.get("vote_average", "N/A"),
            "realisateur": director,
            "api_source": "TMDB"
        }
    elif api_name == "OMDb":
        return {
            "id": movie_data["imdbID"],
            "titre": movie_data.get("Title", "N/A"),
            "annee": movie_data.get("Year", "N/A"),
            "resume": movie_data.get("Plot", "Résumé non disponible"),
            "affiche_url": (
                movie_data["Poster"]
                if movie_data.get("Poster") and movie_data["Poster"] != "N/A"
                else None
            ),
            "note": movie_data.get("imdbRating", "N/A"),
            "realisateur": movie_data.get("Director", "N/A"),
            "api_source": "OMDb"
        }
    else:
        return None
