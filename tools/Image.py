from dotenv import load_dotenv
import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Any, Dict
from llm import llm

load_dotenv()  # Load environment variables


class ImageDeliveryRequest(BaseModel):
    patient_id: str
    doctor_endpoint: str
    image_filename: Any


@tool
def deliver_medical_image(request: ImageDeliveryRequest) -> Dict:
    """
    This tool is used to send a medical image directly to the doctor.

    It first asks the patient, via a language model prompt, if they want to send the image.
    If the patient responds "Yes", the tool proceeds to send the image (in jpg format) to the specified
    doctor's API endpoint, including the patient's ID for reference.
    If the patient responds "No", it returns a cancellation message.
    """
    # Ask for confirmation using the LLM
    confirmed = analyze_image_delivery_with_ai(request)
    if not confirmed:
        return {
            "status": "cancelled",
            "message": "Patient opted not to send the medical image."
        }

    try:
        # Use the uploaded file directly (Streamlit returns a file-like object)
        filename = getattr(request.image_file, "name", "uploaded_image.jpg")
        files = {"image": (filename, request.image_file, "image/jpeg")}
        payload = {"patient_id": request.patient_id}
        headers = {"Authorization": "Bearer YOUR_DOCTOR_API_KEY"}
        response = requests.post(request.doctor_endpoint, data=payload, files=files, headers=headers)
        response.raise_for_status()
        return {
            "status": "success",
            "message": "Image delivered successfully.",
            "response": response.json()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def analyze_image_delivery_with_ai(request: ImageDeliveryRequest) -> bool:
    """
    Uses a language model (LLM) to ask the patient if they want to send the medical image.
    If the patient responds "Yes", returns True. If the patient responds "No", returns False.
    """
    prompt_text = f"""
    You are about to send a medical image to your doctor.
    Patient ID: {request.patient_id}

    Do you want to proceed with sending the image? Please answer "yes" to confirm, or "No" to cancel.

    Response:
    """
    response = llm.invoke(prompt_text)

    # Check if the response includes "yes" (ignoring case)
    if "yes" in response.content.lower():
        return True
    else:
        return False
