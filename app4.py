import base64
import random as rd
import uuid
from datetime import datetime
from typing import List, Dict, Optional

import langchain_core
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, ValidationError

from llm import llm, prompt
from tools import tools
from tools.diagnosis_delivery import create_diagnosis_pdf

USER_COLOR = "#228B22"
PHARMACY_COLOR = "#B4C424"
HOSPITAL_COLOR = "#FF5733"
DEFAULT_LOCATION = {"lat": 18.3736, "lon": 65.9631}

# DEMO: Belgrano 1092, Ciudad de Mendoza


# Models for structured data handling
class Patient(BaseModel):
    id: str
    location: Optional[Dict[str, float]] = None
    location_name: str = ""


class MedicalCase(BaseModel):
    patient_id: str
    symptoms: List[str]
    diagnosis: Optional[str] = None
    timestamp: str
    report: Optional[Dict] = None
    validation: Optional[Dict] = None


class Medication(BaseModel):
    name: str
    dosage: str
    price: float
    description: str


# Response models for agent
class ChoiceResponse(BaseModel):
    choice: str = Field(description="One of: general, medication, diagnosis")


class GeneralResponse(BaseModel):
    content: str = Field(description="Response content")
    tools_used: List[str] = Field(description="Tools used in the response")


class MedicationResponse(BaseModel):
    content: str = Field(description="Medication explanation")
    medications: List[Dict[str, str]] = Field(description="List of medications")


class DiagnosisResponse(BaseModel):
    content: str = Field(description="Diagnosis explanation")
    diagnosis: str = Field(description="Short diagnosis summary")
    recommendations: str = Field(description="Treatment recommendations")
    severity: str = Field(description="Low, Medium, or High")


# Initialize session state in a structured way
def initialize_session_state():
    if 'patient' not in st.session_state:
        st.session_state.patient = Patient(
            id=str(uuid.uuid4())[:8],
            location=DEFAULT_LOCATION,
            location_name=""
        )

    st.session_state.setdefault("medical_history", [])
    st.session_state.setdefault("medications", [])
    st.session_state.setdefault("messages", [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de salud. ¿Qué síntomas estás experimentando?"}
    ])
    st.session_state.setdefault("error", None)


# Agent configuration with error handling
def setup_agent():
    try:
        agent = create_tool_calling_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)
    except Exception as e:
        st.error(f"Error initializing agent: {str(e)}")
        return None


# Location services with error handling
def update_user_location(location_name: str) -> bool:
    """Update user location based on provided address"""
    try:
        geolocator = Nominatim(user_agent="medical_app")
        location = geolocator.geocode(location_name)
        if location:
            st.session_state.patient.location = {'lat': location.latitude, 'lon': location.longitude}
            st.session_state.patient.location_name = location_name
            return True
        else:
            st.warning("No se pudo encontrar la ubicación. Por favor, intenta con otra dirección.")
            return False
    except Exception as e:
        st.error(f"Error en el servicio de geolocalización: {str(e)}")
        return False


# Generate locations for map with randomized but realistic coordinates
def generate_healthcare_locations(user_loc: dict, entity_type: str = "pharmacy"):
    """Generate pharmacy or hospital locations near user"""
    color = PHARMACY_COLOR if entity_type == "pharmacy" else HOSPITAL_COLOR
    count = rd.randint(1, 1) if entity_type == "pharmacy" else rd.randint(1, 1)
    spread = 2 if entity_type == "pharmacy" else 150  # Smaller spread for pharmacies

    return pd.DataFrame([
        {
            'lat': user_loc['lat'] + rd.randint(-spread, spread) / 100,
            'lon': user_loc['lon'] + rd.randint(-spread, spread) / 100,
            'col': color,
            'name': f"{entity_type.capitalize()} {i + 1}"
        }
        for i in range(count)
    ])


