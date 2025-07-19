from fastapi import APIRouter, HTTPException
from models.schemas import AnalisisIARequest
import httpx
import os
import re
import json5 as json

router = APIRouter()

# Endpoint de la Generative Language API (Gemini / Text-Bison)
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"

@router.post("/analizar")
async def analizar_datos(data: AnalisisIARequest):
    """
    Recibe los datos del reporte, construye un prompt agronómico,
    lo envía a la API de Gemini (Text-Bison) y devuelve el JSON parseado.
    """
    # 1. Construir el prompt con todos los detalles
    prompt = f"""
Eres un ingeniero agrónomo experto en germinación de cultivos y evaluación ambiental.
Recibe un reporte con los siguientes datos promedio para el cultivo '{data.semilla}':
- Temperatura (°C): {data.temperatura}
- Humedad ambiental (%): {data.humedad}
- Humedad del suelo (%): {data.humedad_suelo}
- Luz (lux): {data.luz}
Información adicional:
- Ubicación del estante: {data.ubicacion_estante}
- Fecha de inicio de germinación: {data.fechaInicioGerminacion}
- Fecha del reporte: {data.fechaDelReporte}
- Descripción adicional: {data.descripcion}
Instrucciones:
Devuelve únicamente un objeto JSON válido con esta estructura exacta (sin ningún texto antes o después):
{
  "diagnostico": "<análisis técnico detallado, 5-10 líneas>",
  "evaluacion": {
    "temperatura": "Adecuada|Moderada|Deficiente",
    "humedad": "Adecuada|Moderada|Deficiente",
    "humedad_suelo": "Adecuada|Moderada|Deficiente",
    "luz": "Adecuada|Moderada|Deficiente"
  },
  "causas": ["<explicación1>", "<explicación2>", ...],
  "recomendaciones": ["<acción1>", "<acción2>", ...]
}
Si no puedes procesar el reporte, responde exactamente:
{ "error": "No se pudo procesar" }
"""

    # 2. Leer la API Key del entorno
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta variable de entorno GEMINI_API_KEY")

    # 3. Preparar la petición HTTP a Gemini
    body = {
        "prompt": {"text": prompt},
        "temperature": 0.1,
        "maxOutputTokens": 512
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 4. Llamar a la API de Gemini
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(GEMINI_ENDPOINT, json=body, headers=headers)
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Gemini API falló: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Extraer y parsear el JSON literal
    try:
        text = result["candidates"][0]["output"].strip()
    except Exception:
        raise HTTPException(status_code=500, detail="Respuesta de Gemini en formato inesperado")
    pattern = r"\{(?:.|)*?\}"  # regex en una sola línea para capturar JSON
    match = re.search(pattern, text)
    if not match:
        raise HTTPException(status_code=500, detail="No se encontró JSON en la respuesta de Gemini")
    try:
        parsed = json.loads(match.group())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parseando JSON: {e}")

    # 6. Devolver resultado
    return parsed
