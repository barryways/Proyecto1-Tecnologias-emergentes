import logging
from fastapi import FastAPI
from dotenv import load_dotenv
from routers import chat_router
from contextlib import asynccontextmanager
from scalar_fastapi import get_scalar_api_reference
from dependencies import get_collection_tutor_advanced_programming

load_dotenv()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_collection_tutor_advanced_programming()
    logger.info("✅ Server started")
    yield
    logger.info("🛑 Cerrando aplicación...")

app = FastAPI(
    lifespan=lifespan,
    docs_url="/api/docs",
    title="Chat API",
    description="API con Claude",
    version="0.0.1"
)

@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="Chat con Claude"
    )

app.include_router(chat_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)