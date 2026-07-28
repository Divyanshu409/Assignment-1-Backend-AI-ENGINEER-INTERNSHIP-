from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small in-memory to-do list API built for FlyRank Internship Week 2, Assignment A1.",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.get("/", summary="API info", description="Returns basic metadata about this API.")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Health check", description="Returns ok if the server is alive.")
def health():
    return {"status": "ok"}
