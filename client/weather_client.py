#!/usr/bin/env python3
"""
MCP Weather Client - Demonstrates MCP protocol with HTTP/SSE transport
"""
import asyncio
import argparse
import json
from typing import Any, Optional
import httpx
from httpx_sse import aconnect_sse


class MCPWeatherClient:
    """MCP Client for weather server"""
    
    def __init__(self, server_url: str = "http://localhost:8000", verbose: bool = False):
        self.server_url = server_url
        self.sse_url = f"{server_url}/sse"
        self.message_url = f"{server_url}/message"
        self.verbose = verbose
        self.message_id = 0
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.sse_task = None
        self.response_queue = asyncio.Queue()
        
    def _next_id(self) -> int:
        """Generate next message ID"""
        self.message_id += 1
        return self.message_id
    
    def _log_request(self, message: dict):
        """Log outgoing request if verbose"""
        if self.verbose:
            print("\n" + "="*60)
            print("📤 CLIENT → SERVER REQUEST:")
            print("="*60)
            print(json.dumps(message, indent=2))
            print()
    
    def _log_response(self, message: dict):
        """Log incoming response if verbose"""
        if self.verbose:
            print("\n" + "="*60)
            print("📥 SERVER → CLIENT RESPONSE:")
            print("="*60)
            print(json.dumps(message, indent=2))
            print()
    
    async def _sse_listener(self):
        """Listen for SSE messages from server"""
        try:
            async with aconnect_sse(
                self.http_client,
                "GET",
                self.sse_url
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    try:
                        data = json.loads(sse.data)
                        await self.response_queue.put(data)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            if self.verbose:
                print(f"⚠️  SSE connection closed: {e}")
    
    async def _send_request(self, method: str, params: Optional[dict] = None) -> dict:
        """Send JSON-RPC request and wait for response"""
        msg_id = self._next_id()
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": msg_id
        }
        
        self._log_request(message)
        
        # Send request
        await self.http_client.post(self.message_url, json=message)
        
        # Wait for response with matching ID
        while True:
            response = await self.response_queue.get()
            if response.get("id") == msg_id:
                self._log_response(response)
                return response
    
    async def connect(self):
        """Establish connection to server"""
        print("🔌 Connecting to MCP server...")
        print(f"   Server URL: {self.server_url}\n")
        
        # Start SSE listener
        self.sse_task = asyncio.create_task(self._sse_listener())
        await asyncio.sleep(0.5)  # Give SSE time to connect
        
        # Initialize protocol
        response = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "weather-client",
                "version": "1.0.0"
            }
        })
        
        if "result" in response:
            print("✅ Connection established")
            print(f"   Protocol version: {response['result']['protocolVersion']}")
            print(f"   Server: {response['result']['serverInfo']['name']}\n")
        else:
            raise Exception("Failed to initialize connection")
    
    async def list_tools(self) -> list[dict]:
        """List available tools from server"""
        print("📋 Discovering available tools...")
        
        response = await self._send_request("tools/list")
        
        if "result" in response:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:\n")
            
            for tool in tools:
                print(f"   • {tool['name']}")
                print(f"     {tool['description']}")
                print()
            
            return tools
        else:
            raise Exception("Failed to list tools")
    
    async def call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool on the server"""
        print(f"🔧 Calling tool: {name}")
        print(f"   Arguments: {arguments}\n")
        
        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        
        if "result" in response:
            content = response["result"]["content"][0]
            result_text = content["text"]
            print("✅ Tool execution successful\n")
            return result_text
        else:
            error = response.get("error", {})
            raise Exception(f"Tool call failed: {error.get('message', 'Unknown error')}")
    
    async def disconnect(self):
        """Close connection"""
        print("\n🔌 Disconnecting from server...")
        
        if self.sse_task:
            self.sse_task.cancel()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                pass
        
        await self.http_client.aclose()
        print("✅ Disconnected\n")


async def run_demo(verbose: bool = False):
    """Run the complete MCP weather demo"""
    
    print("\n" + "="*60)
    print("🌤️  MCP WEATHER DEMO - CLIENT")
    print("="*60)
    print("Demonstrating MCP Protocol with HTTP/SSE Transport\n")
    
    client = MCPWeatherClient(verbose=verbose)
    
    try:
        # Step 1: Connect to server
        await client.connect()
        
        # Step 2: Discover tools
        await client.list_tools()
        
        # Step 3: Get current weather
        print("-" * 60)
        print("DEMO 1: Get Current Weather")
        print("-" * 60)
        result = await client.call_tool(
            "get_current_weather",
            {"city": "London"}
        )
        print("📊 Result:")
        print(result)
        print()
        
        # Step 4: Get forecast
        print("-" * 60)
        print("DEMO 2: Get Weather Forecast")
        print("-" * 60)
        result = await client.call_tool(
            "get_forecast",
            {"city": "Tokyo", "days": 3}
        )
        print("📊 Result:")
        print(result)
        print()
        
        # Step 5: Another example
        print("-" * 60)
        print("DEMO 3: Another Current Weather Query")
        print("-" * 60)
        result = await client.call_tool(
            "get_current_weather",
            {"city": "Bengaluru"}
        )
        print("📊 Result:")
        print(result)
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
    finally:
        await client.disconnect()
    
    print("="*60)
    print("✅ Demo completed!")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="MCP Weather Client Demo")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed JSON-RPC messages"
    )
    args = parser.parse_args()
    
    asyncio.run(run_demo(verbose=args.verbose))


if __name__ == "__main__":
    main()
