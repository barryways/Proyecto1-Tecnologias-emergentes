import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from dotenv import load_dotenv
from routers import auth_router, chat_router

load_dotenv()

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    docs_url="/api/docs",
    title="StudyBot API",
    description="API para autenticacion y chat estudiantil",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="StudyBot API"
    )

app.include_router(auth_router.router)
app.include_router(chat_router.router)
