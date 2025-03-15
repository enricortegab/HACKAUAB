import streamlit as st
from datetime import datetime
import pandas as pd
from langchain.agents import AgentExecutor, create_tool_calling_agent

from tools import tools

from llm import llm, prompt

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

st.session_state.setdefault("medical_history", [])
st.session_state.setdefault("messages", [
    {"role": "assistant", "content": "¡Hola! Soy tu asistente de salud rural. ¿Qué síntomas estás experimentando?"}])

st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 1])

patient_location = {'lat': 19.4326, 'lon': -99.1332}

meds = []

# Ubicaciones de farmacias cercanas
pharmacies_locations = pd.DataFrame([
    {'lat': 19.434, 'lon': -99.140, 'nombre': 'Farmacia Uno'},
    {'lat': 19.429, 'lon': -99.130, 'nombre': 'Farmacia Dos'},
    {'lat': 19.431, 'lon': -99.135, 'nombre': 'Farmacia Tres'},
    {'lat': 19.435, 'lon': -99.132, 'nombre': 'Farmacia Cuatro'}
])
with col1:
    st.header("Contexto Médico")

    tabs = st.tabs(["Red de Farmacias cercanas", "Resumen del Caso", "Historial Completo", "Centro de Validación Médica", "Pago"])


    # Red sanitaria según ubicación
    with tabs[0]:
        st.subheader("Red de Farmacias Local")
        st.write("Farmacias cercanas según la ubicación del paciente")

        st.map(pd.concat([pd.DataFrame([patient_location]), pharmacies_locations]))


    # Informe detallado del caso
    with tabs[1]:
        st.subheader("Resumen Completo del Caso")

        if st.session_state.medical_history:
            latest_case = st.session_state.medical_history[-1]
            st.write(f"**Paciente:** {latest_case.get('patient_id', 'N/A')}")
            st.write(f"**Síntomas:** {', '.join(latest_case.get('symptoms', []))}")
            st.write(f"**Diagnóstico:** {latest_case.get('diagnosis', 'Pendiente')}")
            st.write(f"**Recomendaciones:** {latest_case.get('recommendations', 'Pendientes')}")
            if latest_case.get("medical_validation"):
                st.write("### Validación Médica")
                val = latest_case['medical_validation']
                st.write(f"**Estado Validación:** {val['status']}")
                st.write(f"**Urgencia:** {val['urgency']}")
                st.write(f"**Notas médicas:** {val['notes']}")
                st.write(f"**Plan tratamiento:** {val['treatment_plan']}")
            else:
                st.warning("El caso aún no ha sido validado médicamente")
        else:
            st.info("No hay datos recientes del paciente")

    with tabs[2]:
        historial_medico = [
    {"Fecha": "2024-03-05", "Edad": 30, "Síntomas": "Dolor muscular", "Diagnóstico": "Contractura muscular", "Tratamiento": "Relajante muscular, descanso"},
    {"Fecha": "2024-01-17", "Edad": 30, "Síntomas": "Dolor de oído", "Diagnóstico": "Otitis", "Tratamiento": "Gotas óticas antibióticas"},
    {"Fecha": "2024-03-01", "Edad": 29, "Síntomas": "Dolor de cabeza frecuente", "Diagnóstico": "Migraña", "Tratamiento": "Ibuprofeno, reducción del estrés"},
    {"Fecha": "2024-02-05", "Edad": 29, "Síntomas": "Congestión nasal", "Diagnóstico": "Rinitis alérgica", "Tratamiento": "Antihistamínicos diarios"},
    {"Fecha": "2024-01-15", "Edad": 27, "Síntomas": "Dolor lumbar", "Diagnóstico": "Lumbalgia", "Tratamiento": "Ibuprofeno, fisioterapia"},
    {"Fecha": "2023-12-02", "Edad": 26, "Síntomas": "Mareos, debilidad", "Diagnóstico": "Hipotensión", "Tratamiento": "Aumento de líquidos y reposo"},
    {"Fecha": "2023-08-20", "Edad": 25, "Síntomas": "Inflamación en rodilla", "Diagnóstico": "Bursitis", "Tratamiento": "Reposo, antiinflamatorios"},
    {"Fecha": "2023-05-05", "Edad": 24, "Síntomas": "Dolor torácico leve", "Diagnóstico": "Costocondritis", "Tratamiento": "Analgésicos, descanso físico"},
    {"Fecha": "2023-03-12", "Edad": 23, "Síntomas": "Cansancio excesivo", "Diagnóstico": "Anemia leve", "Tratamiento": "Suplementos de hierro"},
    {"Fecha": "2023-01-25", "Edad": 23, "Síntomas": "Erupción cutánea", "Diagnóstico": "Dermatitis", "Tratamiento": "Crema tópica, evitar irritantes"},
    {"Fecha": "2022-11-09", "Edad": 21, "Síntomas": "Tos persistente, fiebre", "Diagnóstico": "Bronquitis", "Tratamiento": "Amoxicilina 500mg cada 8h por 7 días"},
    {"Fecha": "2022-02-05", "Edad": 20, "Síntomas": "Mareos frecuentes", "Diagnóstico": "Vértigo posicional benigno", "Tratamiento": "Ejercicios vestibulares, reposo"},
    {"Fecha": "2021-11-10", "Edad": 20, "Síntomas": "Dolor en la garganta", "Diagnóstico": "Faringitis", "Tratamiento": "Ibuprofeno, gárgaras salinas"},
    {"Fecha": "2021-08-15", "Edad": 18, "Síntomas": "Dolor muscular generalizado", "Diagnóstico": "Fibromialgia leve", "Tratamiento": "Fisioterapia, ejercicios moderados"},
    {"Fecha": "2021-04-20", "Edad": 15, "Síntomas": "Acidez frecuente", "Diagnóstico": "Reflujo gastroesofágico", "Tratamiento": "Omeprazol, dieta especial"}
]

        df_history = pd.DataFrame(historial_medico)
        st.dataframe(df_history, use_container_width=True)

    # Centro de validación médica
    with tabs[3]:
        st.subheader("Centro de Validación Médica")
        st.map(pd.DataFrame([patient_location]))


        if st.session_state.medical_history:
            latest_case = st.session_state.medical_history[-1]

            with tabs[3]:
                st.subheader("Centro de Validación Médica")
                st.map(pd.DataFrame([patient_location]))

                if st.session_state.medical_history:
                    latest_case = st.session_state.medical_history[-1]

                    # Mostrar PDF si existe
                    if latest_case.get("diagnosis_report"):
                        report = latest_case["diagnosis_report"]

                        st.markdown("### Reporte de Diagnóstico")
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write("**Diagnóstico:**")
                            st.markdown(f"> {report['data']['diagnosis']}")

                            st.write("**Recomendaciones:**")
                            st.markdown(report['data']['recommendations'])

                        with col2:
                            st.write("**Descargar Reporte**")
                            pdf_bytes = base64.b64decode(report['pdf'])

                            st.download_button(
                                label="📄 Descargar PDF",
                                data=pdf_bytes,
                                file_name=f"diagnostico_{latest_case.get('patient_id', '')}.pdf",
                                mime="application/pdf"
                            )

            if latest_case.get("medical_validation"):
                st.success("✅ Caso Validado")
                st.write(f"**Estado:** {latest_case['medical_validation']['status']}")
                st.write(f"**Urgencia:** {latest_case['medical_validation'].get('urgency', 'N/A')}")
                st.write("**Plan de Tratamiento:**")
                st.markdown(latest_case['medical_validation']['treatment_plan'])

                if st.button("Reabrir Validación"):
                    del latest_case["medical_validation"]
                    st.experimental_rerun()
            else:
                with st.form("medical_review_form"):
                    st.subheader("Validación del Diagnóstico")
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

                        latest_case["medical_validation"] = validation_data

                        feedback_message = f"""
                        🩺 **Actualización Médica Oficial**  
                        **Estado:** {diagnosis_status}  
                        **Urgencia:** {medical_urgency}  
                        **Tratamiento:** {treatment_plan}  
                        _Validado por: {validation_data['validator']}_
                        """

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": feedback_message
                        })

                        st.success("Diagnóstico validado y enviado")
                        st.experimental_rerun()
    with tabs[4]:
        st.subheader("Pago del Producto - PayRetails")

        # Mostrar logo de PayRetails
        st.image("data/PayRetailers.png", width=400)

        # Botón directo para abrir la página en otra pestaña
        st.markdown("[🔗 Accede directamente a Pay Retailers para realizar tu pago](https://payretailers.com/es/)",
                    unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Medicamentos disponibles")

        medicamentos = [
            {"nombre": "Paracetamol 500mg", "precio": "$50 MXN", "imagen": "https://via.placeholder.com/150"},
            {"nombre": "Omeprazol 20mg", "precio": "$75 MXN", "imagen": "https://via.placeholder.com/150"},
            {"nombre": "Ibuprofeno 400mg", "precio": "$65 MXN", "imagen": "https://via.placeholder.com/150"}
        ]

        for med in medicamentos:
            st.image(med["imagen"], width=100)
            st.write(f"**{med['nombre']}** - {med['precio']}")
            if st.button(f"Pagar {med['nombre']}"):
                st.success(f"Redirigiendo a Pay Retailers para realizar el pago de {med['nombre']}...")

with col2:
    st.header("Asistente de Salud Rural")
    uploaded_image = st.file_uploader("Subir imagen médica", type=["jpg", "png"])
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    user_input = st.chat_input("Describe síntomas...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        raw = agent_executor.invoke({"query": user_input, "chat_history": st.session_state.messages})
        response_content = raw.get("output", "No se pudo procesar la respuesta.")
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.chat_message("assistant").write(response_content)
