from llm import llm
from langchain.tools import Tool

def diagnose_and_prescribe(symptoms: str, observations: str = ""):
    """
    This function takes symptoms and additional observations,
    then returns a suggested medication and a response from the LLM "doctor".
    """
    prompt = f"""
    You are an AI acting as a rural health assistant. Given the symptoms and observations,
    suggest a possible diagnosis, recommended medications, and any necessary actions.

    Symptoms: {symptoms}
    Observations: {observations}
    """
    response = llm.invoke(prompt)
    return response

medical_diagnosis_tool = Tool(
    name="Medical_Diagnosis_Tool",
    func=diagnose_and_prescribe,
    description="Takes symptoms and observations, returns medication suggestions and doctor response."
)
