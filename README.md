# Arduino MCP Button Monitor

A real-time Arduino button monitoring system using the **Model Context Protocol (MCP)** standard with WebSocket transport and optional LLM-powered intelligent narration.

## 🚀 Features

- **MCP Standard Compliant** - Follows Anthropic's Model Context Protocol specification
- **WebSocket Transport** - Real-time bidirectional communication
- **Arduino Integration** - Automatic port detection and serial communication
- **LLM Enhancement** - GPT-4o powered intelligent event narration
- **Real-time Events** - Instant button press/release detection and streaming
- **Cross-platform** - Works on Windows, macOS, and Linux

## 🏗️ Architecture

```
Arduino (button_monitor.ino)
    ↓ Serial Communication
MCP WebSocket Server (mcp_websocket_server.py)
    ↓ WebSocket MCP Protocol
MCP WebSocket Client (mcp_websocket_client.py)
    ↓ Optional LLM Integration
LLM MCP Client (llm_mcp_client_standard.py)
```

## 📋 Requirements

### Hardware
- Arduino board (Arduino Uno, MKR WiFi 1010, etc.)
- Push button
- Breadboard and jumper wires
- USB cable

### Software
- Python 3.8+
- Arduino IDE
- OpenAI API key (for LLM features)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ArduinoMCP
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

## 🔌 Hardware Setup

1. **Connect the button to Arduino:**
   - Button pin 1 → Arduino pin 2
   - Button pin 2 → Arduino GND
   - Arduino pin 2 has internal pull-up resistor enabled

2. **Upload the Arduino sketch:**
   - Open `button_monitor.ino` in Arduino IDE
   - Select your board and port
   - Upload the sketch

## 🚀 Quick Start

### 1. Start the MCP Server
```bash
python3 mcp_websocket_server.py
```
The server will start on `http://localhost:5001` and automatically detect your Arduino.

### 2. Test Basic MCP Functionality
```bash
python3 demo_mcp_standards.py
```
This tests the basic MCP connection without requiring an OpenAI API key.

### 3. Run the LLM-Enhanced Client
```bash
python3 llm_mcp_client_standard.py
```
This provides intelligent narration of button events using GPT-4o.

## 📚 Usage Examples

### Basic MCP Client
```python
from mcp_websocket_client import MCPWebSocketClient

async def main():
    client = MCPWebSocketClient()
    
    # Connect to server
    await client.connect()
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {tools}")
    
    # Connect to Arduino
    result = await client.connect_arduino()
    print(f"Arduino connection: {result}")
    
    # Get button state
    state = await client.get_button_state()
    print(f"Button state: {state}")
    
    await client.disconnect()

asyncio.run(main())
```

### LLM-Enhanced Monitoring
```python
from llm_mcp_client_standard import LLMMCPClient

async def main():
    client = LLMMCPClient()
    await client.start_monitoring(duration=300)  # 5 minutes

asyncio.run(main())
```

## 🔧 MCP Protocol Methods

The server implements the following MCP standard methods:

- **`mcp/servers/list`** - List available servers
- **`mcp/servers/read`** - Read server information
- **`mcp/tools/list`** - List available tools
- **`mcp/tools/call`** - Call tools with arguments
- **`mcp/tools/subscribe`** - Subscribe to tool updates
- **`mcp/notifications/subscribe`** - Subscribe to notifications

### Available Tools

- **`get_button_state`** - Get current button state (0 or 1)
- **`subscribe_button_edges`** - Subscribe to button edge events
- **`connect_arduino`** - Connect to Arduino (auto-detects port)
- **`disconnect_arduino`** - Disconnect from Arduino

## 📡 Real-time Events

Button events are streamed in real-time via MCP notifications:

```json
{
  "jsonrpc": "2.0",
  "method": "button_event",
  "params": {
    "event": "RISING",
    "timestamp": 1755367431.522897
  }
}
```

- **`RISING`** - Button pressed (state changes from 0 to 1)
- **`FALLING`** - Button released (state changes from 1 to 0)

## 🧪 Testing

### Test MCP Compliance
```bash
python3 test_mcp_protocol_compliance.py
```

### Test Basic Functionality
```bash
python3 mcp_websocket_client.py
```

## 🔍 Troubleshooting

### Common Issues

1. **Arduino not detected**
   - Check USB connection
   - Verify Arduino IDE port selection
   - Restart the server

2. **Connection refused**
   - Ensure server is running on port 5001
   - Check firewall settings

3. **LLM narration fails**
   - Verify `OPENAI_API_KEY` is set
   - Check internet connection
   - Verify API key has sufficient credits

### Debug Mode
Enable detailed logging by modifying the logging level in any Python file:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📖 API Reference

### MCPWebSocketClient
- `connect()` - Connect to MCP server
- `disconnect()` - Disconnect from server
- `list_servers()` - List available servers
- `list_tools()` - List available tools
- `call_tool(name, arguments)` - Call a specific tool
- `subscribe_to_tool(name)` - Subscribe to tool updates
- `get_button_state()` - Get current button state
- `connect_arduino(port)` - Connect to Arduino

### LLMMCPClient
- `start_monitoring(duration)` - Start monitoring with LLM narration
- `connect()` - Connect to MCP server and Arduino
- `subscribe_to_events()` - Subscribe to button events


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
