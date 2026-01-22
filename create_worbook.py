"""
Fonctions de création de workbooks Excel avec images
"""

import pandas as pd
import xlsxwriter  # noqa: F401
import requests
from io import BytesIO
from datetime import datetime


def create_simple_excel(movies_list):
    """
    Crée un fichier Excel simple sans images

    Args:
        movies_list (list): Liste des films sélectionnés

    Returns:
        BytesIO: Buffer contenant le fichier Excel
    """
    if not movies_list:
        return None

    df = pd.DataFrame(movies_list)
    df = df[["titre", "annee", "realisateur", "note", "resume"]]

    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name="Films CDI")
    excel_buffer.seek(0)

    return excel_buffer


def create_excel_with_images(movies_list):
    """
    Crée un fichier Excel avec les images intégrées

    Args:
        movies_list (list): Liste des films sélectionnés

    Returns:
        BytesIO: Buffer contenant le fichier Excel ou None
    """
    if not movies_list:
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
    headers = ['Affiche', 'Titre', 'Année', 'Réalisateur', 'Note', 'Résumé',
               'Source API']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Définir les largeurs des colonnes
    worksheet.set_column(0, 0, 15)  # Colonne affiche
    worksheet.set_column(1, 1, 25)  # Titre
    worksheet.set_column(2, 2, 8)   # Année
    worksheet.set_column(3, 3, 20)  # Réalisateur
    worksheet.set_column(4, 4, 8)   # Note
    worksheet.set_column(5, 5, 50)  # Résumé
    worksheet.set_column(6, 6, 10)  # Source API

    # Ajouter les données et images
    for row, movie in enumerate(movies_list, 1):
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
            except Exception:
                worksheet.write(row, 0, "Image indisponible", cell_format)
        else:
            worksheet.write(row, 0, "Pas d'image", cell_format)

        # Ajouter les autres données
        worksheet.write(row, 1, movie["titre"], cell_format)
        worksheet.write(row, 2, str(movie["annee"]), cell_format)
        worksheet.write(row, 3, movie.get("realisateur", "N/A"), cell_format)
        worksheet.write(row, 4, str(movie["note"]), cell_format)
        worksheet.write(row, 5, movie["resume"], cell_format)
        worksheet.write(row, 6, movie.get("api_source", "N/A"), cell_format)

    workbook.close()
    excel_buffer.seek(0)
    return excel_buffer


def create_csv_export(movies_list):
    """
    Crée un export CSV des films

    Args:
        movies_list (list): Liste des films sélectionnés

    Returns:
        str: Contenu CSV
    """
    if not movies_list:
        return None

    df = pd.DataFrame(movies_list)
    df = df[["titre", "annee", "realisateur", "note", "resume", "api_source"]]

    return df.to_csv(index=False)


def create_printable_html(movies_list):
    """
    Crée une version HTML imprimable

    Args:
        movies_list (list): Liste des films sélectionnés

    Returns:
        str: Contenu HTML
    """
    if not movies_list:
        return None

    df = pd.DataFrame(movies_list)
    df = df[["titre", "annee", "realisateur", "note", "resume", "api_source"]]

    # Créer un style CSS pour l'impression
    html_style = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #4472C4;
            color: white;
            font-weight: bold;
        }
        .title {
            text-align: center;
            margin-bottom: 20px;
            font-size: 24px;
            color: #4472C4;
        }
        .summary {
            max-width: 300px;
            word-wrap: break-word;
        }
        @media print {
            .no-print { display: none; }
        }
    </style>
    """

    export_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    html_content = f"""
    {html_style}
    <div class="title">🎬 Liste des Films du CDI</div>
    <p><strong>Date d'export :</strong> {export_date}</p>
    <p><strong>Nombre de films :</strong> {len(movies_list)}</p>
    {df.to_html(index=False, classes='printable-table', escape=False)}
    """

    return html_content


def get_export_filename(export_type, with_timestamp=True):
    """
    Génère un nom de fichier pour l'export

    Args:
        export_type (str): Type d'export ('excel', 'csv', 'zip')
        with_timestamp (bool): Inclure un timestamp

    Returns:
        str: Nom de fichier
    """
    base_name = "films_cdi"

    if with_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name += f"_{timestamp}"

    extensions = {
        'excel_simple': '.xlsx',
        'excel_images': '.xlsx',
        'csv': '.csv',
        'zip': '.zip'
    }

    return base_name + extensions.get(export_type, '.txt')
