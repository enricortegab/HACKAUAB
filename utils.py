import json


def extract_from_response(response, field_name):
    """Extracts a specific field from the AI response, returning an empty string or list if not found."""
    try:
        start_marker = f"{field_name}:"
        start_index = response.find(start_marker)

        if start_index == -1:
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
            # Check for direct location data
            if "locations" in content:
                return content["locations"]

            # Check for pharmacy data
            if "pharmacy_info" in content:
                return [content["pharmacy_info"].get("coordinates", {})]

            # Check for hospital data
            if "hospital_info" in content:
                return [content["hospital_info"].get("location", {})]

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
            return {
                "transaction_id": content.get("transaction_id"),
                "amount": content.get("processed_amount"),
                "status": content.get("payment_status"),
                "method": content.get("payment_method"),
                "currency": content.get("currency", "USD")
            }

        return {}
    except Exception:
        return {}
