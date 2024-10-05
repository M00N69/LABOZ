import re
import pandas as pd
import streamlit as st
from tika import parser  # Import de Tika

def extraire_texte_pdf_tika(fichier):
    """Extrait le texte d'un fichier PDF en utilisant Tika."""
    raw = parser.from_file(fichier)
    texte = raw['content']  # Extraction du texte brut
    return texte

def preprocess_text(texte):
    """Normalise le texte pour faciliter l'analyse."""
    texte = re.sub(r'\s+', ' ', texte)  # Remplace plusieurs espaces par un seul
    texte = re.sub(r'([a-z])([A-Z])', r'\1\n\2', texte)  # Sépare minuscule et majuscule
    texte = re.sub(r'(\d)([A-Z])', r'\1\n\2', texte)  # Sépare les chiffres des majuscules
    texte = texte.replace("CHIMIE", "\nCHIMIE\n")
    texte = texte.replace("Conclusion", "\nConclusion\n")
    return texte

def extraire_analyse_chimique(texte):
    """Extrait les données d'analyse chimique du texte."""
    lignes = texte.split('\n')
    data = []
    current_entry = []

    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue

        # Check if the line looks like a new determination or part of a previous one
        if re.match(r'^[A-Za-z]', ligne):
            if current_entry:
                data.append(' '.join(current_entry))  # Join multiline entries
            current_entry = [ligne]  # Start a new entry
        else:
            if current_entry:
                current_entry.append(ligne)
            else:
                continue  # Unexpected continuation without a start

    if current_entry:
        data.append(' '.join(current_entry))

    # Splitting each entry into columns based on the structure of your data
    structured_data = []
    for entry in data:
        elements = re.split(r'\s{2,}', entry)  # Split on multiple spaces
        if len(elements) == 6:  # Ensuring there are exactly 6 elements
            structured_data.append(elements)
        else:
            # Attempt to handle cases where the data isn't split properly
            structured_data.append(elements + [""] * (6 - len(elements)))

    # Create DataFrame with appropriate column names
    colonnes = ["Détermination", "Méthode", "Unité", "Résultat", "Spécification", "Incertitude"]
    df_analyse = pd.DataFrame(structured_data, columns=colonnes)

    return df_analyse

# Streamlit App Interface
st.title("Extracteur de Rapports d'Analyses LABEXIA")

uploaded_file = st.file_uploader("Choisissez le rapport d'analyse (PDF)", type=["pdf"], key="unique_file_uploader")

if uploaded_file is not None:
    # Enregistrement du fichier PDF
    pdf_path = f'labex-{uploaded_file.name}'
    with open(pdf_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    # Extraction du texte brut du PDF via Tika
    texte_brut = extraire_texte_pdf_tika(pdf_path)

    # Affichage du texte brut extrait pour le débogage
    st.write("## Texte Brut Extrait:")
    st.text(texte_brut)

    # Prétraitement du texte pour normalisation
    texte_brut = preprocess_text(texte_brut)

    # Affichage du texte prétraité pour le débogage
    st.write("## Texte Prétraité:")
    st.text(texte_brut)

    # Extraction des analyses chimiques
    df_analyse_chimique = extraire_analyse_chimique(texte_brut)

    st.write("## Analyses Chimiques:")
    st.dataframe(df_analyse_chimique)

