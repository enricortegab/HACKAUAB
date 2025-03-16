from dotenv import load_dotenv
import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from llm import llm

load_dotenv()


class AppointmentRequest(BaseModel):
    patient_id: str
    desired_date: str
    urgency: str
    appointment_api: str


@tool
def schedule_appointment(request: AppointmentRequest) -> dict:
    """
     This tool is designed for patients who wish to change or reschedule their appointment.

     It interacts with the patient by asking, through a language model prompt, if they would like to modify their appointment
     to the specified date with the given urgency. If the patient responds "Yes", the tool proceeds to update the appointment
     by calling the provided API endpoint. Otherwise, it returns a cancellation message.
     """
    # LLM asks for confirmation
    confirmed = ask_patient_confirmation(request)
    if confirmed:
        while(confirmed):
            print ("Le aplazamos la cita 24 horas")
            confirmed= ask_patient_confirmation(request)


def ask_patient_confirmation(request: AppointmentRequest) -> bool:
    """
    Uses a language model (LLM) to ask the patient if they want to schedule an appointment
    on the given date with the specified urgency.
    Returns True if the patient responds 'Yes', otherwise returns False.
    """
    prompt_text = f"""
    The following appointment is proposed:

    Patient ID: {request.patient_id}
    Desired Date: {request.desired_date}
    Urgency: {request.urgency}

    Would you like to confirm this appointment? Please answer with "Yes" to confirm or "No" to cancel.

    Response:
    """
    response = llm.invoke(prompt_text)

    # Verifica si la respuesta incluye "yes" (ignora mayúsculas/minúsculas)
    if "yes" in response.content.lower():
        return True
    else:
        return False
