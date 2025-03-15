"""
from langchain.tools import tool
from pydantic import BaseModel, Field

class SymptomInput(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    symptoms: list[str] = Field(..., description="List of reported symptoms")
    medical_history: dict = Field(None, description="Patient's medical history")

@tool(args_schema=SymptomInput)
def symptom_checker(patient_id: str, symptoms: list[str], medical_history: dict = None) -> dict:

    # Implementation would integrate with ML models and medical databases
    return {
        "patient_id": patient_id,
        "possible_conditions": ["common_cold", "flu", "allergy"],
        "confidence_levels": [0.65, 0.25, 0.10],
        "recommended_actions": ["rest", "hydration", "medical_checkup"],
        "urgency_level": "medium"
    }
"""
import os

import pandas as pd
import requests
from fpdf import FPDF
from langchain.tools import tool
from pydantic import BaseModel, Field

from utils import haversine

df = pd.read_csv("../data/hospitales.csv")


class MedicalQuery(BaseModel):
    conversacion: str = Field(..., description="Resumen o conversación original entre paciente y agente IA.")


class PerplexityMedicalTool:
    api_key: str = os.environ.get("PERPLEXITY_API")
    url: str = os.environ.get("PERPLEXITY_URL")


@tool("obtener_info_medica", args_schema=MedicalQuery)
def obtener_info_medica(conversacion: str) -> str:
    """Obtiene información médica relevante usando la API de Perplexity."""
    headers = {
        "Authorization": f"Bearer {PerplexityMedicalTool.api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "pplx-70b-online",
        "messages": [
            {"role": "system",
             "content": "Eres un asistente experto en búsqueda y recomendaciones médicas basadas en evidencia científica."},
            {"role": "user", "content": conversacion}
        ],
        "max_tokens": 1000,
        "temperature": 0.2
    }

    response = requests.post(PerplexityMedicalTool.url, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"Error al consultar la API: {response.status_code} {response.text}"


def generate_pdf(patient_id: str, perplexity_output: dict, filename: str = "medical_report.pdf"):
    """Genera un archivo PDF con la información médica estructurada en el formato solicitado."""
    # Crear un objeto FPDF
    pdf = FPDF()

    # Agregar una página
    pdf.add_page()

    # Establecer fuente
    pdf.set_font("Arial", size=12)

    # Título del documento
    pdf.cell(200, 10, txt="Información Médica Solicitada", ln=True, align="C")

    # Espacio en blanco
    pdf.ln(10)

    # Síntomas reportados por el paciente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="📋 *Síntomas Reportados por el Paciente:* ", ln=True)
    pdf.set_font("Arial", size=12)
    for symptom in perplexity_output.get("symptoms", []):
        pdf.cell(200, 10, txt=f"- {symptom}", ln=True)

    # Espacio en blanco
    pdf.ln(5)

    # Hipótesis o posibles diagnósticos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="🔍 *Hipótesis o Posibles Diagnósticos:* ", ln=True)
    pdf.set_font("Arial", size=12)
    for diagnosis in perplexity_output.get("possible_conditions", []):
        pdf.cell(200, 10, txt=f"- {diagnosis}", ln=True)

    # Espacio en blanco
    pdf.ln(5)

    # Artículos o estudios recomendados
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="📑 *Artículos o Estudios Recomendados:* ", ln=True)
    pdf.set_font("Arial", size=12)
    for article in perplexity_output.get("recommended_articles", []):
        title, link = article.get("title", ""), article.get("link", "")
        pdf.cell(200, 10, txt=f"1. {title} - {link}", ln=True)

    # Espacio en blanco
    pdf.ln(5)

    # Gravedad del paciente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="*Gravedad del Paciente:* ", ln=True)
    pdf.set_font("Arial", size=12)
    severity = perplexity_output.get("urgency_level", "Media")  # Default to "Media" if not provided
    severity_map = {
        "Muy Alta": "1. Muy Alta",
        "Alta": "2. Alta",
        "Media": "3. Media",
        "Baja": "4. Baja",
        "Muy Baja": "5. Muy Baja"
    }
    pdf.cell(200, 10, txt=severity_map.get(severity, "3. Media"), ln=True)

    # Guardar el archivo PDF
    pdf.output(filename)

    return filename


# Integración final
def process_medical_query_and_generate_report(patient_id: str, conversation: str):
    # Llamamos al servicio de Perplexity para obtener la respuesta
    perplexity_tool = PerplexityMedicalTool()
    response = perplexity_tool.obtener_info_medica(conversacion=conversation)

    # Luego, generamos el PDF con la información obtenida
    pdf_filename = perplexity_tool.generate_pdf(patient_id, response, filename=f"medical_report_{patient_id}.pdf")

    return pdf_filename


def find_nearest_hospital(location: dict, df):
    closest_hospital = None
    min_distance = float('inf')  # Iniciar con una distancia infinita
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    for hospital in df:

        hospital_name = hospital["EstablecimientoGlosa"]
        hospital_lat = hospital["latitud"]
        hospital_lon = hospital["longitud"]

        # Calcular la distancia usando la fórmula Haversine
        distance = haversine(latitude, longitude, hospital_lat, hospital_lon)

        # Si es el hospital más cercano, actualizamos
        if distance < min_distance:
            min_distance = distance
            closest_hospital = hospital
    print(f"Se ha enviado al hospital más cercano {closest_hospital}")
    return closest_hospital, min_distance
