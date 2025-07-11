# 🧠 Multi-Service NLP Platform

Este proyecto es una arquitectura basada en microservicios para tareas de procesamiento de lenguaje natural (NLP), como generación de preguntas, resumen de textos, traducción, y lectura de documentos (PDF, DOCX, PPTX). El objetivo es proveer una plataforma extensible y escalable para aplicaciones educativas, análisis de texto y generación automática de evaluaciones.

---

## 🎯 Pilares

- Separar responsabilidades por servicio (mejor mantenibilidad).
- Preparar la arquitectura para escalamiento horizontal (balanceo de carga futuro).
- Facilitar el desarrollo de nuevas funciones (añadir un nuevo modelo = nuevo microservicio).
- Orquestar modelos que funcionan mejor en inglés, aunque el frontend esté en español (incluye traducción automática).
- Acceder a modelos pesados (como Flan-T5) sin acoplarlos al frontend ni al gateway directamente.

---

## 🏗️ Arquitectura

````text
Cada servicio expone su propio endpoint HTTP.
El Model Router coordina llamados en cadena (como extraer texto, traducirlo y luego generar preguntas).
Esto permite desacoplar la lógica de negocio y mantener cada servicio aislado.

### 🧪 Tecnologías

Python 3.10+

FastAPI para todos los endpoints

<VIENDO> para comunicación entre servicios

Transformers (Hugging Face) para todos los modelos

<VIENDO> para lectura de archivos

Docker + Docker Compose para contenerización y orquestación

### 🗂️ Estructura de archivos

```bash
project/
│
├── docker-compose.yml            # Orquesta todos los servicios
├── frontend/                     # (opcional) Webapp
│
├── gateway/                      # API pública (Frontend → Backend)
│   ├── app.py
│   └── requirements.txt
│
├── model_router/                 # Lógica de orquestación (Router interno)
│   ├── app.py
│   └── requirements.txt
│
├── services/                     # Microservicios independientes
│   ├── question_service/         # Generación de preguntas y respuestas
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── summarizer_service/
│   ├── translator_service/
│   ├── document_service/
│   └── ...
│
└── shared/                       # Funciones comunes opcionales (schemas, logging)
````