# Process diagnosis and generate PDF report
def process_diagnosis(user_input: str, diagnosis_data: DiagnosisResponse) -> Dict:
    """Process diagnosis data and create PDF report"""
    try:
        report_data = {
            "diagnosis": diagnosis_data.diagnosis,
            "prescriptions": "Según recomendación médica",
            "recommendations": diagnosis_data.recommendations,
            "tests": "Análisis clínicos según sea necesario"
        }

        pdf_bytes = create_diagnosis_pdf(st.session_state.patient.id, report_data)
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

        new_case = {
            "patient_id": st.session_state.patient.id,
            "symptoms": [user_input],
            "diagnosis": diagnosis_data.diagnosis,
            "timestamp": datetime.now().isoformat(),
            "severity": diagnosis_data.severity,
            "report": {
                "pdf": pdf_b64,
                "data": report_data
            }
        }

        return new_case
    except Exception as e:
        st.error(f"Error al generar diagnóstico: {str(e)}")
        return None


# Process agent response based on response type
def process_agent_response(agent_executor, user_input: str):
    """Process user input through agent and handle different response types"""
    try:
        # Create parsers
        generic_parser = PydanticOutputParser(pydantic_object=ChoiceResponse)
        general_parser = PydanticOutputParser(pydantic_object=GeneralResponse)
        medication_parser = PydanticOutputParser(pydantic_object=MedicationResponse)
        diagnosis_parser = PydanticOutputParser(pydantic_object=DiagnosisResponse)

        # First determine response type
        with st.spinner("Procesando tu consulta..."):
            choice_response = agent_executor.invoke({
                "query": f"Determine response type for: {user_input}",
                "chat_history": st.session_state.messages,
                "format_instructions": generic_parser.get_format_instructions()
            })

            try:
                choice = generic_parser.parse(choice_response["output"]).choice
            except Exception:
                choice = choice_response["output"]

            # Select parser based on response type
            if choice == "medication":
                parser = medication_parser
                format_instructions = "Return the response as a JSON object with 'content' (string) and 'medications' fields. The medication fields should be a list with one dictionary for each medication in the following format: [{'name': <name>, 'description': <description>, 'price': <price>}]"
                print("Choosing medication parser")
            elif choice == "diagnosis":
                parser = diagnosis_parser
                format_instructions = "Return the response as a JSON object with 'content', 'diagnosis', 'recommendation' and 'severities' fields. All of the previous are strings."
                print("Choosing diagnosis parser")
            else:
                parser = general_parser
                format_instructions = "Return the response as a JSON object with 'content' and 'tools_used' fields. For example: {{\"content\": \"Your response here\", \"tools_used\": [\"tool1\", \"tool2\"]}}"
                print("Choosing general parser")

            # Get detailed response
            response = agent_executor.invoke({
                "query": f"{user_input}",
                # "query": f"{user_input}. {format_instructions}",
                "chat_history": st.session_state.messages,
                "format_instructions": parser.get_format_instructions()
            })

            print(f"RAW: {response}")
            print(parser.get_format_instructions())

            # Process based on response type
            if choice == "medication":
                try:
                    med_data = medication_parser.parse(response["output"])
                except Exception:
                    med_data = response["output"]

                if isinstance(med_data, MedicationResponse):
                    st.session_state.medications = med_data.medications
                response_content = med_data.content if isinstance(med_data, MedicationResponse) else med_data

            elif choice == "diagnosis":
                try:
                    diagnosis_data = diagnosis_parser.parse(response["output"])
                except Exception:
                    diagnosis_data = response["output"]

                response_content = diagnosis_data.content if isinstance(diagnosis_data, DiagnosisResponse) else diagnosis_data

                # Create medical case record
                new_case = process_diagnosis(user_input, diagnosis_data)
                if new_case:
                    st.session_state.medical_history.append(new_case)

            else:
                try:
                    response_content = general_parser.parse(response["output"]).content
                except Exception:
                    response_content = response["output"]


            # Update chat history
            st.session_state.messages.append({"role": "assistant", "content": response_content})

    except ZeroDivisionError as e:
        st.error(f"Error al procesar la respuesta: {str(e)}")
        st.session_state.error = str(e)
        response_content = "Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, intenta de nuevo."
        st.session_state.messages.append({"role": "assistant", "content": response_content})


