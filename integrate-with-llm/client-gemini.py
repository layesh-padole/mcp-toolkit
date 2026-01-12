import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any, List, Optional

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types

# Allow nested event loops (Jupyter/IPython)
nest_asyncio.apply()

# Load env vars
load_dotenv("../.env")


class MCPGeminiClient:
    """Client for interacting with Gemini using MCP tools."""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()  # Context manager for cleanup

        # ---- Load from env ----
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=self.api_key)

        self.stdio: Optional[Any] = None
        self.write: Optional[Any] = None

    async def connect_to_server(self, server_script_path: str = "server.py"):
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        tools_result = await self.session.list_tools()
        print("\nConnected to server with tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")

    async def get_gemini_tools(self) -> List[types.Tool]:
        tools_result = await self.session.list_tools()

        function_decls = [
            types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema,
            )
            for tool in tools_result.tools
        ]

        return [types.Tool(function_declarations=function_decls)]

    async def process_query(self, query: str) -> str:
        tools = await self.get_gemini_tools()

        system_instruction = (
            "You are a workplace assistant with access to a knowledge base of sarcastic/funny responses. "
            "When the user asks a question, ALWAYS check the knowledge base first using the available tool "
            "to see if there's a matching response. If found, use that response."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=query,
            config=types.GenerateContentConfig(
                tools=tools,
                system_instruction=system_instruction,
            ),
        )

        parts = response.candidates[0].content.parts
        tool_parts = []
        tool_called = False

        for part in parts:
            if part.function_call:
                tool_called = True
                fn_name = part.function_call.name
                args = dict(part.function_call.args)

                result = await self.session.call_tool(fn_name, arguments=args)

                tool_parts.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result.content[0].text},
                    )
                )

        if not tool_called:
            return response.text

        followup = self.client.models.generate_content(
            model=self.model,
            contents=[
                query,
                response.candidates[0].content,
                types.Content(role="tool", parts=tool_parts),
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )

        return followup.text

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPGeminiClient()
    await client.connect_to_server("server.py")

    query = "Hey, how are you doing?"
    print(f"\nQuery: {query}")

    response = await client.process_query(query)
    print(f"\nResponse: {response}")

    await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())