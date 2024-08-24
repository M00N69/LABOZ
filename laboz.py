import streamlit as st
import pandas as pd
import re
import PyPDF2

def extraire_texte_pdf(fichier):
    """Extrait le texte d'un fichier PDF en utilisant PyPDF2."""
    with open(fichier, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        texte = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            texte += page.extract_text()
    return texte

def preprocess_text(texte):
    """Normalise le texte pour faciliter l'analyse."""
    # Replace missing delimiters and normalize text
    texte = texte.replace("Données Client :", "\nDonnées Client :")
    texte = texte.replace("CHIMIE", "\nCHIMIE\n")
    texte = texte.replace("Conclusion", "\nConclusion\n")
    
    # Insert line breaks between sections that are concatenated together
    texte = re.sub(r'([a-z])([A-Z])', r'\1\n\2', texte)  # Lowercase followed by uppercase
    texte = re.sub(r'(\d)([A-Z])', r'\1\n\2', texte)      # Digit followed by uppercase

    # Additional cleanup if necessary
    texte = texte.replace("Page 1/2", "").replace("Page 2/2", "").strip()

    return texte

def segmenter_texte(texte):
    """Segmente le texte en sections pour une extraction plus facile."""
    try:
        sections = {}
        sections["general_info"], reste = re.split(r"\nCHIMIE\n", texte, 1)
        sections["chemical_analysis"], sections["conclusion"] = re.split(r"\nConclusion\n", reste, 1)
        return sections
    except ValueError:
        st.error("Erreur lors de la segmentation du texte. Assurez-vous que le format du document est correct.")
        return None

def extraire_informations_generales(texte):
    """Extrait les informations générales du texte."""
    regex_generales = {
        "Demande d'analyse": r"Demande d'analyse\s*:\s*(.+)",
        "Echantillon reçu le": r"Echantillon reçu le\s*:\s*(\d{2}/\d{2}/\d{4})",
        "Echantillon analysé le": r"Echantillon analysé le\s*:\s*(\d{2}/\d{2}/\d{4})",
        "Dénomination": r"Dénomination\s*:\s*(.+)",
        "Conditionnement": r"Conditionnement\s*:\s*(.+)",
        "Code produit client": r"Code produit client\s*:\s*(.+)",
        "Lot": r"Lot\s*:\s*(.+)",
        "N° d'échantillon": r"N° d'échantillon\s*:\s*(.+)"
    }
    
    informations_generales = {}
    for cle, regex in regex_generales.items():
        match = re.search(regex, texte)
        informations_generales[cle] = match.group(1).strip() if match else "Non spécifié"
    
    return informations_generales

def extraire_analyse_chimique(texte):
    """Extrait les données d'analyse chimique du texte."""
    lignes = texte.split('\n')
    data = []
    current_entry = []
    
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue

        # Check if the line is the start of a new entry
        if re.match(r'^[A-Za-z]', ligne):
            if current_entry:
                data.append(' '.join(current_entry))  # Join multiline entries
            current_entry = [ligne]  # Start new entry
        else:
            if current_entry:
                current_entry.append(ligne)
            else:
                # Unexpected continuation without a start
                continue
    
    if current_entry:
        data.append(' '.join(current_entry))

    # Splitting each item into the expected columns
    structured_data = []
    for entry in data:
        elements = re.split(r'\s{2,}', entry)  # Split on multiple spaces
        if len(elements) >= 6:
            structured_data.append(elements[:6])  # Ensure exactly 6 columns

    # Create DataFrame
    colonnes = ["Détermination", "Méthode", "Unité", "Résultat", "Spécification", "Incertitude"]
    df_analyse = pd.DataFrame(structured_data, columns=colonnes)
    
    return df_analyse

def extraire_conclusion(texte):
    """Extrait la conclusion du rapport."""
    match = re.search(r"Conclusion\s*(.+)", texte, re.DOTALL)
    return match.group(1).strip() if match else "Non spécifié"

# Streamlit App Interface
st.title("Extracteur de Rapports d'Analyses LABEXIA")

uploaded_file = st.file_uploader("Choisissez le rapport d'analyse (PDF)", type=["pdf"], key="unique_file_uploader")

if uploaded_file is not None:
    # Enregistrement du fichier PDF
    pdf_path = f'labex-{uploaded_file.name}'
    with open(pdf_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    # Extraction du texte brut du PDF
    texte_brut = extraire_texte_pdf(pdf_path)
    
    # Display the raw extracted text for debugging
    st.write("## Texte Brut Extrait:")
    st.text(texte_brut)
    
    # Prétraitement du texte pour normalisation
    texte_brut = preprocess_text(texte_brut)
    
    # Display the preprocessed text for debugging
    st.write("## Texte Prétraité:")
    st.text(texte_brut)
    
    # Segmentation du texte
    sections = segmenter_texte(texte_brut)
    
    if sections:
        # Extraction des informations générales
        informations_generales = extraire_informations_generales(sections["general_info"])
        
        # Extraction des analyses chimiques
        df_analyse_chimique = extraire_analyse_chimique(sections["chemical_analysis"])

        st.write("## Informations Générales:")
        df_generales = pd.DataFrame(informations_generales.items(), columns=["Information", "Valeur"])
        st.dataframe(df_generales)

        st.write("## Analyses Chimiques:")
        st.dataframe(df_analyse_chimique)
        
        st.write("## Conclusion:")
        conclusion = extraire_conclusion(sections["conclusion"])
        st.write(conclusion)
