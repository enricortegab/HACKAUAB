from llm import llm
from langchain.tools import Tool

def diagnose_and_prescribe(symptoms: str, observations: str = ""):
    """
    This function takes symptoms and additional observations,
    then returns a suggested medication and a response from the LLM "doctor".
    """
    prompt = f"""
    You have two functions: suggest medications or help the user buy them directly.
    
    
    
    Given the symptoms and observations, recommended medications, and any necessary actions. Mention that this was first approved by the doctor.
    If the user wants to directly buy the medication, just send them the suggestion with that medication so the user can buy them.
    
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
