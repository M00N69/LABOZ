import streamlit as st
import pandas as pd
import re
import PyPDF2

def extraire_texte_pdf(fichier):
    """Extrait le texte d'un fichier PDF."""
    with open(fichier, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        texte = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            texte += page.extract_text()
        return texte

def segmenter_texte(texte):
    """Segmente le texte en sections pour une extraction plus facile."""
    sections = {
        "general_info": "",
        "chemical_analysis": ""
    }
    
    # Separate general info and chemical analysis based on common keywords
    sections["general_info"], sections["chemical_analysis"] = re.split(r"CHIMIE", texte, 1)
    
    return sections

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
        informations_generales[cle] = match.group(1).strip() if match else None
    
    return informations_generales

def extraire_analyse_chimique(texte):
    """Extrait les données d'analyse chimique du texte."""
    regex_ligne = r"(\w[\w\s]*?)\s+([\w\s]*?)\s+([\w/%]*?)\s+([\d,\.]*?)\s+([\w<=/\.]*?)\s+([\d,\.]*?)\s+([\w]*)"
    
    analyses = []
    for match in re.finditer(regex_ligne, texte):
        analyses.append(match.groups())
    
    colonnes = [
        "Détermination", "Méthode", "Unité", "Résultat", "Spécification", "Incertitude", "Conclusion"
    ]
    
    df_analyse = pd.DataFrame(analyses, columns=colonnes)
    return df_analyse

# URL du GIF
gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbTV5dWI1M3dheG92aGI2NXRydXpuMDBqeHhvOWY3ZWhtOG1qNDM4diZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgN8YKRhByRBzMI/giphy-downsized-large.gif"

# Définir le CSS pour l'arrière-plan
css_background = f"""
<style>
.stApp {{
    background: url("{gif_url}") no-repeat center center fixed;
    background-size: cover;
}}
</style>
"""

# Injecter le CSS dans l'application Streamlit
st.markdown(css_background, unsafe_allow_html=True)

st.title("Extracteur de Rapports d'Analyses LABEXIA")

uploaded_file = st.file_uploader("Choisissez le rapport d'analyse (PDF)", type=["pdf"])

if uploaded_file is not None:
    # Enregistrement du fichier PDF
    pdf_path = f'labex-{uploaded_file.name}'
    with open(pdf_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    # Extraction du texte brut du PDF
    texte_brut = extraire_texte_pdf(pdf_path)
    
    # Segmentation du texte
    sections = segmenter_texte(texte_brut)
    
    # Extraction des informations générales
    informations_generales = extraire_informations_generales(sections["general_info"])
    
    # Extraction des analyses chimiques
    df_analyse_chimique = extraire_analyse_chimique(sections["chemical_analysis"])

    st.write("## Informations Générales:")
    df_generales = pd.DataFrame(informations_generales.items(), columns=["Information", "Valeur"])
    st.dataframe(df_generales)

    st.write("## Analyses Chimiques:")
    st.dataframe(df_analyse_chimique)
