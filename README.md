# MCP Weather Demo

A practical demonstration of Model Context Protocol (MCP) client-server architecture using HTTP/SSE transport.

## Overview

This demo showcases:
- **MCP Server**: Exposes weather tools via HTTP/SSE
- **MCP Client**: Connects to server, discovers tools, and executes requests
- **Real-world Integration**: Fetches live weather data from wttr.in API
- **Protocol Transparency**: Verbose mode shows actual JSON-RPC messages

## Architecture

```
┌─────────────────────┐         HTTP/SSE          ┌──────────────────────┐
│  weather_client.py  │  ←-------------------→    │  weather_server.py   │
│    (MCP Client)     │                           │    (MCP Server)      │
└─────────────────────┘                           └──────────────────────┘
         ↓                                                  ↓
    User Terminal                                    wttr.in API
```

### Communication Flow

1. **SSE Connection**: Client establishes persistent connection for server responses
2. **HTTP POST**: Client sends JSON-RPC requests to `/message` endpoint
3. **Tool Discovery**: Client lists available tools and schemas
4. **Tool Execution**: Client calls tools with parameters
5. **Response Handling**: Server sends results via SSE stream

## Prerequisites

- Python 3.10 or higher
- Internet connection (for weather API)
- Two terminal windows

## Installation

### Terminal 1 - Server Setup

```bash
cd server
pip install -r requirements.txt
```

### Terminal 2 - Client Setup

```bash
cd client
pip install -r requirements.txt
```

## Running the Demo

### Step 1: Start the Server

In **Terminal 1**:

```bash
cd server
python weather_server.py
```

You should see:
```
🌤️  MCP Weather Server
==================================================
Server starting on http://localhost:8000
SSE endpoint: http://localhost:8000/sse
Message endpoint: http://localhost:8000/message
==================================================

Waiting for client connections...
```

### Step 2: Run the Client

In **Terminal 2**:

```bash
cd client
python weather_client.py
```

**For verbose mode (shows JSON-RPC messages):**

```bash
python weather_client.py --verbose
```

## What the Demo Shows

### 1. Connection Lifecycle
- Client connects to server via SSE
- Initialize handshake with protocol version
- Server returns capabilities

### 2. Tool Discovery
- Client requests list of available tools
- Server returns tool schemas with parameters

### 3. Tool Execution Examples
- **Current Weather**: Get temperature, conditions, humidity for London
- **Forecast**: Get 3-day forecast for Tokyo
- **Multiple Queries**: Additional weather request for Bengaluru

### 4. JSON-RPC Protocol (Verbose Mode)

Example request:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_current_weather",
    "arguments": {"city": "London"}
  },
  "id": 1
}
```

Example response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Current Weather in London:\nTemperature: 8°C (46°F)..."
      }
    ]
  }
}
```

## Available Tools

### 1. get_current_weather
- **Description**: Get current weather conditions for a city
- **Parameters**:
  - `city` (string, required): City name

### 2. get_forecast
- **Description**: Get weather forecast for a city
- **Parameters**:
  - `city` (string, required): City name
  - `days` (integer, required): Number of days (1-3)

## Technical Details

### MCP Protocol Version
- **Version**: 2024-11-05
- **Transport**: HTTP with SSE for streaming

### Transport Mechanisms

**HTTP POST** (`/message` endpoint):
- Client-to-server requests
- JSON-RPC 2.0 format
- Request/response pattern

**SSE** (`/sse` endpoint):
- Server-to-client responses
- Persistent connection
- Real-time message delivery

### Key Components

**Server** (`weather_server.py`):
- FastAPI/Starlette web framework
- MCP server decorators (`@server.list_tools()`, `@server.call_tool()`)
- Async HTTP client for weather API
- SSE connection management

**Client** (`weather_client.py`):
- HTTP client with SSE support
- Message ID tracking for request/response correlation
- Async queue for response handling
- Verbose logging for educational purposes

## Troubleshooting

### Port Already in Use
```
Error: Address already in use
```
**Solution**: Kill the process using port 8000 or change the port in both files.

```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Connection Refused
```
Error: Connection refused
```
**Solution**: Ensure server is running before starting the client.

### API Timeout
```
Error: Failed to fetch weather data
```
**Solution**: Check internet connection. wttr.in might be temporarily unavailable.

## Extending the Demo

### Add More Tools
Modify `weather_server.py` to add new tools:
```python
@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ... existing tools ...
        Tool(
            name="your_new_tool",
            description="Your tool description",
            inputSchema={...}
        )
    ]
```

### Modify Client Behavior
Edit `weather_client.py` to customize:
- Different cities
- Error handling
- Response formatting
- Additional tool calls

## Learning Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [wttr.in API Documentation](https://github.com/chubin/wttr.in)

## Key Takeaways

1. **Separation of Concerns**: Client and server run independently
2. **Standard Protocol**: JSON-RPC 2.0 for interoperability
3. **Real-time Communication**: SSE enables server-push capability
4. **Type Safety**: JSON Schema for parameter validation
5. **Production Ready**: Architecture matches enterprise deployments

## License

MIT License - Free to use and modify for educational purposes.
