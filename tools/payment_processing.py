from dotenv import load_dotenv
import requests
from langchain_core.tools import tool
from pydantic import BaseModel
from llm import llm




class PaymentProcessingRequest(BaseModel):
    patient_id: str
    medication: str
    amount: float
    pharmacy_endpoint: str
    patient_decision: bool

@tool
def payment_processing(request: PaymentProcessingRequest)->dict:
    """
 Ask the patient if they want to purchase the medication.
If the patient says "yes," continue with  the procediment of the payment, if the patient says "no" return false.
"""
    patient_decision = analyze_payment_processing_with_ai(request)
    if not patient_decision:
        return {
            "status": "cancelled",
            "message": "Paciente optó por no proceder con la compra del medicamento."
        }

    # Si el paciente aceptó, procedemos con el procesamiento del pago
    payload = {
        "patient_id": request.patient_id,
        "medication": request.medication,
        "amount": request.amount,
        "payment_method": "PayRetailers"
    }

    headers = {
        'Authorization': 'Bearer YOUR_PAYRETAILERS_API_KEY',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(request.pharmacy_endpoint, json=payload, headers=headers)
        response.raise_for_status()  # Esto asegura que si hay un error en la respuesta, se lanza una excepción.
        return {
            "status": "success",
            "payment_confirmation": response.json()
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": str(e)
        }

def analyze_payment_processing_with_ai(request:PaymentProcessingRequest) -> bool:
    """Analiza si el paciente desea comprar el medicamento recetado."""

    prompt_ai = f"""
    El paciente ha recibido la siguiente receta médica:

    Medicamento: {request.medication}
    Costo: ${request.amount}

    Pregunta al paciente: ¿Desea comprar este medicamento? Responda "Sí" si desea proceder con la compra o "No" si no desea comprarlo.

    Respuesta:
    """
    response = llm.invoke(prompt_ai)

    # Lógica para verificar la respuesta y determinar si la compra se realizó
    if "sí" in response.content.lower():
        return True  # La compra fue realizada
    else:
        return False  # La compra no fue realizada


