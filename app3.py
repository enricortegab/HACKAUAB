import base64
import random as rd
import uuid
import webbrowser
from datetime import datetime
from typing import List, Dict

import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from llm import llm, prompt
from tools import tools
from tools.diagnosis_delivery import create_diagnosis_pdf

# Agent configuration
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Session state initialization
if 'patient_id' not in st.session_state:
    st.session_state.patient_id = str(uuid.uuid4())[:8]

st.session_state.setdefault("medical_history", [])
st.session_state.setdefault("medicamentos", [])
st.session_state.setdefault("messages", [
    {"role": "assistant", "content": "¡Hola! Soy tu asistente de salud. ¿Qué síntomas estás experimentando?"}])
st.session_state.setdefault("user_location", "")
st.session_state.setdefault("user_coordinates", {'lat': 19.4326, 'lon': -99.1332})

# Page configuration
st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 1])


def generate_pharmacies(loc: dict):
    pharmacies_locations = pd.DataFrame([
        {'lat': loc['lat'] + rd.randint(-2, 2) / 100, 'lon': loc['lon'] + rd.randint(-2, 2) / 100,
         "col": pharmacy_color}
        for _ in range(rd.randint(5, 10))
    ])
    return pharmacies_locations


def generate_hospitals(loc: dict):
    hospitals_locations = pd.DataFrame([
        {'lat': loc['lat'] + rd.randint(-5, 5) / 100, 'lon': loc['lon'] + rd.randint(-5, 5) / 100,
         "col": hospital_color}
        for _ in range(rd.randint(1, 3))
    ])
    return hospitals_locations


user_color = "#228B22"
pharmacy_color = "#FF5733"
hospital_color = "#B4C424"

# Medical Context Column
with col1:
    st.header("Contexto Médico")
    tabs = st.tabs(["Mapa", "Ficha", "Historial", "Validación", "Cesta"])

    # Location Tab
    with tabs[0]:
        st.subheader("Consulta farmacias y hospitales cercanos")
        ubicacion = st.text_input("Introduce tu ubicación:", value=st.session_state.user_location)
        if ubicacion:
            geolocator = Nominatim(user_agent="medical_app")
            location = geolocator.geocode(ubicacion)
            if location:
                st.session_state.user_coordinates = {'lat': location.latitude, 'lon': location.longitude}

                loc = st.session_state.user_coordinates
                loc["col"] = user_color

                pharmacies = generate_pharmacies(st.session_state.user_coordinates)
                hospitals = generate_hospitals(st.session_state.user_coordinates)

                st.map(pd.concat([pd.DataFrame([loc]), pharmacies, hospitals]), color="col")

                # Add legend
                st.markdown(f"<span style='color:{user_color}'>●</span> Paciente", unsafe_allow_html=True)
                st.markdown(f"<span style='color:{hospital_color}'>●</span> Hospitales", unsafe_allow_html=True)
                st.markdown(f"<span style='color:{pharmacy_color}'>●</span> Farmacias", unsafe_allow_html=True)

    # Case Summary Tab
    with tabs[1]:
        if st.session_state.medical_history:
            latest_case = st.session_state.medical_history[-1]
            st.write(f"**Paciente:** {st.session_state.patient_id}")
            st.write(f"**Síntomas:** {', '.join(latest_case.get('symptoms', []))}")
            st.write(f"**Diagnóstico:** {latest_case.get('diagnosis', 'Pendiente')}")

            if latest_case.get("report"):
                st.markdown("### Reporte Médico")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write("**Recomendaciones:**")
                    st.markdown(latest_case['report']['data']['recommendations'])
                with col2:
                    pdf_bytes = base64.b64decode(latest_case['report']['pdf'])
                    st.download_button(
                        label="📄 Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"diagnostico_{st.session_state.patient_id}.pdf",
                        mime="application/pdf"
                    )

    # Medical History Tab
    with tabs[2]:
        if st.session_state.medical_history:
            df_history = pd.DataFrame([{
                'Fecha': case['timestamp'],
                'Síntomas': ', '.join(case.get('symptoms', [])),
                'Diagnóstico': case.get('diagnosis', ''),
                'Validado': '✅' if case.get('validation') else '❌'
            } for case in st.session_state.medical_history])
            st.dataframe(df_history, use_container_width=True)

    # Medical Validation Tab
    with tabs[3]:
        if st.session_state.medical_history:
            latest_case = st.session_state.medical_history[-1]

            if latest_case.get("validation"):
                st.success("✅ Caso Validado")
                st.write(f"**Estado:** {latest_case['validation']['status']}")
                st.write(f"**Urgencia:** {latest_case['validation'].get('urgency', 'N/A')}")
                st.write("**Plan de Tratamiento:**")
                st.markdown(latest_case['validation']['treatment_plan'])
            else:
                with st.form("medical_review_form"):
                    st.subheader("Validación Médica")
                    diagnosis_status = st.radio(
                        "Estado del Diagnóstico",
                        options=["Confirmado", "Modificado", "Rechazado"],
                        horizontal=True
                    )
                    medical_urgency = st.select_slider(
                        "Nivel de Urgencia",
                        options=["Baja", "Media", "Alta"],
                        value="Media"
                    )
                    clinical_notes = st.text_area("Notas Clínicas")
                    treatment_plan = st.text_area("Plan de Tratamiento")

                    if st.form_submit_button("Validar Diagnóstico"):
                        validation_data = {
                            "status": diagnosis_status,
                            "urgency": medical_urgency,
                            "notes": clinical_notes,
                            "treatment_plan": treatment_plan,
                            "validator": "Dr. Juan Pérez",
                            "timestamp": datetime.now().isoformat()
                        }
                        latest_case["validation"] = validation_data
                        st.rerun()

    # Payment Tab
    with tabs[4]:
        st.subheader("Pago de Medicamentos")
        st.image("data/PayRetailers.png", width=400)
        st.markdown("[▶ Ir a PayRetailers](https://payretailers.com/es/)")
        st.markdown("---")

        if st.session_state.medicamentos:
            for med in st.session_state.medicamentos:
                st.write(f"**{med['name']}** - ")
                if st.button(f"Pagar {med['name']}"):
                    st.success(f"Redirigiendo a PayRetailers para {med['name']}...")
                    webbrowser.open("https://www.payretailers.com/es/")
        else:
            st.write("No hay nada en la cesta")
        st.markdown("---")

