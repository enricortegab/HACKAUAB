from langchain.tools import tool
from pydantic import BaseModel, Field
import random

FAKE_PHARMACIES = [
    {
        "name": "Farmacia Salud Rural",
        "coordinates": {"lat": -12.3456, "lng": -76.7890},
        "stock_available": ["paracetamol", "amoxicillin", "ibuprofen"],
        "payment_options": ["cash", "mobile_money"],
        "distance": round(random.uniform(1, 5), 1)
    },
    {
        "name": "Farmacia CentroMed",
        "coordinates": {"lat": -12.4567, "lng": -76.6789},
        "stock_available": ["azithromycin", "loratadine", "omeprazole"],
        "payment_options": ["card", "cash"],
        "distance": round(random.uniform(2, 6), 1)
    },
    {
        "name": "Botica Esperanza",
        "coordinates": {"lat": -12.5678, "lng": -76.5678},
        "stock_available": ["paracetamol", "ibuprofen", "diphenhydramine"],
        "payment_options": ["cash", "bank_transfer"],
        "distance": round(random.uniform(3, 7), 1)
    },
    {
        "name": "Droguería Vida Sana",
        "coordinates": {"lat": -12.6789, "lng": -76.4567},
        "stock_available": ["metformin", "insulin", "atorvastatin"],
        "payment_options": ["mobile_money", "insurance"],
        "distance": round(random.uniform(4, 8), 1)
    }
]


class PharmacyRequest(BaseModel):
    """
    Represents a request to locate pharmacies, including patient location and required medications.
    """
    patient_location: str
    medication_list: list[str]

def fake_pharmacy_api(request: PharmacyRequest):
    """
    Simulates a pharmacy API by returning the closest pharmacy that has at least one of the required medications.
    """
    try:
        available_pharmacies = [
            pharmacy for pharmacy in FAKE_PHARMACIES
            if any(med in pharmacy["stock_available"] for med in request.medication_list)
        ]
        available_pharmacies.sort(key=lambda p: p["distance"])
        if available_pharmacies:
            return {
                "nearest_pharmacy": available_pharmacies[0],
                "message": f"Farmacia más cercana: {available_pharmacies[0]['name']} ({available_pharmacies[0]['distance']} km)."
            }
        else:
            return {"error": "No se encontraron farmacias cercanas."}
    except Exception as e:
        return {"error": str(e)}

@tool
def pharmacy_locator(request: PharmacyRequest) -> str:
    """Use this tool to locate nearby pharmacies."""
    result = fake_pharmacy_api(request)
    if "nearest_pharmacy" in result:
        pharmacy = result["nearest_pharmacy"]
        return f"Farmacia más cercana encontrada: {pharmacy['name']} a {pharmacy['distance']} km."
    else:
        return result["error"]