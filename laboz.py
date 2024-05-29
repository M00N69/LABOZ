import streamlit as st
import pandas as pd
import re
import PyPDF2

def extraire_texte_pdf(fichier):
    """
    Extrait le texte d'un fichier PDF.
    Args:
        fichier (str): Chemin vers le fichier PDF.
    Returns:
        str: Texte extrait du fichier PDF.
    """
    with open(fichier, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        texte = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            texte += page.extract_text()
        return texte

def extraire_donnees_labexia(texte):
    """
    Extrait les données d'un rapport LABEXIA à partir du texte brut.
    Args:
        texte (str): Texte brut du rapport LABEXIA.
    Returns:
        pandas.DataFrame: DataFrame contenant les données extraites.
    """
    regex_generales = {
        'Demande d\'analyse': r'Demande d\'analyse\s*:\s*(.+)',
        'Echantillon reçu le': r'Echantillon reçu le\s*:\s*(\d{2}/\d{2}/\d{4})',
        'Echantillon analysé le': r'Echantillon analysé le\s*:\s*(\d{2}/\d{2}/\d{4})',
        'Dénomination': r'Dénomination\s*:\s*(.+)',
        'Conditionnement': r'Conditionnement\s*:\s*(.+)',
        'Code produit client': r'Code produit client\s*:\s*(.+)',
        'Lot': r'Lot\s*:\s*(.+)',
        'N° d\'échantillon': r'N° d\'échantillon\s*:\s*(.+)'
    }
    
    informations_generales = extraire_informations_generales(texte, regex_generales)
    
    regex_valeurs = r'CHIMIE\n(.+?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n'
    colonnes = [
        'Détermination', 'Unité', 'Résultat', 'Règlementation', 'Etiquetage',
        'CDC', 'Incertitude'
    ]
    
    valeurs_nutritionnelles = extraire_valeurs_nutritionnelles(texte, regex_valeurs)
    
    df_generales = pd.DataFrame(informations_generales.items(), columns=['Information', 'Valeur'])
    df_valeurs = pd.DataFrame(valeurs_nutritionnelles, columns=colonnes)
    
    return df_generales, df_valeurs

def extraire_informations_generales(texte, regex_dict):
    """Extrait les informations générales d'un texte donné en utilisant un dictionnaire de regex."""
    informations_generales = {}
    for cle, regex in regex_dict.items():
        match = re.search(regex, texte)
        informations_generales[cle] = match.group(1).strip() if match else None
    return informations_generales

def extraire_valeurs_nutritionnelles(texte, regex):
    """Extrait les valeurs nutritionnelles d'un texte donné en utilisant une regex."""
    valeurs_nutritionnelles = []
    for match in re.finditer(regex, texte, re.DOTALL):
        valeurs_nutritionnelles.append([group.strip() if group else '' for group in match.groups()])
    return valeurs_nutritionnelles

st.title("Extracteur de Rapports d'Analyses LABEXIA")

uploaded_file = st.file_uploader("Choisissez le rapport d'analyse (PDF)", type=["pdf"])

if uploaded_file is not None:
    # Enregistrement du fichier PDF
    pdf_path = f'labex-{uploaded_file.name}'
    with open(pdf_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    # Extraction du texte brut du PDF
    texte_brut = extraire_texte_pdf(pdf_path)

    # Affichage du texte brut (optionnel)
    st.write("## Texte Brut du Rapport:")
    st.text(texte_brut) 

    # Extraction des données du texte brut
    df_generales, df_valeurs = extraire_donnees_labexia(texte_brut)
    
    st.write("## Informations Générales:")
    st.dataframe(df_generales)

    st.write("## Valeurs Nutritionnelles:")
    st.dataframe(df_valeurs)
