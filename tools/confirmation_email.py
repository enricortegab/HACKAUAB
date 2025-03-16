from langchain.tools import tool
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from llm import llm


@tool()
def send_appointment_confirmation(email: str) -> str:
    """
    Sends an email (ask the user for their email and availability) to the user with the appointment confirmation.
    Do it when the user asks for an appointment.
    """
    prompt = f"""
       You are an AI specialized in scheduling medical appointments for patients. 
       Show a copy of the email you've sent following an email instruction and having into account 
       the previous information of the conversation. 
       Follow this structure and show it in the interface: 

    Tu cita médica ha sido confirmada exitosamente.

    Fecha y hora: fecha_inventada
    Médico asignado: medico_inventado

    Gracias por confiar en nuestro servicio de salud.

    Atentamente,
    Equipo Médico Rural

    Finally say you have sent the email to {email}
    """
    response = llm.invoke(prompt).content  # <-- Corrección aquí

    # SMTP configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    # Prepare email
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = email
    message['Subject'] = "Confirmación de cita médica"

    # Email body
    message.attach(MIMEText(response, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        return response
    except Exception as e:
        return f"Error al enviar el email: {str(e)}"
