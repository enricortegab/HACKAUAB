from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

# TODO: not implemented

class DiagnosisDeliveryInput(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    diagnosis: Dict = Field(..., description="Validated medical diagnosis")
    treatment_plan: Dict = Field(..., description="Structured treatment plan")
    communication_preferences: Dict


@tool(args_schema=DiagnosisDeliveryInput)
def diagnosis_delivery(
        patient_id: str,
        diagnosis: Dict,
        treatment_plan: Dict,
        communication_preferences: Optional[Dict] = None
) -> dict:
    """
    Delivers validated diagnosis and treatment plan to patient through the chatbot interface.
    Formats information according to patient's communication preferences.
    """
    try:
        # Default communication preferences
        if communication_preferences is None:
            communication_preferences = {"channel": "chat", "language": "es"}

        # Format the diagnosis message
        formatted_message = format_diagnosis_message(
            diagnosis,
            treatment_plan,
            communication_preferences["language"]
        )

        # Create delivery record
        delivery_record = {
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat(),
            "status": "delivered",
            "content": formatted_message,
            "communication_channel": communication_preferences["channel"]
        }

        return {
            "status": "success",
            "delivery_record": delivery_record,
            "formatted_message": formatted_message
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def format_diagnosis_message(
        diagnosis: Dict,
        treatment_plan: Dict,
        language: str = "es"
) -> str:
    """
    Formats diagnosis and treatment plan into patient-friendly message
    """
    # Base template
    template = """
    🩺 **Resultados Médicos Validados**  

    **Diagnóstico Principal:**  
    {diagnosis}  

    **Detalles del Diagnóstico:**  
    {diagnosis_details}  

    **Plan de Tratamiento:**  
    {treatment_plan}  

    **Instrucciones Importantes:**  
    {important_notes}  

    **Siguientes Pasos:**  
    {next_steps}  

    _Este diagnóstico ha sido validado por nuestro equipo médico._
    """

    # Extract components
    components = {
        "diagnosis": diagnosis.get("condition", "N/A"),
        "diagnosis_details": diagnosis.get("details", "N/A"),
        "treatment_plan": "\n".join(
            f"- {k}: {v}" for k, v in treatment_plan.items()
        ),
        "important_notes": diagnosis.get("important_notes", "Siga las indicaciones médicas"),
        "next_steps": diagnosis.get("next_steps", "Programar")}