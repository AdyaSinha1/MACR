import asyncio
import uuid
import json
import os
from typing import Dict, Any
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from orchestrator.coordinator import ReviewCoordinator
from memory.faiss_store import FaissMemoryStore
from memory.embeddings import EmbeddingService
from api.events import EventBus, active_job_id
from structlog import get_logger

logger = get_logger()

app = FastAPI(title="MACR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dependencies
memory_store = None

@app.on_event("startup")
async def startup_event():
    global memory_store
    logger.info("Initializing MACR API...")
    # Initialize memory in background or lazily if we don't want to block startup
    # For now, we'll initialize it lazily when first needed to speed up boot.

class ReviewRequest(BaseModel):
    file_path: str
    code_content: str
    use_memory: bool = False

async def get_coordinator(use_memory: bool) -> ReviewCoordinator:
    global memory_store
    if use_memory:
        if memory_store is None:
            logger.info("Initializing Memory System...")
            EventBus.publish_sync('review_status', {'status': 'initializing_memory'})
            # This is synchronous and blocks, in a real production app we'd offload to a thread
            # but for our portfolio project it's fine.
            embedding_service = EmbeddingService()
            memory_store = FaissMemoryStore(embedding_service=embedding_service)
        return ReviewCoordinator(memory_store=memory_store)
    return ReviewCoordinator()

async def run_review_task(job_id: str, req: ReviewRequest):
    """Background task to run the review and publish events."""
    active_job_id.set(job_id)
    try:
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY is not set.")
            
        coordinator = await get_coordinator(req.use_memory)
        await coordinator.review_file(req.file_path, req.code_content)
    except Exception as e:
        logger.error("Review task failed", job_id=job_id, error=str(e))
        EventBus.publish_sync('review_error', {'error': str(e)})
    finally:
        # Give clients a moment to receive the final message before tearing down the queue
        await asyncio.sleep(2)
        EventBus.unsubscribe(job_id)

@app.post("/api/review")
async def start_review(req: ReviewRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    # Ensure queue is created before returning
    await EventBus.subscribe(job_id)
    
    background_tasks.add_task(run_review_task, job_id, req)
    return {"job_id": job_id}

@app.get("/api/stream/{job_id}")
async def stream_review(job_id: str, request: Request):
    async def event_generator():
        queue = await EventBus.subscribe(job_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                # Wait for the next event
                message = await queue.get()
                yield {
                    "data": json.dumps({
                        "event": message["event"],
                        "data": message["data"]
                    })
                }
                
                # Stop streaming if we reached terminal states
                if message["event"] in ('review_complete', 'review_error'):
                    break
        except asyncio.CancelledError:
            pass
            
    return EventSourceResponse(event_generator())

# Mount static files (will be created next)
ui_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(ui_path):
    os.makedirs(ui_path)
    
app.mount("/", StaticFiles(directory=ui_path, html=True), name="static")
