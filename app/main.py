from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.rag.ingest import ingest_pdf
from app.rag.llm import generate_answer
from app.rag.vector_store import ChromaStore

app = FastAPI(
    title="Paper Research Agent",
    version="0.1.0",
    description="A local-first RAG assistant for research papers.",
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    n_results: int = Field(default=3, ge=1, le=20)


class AskRequest(SearchRequest):
    pass


PAPERS_DIR = Path(__file__).resolve().parents[1] / "data" / "papers"
WEB_DIR = Path(__file__).resolve().parent / "web"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/papers")
def list_papers() -> list[dict[str, str | int]]:
    if not PAPERS_DIR.exists():
        return []

    return [
        {
            "file_name": path.name,
            "size": path.stat().st_size,
        }
        for path in sorted(PAPERS_DIR.glob("*.pdf"))
    ]


@app.delete("/api/papers/{file_name}")
def delete_paper(file_name: str) -> dict[str, str]:
    safe_name = Path(file_name).name
    if safe_name != file_name or not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid PDF file name")

    paper_path = PAPERS_DIR / safe_name
    if not paper_path.exists():
        raise HTTPException(status_code=404, detail="Paper not found")

    ChromaStore().delete_document(safe_name)
    paper_path.unlink()
    return {"file_name": safe_name, "status": "deleted"}


@app.post("/search")
def search(request: SearchRequest) -> dict:
    result = ChromaStore().search(request.query, n_results=request.n_results)
    return {
        "query": request.query,
        "results": [
            {
                "id": result["ids"][0][index],
                "document": result["documents"][0][index],
                "distance": result["distances"][0][index],
                "metadata": result["metadatas"][0][index],
            }
            for index in range(len(result["ids"][0]))
        ],
    }


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)) -> dict:
    file_name = Path(file.filename or "").name
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = PAPERS_DIR / file_name
    target_path.write_bytes(await file.read())

    count = ingest_pdf(target_path)
    return {
        "file_name": file_name,
        "path": str(target_path),
        "chunks": count,
    }


@app.post("/ask")
async def ask(request: AskRequest) -> dict:
    result = ChromaStore().search(request.query, n_results=request.n_results)
    contexts = [
        {
            "document": result["documents"][0][index],
            "metadata": result["metadatas"][0][index],
        }
        for index in range(len(result["ids"][0]))
    ]
    try:
        answer = await generate_answer(request.query, contexts)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {error}") from error

    return {
        "question": request.query,
        "answer": answer,
        "sources": [item["metadata"] for item in contexts],
    }
