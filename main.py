import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import create_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = None

SKILLS_DIR = Path("skills")


# ========================================================
# Models
# ========================================================

class SkillCreateRequest(BaseModel):
    name: str
    content: str


class AnalyzeRequest(BaseModel):
    message: str


# ========================================================
# Agent Management
# ========================================================

async def reload_agent():
    global agent

    print("🔄 Reloading Deep Agent...")
    agent = await create_app()
    print("✅ Agent Reloaded")


@app.on_event("startup")
async def startup():
    await reload_agent()


# ========================================================
# Skills
# ========================================================

@app.post("/api/skills")
async def create_skill(request: SkillCreateRequest):

    skill_dir = SKILLS_DIR / request.name
    skill_file = skill_dir / "SKILL.md"

    if skill_dir.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Skill '{request.name}' already exists"
        )

    skill_dir.mkdir(parents=True)

    skill_file.write_text(
        request.content,
        encoding="utf-8"
    )

    await reload_agent()

    return {
        "success": True,
        "skill": request.name
    }


@app.get("/api/skills")
async def list_skills():

    results = []

    if not SKILLS_DIR.exists():
        return []

    for skill_dir in SKILLS_DIR.iterdir():

        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            continue

        results.append({
            "name": skill_dir.name,
            "content": skill_file.read_text(
                encoding="utf-8"
            )
        })

    return results


@app.delete("/api/skills/{skill_name}")
async def delete_skill(skill_name: str):

    skill_dir = SKILLS_DIR / skill_name

    if not skill_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    shutil.rmtree(skill_dir)

    await reload_agent()

    return {
        "success": True,
        "deleted": skill_name
    }


# ========================================================
# Analyze
# ========================================================

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request.message
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": str(uuid.uuid4())
            }
        }
    )

    final_message = result["messages"][-1]

    return {
        "result": final_message.content
    }