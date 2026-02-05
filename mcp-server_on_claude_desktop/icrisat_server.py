from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
import json

app = Server("icrisat-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_pest_info",
            description="Get information about citrus pests and diseases",
            inputSchema={
                "type": "object",
                "properties": {
                    "pest_name": {
                        "type": "string",
                        "description": "Name of the pest or disease"
                    }
                },
                "required": ["pest_name"]
            }
        ),
        Tool(
            name="get_soil_health",
            description="Get soil health indicators for citrus cultivation",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location/region for soil data"
                    }
                },
                "required": ["location"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_pest_info":
        pest_name = arguments.get("pest_name", "unknown")
        return [
            TextContent(
                type="text",
                text=f"Hello World from ICRISAT! Pest info request for: {pest_name}"
            )
        ]
    elif name == "get_soil_health":
        location = arguments.get("location", "unknown")
        return [
            TextContent(
                type="text",
                text=f"Hello World from ICRISAT! Soil health request for: {location}"
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