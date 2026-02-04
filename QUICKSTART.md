# Quick Start Guide

## Setup (5 minutes)

### Terminal 1 - Server
```bash
cd server
pip install -r requirements.txt
python weather_server.py
```

### Terminal 2 - Client
```bash
cd client
pip install -r requirements.txt

# Normal mode
python weather_client.py

# Verbose mode (shows JSON-RPC)
python weather_client.py --verbose
```

## Demo Flow

1. **Server starts** → Listens on port 8000
2. **Client connects** → Establishes SSE connection
3. **Initialize** → Protocol handshake
4. **Discover tools** → Lists weather APIs
5. **Execute tools** → 3 weather queries
6. **Disconnect** → Clean shutdown

## Key Files

- `server/weather_server.py` - MCP server (200 lines)
- `client/weather_client.py` - MCP client (220 lines)
- `README.md` - Full documentation

## Presentation Tips

1. Start server first, show it waiting
2. Run client in verbose mode to show protocol
3. Point out JSON-RPC structure
4. Highlight separation of concerns
5. Emphasize production-ready pattern

## Common Issues

- **Port conflict**: Kill process on 8000 or change port
- **Connection refused**: Server must run first
- **No internet**: Need connection for wttr.in API
