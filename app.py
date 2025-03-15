import os
from datetime import datetime
import streamlit as st
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from models import MedicalEncounter
from utils import extract_from_response, extract_payment_info, get_locations
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI()

class Response(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

parser = PydanticOutputParser(pydantic_object=Response)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a compassionate healthcare assistant for rural populations. Guide the conversation to:
1. Conduct complete symptom analysis
2. Request medical images when necessary
3. Provide diagnosis with confidence levels
4. Suggest nearby treatment options
5. Offer payment solutions
6. Maintain multilingual support""",
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = []

agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Initialize session state
st.session_state.setdefault("medical_history", [])
st.session_state.setdefault("messages", [{"role": "assistant", "content": "¡Hola! Soy tu asistente de salud rural. ¿Qué síntomas estás experimentando?"}])

# Page layout
st.set_page_config(layout="wide")

# Create columns outside of the sidebar context
col1, col2 = st.columns([1, 1])

# Left Column (Sidebar-like content)
with col1:
    st.header("Contexto Médico")  # Traducido: "Medical Context"
    tabs = st.tabs(["Mapa Sanitario", "Red de Farmacias", "Resumen del Caso", "Historial Completo", "Validación Médica"])

    # ... (rest of the left column content, including the validation tab)
    with tabs[4]:  # Nueva pestaña de validación médica
        st.subheader("Centro de Validación Médica")  # Traducido: "Medical Validation Hub"

        if st.session_state.medical_history:
            latest_case = st.session_state.medical_history[-1]

            # Sección de validación médica
            if latest_case.get("medical_validation"):
                st.success("✅ Caso Validado")
                st.write(f"**Estado:** {latest_case['medical_validation']['status']}")
                st.write(f"**Urgencia:** {latest_case['medical_validation'].get('urgency', 'N/A')}")
                st.write("**Notas Médicas:**")
                st.markdown(f"> {latest_case['medical_validation']['notes']}")
                st.write("**Plan de Tratamiento:**")
                st.markdown(latest_case['medical_validation']['treatment_plan'])

                if st.button("Reabrir Validación"):
                    del latest_case["medical_validation"]
                    st.experimental_rerun()
            else:
                with st.form("medical_review_form"):
                    st.subheader("Validación del Diagnóstico")

                    # Datos del caso
                    st.write(f"**Paciente:** {latest_case.get('patient_id', 'N/A')}")
                    st.write(f"**Diagnóstico Preliminar:** {latest_case.get('diagnosis', 'N/A')}")
                    st.write(f"**Síntomas:** {', '.join(latest_case.get('symptoms', []))}")

                    # Campos de validación
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

                    clinical_notes = st.text_area(
                        "Notas Clínicas",
                        help="Observaciones profesionales para el caso"
                    )

                    treatment_plan = st.text_area(
                        "Plan de Tratamiento Oficial",
                        value=latest_case.get('recommendations', ''),
                        height=150
                    )

                    if st.form_submit_button("Validar Diagnóstico"):
                        # Guardar validación
                        validation_data = {
                            "status": diagnosis_status,
                            "urgency": medical_urgency,
                            "notes": clinical_notes,
                            "treatment_plan": treatment_plan,
                            "validator": "Dr. " + st.secrets.get("DOCTOR_NAME", "Médico"),
                            "timestamp": datetime.now().isoformat()
                        }

                        # Actualizar historial médico
                        latest_case["medical_validation"] = validation_data

                        # Generar mensaje para el paciente
                        feedback_message = f"""
                        🩺 **Actualización Médica Oficial** **Estado:** {diagnosis_status}  
                        **Urgencia:** {medical_urgency}  
                        **Plan de Tratamiento:** {treatment_plan}  
                        _Validado por: {validation_data['validator']}_  
                        """

                        # Agregar al historial de chat
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": feedback_message
                        })

                        st.success("Diagnóstico validado y enviado al paciente")
                        st.experimental_rerun()

# Right Column - Chat Interface
with col2:
    st.header("Asistente de Salud Rural")  # Traducido: "Rural Health Assistant"

    # Image upload
    uploaded_image = st.file_uploader("Subir imagen médica", type=["jpg", "png"])  # Traducido: "Upload medical image"

    # Display chat messages
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # User input handling
    user_input = st.chat_input("Describe tus síntomas o haz una pregunta...")  # Traducido: "Describe your symptoms or ask a question..."

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        try:
            # Get AI response
            content = agent_executor.invoke({"query": user_input})

            # Process and store medical data
            try:
                encounter_data = {
                    "symptoms": extract_from_response(content, "symptoms"),
                    "diagnosis": extract_from_response(content, "diagnosis"),
                    "recommendations": extract_from_response(content, "recommendations"),
                    "locations": get_locations(content),
                    "timestamp": datetime.now().isoformat(),
                    "payment_info": extract_payment_info(content)
                }
                encounter = MedicalEncounter(**encounter_data)
                st.session_state.medical_history.append(encounter.dict())
            except Exception as e:
                st.error(f"Error al guardar datos: {str(e)}")  # Traducido: "Data saving error"

            # Display response
            st.session_state.messages.append({"role": "assistant", "content": content})
            st.chat_message("assistant").write(content["output"])

        except Exception as e:
            st.error(f"Error de procesamiento: {str(e)}")  # Traducido: "Processing error"