# UI Components
def render_map_tab():
    """Render the location map tab"""
    st.subheader("Consulta farmacias y hospitales cercanos")

    # Check if location has been set using the existing attributes
    location_set = (
            hasattr(st.session_state, 'patient') and
            hasattr(st.session_state.patient, 'location_name') and
            st.session_state.patient.location_name != "" and
            st.session_state.patient.location is not None
    )

    # Show map or input based on whether location is set
    if not location_set:
        # Only show input field if no location set
        location = st.text_input(
            "Introduce tu ubicación:",
            value="",
            placeholder="Ej: Calle Mayor 1, Madrid",
            help="Ingresa tu dirección para ver servicios médicos cercanos"
        )

        if st.button("Buscar ubicación") and location:
            if update_user_location(location):
                st.success(f"Ubicación actualizada: {location}")
                st.rerun()  # Refresh to show map
    else:
        # Display the map since we have coordinates
        loc = st.session_state.patient.location.copy()
        loc["col"] = USER_COLOR
        loc["name"] = "Tu ubicación"

        # Generate nearby healthcare locations
        pharmacies = generate_healthcare_locations(st.session_state.patient.location, "pharmacy")
        hospitals = generate_healthcare_locations(st.session_state.patient.location, "hospital")

        # Create and display map
        locations_df = pd.concat([pd.DataFrame([loc]), pharmacies, hospitals])
        st.map(locations_df, color="col")

        # Add legend with tooltips
        with st.expander("Leyenda del mapa"):
            st.markdown(f"<span style='color:{USER_COLOR}'>●</span> Paciente: Tu ubicación actual",
                        unsafe_allow_html=True)
            st.markdown(f"<span style='color:{HOSPITAL_COLOR}'>●</span> Hospitales: Centros médicos cercanos",
                        unsafe_allow_html=True)
            st.markdown(
                f"<span style='color:{PHARMACY_COLOR}'>●</span> Farmacias: Establecimientos donde puedes adquirir medicamentos",
                unsafe_allow_html=True)

        # Button to change address (shows a form when clicked)
        if st.button("Cambiar ubicación"):
            # Reset location
            if hasattr(st.session_state, 'patient'):
                st.session_state.patient.location_name = ""
            st.rerun()  # Refresh to show input


def render_case_summary_tab():
    """Render patient case summary tab"""
    if st.session_state.medical_history:
        latest_case = st.session_state.medical_history[-1]

        # Patient info card
        with st.container():
            st.markdown("### Información del Paciente")
            st.write(f"**ID:** {st.session_state.patient.id}")
            st.write(f"**Síntomas:** {', '.join(latest_case.get('symptoms', []))}")
            st.write(f"**Diagnóstico:** {latest_case.get('diagnosis', 'Pendiente')}")
            st.write(f"**Severidad:** {latest_case.get('severity', 'No especificada')}")

        # Medical report section
        if latest_case.get("report"):
            st.markdown("### Reporte Médico")

            # Two column layout for recommendations and download button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("**Recomendaciones:**")
                st.markdown(latest_case['report']['data']['recommendations'])
            with col2:
                pdf_bytes = base64.b64decode(latest_case['report']['pdf'])
                st.download_button(
                    label="📄 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"diagnostico_{st.session_state.patient.id}.pdf",
                    mime="application/pdf",
                    help="Descarga el informe médico en formato PDF"
                )
    else:
        st.info("Aún no hay diagnósticos registrados. Consulta con el asistente para obtener ayuda.")


def render_medical_history_tab():
    """Render medical history tab with filtering options"""
    if st.session_state.medical_history:
        # Add search and filter options
        search_term = st.text_input("Buscar en historial:", placeholder="Filtrar por síntomas o diagnóstico")

        # Convert history to dataframe
        df_history = pd.DataFrame([{
            'Fecha': case['timestamp'],
            'Síntomas': ', '.join(case.get('symptoms', [])),
            'Diagnóstico': case.get('diagnosis', ''),
            'Severidad': case.get('severity', 'No especificada'),
            'Validado': '✅' if case.get('validation') else '❌'
        } for case in st.session_state.medical_history])

        # Apply search filter if provided
        if search_term:
            mask = (
                    df_history['Síntomas'].str.contains(search_term, case=False, na=False) |
                    df_history['Diagnóstico'].str.contains(search_term, case=False, na=False)
            )
            df_history = df_history[mask]

        # Allow sorting by date
        st.dataframe(
            df_history.sort_values('Fecha', ascending=False),
            use_container_width=True,
            hide_index=True
        )

        # Export options
        if st.button("Exportar Historial (CSV)"):
            csv_data = df_history.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv_data,
                file_name=f"historial_medico_{st.session_state.patient.id}.csv",
                mime="text/csv"
            )
    else:
        st.info("No hay historial médico disponible.")


