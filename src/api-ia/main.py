from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from config import CORS_ORIGINS
from database import init_database
from routers import auth_router, chat_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield

app = FastAPI(
    docs_url="/api/docs",
    title="StudyBot API",
    description="API para autenticacion y chat estudiantil",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
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
