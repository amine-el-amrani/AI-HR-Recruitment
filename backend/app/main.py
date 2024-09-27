from fastapi import FastAPI, File, UploadFile
import spacy
from transformers import pipeline
import PyPDF2
import re
from datetime import datetime

# Créer l'application FastAPI
app = FastAPI()

# Charger un pipeline pour l'extraction d'entités nommées (NER)
ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

# Fonction pour extraire le texte d'un PDF
def extract_text_from_pdf(pdf_file):
    """Extrait le texte d'un fichier PDF."""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Fonction pour extraire les années d'expérience à partir des dates
def extract_years_of_experience(text):
    # Chercher des plages de dates comme "février 2023 - septembre 2024"
    date_patterns = [
        r"(\d{4})\s*-\s*(\d{4})",  # Ex : 2019 - 2021
        r"(\d{2}/\d{4})\s*-\s*(\d{2}/\d{4})",  # Ex : 01/2019 - 12/2021
        r"(\b(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b\s*\d{4})\s*-\s*(\b(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b\s*\d{4})",  # Ex : janvier 2019 - décembre 2021
    ]

    total_experience = 0
    current_year = datetime.now().year

    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Extraire les années (si on a les deux)
            try:
                start_year = int(match[0][-4:])
                end_year = int(match[1][-4:])
                if start_year <= current_year and start_year <= end_year:
                    total_experience += (end_year - start_year)
            except ValueError:
                continue

    return total_experience

# Fonction pour extraire les compétences
def extract_skills(text):
    # Définir les compétences courantes à rechercher
    skills_keywords = [
        "Python", "Django", "Flask", "React", "SQL", "PostgreSQL", "Machine Learning", 
        "TensorFlow", "Docker", "Kubernetes", "JavaScript", "CSS", "Git", "GitHub",
        "Agile", "SCRUM", "Kanban", "Linux", "Bash", "Scripting", "AWS", "Azure", "GCP"
    ]
    found_skills = [skill for skill in skills_keywords if skill.lower() in text.lower()]
    return found_skills

# Fonction pour extraire le niveau d'études
def extract_education_level(text):
    # Chercher des indices de niveaux d'études
    education_keywords = ["Licence", "Master", "Mastère", "Doctorat", "Bachelor", "PhD", "Diplôme", "Bac+5", "Bac+4", "Bac+3", "Bac+2", "Bac+1"]
    found_education = [edu for edu in education_keywords if edu.lower() in text.lower()]
    return found_education

@app.post("/upload-cv/")
async def upload_cv(file: UploadFile = File(...)):
    if file.content_type == "application/pdf":
        text = extract_text_from_pdf(file.file)
    else:
        content = await file.read()
        text = content.decode("utf-8")
    
    # Extraire les informations spécifiques
    years_of_experience = extract_years_of_experience(text)
    skills = extract_skills(text)
    education_level = extract_education_level(text)
    
    return {
        "filename": file.filename,
        "years_of_experience": years_of_experience,
        "skills": skills,
        "education_level": education_level
    }