def render_medical_validation_tab():
    """Render medical validation tab for professionals"""
    if st.session_state.medical_history:
        latest_case = st.session_state.medical_history[-1]

        # Show validation status or form
        if latest_case.get("validation"):
            with st.container():
                st.success("✅ Caso Validado por Profesional Médico")
                st.write(f"**Estado:** {latest_case['validation']['status']}")
                st.write(f"**Urgencia:** {latest_case['validation'].get('urgency', 'N/A')}")
                st.write(f"**Validado por:** {latest_case['validation'].get('validator', 'N/A')}")
                st.write(f"**Fecha de validación:** {latest_case['validation'].get('timestamp', 'N/A')}")

                st.markdown("### Plan de Tratamiento")
                st.markdown(latest_case['validation']['treatment_plan'])

                if latest_case['validation'].get('notes'):
                    st.markdown("### Notas Clínicas")
                    st.markdown(latest_case['validation']['notes'])
        else:
            # Professional authentication
            with st.expander("Autenticación de Profesional Médico"):
                col1, col2 = st.columns(2)
                with col1:
                    professional_id = st.text_input("ID de Profesional:", placeholder="Ingrese su ID")
                with col2:
                    professional_pin = st.text_input("PIN:", type="password", placeholder="Ingrese su PIN")

                # In a real app, this would verify against a secure database
                is_authenticated = professional_id and professional_pin

            # Only show validation form if authenticated
            if is_authenticated:
                with st.form("medical_review_form"):
                    st.subheader("Validación Médica")

                    diagnosis_status = st.radio(
                        "Estado del Diagnóstico",
                        options=["Confirmado", "Modificado", "Rechazado"],
                        horizontal=True,
                        help="Seleccione si confirma, modifica o rechaza el diagnóstico propuesto"
                    )

                    if diagnosis_status == "Modificado":
                        modified_diagnosis = st.text_area(
                            "Diagnóstico Corregido",
                            value=latest_case.get('diagnosis', ''),
                            help="Ingrese el diagnóstico correcto"
                        )

                    medical_urgency = st.select_slider(
                        "Nivel de Urgencia",
                        options=["Baja", "Media", "Alta", "Crítica"],
                        value="Media",
                        help="Seleccione el nivel de urgencia médica"
                    )

                    clinical_notes = st.text_area(
                        "Notas Clínicas",
                        help="Notas adicionales para el equipo médico"
                    )

                    treatment_plan = st.text_area(
                        "Plan de Tratamiento",
                        help="Detalle el plan de tratamiento recomendado"
                    )

                    if st.form_submit_button("Validar Diagnóstico"):
                        if not treatment_plan:
                            st.error("El plan de tratamiento es obligatorio")
                        else:
                            validation_data = {
                                "status": diagnosis_status,
                                "diagnosis": modified_diagnosis if diagnosis_status == "Modificado" else latest_case.get(
                                    'diagnosis'),
                                "urgency": medical_urgency,
                                "notes": clinical_notes,
                                "treatment_plan": treatment_plan,
                                "validator": f"Dr. {professional_id}",
                                "timestamp": datetime.now().isoformat()
                            }
                            latest_case["validation"] = validation_data
                            st.success("¡Diagnóstico validado correctamente!")
                            st.rerun()
            else:
                st.warning("Se requiere autenticación para validar diagnósticos.")
    else:
        st.info("No hay casos pendientes de validación.")


