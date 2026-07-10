import os
import csv
import io
import asyncio  # ✅ NEW: Required to support async MCP loading
from datetime import datetime
from pathlib import Path

# ===== DeepSeek (OpenAI-compatible) =====
from langchain_openai import ChatOpenAI

# ===== LangChain / Agent =====
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool
from langchain_core.messages import AIMessageChunk

# ===== LangChain / Deep Agent =====
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

# ===== MCP (NEW) =====
# ✅ Import MCP tool loader from external module
# This keeps MCP logic decoupled from agent logic
from mcp_client import get_mcp_tools

# ===== ENV =====
from pydantic_settings import BaseSettings, SettingsConfigDict


# =========================================================
# 1. CONFIG
# =========================================================
class AppConfig(BaseSettings):
    """
    Application configuration loaded from .env file.

    This config is used for LLM (DeepSeek).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str 
    DEEPSEEK_MODEL: str


# =========================================================
# 2. LLM CREATION
# =========================================================
def create_llm(config: AppConfig):
    """
    Initialize DeepSeek LLM.

    DeepSeek is OpenAI-compatible, so we use ChatOpenAI
    and override base_url.
    """

    llm = ChatOpenAI(
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
        model=config.DEEPSEEK_MODEL,
        temperature=0,
    )

    return llm


# =========================================================
# 3. Define Skill location
# =========================================================

backend = FilesystemBackend(
    root_dir=".",
    virtual_mode=True
)

# =========================================================
# 4. LOCAL TOOLS (unchanged)
# =========================================================

@tool
def get_tickets_data(month: str, year: int, activity_type: str = "") -> str:
    """
    Load ticket data filtered by month/year and optionally activity type.

    Args:
        month: Full month name (e.g., 'March')
        year: Year (e.g., 2024)
        activity_type: Optional filter for Subaccount activity type
    """

    csv_path = Path(__file__).parent / "tickets.csv"

    if not csv_path.exists():
        return "tickets.csv not found."

    with open(csv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")

        rows = []
        for row in reader:
            created_date = datetime.strptime(row["Created"], "%m/%d/%Y %H:%M")

            month_name = created_date.strftime("%B")

            if month_name == month and created_date.year == year:
                if activity_type:
                    if row["Subaccount activity type:"] == activity_type:
                        rows.append(row)
                else:
                    rows.append(row)

    if not rows:
        return f"No tickets found for {month} {year}."

    # Return CSV string
    header = "Request Number,Created,Subaccount activity type"
    lines = [header]

    for r in rows:
        lines.append(
            f"{r['Request Number']},{r['Created']},{r['Subaccount activity type:']}"
        )

    return "\n".join(lines)

@tool
def analyze_ticket_summary(ticket_data: str) -> str:
    """
    Analyze ticket data and provide summary statistics.

    Use this AFTER get_tickets_data.

    Args:
        ticket_data: CSV-formatted ticket data
    """

    reader = csv.DictReader(io.StringIO(ticket_data))
    rows = list(reader)

    if not rows:
        return "No data to analyze."

    total_tickets = len(rows)

    # ✅ Count per activity type
    activity_count = {}
    for r in rows:
        activity = r["Subaccount activity type"]
        activity_count[activity] = activity_count.get(activity, 0) + 1

    # ✅ Find most frequent activity
    top_activity = max(activity_count, key=activity_count.get)

    # ✅ Build summary
    summary_lines = [
        f"Total Tickets: {total_tickets}",
        f"Top Activity Type: {top_activity} ({activity_count[top_activity]})",
        "",
        "Activity Breakdown:"
    ]

    for k, v in activity_count.items():
        summary_lines.append(f" - {k}: {v}")

    return "\n".join(summary_lines)
# =========================================================
# 5. AGENT CREATION (integrated with MCP)
# =========================================================
async def create_app():
    """
    Create the LangChain agent.

    ✅ Key responsibilities:
    - Initialize LLM
    - Dynamically load MCP tools
    - Merge local + MCP tools
    - Create unified agent

    ✅ Important design:
    MCP tools are loaded at runtime so that:
    - Discovery logs are visible
    - Tools are always up-to-date
    """

    config = AppConfig()
    llm = create_llm(config)

    # =====================================================
    # ✅ MCP INTEGRATION START
    # =====================================================
    print("\n🔗 Loading MCP tools inside agent...")

    # ✅ This will:
    #  - Connect to SAP MCP server
    #  - Discover available tools
    #  - Print tool list
    #  - Return tool objects
    mcp_tools = await get_mcp_tools()

    print(f"✅ MCP tools loaded: {len(mcp_tools)}")

    # ✅ Merge local tools with MCP tools
    # This enables the agent to decide automatically
    # whether to call:
    # - local CSV tools
    # - SAP MCP tools
    
    all_tools = [
        get_tickets_data,
        analyze_ticket_summary,
        *mcp_tools
    ]

    print(f"✅ Total tools available to agent: {len(all_tools)}")
    # =====================================================
    # ✅ MCP INTEGRATION END
    # =====================================================

    agent = create_deep_agent(
        model=llm,
        tools=all_tools,  # ✅ Now includes MCP tools
        backend=backend,
        skills=["skills"],
        checkpointer=InMemorySaver()  # ✅ Maintains conversation memory
    )

    return agent


# =========================================================
# 6. CLI TEST (async adapted)
# =========================================================
# --- CHANGE START (Plan A): switch REPL to async and use astream ---
async def main_async():
    """
    CLI test entry.

    Uses asyncio because create_app is async.
    Uses agent.astream to support async-only MCP tools.
    """
    agent = await create_app()  # Await async creation

    print("\n✅ DeepSeek + MCP Agent Ready")
    print("Type 'quit' to exit\n")

    thread_config = {"configurable": {"thread_id": "1"}}

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            break

        print("\nAssistant: ", end="", flush=True)

        # Use async streaming to ensure async MCP tools work
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": user_input}]},
            thread_config,
            stream_mode="messages",
            version="v2",
        ):
            if chunk["type"] == "messages":
                token, _ = chunk["data"]

                if isinstance(token, AIMessageChunk) and token.text:
                    print(token.text, end="", flush=True)

        print("\n")
# --- CHANGE END ---


if __name__ == "__main__":
    # --- CHANGE START (Plan A): run async entrypoint ---
    asyncio.run(main_async())
    # --- CHANGE END ---