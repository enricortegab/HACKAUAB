from langchain_core.tools import tool

from llm import llm

@tool
def assess_situation(symptoms: str) -> str:
    """Depending on the case, calls an ambulance if it is an emergency, change the visit date if it is a difficult situation but not an emergency situation and don't change anything if it is a safety situation like using AI analysis."""
    """Analyzes symptoms using the LLM and returns 4 if a medical emergency is critical, 3 if it is a difficult situation and 1 or 2 if it is a safety situation."""

    if analyze_symptoms_with_ai(llm, symptoms)==4:
        return "Ambulance dispatched."
    elif analyze_symptoms_with_ai(llm, symptoms)==3:
        return "Le hemos adelantado su visita para de aqui 24 horas"
    else:
        return "Symptoms do not indicate an immediate emergency."


def analyze_symptoms_with_ai(llm, symptoms: str) -> int:
    """Analyzes symptoms using the LLM and returns 3 if a medical emergency is likely, 2 if it is a difficult situation and 1 if it is a safety situation."""

    prompt_ai = f"""
    Analiza los siguientes síntomas y determina si indican una emergencia médica urgente.
    Responde "emergencia" si es una emergencia como un ataque cardíaco o un derrame cerebral, 
    "grave" si no llega a emergencia pero debería tener una visita en cuanto antes (complicación de resfriado),
    responde "leve" si es un simple resfriado y "sano" si hay una evidencia muy clara de que el estado 
    del paciente es correcto

    Síntomas: {symptoms}

    Respuesta:
    """

    response = llm.invoke(prompt_ai)

    if "emergencia" in response.content.lower():
        return 4
    elif "grave" in response.content.lower():
        return 3
    elif "leve":
        return 2
    else:
        return 1
