from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from dotenv import load_dotenv
from routers import chat_router

load_dotenv()

app = FastAPI(
    docs_url="/api/docs",
    title="Chat API",
    description="API con Claude",
    version="0.0.1"
)

@app.get("/", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title="Chat con Claude"
    )

app.include_router(chat_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)