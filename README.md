#### Hector Alvarez
#### Eloi Mercader
#### Enric Ortega
#### Natan Sisoev


# Proyecto: AI Agent para Telemedicina Preventiva en Zonas Rurales.

## Descripción del Problema
Uno de los desafíos más importantes en Latinoamérica es el limitado acceso a recursos médicos en zonas rurales y subdesarrolladas, lo que afecta la calidad y rapidez en la atención médica. Las largas distancias, la falta de infraestructura y la escasez de personal médico dificultan que los pacientes reciban una atención adecuada y oportuna.

##  Funcionalidades Principales


### 1. Diagnóstico Virtual Autónomo
Interacción con pacientes mediante preguntas para recopilar información sobre su estado de salud.

Análisis automático de síntomas utilizando un modelo de lenguaje avanzado.

Generación de un prediagnóstico que se remite al personal médico para su validación.

### 2. Comunicación Directa con Centros Médicos
Enío automático y seguro del prediagnóstico al centro médico correspondiente.

Recepción del prospecto médico redactado por el doctor y entrega clara de las indicaciones al paciente.

### 3. Gestión Médica y Seguimiento
Validación final del diagnóstico por parte de un profesional médico.

Envio de instrucciones detalladas al paciente y seguimiento de su estado de salud.
### 4. Gestión y Compra de Medicamentos
Recomendación de medicamentos basada en el diagnóstico.

Compra directa a través de la integración con PayRetailers.


Opciones de pago adaptadas a las necesidades de cada región.
### 5. Gestión de citas médicas
Programación de citas médicas automática en función del diagnóstico.

Posibilidad de reprogramar la cita según la disponibilidad del paciente.

Confirmación interactiva mediante el agente conversacional.
##  Tecnologías Utilizadas
NLP (Procesamiento del Lenguaje Natural) para la comprensión y generación de texto.

API de PayRetailers para gestión de pagos seguros y compra de medicamentos.

Integraciones Seguras para la transmisión de datos médicos confidenciales.

Streamlit para la carga y transmisión de imágenes médicas al doctor.

## Fases de Implementación

### Fase 1: Investigación y recopilación de datos
Obtención de datos médicos relevantes para las patologías más comunes en zonas rurales.

Etiquetado y curación de los datos para entrenar el modelo de diagnóstico.
### Fase 2: Desarrollo del diagnóstico autónomo
Implementación de algoritmos de análisis de síntomas y modelos de lenguaje.

Evaluación y ajuste del rendimiento del modelo.

### Fase 3: Desarrollo del agente conversacional
Creación del chatbot interactivo para comunicación con los pacientes.

Optimización del flujo de conversación y la comprensión del lenguaje.

### Fase 4: Integración con centros médicos
Diseño de un sistema seguro para la transferencia de información médica.

Validación de la compatibilidad con los protocolos médicos existentes.

### Fase 5: Integración financiera con PayRetailers
Desarrollo de las funciones de pago automático y gestión de medicamentos.

Pruebas de seguridad y cumplimiento de normativas financieras.

## Uso

1. Clonar el repositorio:
```bash
git clone https://github.com/enricortegab/HACKAUAB.git
```
2. Entrar a la carpeta:
```bash
cd ./HACKAUAB
```
3. Crear virtual environment:
```bash
py -m venv .venv
```
4. Activar virtual environment (depende del sistema):
```bash
.venv\Scripts\activate
```
5. Instalar requerimientos:
```bash
pip install -r ./requirements.txt
```
6. Lanzar la página:
```bash
streamlit run ./app.py
```

## Distribución de Tareas

### Participante 1: Desarrollo del Agente Conversacional
Implementación del modelo de lenguaje (NLP) y optimización de interacción.

Diseño de la interfaz del chatbot y experiencia de usuario (UX/UI).

### Participante 2: Integración de diferentes tools
Diseño de diferentes herramientas para que sean reconocidas por nuestro AI agent


### Participante 3: Integración segura con centros médicos
Desarrollo de la plataforma segura para el manejo de datos sensibles.

Implementación de protocolos de seguridad y cifrado de datos.

### Participante 4: Integración con PayRetailers
Implementación de pagos automatizados y validación de transacciones.

Gestión del flujo de compra de medicamentos y confirmaciones de pago.

## Beneficio para PayRetailers
Expansión a Nuevos Mercados: Ingreso a zonas rurales con demanda insatisfecha.

Aumento de Clientes: Captación de nuevos usuarios mediante soluciones de salud.

Innovación en Financiación Médica: Adaptación de métodos de pago a las necesidades regionales.

