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

def preprocess_text(texte):
    """Normalise le texte pour faciliter l'analyse."""
    texte = re.sub(r'\n+', '\n', texte)
    texte = re.sub(r'(Demande d\'analyse.+?)(?=Echantillon reçu le)', r'\1\n', texte)
    texte = re.sub(r'(Echantillon reçu le.+?)(?=Echantillon analysé le)', r'\1\n', texte)
    texte = re.sub(r'(Echantillon analysé le.+?)(?=T° à réception)', r'\1\n', texte)
    texte = re.sub(r'(T° à réception .+?)(?=Dénomination)', r'\1\n', texte)
    texte = re.sub(r'(Dénomination.+?)(?=Conditionnement)', r'\1\n', texte)
    texte = re.sub(r'(Conditionnement.+?)(?=Code produit client)', r'\1\n', texte)
    texte = re.sub(r'(Code produit client.+?)(?=Nombre d\'uvc analysées)', r'\1\n', texte)
    texte = re.sub(r'(Nombre d\'uvc analysées.+?)(?=Numéro bon de commande)', r'\1\n', texte)
    texte = re.sub(r'(Numéro bon de commande.+?)(?=Famille de produit)', r'\1\n', texte)
    texte = re.sub(r'(Famille de produit.+?)(?=N° client)', r'\1\n', texte)
    texte = re.sub(r'(N° client.+?)(?=Lot)', r'\1\n', texte)
    texte = re.sub(r'(Lot.+?)(?=Données Client)', r'\1\n', texte)
    texte = re.sub(r'(Données Client.+?)(?=N° d\'échantillon)', r'\1\n', texte)
    texte = re.sub(r'(N° d\'échantillon.+?)(?=CHIMIE)', r'\1\n', texte)
    return texte

def segmenter_texte(texte):
    """Segmente le texte en sections pour une extraction plus facile."""
    sections = {}
    try:
        sections["general_info"], reste = re.split(r"CHIMIE", texte, 1)
        sections["chemical_analysis"], sections["conclusion"] = re.split(r"Conclusion", reste, 1)
    except ValueError:
        st.error("Erreur lors de la segmentation du texte. Assurez-vous que le format du document est correct.")
        return None
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
    lignes = texte.split('\n')
    data = []
    
    for i in range(1, len(lignes), 2):
        try:
            ligne_principale = lignes[i].strip()
            ligne_suivante = lignes[i+1].strip()
            
            # Handling cases where the method and unit appear on the next line
            if re.match(r'^[A-Za-z]', ligne_suivante):
                # This is a new determination line; start a new row
                continue

            # Splitting the line based on expected spaces
            elements = re.split(r'\s{2,}', ligne_principale + ' ' + ligne_suivante)
            
            # Handling potential overflow into the next line
            if len(elements) < 7 and i+2 < len(lignes):
                ligne_suivante_suivante = lignes[i+2].strip()
                elements.extend(re.split(r'\s{2,}', ligne_suivante_suivante))
            
            if len(elements) == 6:  # We expect six columns (7th is optional)
                elements.append('')  # Adding empty entry for Incertitude
            
            data.append(elements[:7])  # Make sure we don't get more than 7 elements
            
        except IndexError:
            continue

    # Creating DataFrame
    colonnes = ["Détermination", "Méthode", "Unité", "Résultat", "Spécification", "Incertitude"]
    df_analyse = pd.DataFrame(data, columns=colonnes)
    return df_analyse

def extraire_conclusion(texte):
    """Extrait la conclusion du rapport."""
    match = re.search(r"Conclusion\s+(.+)", texte)
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
    
    # Prétraitement du texte pour normalisation
    texte_brut = preprocess_text(texte_brut)
    
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

