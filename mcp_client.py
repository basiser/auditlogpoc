"""
mcp.py

Integrated Version:
LangChain + SAP Automation Pilot MCP + DeepSeek LLM

✅ Now supports:
- Standalone run (main)
- Import by agent.py (get_mcp_tools)
- Dynamic tool discovery printing
"""

import asyncio
import base64
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI


# =========================
# Configuration Section
# =========================
load_dotenv()
class Config:

    MCP_BASE_URL = os.getenv("MCP_BASE_URL")

    USERNAME = os.getenv("MCP_USERNAME")
    PASSWORD = os.getenv("MCP_PASSWORD")

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

    @staticmethod
    def get_basic_auth():
        raw = f"{Config.USERNAME}:{Config.PASSWORD}"
        return base64.b64encode(raw.encode()).decode()


# =========================
# ✅ NEW: Reusable MCP loader
# =========================
async def get_mcp_tools():

    print("\n🔗 [MCP] Connecting to SAP MCP Server...")

    basic_auth = Config.get_basic_auth()

    mcp_client = MultiServerMCPClient(
        connections={
            "sap": {
                "transport": "streamable_http",
                "url": Config.MCP_BASE_URL,
                "headers": {
                    "Authorization": f"Basic {basic_auth}"
                },
            }
        }
    )

    print("🔍 [MCP] Discovering tools...")

    try:
        tools = await mcp_client.get_tools()

        print("✅ [MCP] Tools discovered:")
        for tool in tools:
            print(f"   - {tool.name}")

        return tools

    except Exception as e:
        print("❌ [MCP] Tool discovery failed:")
        print(e)
        return []


# =========================
# Main Logic (Standalone)
# =========================
async def main():

    print("🔗 Running standalone MCP agent...")

    # ✅ reuse the same function
    tools = await get_mcp_tools()

    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0.2,
        api_key=Config.DEEPSEEK_API_KEY,
        base_url=Config.DEEPSEEK_BASE_URL
    )

    agent = create_agent(
        model=llm,
        tools=tools
    )

    print("\n✅ MCP Agent Ready!")
    print("💬 Enter your question (type 'q' to quit)")

    while True:

        user_prompt = input("\n🧑 Your question: ")

        if user_prompt.lower() == "q":
            break

        print("\n🤖 Thinking...")

        try:
            response = await agent.ainvoke(
                {
                    "messages": [
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )

            final_msg = response["messages"][-1].content
            print("\n✅ Answer:")
            print(final_msg)

        except Exception as e:
            print("\n❌ Execution failed:")
            print(e)


# =========================
# Entry Point
# =========================
if __name__ == "__main__":
    asyncio.run(main())