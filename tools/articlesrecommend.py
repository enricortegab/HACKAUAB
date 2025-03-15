import os
from langchain.tools import tool
from pydantic import BaseModel, Field
import requests
from llm import llm

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API")
PERPLEXITY_API_URL = os.getenv("PERPLEXITY_URL")


class MedicalQuery(BaseModel):
    conversation: str = Field(..., description="The medical conversation to analyze")


def summarize_conversation(conversation: str) -> str:
    """Summarize medical conversation for API query"""
    prompt = f"""
    Summarize the following patient conversation, focusing on:
    - Main symptoms and their duration
    - Existing medical conditions
    - Medications mentioned
    - Specific health concerns
    - Any other relevant medical information

    Conversation:
    {conversation}

    Provide a concise summary suitable for medical research lookup.
    """
    return llm.invoke(prompt)


@tool(args_schema=MedicalQuery)
def obtener_info_medica(conversation: str) -> str:
    """
    Analyzes medical conversations using Perplexity API to provide:
    - Possible conditions
    - Recommended medications
    - Scientific insights
    - When to see a doctor
    Use when user shows health concerns or needs medical guidance.
    """
    try:
        # Step 1: Create focused medical summary
        summary = summarize_conversation(conversation)

        # Step 2: Prepare Perplexity API request
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "pplx-70b-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a medical research assistant. Analyze the patient summary and provide: "
                               "1. Potential diagnoses based on symptoms\n"
                               "2. Recommended OTC medications\n"
                               "3. When to seek professional care\n"
                               "4. Relevant scientific findings\n"
                               "Format clearly with markdown headings."
                },
                {
                    "role": "user",
                    "content": f"Patient summary:\n{summary}"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }

        # Step 3: Make API call
        response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers)
        response.raise_for_status()

        # Step 4: Process response
        result = response.json()
        print("##=>", result["choices"][0]["message"]["content"])
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Error obtaining medical information: {str(e)}"
