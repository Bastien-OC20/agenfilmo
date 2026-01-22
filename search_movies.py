"""
Fonctions spécifiques de recherche de films
Recherche par nom, titre, année, réalisateurs, résumé, affiche et note
"""

import streamlit as st
from connexion import get_api_config
from search_functions import (
    make_api_request,
    check_api_availability,
    format_movie_data
)


def search_movies_tmdb(query: str) -> list:
    """
    Recherche de films via l'API TMDB

    Args:
        query (str): Terme de recherche

    Returns:
        list: Liste des films trouvés
    """
    if not query or not check_api_availability("TMDB"):
        return []

    config = get_api_config("TMDB")
    if not config:
        return []

    url = f"{config['base_url']}/search/movie"
    params = {
        "api_key": config['api_key'],
        "query": query,
        "language": "fr-FR",
        "include_adult": False,
    }

    data = make_api_request(url, params)
    if not data:
        return []

    movies = []
    for movie in data.get("results", [])[:20]:
        formatted_movie = format_movie_data(movie, "TMDB")
        if formatted_movie:
            movies.append(formatted_movie)

    return movies


def search_movies_omdb(query: str) -> list:
    """
    Recherche de films via l'API OMDb

    Args:
        query (str): Terme de recherche

    Returns:
        list: Liste des films trouvés
    """
    if not query or not check_api_availability("OMDb"):
        return []

    config = get_api_config("OMDb")
    if not config:
        return []

    # Recherche avec le titre principal
    search_params = {
        "apikey": config['api_key'],
        "s": query,
        "type": "movie",
    }

    data = make_api_request(config['base_url'], search_params)
    if not data or data.get("Response") != "True" or "Search" not in data:
        return []

    movies = []
    for movie in data["Search"][:20]:
        # Pour chaque film, on fait une requête détaillée
        detail_params = {
            "apikey": config['api_key'],
            "i": movie["imdbID"],
            "plot": "full"
        }

        detail_data = make_api_request(config['base_url'], detail_params)

        if detail_data and detail_data.get("Response") == "True":
            formatted_movie = format_movie_data(detail_data, "OMDb")
            if formatted_movie:
                movies.append(formatted_movie)
        else:
            # Si la requête détaillée échoue, on utilise les infos de base
            basic_movie = {
                "imdbID": movie["imdbID"],
                "Title": movie.get("Title", "N/A"),
                "Year": movie.get("Year", "N/A"),
                "Plot": "Résumé non disponible",
                "Poster": (movie.get("Poster")
                           if movie.get("Poster") != "N/A" else None),
                "imdbRating": "N/A",
            }
            formatted_movie = format_movie_data(basic_movie, "OMDb")
            if formatted_movie:
                movies.append(formatted_movie)

    return movies


def search_movies(query: str, api_name: str) -> list:
    """
    Fonction de recherche unifiée qui utilise l'API sélectionnée

    Args:
        query (str): Terme de recherche
        api_name (str): Nom de l'API à utiliser ('TMDB' ou 'OMDb')

    Returns:
        list: Liste des films trouvés
    """
    if api_name == "TMDB":
        return search_movies_tmdb(query)
    elif api_name == "OMDb":
        return search_movies_omdb(query)
    else:
        st.error(f"API '{api_name}' non reconnue")
        return []


def search_by_filters(
    query: str, api_name: str, filters: dict | None = None
) -> list:
    """
    Recherche avancée avec filtres (année, réalisateur, etc.)

    Args:
        query (str): Terme de recherche principal
        api_name (str): Nom de l'API
        filters (dict): Filtres optionnels (année, réalisateur, etc.)

    Returns:
        list: Liste des films filtrés
    """
    # Recherche de base
    movies = search_movies(query, api_name)

    if not filters:
        return movies

    # Application des filtres
    filtered_movies = []
    for movie in movies:
        include_movie = True

        # Filtre par année
        if filters.get('year') and movie['annee'] != "N/A":
            if str(filters['year']) not in movie['annee']:
                include_movie = False

        # Filtre par note minimale
        if filters.get('min_rating') and movie['note'] != "N/A":
            try:
                if float(movie['note']) < float(filters['min_rating']):
                    include_movie = False
            except (ValueError, TypeError):
                pass

        if include_movie:
            filtered_movies.append(movie)

    return filtered_movies
