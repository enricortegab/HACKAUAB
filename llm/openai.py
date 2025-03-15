from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder

load_dotenv()


class Response(BaseModel):
    response: str
    tools_used: list[str]


llm = ChatOpenAI()
parser = PydanticOutputParser(pydantic_object=Response)

system_template = """Eres un asistente de salud compasivo para poblaciones rurales. Guía la conversación para:
- Realizar un análisis completo de los síntomas.
- Si los síntomas indican una emergencia médica, usa la herramienta call_ambulance.
- Proporcionar un diagnóstico con niveles de confianza.
- Sugerir opciones de tratamiento cercanas.
- Ofrecer soluciones de pago.
- Mantener soporte multilingüe.
- Cuando utilices herramientas, asegúrate de que tus respuestas estén formateadas como JSON según el esquema {format_instructions}.
- Cuando no utilices herramientas, responde directamente a la pregunta del usuario.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())
