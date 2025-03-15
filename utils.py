import json
import math


def extract_from_response(response, field_name):
    """Extracts a specific field from the AI response, returning an empty string or list if not found."""
    # Mapeo de campos en inglés a castellano para buscar en la respuesta
    field_mapping = {
        "symptoms": "síntomas",
        "diagnosis": "diagnóstico",
        "recommendations": "recomendaciones"
    }

    # Usar el término en castellano si existe en el mapeo
    search_term = field_mapping.get(field_name, field_name)

    try:
        # Buscar tanto el término en inglés como en castellano
        start_marker_es = f"{search_term}:"
        start_marker_en = f"{field_name}:"

        start_index_es = response.lower().find(start_marker_es.lower())
        start_index_en = response.lower().find(start_marker_en.lower())

        # Usar el que se encuentre (con preferencia por castellano)
        if start_index_es != -1:
            start_index = start_index_es
            start_marker = start_marker_es
        elif start_index_en != -1:
            start_index = start_index_en
            start_marker = start_marker_en
        else:
            # No se encontró ninguna versión
            if field_name in ["symptoms", "recommendations"]:
                return []  # Return empty list for symptoms and recommendations
            else:
                return ""  # Return empty string for other fields

        start_index += len(start_marker)
        end_index = response.find("\n", start_index)
        if end_index == -1:
            end_index = len(response)
        extracted_value = response[start_index:end_index].strip()
        if field_name in ["symptoms", "recommendations"]:
            return [item.strip() for item in extracted_value.split(',')] if extracted_value else []
        return extracted_value
    except Exception:
        if field_name in ["symptoms", "recommendations"]:
            return []  # Return empty list on error for symptoms and recommendations
        return ""


def get_locations(content):
    """
    Extracts location information from the agent's response.
    Handles both direct location data and inferred locations.
    """
    try:
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                return []
        if isinstance(content, dict):
            # Check for direct location data (both English and Spanish terms)
            if "locations" in content:
                return content["locations"]
            if "ubicaciones" in content:
                return content["ubicaciones"]

            # Check for pharmacy data (both English and Spanish terms)
            if "pharmacy_info" in content:
                return [content["pharmacy_info"].get("coordinates", {})]
            if "info_farmacia" in content:
                return [content["info_farmacia"].get("coordenadas", {})]

            # Check for hospital data (both English and Spanish terms)
            if "hospital_info" in content:
                return [content["hospital_info"].get("location", {})]
            if "info_hospital" in content:
                return [content["info_hospital"].get("ubicacion", {})]
        return []
    except Exception:
        return []


def extract_payment_info(content):
    """
    Extracts payment-related information from the agent's response.
    """
    try:
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                return {}
        if isinstance(content, dict):
            # Buscar campos en inglés y castellano
            transaction_id = content.get("transaction_id", content.get("id_transaccion"))
            amount = content.get("processed_amount", content.get("monto_procesado"))
            status = content.get("payment_status", content.get("estado_pago"))
            method = content.get("payment_method", content.get("metodo_pago"))
            currency = content.get("currency", content.get("moneda", "USD"))

            return {
                "transaction_id": transaction_id,
                "amount": amount,
                "status": status,
                "method": method,
                "currency": currency
            }
        return {}
    except Exception:
        return {}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en kilómetros
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferencias de latitud y longitud
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Fórmula Haversine
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distancia en kilómetros
    distance = R * c
    return distance
