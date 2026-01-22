"""
Configuration et gestion des connexions aux APIs
TMDB (The Movie Database) et OMDb (Open Movie Database)
"""

import streamlit as st

# ---------------- CONFIGURATION TMDB ----------------
TMDB_API_KEY = (st.secrets.get("TMDB_API_KEY") or
                "f33777ec358d3512b768a560f2817f19")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w300"  # image plus petite

# Debug pour vérifier les secrets (à supprimer en production)
if TMDB_API_KEY:
    st.write(f"✅ TMDB API Key configurée: {TMDB_API_KEY[:8]}...")
else:
    st.error("❌ TMDB API Key manquante dans les secrets Streamlit Cloud")

# ---------------- CONFIGURATION OMDB ----------------
# Alternative: OMDb API (plus simple mais moins de données)
# Pour utiliser OMDb, configurez OMDB_API_KEY dans .streamlit/secrets.toml
# Exemple d'URL: http://www.omdbapi.com/?i=tt3896198&apikey=VOTRE_CLE
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY") or "4b5174cf"
OMDB_BASE_URL = "http://www.omdbapi.com/"

# Debug pour vérifier les secrets (à supprimer en production)
if OMDB_API_KEY:
    st.write(f"✅ OMDb API Key configurée: {OMDB_API_KEY[:8]}...")
else:
    st.error("❌ OMDb API Key manquante dans les secrets Streamlit Cloud")


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
