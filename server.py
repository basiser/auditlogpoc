import json
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk
from pydantic import BaseModel
# import custom agent
from agent import create_app       

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# CHANGE: defer agent creation to startup and keep a global reference
agent = None  # will be initialized in the startup event
threads: dict = {}


class ChatRequest(BaseModel):
    thread_id: str | None = None
    message: str


def _create_thread() -> dict:
    thread_id = str(uuid.uuid4())
    threads[thread_id] = {
        "id": thread_id,
        "title": "New Chat",
        "created_at": datetime.now().isoformat(),
        "messages": [],
    }
    return threads[thread_id]


@app.get("/api/threads")
def list_threads():
    return sorted(threads.values(), key=lambda t: t["created_at"], reverse=True)


@app.post("/api/threads")
def create_thread():
    return _create_thread()


@app.delete("/api/threads/{thread_id}")
def delete_thread(thread_id: str):
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    del threads[thread_id]
    return {"ok": True}


@app.get("/api/threads/{thread_id}/messages")
def get_messages(thread_id: str):
    if thread_id not in threads:
        return []
    return threads[thread_id]["messages"]


# CHANGE: initialize the async agent (with MCP tools) at app startup
@app.on_event("startup")
async def startup():
    global agent
    agent = await create_app()  # await async factory so MCP async tools are supported


# CHANGE: make this endpoint async and stream via agent.astream to support async-only MCP tools
@app.post("/api/chat")
async def chat(request: ChatRequest):
    if request.thread_id and request.thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    new_thread = request.thread_id is None
    thread = _create_thread() if new_thread else threads[request.thread_id]

    thread["messages"].append({"role": "user", "content": request.message})

    if thread["title"] == "New Chat":
        thread["title"] = request.message[:50]

    config = {"configurable": {"thread_id": thread["id"]}}

    async def stream():
        if new_thread:
            yield f"data: {json.dumps({'thread_id': thread['id']})}\n\n"

        full_response = ""
        # CHANGE: use async streaming to allow MCP async tools to run
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": request.message}]},
            config,
            stream_mode="messages",
            version="v2",
        ):
            if chunk["type"] == "messages":
                token, metadata = chunk["data"]
                if isinstance(token, AIMessageChunk) and token.text:
                    full_response += token.text
                    yield f"data: {json.dumps({'token': token.text})}\n\n"

        thread["messages"].append({"role": "assistant", "content": full_response})
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# def start():
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)