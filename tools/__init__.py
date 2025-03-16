from .articlesrecommend import obtener_info_medica
from .critical_situation import assess_situation
from .medication import medical_diagnosis_tool
from .payment_processing import payment_processing
from .pharmacy_locator import pharmacy_locator_tool
from .enviarmail import send_appointment_confirmation
from .diagnosis_delivery import expert_diagnosis
from .Date import schedule_appointment
tools = [
    # obtener_info_medica,
    assess_situation,
    payment_processing,
    pharmacy_locator_tool,
    medical_diagnosis_tool,
    send_appointment_confirmation,
    expert_diagnosis,
    schedule_appointment
]
