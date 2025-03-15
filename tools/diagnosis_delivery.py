from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict
import os
import requests
from datetime import datetime
from fpdf import FPDF
import base64
import streamlit as st


class DiagnosisInput(BaseModel):
    patient_id: str = Field(..., description="ID del paciente")
    symptoms: str = Field(..., description="Síntomas actuales")
    medical_history: str = Field(..., description="Historial médico relevante")
    current_medications: str = Field(..., description="Medicación actual")


def generate_expert_diagnosis(llm, symptoms, medical_history, current_medications) -> Dict:
    prompt = f"""
    Como médico especialista, analice la siguiente información:

    **Síntomas actuales:**
    {symptoms}

    **Historial médico:**
    {medical_history}

    **Medicación actual:**
    {current_medications}

    Proporcione:
    1. Diagnóstico detallado
    2. Recetas médicas necesarias
    3. Recomendaciones de tratamiento
    4. Pruebas adicionales requeridas

    Formato de respuesta:
    ### Diagnóstico:
    [texto]

    ### Recetas: 
    [texto]

    ### Recomendaciones:
    [texto]

    ### Pruebas:
    [texto]
    """

    response = llm.invoke(prompt)
    content = response.content if hasattr(response, 'content') else str(response)

    sections = {
        "diagnosis": "No disponible",
        "prescriptions": "No requeridas",
        "recommendations": "No disponibles",
        "tests": "No requeridas"
    }

    current_section = None
    for line in content.split('\n'):
        if line.startswith("### Diagnóstico:"):
            current_section = "diagnosis"
            sections[current_section] = line.replace("### Diagnóstico:", "").strip()
        elif line.startswith("### Recetas:"):
            current_section = "prescriptions"
            sections[current_section] = line.replace("### Recetas:", "").strip()
        elif line.startswith("### Recomendaciones:"):
            current_section = "recommendations"
            sections[current_section] = line.replace("### Recomendaciones:", "").strip()
        elif line.startswith("### Pruebas:"):
            current_section = "tests"
            sections[current_section] = line.replace("### Pruebas:", "").strip()
        elif current_section:
            sections[current_section] += "\n" + line.strip()

    return sections


def create_diagnosis_pdf(patient_id, diagnosis_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Encabezado
    pdf.cell(0, 10, f"Reporte Médico - {patient_id}", 0, 1, 'C')
    pdf.ln(10)

    # Diagnóstico
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Diagnóstico:', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, diagnosis_data['diagnosis'])

    # Recetas
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Recetas Médicas:', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, diagnosis_data['prescriptions'])

    # Recomendaciones
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Recomendaciones:', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, diagnosis_data['recommendations'])

    # Generar PDF en memoria
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes


@tool(args_schema=DiagnosisInput)
def expert_diagnosis(patient_id: str, symptoms: str, medical_history: str, current_medications: str) -> Dict:
    """
    do something
    :param patient_id:
    :param symptoms:
    :param medical_history:
    :param current_medications:
    :return:
    """
    from llm import llm  # Importa tu LLM real

    try:
        # Generar diagnóstico
        diagnosis_data = generate_expert_diagnosis(llm, symptoms, medical_history, current_medications)

        # Crear PDF
        pdf_bytes = create_diagnosis_pdf(patient_id, diagnosis_data)
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

        # Actualizar historial médico
        if st.session_state.medical_history:
            latest_case = st.session_state.medical_history[-1]
            latest_case["diagnosis_report"] = {
                "pdf": pdf_b64,
                "data": diagnosis_data,
                "timestamp": datetime.now().isoformat()
            }

        return {
            "status": "success",
            "diagnosis": diagnosis_data['diagnosis'],
            "prescriptions": diagnosis_data['prescriptions'],
            "recommendations": diagnosis_data['recommendations'],
            "tests": diagnosis_data['tests'],
            "pdf_available": True
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}