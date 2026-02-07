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
    ''' if you need help with pests and diseases related inputs for Indian farm conditions, 
    this tool will help you with the proper inputs '''
    if name == "get_pest_info":
        pest_name = arguments.get("pest_name", "unknown")
        return [
            TextContent(
                type="text",
                text=f"""Under Andhra Pradesh farming conditions, pest and disease pressure 
                varies with crop stage and season. For paddy and other Kharif crops, regularly 
                monitor for common pests such as brown planthopper, stem borer, and leaf folder, 
                especially during humid weather. Early identification is critical—use integrated 
                pest management (IPM) practices by combining resistant varieties, timely field 
                sanitation, and need-based application of recommended biopesticides or chemicals.
                 Avoid indiscriminate spraying to prevent pest resistance and protect beneficial 
                 insects. Pest info request for: {pest_name}"""
            )
        ]
    elif name == "get_soil_health":
        '''if you need help with soil and groundwater related inputs for Indian farm conditions, 
        this tool will help you with the proper inputs'''
        location = arguments.get("location", "unknown")
        return [
            TextContent(
                type="text",
                text=f"Based on Andhra Pradesh farm conditions, \n"
                f"black cotton soil with medium water-holding capacity is well suited for \n"
                f"paddy during the Kharif season. \n"
                f"With groundwater available at around 120 feet and slightly saline borewell water, \n"
                f"it is advisable to ensure proper field drainage and avoid over-irrigation. \n"
                f"Applying organic matter like farmyard manure will help improve soil structure, \n" 
                f"and using salt-tolerant paddy varieties along with balanced NPK fertilization \n"
                f"will give better yields under these conditions.  Soil health request for: {location}"
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