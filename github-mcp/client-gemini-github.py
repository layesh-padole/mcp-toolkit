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

# Allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv("../.env")  # Load from parent directory
load_dotenv(".env")     # Override with local .env if exists


class GitHubMCPGeminiClient:
    """Client for interacting with GitHub via MCP using Gemini."""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Load Gemini API key
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY is not set")
        
        self.gemini_client = genai.Client(api_key=self.gemini_key)
        
        # Load GitHub token
        self.github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not self.github_token or self.github_token == "your-github-token-here":
            raise ValueError(
                "GITHUB_PERSONAL_ACCESS_TOKEN is not set in .env file. "
                "Get it from: https://github.com/settings/tokens"
            )
        
        self.toolsets = os.getenv("GITHUB_TOOLSETS", "repos,issues,pull_requests")
        
    async def connect_to_github_mcp(self):
        """Connect to GitHub MCP server via Docker."""
        print("Starting GitHub MCP server...")

        server_params = StdioServerParameters(
            command="/usr/local/bin/docker",  # Full path to docker
            args=[
                "run", "-i", "--rm",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                "-e", "GITHUB_TOOLSETS",
                "ghcr.io/github/github-mcp-server"
            ],
            env={
                "GITHUB_PERSONAL_ACCESS_TOKEN": self.github_token,
                "GITHUB_TOOLSETS": self.toolsets
            }
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )
        
        await self.session.initialize()
        
        # List available tools
        tools_result = await self.session.list_tools()
        print(f"Connected to GitHub MCP with {len(tools_result.tools)} tools\n")
        
        # Show some example tools
        print("Example tools:")
        for tool in tools_result.tools[:5]:
            print(f"  • {tool.name}")
        if len(tools_result.tools) > 5:
            print(f"  ... and {len(tools_result.tools) - 5} more\n")
        
    async def get_gemini_tools(self) -> List[types.Tool]:
        """Convert MCP tools to Gemini format."""
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
        """Process a query using Gemini with GitHub MCP tools."""
        tools = await self.get_gemini_tools()
        
        system_instruction = (
            "You are a GitHub assistant with access to GitHub's API via MCP tools. "
            "You can help with repositories, issues, pull requests, code search, and more. "
            "When users ask about GitHub operations, use the available tools to fetch real data."
        )
        
        # First call to Gemini
        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=query,
            config=types.GenerateContentConfig(
                tools=tools,
                system_instruction=system_instruction,
            ),
        )
        
        # Check for tool calls
        parts = response.candidates[0].content.parts
        tool_parts = []
        tool_called = False
        
        for part in parts:
            if part.function_call:
                tool_called = True
                fn_name = part.function_call.name
                args = dict(part.function_call.args)
                
                print(f"Calling tool: {fn_name}")
                print(f" Arguments: {args}\n")
                
                # Execute tool via MCP
                result = await self.session.call_tool(fn_name, arguments=args)
                
                tool_parts.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result.content[0].text},
                    )
                )
        
        if not tool_called:
            return response.text
        
        # Follow-up call with tool results
        followup = self.gemini_client.models.generate_content(
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
        """Clean up resources."""
        await self.exit_stack.aclose()


async def main():
    """Example usage."""
    client = GitHubMCPGeminiClient()
    await client.connect_to_github_mcp()
    
    # Example queries - customize these based on your needs
    queries = [
        "List my recent repositories",
        "Show me open issues in my repositories",
        # Add more queries here
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}\n")
        
        try:
            response = await client.process_query(query)
            print(f"Response:\n{response}\n")
        except Exception as e:
            print(f"Error: {e}\n")
    
    await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
