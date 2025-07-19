# controllers/analysis_controller.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models.schemas import AnalisisIARequest  # adapta este import a tu estructura
import httpx
import os

router = APIRouter()

# Lee la API key de Gemini (variable de entorno que pusiste en Railway)
GEMINI_KEY      = os.getenv("GEMINI_API_KEY")
# Endpoint público de Gemini para text-bison-001
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"

@router.post("/analizar")
async def analizar_datos(request: AnalisisIARequest):
    if not GEMINI_KEY:
        raise HTTPException(500, detail="Falta configurar GEMINI_API_KEY")

    # Construcción completa del prompt:
    prompt = f"""
Eres un ingeniero agrónomo experto en germinación de cultivos y evaluación ambiental. Tu tarea es analizar las condiciones de un cultivo en función de sus parámetros al término de germinación.

Recibes este reporte del cultivo '{request.semilla}' con los siguientes valores promedio:

 Temperatura: {request.temperatura} °C  
 Humedad ambiental: {request.humedad} %  
 Humedad del suelo: {request.humedad_suelo} % 
 Luz: {request.luz} lux

Descripción del cultivo:
- Ubicación del estante: {request.ubicacion_estante}
- Fecha de inicio de germinación: {request.fechaInicioGerminacion}
- Fecha del reporte: {request.fechaDelReporte}
- Descripción adicional: {request.descripcion}

Tu respuesta debe incluir:

1. "diagnostico": Escribe un **diagnóstico extremadamente detallado y técnico**, de al menos 5 a 10 líneas. Debes analizar cómo cada uno de estos parámetros afecta al desarrollo de la semilla, las interacciones entre ellos, posibles consecuencias agronómicas, y cómo estas condiciones se comparan con lo que sería ideal. Usa vocabulario técnico agrícola, pero que sea entendible para un ingeniero en agronomía.

2. "evaluacion": Evalúa cada parámetro con uno de estos valores:
Adecuada / Moderada / Deficiente

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
""".strip()

    # Cabeceras para Gemini
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_KEY}"
    }

    # Cuerpo de la petición a Gemini
    body = {
        "model": "text-bison-001",
        "prompt": prompt,
        "temperature": 0.2,
        "maxOutputTokens": 512
    }

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(GEMINI_ENDPOINT, json=body, headers=headers)
            resp.raise_for_status()
            response_data = resp.json()
    except httpx.HTTPStatusError as e:
        # Error retornado por Gemini
        raise HTTPException(502, detail=f"Gemini API falló: {e.response.text}")
    except Exception as e:
        raise HTTPException(500, detail=f"Error interno: {str(e)}")

    # Extraer la salida generada
    try:
        texto = response_data["candidates"][0]["output"]
    except (KeyError, IndexError):
        raise HTTPException(502, detail="Respuesta inesperada de Gemini")

    # Intentamos parsear el JSON que nos devolvió el modelo
    import json
    try:
        parsed = json.loads(texto)
        return JSONResponse(content=parsed)
    except json.JSONDecodeError:
        # Si no es JSON válido, lo devolvemos en crudo bajo clave "analisis_modelo"
        return JSONResponse(content={"analisis_modelo": texto})

