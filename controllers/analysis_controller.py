from fastapi import APIRouter, HTTPException
from models.schemas import AnalisisIARequest, AnalisisIAResponse
import os, httpx, re

router = APIRouter()

# Debes llevar en tu .env:
# GEMINI_ENDPOINT=https://us-central1-generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText
# GEMINI_API_KEY=tu_api_key_de_Google
GEMINI_ENDPOINT = os.getenv("GEMINI_ENDPOINT")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")

@router.post("/analizar", response_model=AnalisisIAResponse)
async def analizar_datos(data: AnalisisIARequest):
    # Aquí defines el prompt completo que enviarás a Gemini
    prompt = f"""
Eres un ingeniero agrónomo experto en germinación de cultivos y evaluación ambiental. Tu tarea es analizar las condiciones de un cultivo en función de sus parámetros al término de germinación.

Recibes este reporte del cultivo '{data.semilla}' con los siguientes valores promedio:

 Temperatura: {data.temperatura} °C  
 Humedad ambiental: {data.humedad} %  
 Humedad del suelo: {data.humedad_suelo} %  
 Luz: {data.luz} lux

Descripción del cultivo:
- Ubicación del estante: {data.ubicacion_estante}
- Fecha de inicio de germinación: {data.fechaInicioGerminacion}
- Fecha del reporte: {data.fechaDelReporte}
- Descripción adicional: {data.descripcion}

Tu respuesta debe incluir:

1. "diagnostico": Escribe un **diagnóstico extremadamente detallado y técnico**, de al menos 5 a 10 líneas. Debes analizar cómo cada uno de estos parámetros afecta al desarrollo de la semilla, las interacciones entre ellos, posibles consecuencias agronómicas, y cómo estas condiciones se comparan con lo que sería ideal.

2. "evaluacion": Evalúa cada parámetro con uno de estos valores: Adecuada / Moderada / Deficiente

3. "causas": Lista técnica con explicaciones del porqué esos parámetros están mal, cómo afectan al cultivo, y qué los pudo provocar.

4. "recomendaciones": Lista de acciones reales que se pueden implementar para mejorar el cultivo. No repitas ideas, sé específico y técnico.

IMPORTANTE:
- Devuelve solo el JSON, sin ningún texto antes ni después.
- Si no puedes responder, devuelve: {{ "error": "No se pudo procesar" }}

Formato exacto del JSON:

{{
  "diagnostico": "Análisis muy detallado aquí...",
  "evaluacion": {{
    "temperatura": "...",
    "humedad": "...",
    "humedad_suelo": "...",
    "luz": "..."
  }},
  "causas": ["..."],
  "recomendaciones": ["..."]
}}
"""

    # Construye la URL con tu key
    url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers=headers,
                json={
                  "model": "text-bison-001",
                  "prompt": { "text": prompt },
                  "temperature": 0.2,
                  "max_output_tokens": 512
                }
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Error de Gemini (status {response.status_code}): {response.text}"
            )

        # La respuesta de Gemini viene en data["candidates"][0]["output"]
        data_model = response.json()
        raw = data_model["candidates"][0]["output"]
        match = re.search(r"\{(?:.|\n)*\}", raw)
        if not match:
            raise HTTPException(502, "No se encontró JSON en la respuesta de Gemini")

        return httpx._models.json.loads(match.group())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"No se pudo procesar el análisis: {e}")
