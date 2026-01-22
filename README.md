# 🎬 AgenFilmo - Gestion des Films du CDI

Application Streamlit pour gérer et rechercher les films du CDI (Centre de Documentation et d'Information) d'un lycée.

## 📋 Fonctionnalités

- **🔍 Recherche de films** : Recherchez des films via l'API TMDB (The Movie Database)
- **📊 Affichage détaillé** : Consultez l'affiche, le résumé, l'année de sortie et le réalisateur
- **✅ Sélection multiple** : Sélectionnez plusieurs films pour l'export
- **📥 Export CSV** : Exportez les films sélectionnés au format CSV
- **🖨️ Impression** : Version imprimable formatée pour les listes de films

## 🚀 Installation

1. Clonez le repository :
```bash
git clone https://github.com/Bastien-OC20/agenfilmo.git
cd agenfilmo
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. (Optionnel) Configurez votre clé API TMDB :
   - Créez un compte gratuit sur [themoviedb.org](https://www.themoviedb.org/)
   - Obtenez votre clé API dans les [paramètres](https://www.themoviedb.org/settings/api)
   - Modifiez la variable `TMDB_API_KEY` dans `app.py`

## 💻 Utilisation

1. Lancez l'application :
```bash
streamlit run app.py
```

2. Ouvrez votre navigateur à l'adresse indiquée (généralement http://localhost:8501)

3. Utilisez l'application :
   - Entrez un titre de film dans la barre de recherche
   - Parcourez les résultats affichés
   - Cochez les films à exporter
   - Cliquez sur "Exporter/Imprimer" pour obtenir la liste

## 🎯 Mode Démonstration

L'application fonctionne en mode démonstration avec des données d'exemple si aucune clé API n'est configurée. Cela permet de tester l'application sans configuration supplémentaire.

## 📦 Dépendances

- `streamlit` : Framework web pour l'application
- `requests` : Requêtes HTTP vers l'API TMDB
- `pandas` : Manipulation et export des données
- `Pillow` : Traitement des images (affiches de films)

## 📝 Structure du projet

```
agenfilmo/
├── app.py              # Application Streamlit principale
├── requirements.txt    # Dépendances Python
├── .gitignore         # Fichiers à ignorer par Git
├── README.md          # Documentation
└── LICENSE            # Licence du projet
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Voir le fichier [LICENSE](LICENSE) pour plus de détails.
