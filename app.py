"""
Application Streamlit pour gérer les films du CDI d'un lycée.
Permet de rechercher, afficher et exporter des informations sur les films.
"""

import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Gestion Films CDI",
    page_icon="🎬",
    layout="wide"
)

# API TMDB (The Movie Database)
# Note: Pour une utilisation en production, créez votre propre clé API gratuite sur https://www.themoviedb.org/settings/api
TMDB_API_KEY = "YOUR_API_KEY_HERE"  # À remplacer par votre clé API
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Alternative: OMDb API (plus simple mais moins de données)
# Pour utiliser OMDb, décommentez les lignes suivantes et commentez TMDB
# OMDB_API_KEY = "YOUR_API_KEY_HERE"
# OMDB_BASE_URL = "http://www.omdbapi.com/"


def search_movies_tmdb(query):
    """
    Recherche des films via l'API TMDB.
    
    Args:
        query (str): Terme de recherche
        
    Returns:
        list: Liste des films trouvés
    """
    if not query:
        return []
    
    # Si l'utilisateur n'a pas configuré de clé API, retourner des données de démonstration
    if TMDB_API_KEY == "YOUR_API_KEY_HERE":
        return get_demo_movies(query)
    
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "fr-FR",
            "include_adult": False
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        movies = []
        
        for movie in data.get("results", [])[:20]:  # Limiter à 20 résultats
            # Obtenir les détails du film pour avoir le réalisateur
            movie_details = get_movie_details_tmdb(movie["id"])
            
            movies.append({
                "id": movie["id"],
                "titre": movie.get("title", "N/A"),
                "titre_original": movie.get("original_title", "N/A"),
                "annee": movie.get("release_date", "")[:4] if movie.get("release_date") else "N/A",
                "resume": movie.get("overview", "Résumé non disponible"),
                "affiche_url": f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
                "realisateur": movie_details.get("realisateur", "N/A"),
                "note": movie.get("vote_average", 0)
            })
        
        return movies
    
    except Exception as e:
        st.error(f"Erreur lors de la recherche : {str(e)}")
        return []


def get_movie_details_tmdb(movie_id):
    """
    Obtient les détails d'un film incluant le réalisateur.
    
    Args:
        movie_id (int): ID du film
        
    Returns:
        dict: Détails du film
    """
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "fr-FR"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Trouver le réalisateur
        directors = [crew["name"] for crew in data.get("crew", []) if crew.get("job") == "Director"]
        realisateur = ", ".join(directors) if directors else "N/A"
        
        return {"realisateur": realisateur}
    
    except Exception as e:
        return {"realisateur": "N/A"}


def get_demo_movies(query):
    """
    Retourne des données de démonstration pour tester l'application sans clé API.
    
    Args:
        query (str): Terme de recherche
        
    Returns:
        list: Liste de films de démonstration
    """
    demo_data = [
        {
            "id": 1,
            "titre": "Inception",
            "titre_original": "Inception",
            "annee": "2010",
            "resume": "Dom Cobb est un voleur expérimenté dans l'art périlleux de l'extraction : sa spécialité consiste à s'approprier les secrets les plus précieux d'un individu, enfouis au plus profond de son subconscient, pendant qu'il rêve et que son esprit est particulièrement vulnérable.",
            "affiche_url": None,
            "realisateur": "Christopher Nolan",
            "note": 8.8
        },
        {
            "id": 2,
            "titre": "Le Parrain",
            "titre_original": "The Godfather",
            "annee": "1972",
            "resume": "En 1945, à New York, les Corleone sont une des cinq familles de la mafia. Don Vito Corleone, parrain de cette famille, marie sa fille à un bookmaker. Sollozzo, parrain de la famille Tattaglia, propose à Don Vito une association dans le trafic de drogue, mais celui-ci refuse.",
            "affiche_url": None,
            "realisateur": "Francis Ford Coppola",
            "note": 9.2
        },
        {
            "id": 3,
            "titre": "La Liste de Schindler",
            "titre_original": "Schindler's List",
            "annee": "1993",
            "resume": "Evocation des années de guerre d'Oskar Schindler, industriel autrichien rentré à Cracovie en 1939 avec les troupes allemandes. Il va, tout au long de la guerre, protéger des juifs en les faisant travailler dans sa fabrique de casseroles.",
            "affiche_url": None,
            "realisateur": "Steven Spielberg",
            "note": 9.0
        }
    ]
    
    # Filtrer les films de démo selon la requête
    query_lower = query.lower()
    filtered = [movie for movie in demo_data if query_lower in movie["titre"].lower() or query_lower in movie["titre_original"].lower()]
    
    if not filtered:
        # Si aucun match, retourner tous les films de démo
        return demo_data
    
    return filtered


def display_movie_card(movie, col, index):
    """
    Affiche une carte de film dans une colonne.
    
    Args:
        movie (dict): Informations du film
        col: Colonne Streamlit
        index (int): Index du film
    """
    with col:
        with st.container():
            st.markdown("---")
            
            # Checkbox pour sélectionner le film
            selected = st.checkbox(
                f"Sélectionner",
                key=f"select_{index}",
                value=st.session_state.get(f"selected_{index}", False)
            )
            st.session_state[f"selected_{index}"] = selected
            
            # Titre
            st.subheader(f"🎬 {movie['titre']}")
            
            # Affiche
            if movie.get("affiche_url"):
                try:
                    response = requests.get(movie["affiche_url"], timeout=10)
                    img = Image.open(BytesIO(response.content))
                    st.image(img, use_container_width=True)
                except:
                    st.info("📽️ Affiche non disponible")
            else:
                st.info("📽️ Affiche non disponible")
            
            # Informations
            st.write(f"**Année :** {movie['annee']}")
            st.write(f"**Réalisateur :** {movie['realisateur']}")
            if movie.get("note"):
                st.write(f"**Note :** ⭐ {movie['note']}/10")
            
            # Résumé
            with st.expander("📖 Résumé"):
                st.write(movie['resume'])


