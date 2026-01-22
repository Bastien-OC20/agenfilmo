"""
Configuration et gestion des connexions aux APIs
TMDB (The Movie Database) et OMDb (Open Movie Database)
"""

import streamlit as st

# ---------------- CONFIGURATION TMDB ----------------
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w300"  # image plus petite

# ---------------- CONFIGURATION OMDB ----------------
# Alternative: OMDb API (plus simple mais moins de données)
# Pour utiliser OMDb, configurez OMDB_API_KEY dans .streamlit/secrets.toml
# Exemple d'URL: http://www.omdbapi.com/?i=tt3896198&apikey=VOTRE_CLE
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY")
OMDB_BASE_URL = "http://www.omdbapi.com/"


def get_api_status():
    """
    Retourne le statut des clés API configurées
    """
    return {
        "TMDB": {
            "configured": bool(TMDB_API_KEY),
            "key": TMDB_API_KEY
        },
        "OMDb": {
            "configured": bool(OMDB_API_KEY),
            "key": OMDB_API_KEY
        }
    }


def get_api_config(api_name):
    """
    Retourne la configuration pour une API spécifique
    """
    if api_name == "TMDB":
        return {
            "api_key": TMDB_API_KEY,
            "base_url": TMDB_BASE_URL,
            "image_base_url": TMDB_IMAGE_BASE_URL
        }
    elif api_name == "OMDb":
        return {
            "api_key": OMDB_API_KEY,
            "base_url": OMDB_BASE_URL
        }
    else:
        return None
