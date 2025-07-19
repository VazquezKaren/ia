from pydantic import BaseModel

class AnalisisIARequest(BaseModel):
    semilla: str
    fechaInicioGerminacion: str
    fechaDelReporte: str
    ubicacion_estante: str
    descripcion: str
    temperatura: float
    humedad: float
    humedad_suelo: float
    luz: float

class AnalisisIAResponse(BaseModel):
    diagnostico: str
    evaluacion: dict
    causas: list[str]
    recomendaciones: list[str]