# Chat Interface Column
with col2:
    st.header("Asistente de Salud")


    # Pydantic Models
    class ChoiceResponse(BaseModel):
        choice: str = Field(description="One of: general, medication")


    class GeneralResponse(BaseModel):
        content: str = Field(description="Response content")
        tools_used: List[str]


    class MedicationResponse(BaseModel):
        content: str = Field(description="Medication explanation")
        medications: List[Dict[str, str]] = Field(description="List of medications")


    # Chat setup
    generic_parser = PydanticOutputParser(pydantic_object=ChoiceResponse)
    general_parser = PydanticOutputParser(pydantic_object=GeneralResponse)
    medication_parser = PydanticOutputParser(pydantic_object=MedicationResponse)

    uploaded_image = st.file_uploader("Subir imagen médica", type=["jpg", "png"])

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("Describe tus síntomas..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        try:
            # First agent call to determine response type
            choice_response = agent_executor.invoke({
                "query": f"Determine response type for: {user_input}",
                "chat_history": st.session_state.messages,
                "format_instructions": generic_parser.get_format_instructions()
            })
            choice = generic_parser.parse(choice_response["output"]).choice

            # Second agent call with selected parser
            parser = medication_parser if choice == "medication" else general_parser
            response = agent_executor.invoke({
                "query": user_input,
                "chat_history": st.session_state.messages,
                "location": st.session_state.user_coordinates,
                "format_instructions": parser.get_format_instructions()
            })

            # Handle medication response
            if choice == "medication":
                med_data = medication_parser.parse(response["output"])
                st.session_state.medicamentos = med_data.medications
                response_content = med_data.content
            else:
                response_content = general_parser.parse(response["output"]).content

            # Generate PDF for diagnoses
            if "diagnóstico" in response_content.lower():
                report_data = {
                    "diagnosis": response_content,
                    "prescriptions": "Medicación según prescripción",
                    "recommendations": "Seguir indicaciones médicas",
                    "tests": "Análisis clínicos básicos"
                }
                pdf_bytes = create_diagnosis_pdf(st.session_state.patient_id, report_data)
                pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

                new_entry = {
                    "patient_id": st.session_state.patient_id,
                    "symptoms": [user_input],
                    "diagnosis": report_data["diagnosis"],
                    "timestamp": datetime.now().isoformat(),
                    "report": {
                        "pdf": pdf_b64,
                        "data": report_data
                    }
                }
                st.session_state.medical_history.append(new_entry)

            # Update chat history
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            st.rerun()

        except Exception as e:
            st.error(f"Error en el sistema: {str(e)}")
