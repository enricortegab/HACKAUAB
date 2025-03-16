import streamlit as st
from datetime import datetime
import pandas as pd
from langchain.agents import AgentExecutor, create_tool_calling_agent
from geopy.geocoders import Nominatim
from fpdf import FPDF
import base64
import uuid
from tools import tools
from llm import llm, prompt
from tools.diagnosis_delivery import create_diagnosis_pdf

# Configuración inicial de sesión
if 'patient_id' not in st.session_state:
    st.session_state.patient_id = str(uuid.uuid4())[:8]  # ID único de paciente

# Configuración del agente
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Inicializar estados de sesión
st.session_state.setdefault("medical_history", [])
st.session_state.setdefault("messages", [
    {"role": "assistant", "content": "¡Hola! Soy tu asistente de salud rural. ¿Qué síntomas estás experimentando?"}
])
st.session_state.setdefault("user_location", "")
st.session_state.setdefault("user_coordinates", {})

# Configuración de página
st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 1])

# Datos de ubicación
patient_location = {'lat': 19.4326, 'lon': -99.1332}
pharmacies_locations = pd.DataFrame([
    {'lat': 19.434, 'lon': -99.140, 'nombre': 'Farmacia Uno'},
    {'lat': 19.429, 'lon': -99.130, 'nombre': 'Farmacia Dos'},
    {'lat': 19.431, 'lon': -99.135, 'nombre': 'Farmacia Tres'},
    {'lat': 19.435, 'lon': -99.132, 'nombre': 'Farmacia Cuatro'}
])

# Columna izquierda - Contexto Médico
with col1:
    st.header("Contexto Médico")
    tabs = st.tabs(["Ubicación", "Farmacias", "Resumen", "Historial", "Validación", "Pago"])

    # Pestaña de Ubicación
    with tabs[0]:
        st.subheader("Ubicación")
        ubicacion = st.text_input("Introduce tu ubicación:", value=st.session_state.user_location)
        if ubicacion:
            # TODO: generate pharmacies and hospitals
            geolocator = Nominatim(user_agent="medical_app")
            location = geolocator.geocode(ubicacion)
            if location:
                st.session_state.user_coordinates = {'lat': location.latitude, 'lon': location.longitude}
                st.map(pd.DataFrame([st.session_state.user_coordinates]))

    # Pestaña de Farmacias
    with tabs[1]:
        # TODO: merge client locatio with pharmacies
        st.subheader("Farmacias Cercanas")
        if st.session_state.user_coordinates:
            df = pd.concat([pd.DataFrame([st.session_state.user_coordinates]), pharmacies_locations])
            st.map(df)

    # Pestaña de Historial
    with tabs[3]:
        if st.session_state.medical_history:
            # TODO: check working
            df = pd.DataFrame([{
                'Fecha': case['timestamp'],
                'Diagnóstico': case.get('diagnosis', ''),
                'Validado': '✅' if case.get('validation') else '❌'
            } for case in st.session_state.medical_history])
            st.dataframe(df)

    # Pestaña de Validación
    with tabs[4]:
        # TODO: download pdf
        if st.session_state.medical_history:
            case = st.session_state.medical_history[-1]
            if case.get('report'):
                st.download_button(
                    label="📥 Descargar Reporte",
                    data=base64.b64decode(case['report']['pdf']),
                    file_name=f"diagnostico_{st.session_state.patient_id}.pdf",
                    mime="application/pdf"
                )

    # Pestaña de Pago
    with tabs[5]:
        st.subheader("Pago de Medicamentos")
        st.image("https://www.payretailers.com/wp-content/uploads/2021/07/logo.svg", width=200)
        st.markdown("[▶ Ir a PayRetailers](https://payretailers.com/es/)")

# Columna derecha - Chat
with col2:
    st.header("Asistente de Salud")

    uploaded_image = st.file_uploader("Subir imagen médica", type=["jpg", "png"])

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("Describe tus síntomas..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        try:
            # Ejecutar el agente
            response = agent_executor.invoke({
                "query": user_input,
                "chat_history": st.session_state.messages,
                "location": st.session_state.user_coordinates
            })
            output = response.get("output", "")

            # Generar reporte médico si hay diagnóstico
            if "diagnóstico" in output.lower():
                # Crear datos para el reporte
                report_data = {
                    "diagnosis": output,
                    "prescriptions": "Medicación según prescripción médica",
                    "recommendations": "Seguir indicaciones del especialista",
                    "tests": "Análisis clínicos básicos"
                }

                # Generar PDF
                pdf_bytes = create_diagnosis_pdf(st.session_state.patient_id, report_data)
                pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

                # Actualizar historial médico
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

                # Añadir mensaje del sistema
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Reporte médico generado. ID: {st.session_state.patient_id}"
                })

            # Mostrar respuesta del agente
            st.session_state.messages.append({"role": "assistant", "content": output})
            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)}")