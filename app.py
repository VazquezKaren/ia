from fastapi import FastAPI
from controllers.analysis_controller import router as analysis_router

app = FastAPI(title="IA Service")

# Incluimos el router en /api
app.include_router(analysis_router, prefix="/api")

# Ruta raíz para salud
@app.get("/")
async def root():
    return {"message": "IA Service OK"}
