from langchain_core.tools import tool

from llm import llm

# TODO: differentiate cases (importance or urgency -> ambulance/visit/call/...)


@tool
def call_ambulance(symptoms: str) -> str:
    """Calls an ambulance based on the user's symptoms, using AI analysis."""

    if analyze_symptoms_with_ai(llm, symptoms)==3:
        return "Ambulance dispatched."
    elif analyze_symptoms_with_ai(llm, symptoms)==2:
        return "Le hemos adelantado su visita para de aqui 24 horas"
    else:
        return "Symptoms do not indicate an immediate emergency."


def analyze_symptoms_with_ai(llm, symptoms: str) -> int:
    """Analyzes symptoms using the LLM and returns 3 if a medical emergency is likely, 2 if it is a difficult situation and 1 if it is a safety situation."""

    prompt_ai = f"""
    Analiza los siguientes síntomas y determina si indican una emergencia médica urgente, como un ataque cardíaco o un derrame cerebral. Responde "Sí" si es una emergencia, "Cuidado" si no llega a emergencia pero no es seguro  y "No" si no lo es.

    Síntomas: {symptoms}

    Respuesta:
    """

    response = llm.invoke(prompt_ai)

    if "Sí" in response.content.lower():
        return 3
    elif "Cuidado" in response.content.lower():
        return 2
    else:
        return 1