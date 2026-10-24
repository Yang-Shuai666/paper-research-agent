from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.config import get_settings
from app.rag.agent import run_agent
from app.rag.bm25_index import invalidate_bm25_index
from app.rag.citations import extract_citations
from app.rag.context import get_expander
from app.rag.ingest import ingest_pdf
from app.rag.llm import generate_answer
from app.rag.pipeline import build_retriever
from app.rag.vector_store import get_store

app = FastAPI(
    title="Paper Research Agent",
    version="0.1.0",
    description="A local-first RAG assistant for research papers.",
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    n_results: int = Field(default=3, ge=1, le=20)


class AskRequest(SearchRequest):
    n_results: int = Field(default=6, ge=1, le=20)


class AgentRequest(BaseModel):
    query: str = Field(min_length=1)
    max_steps: int = Field(default=6, ge=1, le=6)


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


@app.get("/api/stats")
def stats() -> dict[str, int]:
    return {
        "papers": len(list(PAPERS_DIR.glob("*.pdf"))) if PAPERS_DIR.exists() else 0,
        "chunks": get_store().count(),
    }


@app.delete("/api/papers/{file_name}")
def delete_paper(file_name: str) -> dict[str, str]:
    safe_name = Path(file_name).name
    if safe_name != file_name or not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid PDF file name")

    paper_path = PAPERS_DIR / safe_name
    if not paper_path.exists():
        raise HTTPException(status_code=404, detail="Paper not found")

    get_store().delete_document(safe_name)
    invalidate_bm25_index()
    paper_path.unlink()
    return {"file_name": safe_name, "status": "deleted"}


@app.post("/search")
def search(request: SearchRequest) -> dict:
    chunks = build_retriever().search(request.query, top_k=request.n_results)
    return {
        "query": request.query,
        "results": [
            {
                "id": chunk.id,
                "document": chunk.text,
                "score": chunk.score,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ],
    }


@app.post("/ingest")
async def ingest(file: Annotated[UploadFile, File()]) -> dict:
    file_name = Path(file.filename or "").name
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = PAPERS_DIR / file_name
    content = await file.read()
    await run_in_threadpool(target_path.write_bytes, content)

    count = await run_in_threadpool(ingest_pdf, target_path)
    return {
        "file_name": file_name,
        "path": str(target_path),
        "chunks": count,
    }


@app.post("/ask")
async def ask(request: AskRequest) -> dict:
    settings = get_settings()
    chunks = build_retriever().search(request.query, top_k=request.n_results)
    if settings.enable_context_expansion:
        chunks = get_expander().expand(chunks)

    contexts = [{"document": chunk.text, "metadata": chunk.metadata} for chunk in chunks]
    try:
        answer = await generate_answer(request.query, contexts)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {error}") from error

    valid_citations, invalid_citations = extract_citations(answer.text, len(contexts))
    return {
        "question": request.query,
        "answer": answer.text,
        "citations": {
            "valid": valid_citations,
            "invalid": invalid_citations,
        },
        "sources": [{**chunk.metadata, "score": round(chunk.score, 4)} for chunk in chunks],
    }


@app.post("/agent/ask")
async def agent_ask(request: AgentRequest) -> dict:
    try:
        result = await run_agent(request.query, max_steps=request.max_steps)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Agent request failed: {error}") from error

    return {
        "question": request.query,
        "answer": result.text,
        "citations": result.citations,
        "sources": result.sources,
        "steps": result.steps,
        "usage": {
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "model": result.model,
        },
        "stop_reason": result.stop_reason,
        "latency_ms": round(result.elapsed_ms, 1),
    }
