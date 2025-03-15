import base64
from datetime import datetime
import streamlit as st
from llm.openai import OpenAIClient
from models import MedicalEncounter
from utils import extract_from_response, extract_payment_info, get_locations

# Initialize OpenAI client
client = OpenAIClient()

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

# Left Column - Visualizations (unchanged)
with col1:
    st.sidebar.header("Medical Context")
    tabs = st.sidebar.tabs(["Healthcare Map", "Pharmacy Network", "Case Summary", "Full History"])

    # ... (keep existing visualization code)

# User input handling
with col2:
    user_input = st.chat_input("Describe your symptoms or ask a question...")

    if user_input or uploaded_image:
        if uploaded_image:
            # Process image
            image_data = base64.b64encode(uploaded_image.read()).decode("utf-8")
            st.session_state.messages.append({"role": "user", "content": "Medical image uploaded"})
            st.chat_message("user").write("Medical image uploaded")

            try:
                content = client.analyze_image(uploaded_image.type, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": content})
                st.chat_message("assistant").write(content)
            except Exception as e:
                st.error(f"Image analysis error: {str(e)}")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.chat_message("user").write(user_input)

            try:
                # Get AI response
                content = client.send_request(user_input, st.session_state.messages)

                # Process and store medical data
                try:
                    encounter_data = {
                        "symptoms": extract_from_response(content, "symptoms"),
                        "diagnosis": extract_from_response(content, "diagnosis"),
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