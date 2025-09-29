from fastapi import FastAPI
from .database import create_tables
from .routes import face_api

app = FastAPI(title="API de reconnaissance faciale")

@app.on_event("startup")
def on_startup():
    create_tables()

app.include_router(face_api.router)

@app.get("/")
def read_root():
    return {"message": "API de reconnaissance faciale opérationnelle"}