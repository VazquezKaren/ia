from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from controllers.analysis_controller import router as analysis_router

app = FastAPI(title="IA Service")
app.include_router(analysis_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html><body style="text-align:center;font-family:sans-serif">
      <h1>🌱 IA Service OK</h1>
      <p>POST /api/analizar → diagnóstico JSON</p>
    </body></html>
    """
