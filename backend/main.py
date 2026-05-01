import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers import analyze, export

app = FastAPI(title="BuyWise API", version="1.0.0")

cors_origins = os.getenv("CORS_ORIGIN", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "BuyWise API is running"}
