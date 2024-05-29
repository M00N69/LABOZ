!pip install PyPDF2 openpyxl

import PyPDF2
import pandas as pd
import re
import streamlit as st

def extraire_donnees_labe(fichier):
  """
  Extrait les données d'un rapport LABEXIA.

  Args:
      fichier (str): Chemin vers le fichier PDF du rapport.

  Returns:
      pandas.DataFrame: DataFrame contenant les données extraites.
  """
  with open(fichier, 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    # Extraire le texte de toutes les pages
    texte = ""
    for page_num in range(len(pdf_reader.pages)):
      page = pdf_reader.pages[page_num]
      texte += page.extract_text()

    # Remplacer le caractère de degré (°) par un espace
    texte = texte.replace('°', ' ')

    # Corriger le formatage du texte (optionnel, mais peut aider)
    texte = texte.replace('\n', ' ')  # Remplace les sauts de ligne par des espaces
    texte = re.sub(r'\s+', ' ', texte)  # Remplace les espaces multiples par un seul espace

    # Affichez le texte extrait pour déboguer
    print(texte) 

    # Extraction des informations générales
    informations_generales = {}
    informations_generales['Dénomination'] = re.search(r'Dénomination :\s+(.+)', texte).group(1)
    informations_generales['Conditionnement'] = re.search(r'Conditionnement :\s+(.+)', texte).group(1)
    informations_generales['Code produit client'] = re.search(r'Code produit client :\s+(.+)', texte).group(1)
    informations_generales['Nombre d\'uvc analysées'] = re.search(r'Nombre d\'uvc analysées :\s+(.+)', texte).group(1)
    informations_generales['Numéro bon de commande'] = re.search(r'Numéro bon de commande :\s+(.+)', texte).group(1)
    informations_generales['Famille de produit'] = re.search(r'Famille de produit :\s+(.+)', texte).group(1)
    informations_generales['N° client'] = re.search(r'N° client :\s+(.+)', texte).group(1)
    informations_generales['Lot'] = re.search(r'Lot :\s+(.+)', texte).group(1)


    # Extraction des valeurs nutritionnelles
    valeurs_nutritionnelles = []
    for match in re.finditer(r'Détermination\s+(.*?)\s+Méthode\s+(.*?)\s+Unité\s+(.*?)\s+Résultat\s+(.*?)\s+Spécification\s+(.*?)\s+Incertitude\s+(.*?)\s+', texte, re.DOTALL):
        valeurs_nutritionnelles.append([
            match.group(1).strip(),
            match.group(2).strip(),
            match.group(3).strip(),
            match.group(4).strip(),
            match.group(5).strip(),
            match.group(6).strip(),
            '', # HPD
            '', # Lipides rapportés à l'HPD 82
            '', # SST rapportés à l'HPD 82
            '', # Rapport collagène/protéine
            '', # Poids net
            '' # Horodatage
        ])
    
    for match in re.finditer(r'HPD\s+(.*?)\s+Lipides rapportés à l\'HPD 82\s+(.*?)\s+SST rapportés à l\'HPD 82\s+(.*?)\s+Rapport collagène/protéine\s+(.*?)\s+Poids net\s+(.*?)\s+', texte, re.DOTALL):
        valeurs_nutritionnelles.append([
            '', # Détermination
            '', # Méthode
            '', # Unité
            '', # Résultat
            '', # Spécification
            '', # Incertitude
            match.group(1).strip(),
            match.group(2).strip(),
            match.group(3).strip(),
            match.group(4).strip(),
            match.group(5).strip(),
            '' # Horodatage
        ])
    
    for match in re.finditer(r'Horodatage\s+(.*?)\s+', texte, re.DOTALL):
        valeurs_nutritionnelles.append([
            '', # Détermination
            '', # Méthode
            '', # Unité
            '', # Résultat
            '', # Spécification
            '', # Incertitude
            '', # HPD
            '', # Lipides rapportés à l'HPD 82
            '', # SST rapportés à l'HPD 82
            '', # Rapport collagène/protéine
            '', # Poids net
            match.group(1).strip() # Horodatage
        ])
    

    # Création du DataFrame
    df = pd.DataFrame(valeurs_nutritionnelles, columns=[
        'Détermination',
        'Méthode',
        'Unité',
        'Résultat',
        'Spécification',
        'Incertitude',
        'HPD',
        'Lipides rapportés à l\'HPD 82',
        'SST rapportés à l\'HPD 82',
        'Rapport collagène/protéine',
        'Poids net',
        'Horodatage'
    ])

    # Ajout des informations générales au DataFrame
    for cle, valeur in informations_generales.items():
        df.loc[len(df)] = [cle, '', '', valeur, '', '', '', '', '', '', '']

    return df


def extraire_donnees_labe_carrefour(fichier):
    """
    Extrait les données d'un rapport LABE-Carrefour.

    Args:
        fichier (str): Chemin vers le fichier PDF du rapport.

    Returns:
        pandas.DataFrame: DataFrame contenant les données extraites.
    """
    with open(fichier, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extraire le texte de toutes les pages
        texte = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            texte += page.extract_text()

        # Remplacer le caractère de degré (°) par un espace
        texte = texte.replace('°', ' ')

        # Corriger le formatage du texte (optionnel, mais peut aider)
        texte = texte.replace('\n', ' ')  # Remplace les sauts de ligne par des espaces
        texte = re.sub(r'\s+', ' ', texte)  # Remplace les espaces multiples par un seul espace

        # Extraction des informations générales
        informations_generales = {}
        informations_generales['Dénomination'] = re.search(r'Dénomination :\s+(.+)', texte).group(1)
        informations_generales['Conditionnement'] = re.search(r'Conditionnement :\s+(.+)', texte).group(1)
        informations_generales['Code produit client'] = re.search(r'Code produit client :\s+(.+)', texte).group(1)
        informations_generales['Lot'] = re.search(r'Lot :\s+(.+)', texte).group(1)
        informations_generales['Fournisseur'] = re.search(r'Fournisseur :\s+(.+)', texte).group(1)

        # Extraction des valeurs nutritionnelles
        valeurs_nutritionnelles = []
        for match in re.finditer(r'CHIMIE\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n', texte, re.DOTALL):
            valeurs_nutritionnelles.append([
                match.group(1).strip(),
                match.group(2).strip(),
                match.group(3).strip(),
                match.group(4).strip(),
                match.group(5).strip(),
                match.group(6).strip(),
                match.group(7).strip(),
                match.group(8).strip(),
                match.group(9).strip(),
                match.group(10).strip(),
                match.group(11).strip()
            ])

        # Création du DataFrame
        df = pd.DataFrame(valeurs_nutritionnelles, columns=[
            'Détermination',
            'Méthode',
            'Unité',
            'Résultat',
            'Règlementation',
            'Étiquetage',
            'CDC',
            'Incertitude',
            'Poids net',
            'Horodatage',
            'Poids net en g'
        ])

        # Ajout des informations générales au DataFrame
        for cle, valeur in informations_generales.items():
            df.loc[len(df)] = [cle, '', '', valeur, '', '', '', '', '', '', '']

        return df

st.title("Extracteur de Rapports d'Analyses LABEXIA")

uploaded_file = st.file_uploader("Choisissez le rapport d'analyse (PDF)", type=["pdf"])

if uploaded_file is not None:
    # Enregistrement du fichier PDF
    with open(f'labex-{uploaded_file.name}', 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    if 'carrefour' in uploaded_file.name:
        df = extraire_donnees_labe_carrefour(f'labex-{uploaded_file.name}')
    else:
        df = extraire_donnees_labe(f'labex-{uploaded_file.name}')

    st.dataframe(df)
