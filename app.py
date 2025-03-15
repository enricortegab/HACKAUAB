import base64
import os
import requests

from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from models import MedicalEncounter
from utils import extract_from_response, extract_payment_info, get_locations

# Load environment variables
load_dotenv()

# API Configuration
API_URL = os.environ.get("API_URL")
API_KEY = os.environ.get("API_KEY")

def query_openai(prompt, chat_history=None, tools_context=None):
    """Direct Azure OpenAI API call with context handling"""
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY
    }

    messages = [
        {"role": "system", "content": """You are a compassionate healthcare assistant for rural populations. Guide the conversation to:
1. Conduct complete symptom analysis
2. Request medical images when necessary
3. Provide diagnosis with confidence levels
4. Suggest nearby treatment options
5. Offer payment solutions
6. Maintain multilingual support"""}
    ]

    if chat_history:
        for msg in chat_history:
            messages.append({"role": "user" if msg["role"] == "user" else "assistant", "content": msg["content"]})

    messages.append({"role": "user", "content": prompt})

    payload = {
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"


# Initialize session state
if "medical_history" not in st.session_state:
    st.session_state.medical_history = []
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your rural health assistant. What symptoms are you experiencing?"}
    ]

# Page layout
st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 2])

# Right Column - Chat Interface
with col2:
    st.header("Rural Health Assistant")

    # Image upload
    uploaded_image = st.file_uploader("Upload medical image", type=["jpg", "png"])

    # Display chat messages
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # User input (moved to the bottom)

# Left Column - Visualizations (same as before)
with col1:
    st.sidebar.header("Medical Context")
    tabs = st.sidebar.tabs(["Healthcare Map", "Pharmacy Network", "Case Summary", "Full History"])

    with tabs[0]:
        st.subheader("Healthcare Facilities Map")
        if st.session_state.medical_history:
            latest = st.session_state.medical_history[-1]
            facilities = [loc for loc in latest.get("locations", []) if loc.get("coordinates")]
            if facilities:
                st.map(facilities, latitude="lat", longitude="lng")

    with tabs[1]:
        st.subheader("Medication Availability")
        if st.session_state.medical_history:
            latest = st.session_state.medical_history[-1]
            if "pharmacy_info" in latest:
                st.write("**Available Medications:**")
                for med in latest["pharmacy_info"].get("stock_available", []):
                    st.write(f"- {med}")
                st.write("**Payment Options:**")
                st.write(", ".join(latest["pharmacy_info"].get("payment_options", [])))

    with tabs[2]:
        st.subheader("Current Case Summary")
        if st.session_state.medical_history:
            latest = st.session_state.medical_history[-1]
            st.write(f"**Symptoms:** {', '.join(latest.get('symptoms', []))}")
            st.write(f"**Preliminary Diagnosis:** {latest.get('diagnosis', 'Pending')}")
            st.write(f"**Urgency Level:** {latest.get('urgency', 'Medium')}")

    with tabs[3]:
        st.subheader("Medical History")
        for idx, record in enumerate(st.session_state.medical_history):
            with st.expander(f"Case {idx + 1} - {record.get('diagnosis', 'Unknown')}"):
                st.json(record)

# User input (fixed at the bottom)
with col2:
    user_input = st.chat_input("Describe your symptoms or ask a question...")

    if user_input or uploaded_image:
        if uploaded_image:
            # Process image
            image_data = base64.b64encode(uploaded_image.read()).decode("utf-8")
            st.session_state.messages.append({"role": "user", "content": "Medical image uploaded"})
            st.chat_message("user").write("Medical image uploaded")

            # Analyze image
            try:
                prompt = f"Analyze this medical image: {uploaded_image.type}"
                content = query_openai(prompt, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": content})
                st.chat_message("assistant").write(content)
            except Exception as e:
                st.error(f"Image analysis error: {str(e)}")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.chat_message("user").write(user_input)

            try:
                # Get AI response
                content = query_openai(user_input, st.session_state.messages)

                # Process and store medical data
                try:
                    diagnosis = extract_from_response(content, "diagnosis")
                    encounter_data = {
                        "symptoms": extract_from_response(content, "symptoms"),
                        "diagnosis": diagnosis,
                        "recommendations": extract_from_response(content, "recommendations"),
                        "locations": get_locations(content),
                        "timestamp": datetime.now().isoformat(),
                        "payment_info": extract_payment_info(content)
                    }
                    encounter = MedicalEncounter(**encounter_data)
                    st.session_state.medical_history.append(encounter.dict())
                except Exception as e:
                    st.error(f"Data saving error: {str(e)}")

                # Display response
                st.session_state.messages.append({"role": "assistant", "content": content})
                st.chat_message("assistant").write(content)

            except Exception as e:
                st.error(f"Processing error: {str(e)}")