def export_selected_movies():
    """
    Exporte les films sélectionnés en CSV et affiche un aperçu pour impression.
    """
    if "search_results" not in st.session_state or not st.session_state.search_results:
        st.warning("Aucun résultat de recherche disponible.")
        return
    
    selected_movies = []
    for i, movie in enumerate(st.session_state.search_results):
        if st.session_state.get(f"selected_{i}", False):
            selected_movies.append({
                "Titre": movie["titre"],
                "Titre Original": movie["titre_original"],
                "Année": movie["annee"],
                "Réalisateur": movie["realisateur"],
                "Résumé": movie["resume"],
                "Note": movie.get("note", "N/A")
            })
    
    if not selected_movies:
        st.warning("Aucun film sélectionné. Veuillez cocher au moins un film.")
        return
    
    # Créer un DataFrame
    df = pd.DataFrame(selected_movies)
    
    # Section d'exportation
    st.subheader("📊 Films sélectionnés")
    
    # Afficher le tableau
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Bouton de téléchargement CSV
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    st.download_button(
        label="📥 Télécharger en CSV",
        data=csv,
        file_name=f"films_cdi_{timestamp}.csv",
        mime="text/csv",
    )
    
    # Version imprimable
    st.subheader("🖨️ Version imprimable")
    
    print_content = "# LISTE DES FILMS - CDI\n\n"
    print_content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    print_content += "---\n\n"
    
    for i, movie_data in enumerate(selected_movies, 1):
        print_content += f"## {i}. {movie_data['Titre']}\n\n"
        print_content += f"**Titre original :** {movie_data['Titre Original']}\n\n"
        print_content += f"**Année :** {movie_data['Année']}\n\n"
        print_content += f"**Réalisateur :** {movie_data['Réalisateur']}\n\n"
        print_content += f"**Note :** {movie_data['Note']}/10\n\n"
        print_content += f"**Résumé :** {movie_data['Résumé']}\n\n"
        print_content += "---\n\n"
    
    st.markdown(print_content)
    
    st.info("💡 Pour imprimer cette liste, utilisez la fonction d'impression de votre navigateur (Ctrl+P ou Cmd+P)")


def main():
    """
    Fonction principale de l'application.
    """
    # En-tête
    st.title("🎬 Gestion des Films du CDI")
    st.markdown("*Application de recherche et gestion des films pour le Centre de Documentation et d'Information*")
    
    # Initialiser l'état de session
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    
    # Sidebar pour la configuration
    with st.sidebar:
        st.header("ℹ️ Informations")
        st.info(
            "Cette application utilise l'API TMDB (The Movie Database) pour rechercher des films.\n\n"
            "**Mode démonstration actif** : Des données d'exemple sont affichées.\n\n"
            "Pour utiliser l'API réelle, obtenez une clé API gratuite sur "
            "[themoviedb.org](https://www.themoviedb.org/settings/api) "
            "et modifiez la variable `TMDB_API_KEY` dans le code."
        )
        
        st.header("📖 Instructions")
        st.markdown("""
        1. Entrez un titre de film dans la barre de recherche
        2. Parcourez les résultats
        3. Sélectionnez les films à exporter
        4. Cliquez sur 'Exporter/Imprimer' pour obtenir la liste
        """)
    
    # Barre de recherche
    st.header("🔍 Rechercher un film")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input(
            "Entrez le titre du film",
            placeholder="Ex: Inception, Le Parrain, Avatar...",
            label_visibility="collapsed"
        )
    with col2:
        search_button = st.button("🔍 Rechercher", use_container_width=True)
    
    # Effectuer la recherche
    if search_button and search_query:
        with st.spinner("Recherche en cours..."):
            st.session_state.search_results = search_movies_tmdb(search_query)
            # Réinitialiser les sélections
            for i in range(100):  # Réinitialiser jusqu'à 100 films
                if f"selected_{i}" in st.session_state:
                    del st.session_state[f"selected_{i}"]
    
    # Afficher les résultats
    if st.session_state.search_results:
        st.header(f"📋 Résultats ({len(st.session_state.search_results)} films trouvés)")
        
        # Bouton d'export en haut
        if st.button("📤 Exporter/Imprimer les films sélectionnés", type="primary"):
            st.session_state.show_export = True
        
        # Afficher les films en grille (2 colonnes)
        for i in range(0, len(st.session_state.search_results), 2):
            col1, col2 = st.columns(2)
            
            display_movie_card(st.session_state.search_results[i], col1, i)
            
            if i + 1 < len(st.session_state.search_results):
                display_movie_card(st.session_state.search_results[i + 1], col2, i + 1)
        
        # Section d'export
        if st.session_state.get("show_export", False):
            st.markdown("---")
            export_selected_movies()
    
    elif search_query and search_button:
        st.warning("Aucun film trouvé. Essayez avec un autre titre.")
    else:
        st.info("👆 Entrez un titre de film et cliquez sur 'Rechercher' pour commencer.")


if __name__ == "__main__":
    main()
