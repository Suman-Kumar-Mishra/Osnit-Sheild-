from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.intelligence import router as intelligence_router
from backend.routes.incidents import router as incidents_router
from backend.routes.operations import router as operations_router

app = FastAPI(title="Osnit Shield API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intelligence_router)
app.include_router(incidents_router)
app.include_router(operations_router)

@app.get("/")
def root():
    return {"status": "Osnit Shield API is running"}