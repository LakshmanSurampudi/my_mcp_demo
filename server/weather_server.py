#!/usr/bin/env python3
"""
MCP Weather Server - Exposes weather tools via HTTP/SSE transport
"""
import asyncio
import json
from typing import Any
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response
from sse_starlette import EventSourceResponse
import uvicorn

# Initialize MCP server
mcp_server = Server("weather-server")

# HTTP client for weather API
http_client = httpx.AsyncClient(timeout=10.0)


async def fetch_weather_data(city: str) -> dict:
    """Fetch weather data from wttr.in API"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = await http_client.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"Failed to fetch weather data: {str(e)}")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available weather tools"""
    return [
        Tool(
            name="get_current_weather",
            description="Get current weather conditions for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., London, Tokyo, New York)"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_forecast",
            description="Get weather forecast for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., London, Tokyo, New York)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days for forecast (1-3)",
                        "minimum": 1,
                        "maximum": 3
                    }
                },
                "required": ["city", "days"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution"""
    
    if name == "get_current_weather":
        city = arguments.get("city")
        if not city:
            return [TextContent(type="text", text="Error: City parameter is required")]
        
        try:
            data = await fetch_weather_data(city)
            current = data["current_condition"][0]
            
            result = {
                "city": city,
                "temperature_c": current["temp_C"],
                "temperature_f": current["temp_F"],
                "condition": current["weatherDesc"][0]["value"],
                "humidity": current["humidity"],
                "wind_speed_kmph": current["windspeedKmph"],
                "wind_direction": current["winddir16Point"]
            }
            
            formatted = f"""Current Weather in {city}:
Temperature: {result['temperature_c']}°C ({result['temperature_f']}°F)
Condition: {result['condition']}
Humidity: {result['humidity']}%
Wind: {result['wind_speed_kmph']} km/h {result['wind_direction']}"""
            
            return [TextContent(type="text", text=formatted)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_forecast":
        city = arguments.get("city")
        days = arguments.get("days", 3)
        
        if not city:
            return [TextContent(type="text", text="Error: City parameter is required")]
        
        try:
            data = await fetch_weather_data(city)
            weather_forecast = data["weather"][:days]
            
            forecast_lines = [f"{days}-Day Weather Forecast for {city}:\n"]
            
            for day in weather_forecast:
                date = day["date"]
                max_temp = day["maxtempC"]
                min_temp = day["mintempC"]
                condition = day["hourly"][0]["weatherDesc"][0]["value"]
                
                forecast_lines.append(
                    f"📅 {date}: {min_temp}°C - {max_temp}°C, {condition}"
                )
            
            return [TextContent(type="text", text="\n".join(forecast_lines))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    else:
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]


# SSE connection management
sse_connections = []


async def handle_sse(request: Request):
    """Handle SSE connection from client"""
    async def event_generator():
        queue = asyncio.Queue()
        sse_connections.append(queue)
        
        try:
            while True:
                message = await queue.get()
                if message is None:
                    break
                yield {"data": json.dumps(message)}
        finally:
            sse_connections.remove(queue)
    
    return EventSourceResponse(event_generator())


async def handle_message(request: Request):
    """Handle incoming JSON-RPC messages from client"""
    try:
        body = await request.json()
        
        # Process the message through MCP server
        # This is a simplified handling - in production you'd use mcp.server's full transport
        method = body.get("method")
        params = body.get("params", {})
        msg_id = body.get("id")
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "weather-server",
                        "version": "1.0.0"
                    }
                }
            }
        elif method == "tools/list":
            tools = await list_tools()
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await call_tool(tool_name, arguments)
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": content.type, "text": content.text}
                        for content in result
                    ]
                }
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        # Send response via SSE to all connected clients
        for queue in sse_connections:
            await queue.put(response)
        
        return Response(
            content=json.dumps({"status": "ok"}),
            media_type="application/json"
        )
        
    except Exception as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json"
        )


# Starlette app setup
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/message", endpoint=handle_message, methods=["POST"]),
    ]
)


async def cleanup():
    """Cleanup resources on shutdown"""
    await http_client.aclose()


if __name__ == "__main__":
    print("🌤️  MCP Weather Server")
    print("=" * 50)
    print("Server starting on http://localhost:8000")
    print("SSE endpoint: http://localhost:8000/sse")
    print("Message endpoint: http://localhost:8000/message")
    print("=" * 50)
    print("\nWaiting for client connections...\n")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    finally:
        asyncio.run(cleanup())