def render_payment_tab():
    """Render payment and medication tab"""
    st.subheader("Pago de Medicamentos")

    # Display medications cart
    if st.session_state.medications:
        st.subheader("Tu Carrito de Medicamentos")

        # Create a shopping cart display
        for i, med in enumerate(st.session_state.medications):

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{med['name']}**")
                    st.caption(f"Desc: {med.get('description', 'Según indicación')}")
                with col2:
                    price = med.get('price', 0) or float(rd.randint(100, 500))
                    st.markdown(f"**${price:.2f}**")
                with col3:
                    if st.button(f"🛒 Comprar", key=f"buy_{i}"):
                        st.session_state['payment_active'] = True
                        st.session_state['payment_med'] = med['name']
                        st.rerun()

        if st.button("🛒 Comprar Todo"):
            st.session_state['payment_active'] = True
            st.session_state['payment_med'] = "todos los medicamentos"
            st.rerun()
    else:
        st.info("No hay medicamentos en tu carrito")

    st.markdown("---")

    # Payment gateway integration
    with st.container():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("data/PayRetailers.png", width=200)
        with col2:
            st.markdown("### Pasarela de Pago Segura")
            st.markdown("Conectado con PayRetailers para procesar pagos de manera segura.")
            st.markdown("[▶ Ir a PayRetailers para más información](https://payretailers.com/es/)")

    # Payment processing simulation
    if st.session_state.get('payment_active'):
        with st.form("payment_form"):
            st.subheader(f"Procesando pago para {st.session_state['payment_med']}")

            st.selectbox("Método de Pago",
                         ["Tarjeta de Crédito", "PayPal", "Transferencia", "Efectivo en Farmacia"])
            st.text_input("Nombre en Tarjeta")
            st.text_input("Número de Tarjeta", placeholder="XXXX XXXX XXXX XXXX")

            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Fecha Exp.", placeholder="MM/AA")
            with col2:
                st.text_input("CVV", type="password")

            if st.form_submit_button("Confirmar Pago"):
                st.success("¡Pago procesado correctamente!")
                st.balloons()
                st.session_state['payment_active'] = False
                st.rerun()


def render_chat_interface(agent_executor):
    """Render the chat interface"""
    st.header("Asistente de Salud")

    # Medical image upload
    uploaded_image = st.file_uploader(
        "Subir imagen médica",
        type=["jpg", "png", "jpeg"],
        help="Puedes subir imágenes médicas para un mejor diagnóstico"
    )

    if uploaded_image:
        st.image(uploaded_image, caption="Imagen subida", use_container_width=True)
        st.session_state.setdefault("image_uploaded", True)

    # Display chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Chat input
    user_input = st.chat_input("Describe tus síntomas...")

    # Process user input
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        process_agent_response(agent_executor, user_input)
        st.rerun()


# Main application function
def main():
    # Page config
    st.set_page_config(
        page_title="Asistente Médico Virtual",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar
    with st.sidebar:
        st.title("🏥 Asistente Médico Virtual")
        st.markdown("Consulta médica basada en inteligencia artificial")

        # User profile section
        with st.expander("Perfil de Paciente"):
            st.write(f"**ID:** {st.session_state.patient.id if 'patient' in st.session_state else ''}")
            if st.button("Nuevo Paciente"):
                st.session_state.patient = Patient(
                    id=str(uuid.uuid4())[:8],
                    location=DEFAULT_LOCATION,
                    location_name=""
                )
                st.session_state.medical_history = []
                st.session_state.medications = []
                st.session_state.messages = [
                    {"role": "assistant",
                     "content": "¡Hola! Soy tu asistente de salud. ¿Qué síntomas estás experimentando?"}
                ]
                st.rerun()

        # Important disclaimers
        st.markdown("---")
        st.markdown("### ⚠️ Importante")
        st.markdown("""
                    Este es un asistente médico virtual. No reemplaza la consulta con un profesional médico. 
                    En caso de emergencia, contacte a servicios médicos de emergencia.
                """)

        # App info
        st.markdown("---")
        st.markdown("Desarrollado con Streamlit y LangChain")
        st.caption("v2.0.0")

    # Initialize state
    initialize_session_state()

    # Setup agent
    agent_executor = setup_agent()

    if not agent_executor:
        st.error("Error al inicializar el asistente médico. Por favor, recarga la página.")
        return

    # Main layout
    col1, col2 = st.columns([1, 1])

    # Medical Context Column
    with col1:
        st.header("Contexto Médico")
        tabs = st.tabs(["Mapa", "Ficha", "Historial", "Validación", "Cesta"])

        with tabs[0]:
            render_map_tab()

        with tabs[1]:
            render_case_summary_tab()

        with tabs[2]:
            render_medical_history_tab()

        with tabs[3]:
            render_medical_validation_tab()

        with tabs[4]:
            render_payment_tab()

    # Chat Interface Column
    with col2:
        render_chat_interface(agent_executor)


if __name__ == "__main__":
    main()
