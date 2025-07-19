from pydantic import BaseModel

class AnalisisIARequest(BaseModel):
    semilla: str
    fechaInicioGerminacion: str
    fechaDelReporte: str
    ubicacion_estante: str
    descripcion: str
    temperatura: float
    humedad: float
    luz: float
    humedad_suelo: float
