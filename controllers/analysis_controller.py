from fastapi import APIRouter, HTTPException
from models.schemas import AnalisisIARequest, AnalisisIAResponse
import os, httpx, re, json, tempfile

router = APIRouter()

# ---------- CREDENCIALES DE SERVICIO (VERTEX AI) ----------
# Espera que subas el JSON de tu service account a la variable de entorno GOOGLE_APPLICATION_CREDENTIALS_JSON
creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_json:
    # Crea un archivo temporal para Google SDK
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as f:
        f.write(creds_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name

# ---------- ENDPOINT VERTEX AI ----------
# Debes usar el endpoint VERTEX AI moderno (NO el de v1beta2, ni API KEY)
# Ejemplo: "https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/publishers/google/models/text-bison:predict"
GEMINI_ENDPOINT = os.getenv("GEMINI_ENDPOINT")

@router.post("/analizar", response_model=AnalisisIAResponse)
async def analizar_datos(data: AnalisisIARequest):
    # ------------- Prompt -------------
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

    # ------------- Construcción del request a Vertex AI -------------
    # Documentación: https://cloud.google.com/vertex-ai/docs/generative-ai/start/quickstarts/quickstart-multimodal
    url = GEMINI_ENDPOINT
    headers = {"Authorization": f"Bearer {get_google_access_token()}", "Content-Type": "application/json"}

    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "temperature": 0.2,
            "maxOutputTokens": 512
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Error de Gemini (status {response.status_code}): {response.text}"
            )

        # Respuesta Vertex AI (puede variar por modelo, ajusta si la key cambia)
        result = response.json()
        raw = result["predictions"][0]["content"] if "predictions" in result else ""
        match = re.search(r"\{(?:.|\n)*\}", raw)
        if not match:
            raise HTTPException(502, "No se encontró JSON en la respuesta de Gemini/Vertex")

        return json.loads(match.group())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"No se pudo procesar el análisis: {e}")

# --------- FUNCION AUXILIAR: Obtener el token OAuth2 ---------
def get_google_access_token():
    """Obtiene el access_token del service account cargado por GOOGLE_APPLICATION_CREDENTIALS."""
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(Request())
    return creds.token
