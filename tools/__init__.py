
from .diagnosis_delivery import diagnosis_delivery
from .payment_processing import payment_processing
from .critical_situation import call_ambulance
from .pharmacy_locator import pharmacy_locator
from .articlesrecommend import obtener_info_medica


tools = [
    obtener_info_medica,
    call_ambulance,
    diagnosis_delivery,
    payment_processing,
    pharmacy_locator
]




