import pandas as pd
from langchain.tools import tool
from pydantic import BaseModel, Field
import requests
import os
from llm import llm

class PerplexityMedicalTool:
    api_key: str = os.environ.get("PERPLEXITY_API")
    url: str = os.environ.get("PERPLEXITY_URL")

def resum_conversa(prompt, model=llm):
    return model.invoke(prompt)

@tool
def obtener_info_medica(conversacion: PerplexityMedicalTool) -> str:
        """"Use it when you notice the user is nervous to understand what’s wrong or when they are willing to go to the doctor.""""
        prompt=f"""
        Summarize our entire conversation so far, including information 
                about my health condition, so that Perplexity artificial intelligence 
                can find the most relevant articles."""
        resum= resum_conversa(prompt)
        headers = {
            "Authorization": f"Bearer {conversacion.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "pplx-70b-online",
            "messages": [
                {"role": "system", "content": "Eres un asistente experto en búsqueda y recomendaciones médicas basadas en evidencia científica."},
                {"role": "user", "content": conversacion}
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }

        response = requests.post(conversacion.url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error al consultar la API: {response.status_code} {response.text}"

