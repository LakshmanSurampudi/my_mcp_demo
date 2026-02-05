from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
import json

app = Server("ap-government-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_schemes",
            description="Get government schemes for citrus farmers in Andhra Pradesh",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category of scheme (subsidy, insurance, training, etc.)"
                    }
                },
                "required": ["category"]
            }
        ),
        Tool(
            name="get_farmer_programs",
            description="Get information about farmer welfare programs",
            inputSchema={
                "type": "object",
                "properties": {
                    "district": {
                        "type": "string",
                        "description": "District name in AP"
                    }
                },
                "required": ["district"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_schemes":
        category = arguments.get("category", "unknown")
        return [
            TextContent(
                type="text",
                text=f"Hello World from AP Government! Schemes request for category: {category}"
            )
        ]
    elif name == "get_farmer_programs":
        district = arguments.get("district", "unknown")
        return [
            TextContent(
                type="text",
                text=f"Hello World from AP Government! Programs request for district: {district}"
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())