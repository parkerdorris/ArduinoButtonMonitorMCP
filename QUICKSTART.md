# 🚀 Quick Start Guide

Get up and running with Arduino MCP Button Monitor in 5 minutes!

## ⚡ Super Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Upload Arduino Code
- Open `button_monitor.ino` in Arduino IDE
- Upload to your Arduino board
- Connect button: pin 2 → button → GND

### 3. Start Server
```bash
python3 mcp_websocket_server.py
```

### 4. Test Connection
```bash
python3 demo_mcp_standards.py
```

### 5. Run LLM Client (Optional)
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your_key_here"

# Run the LLM-enhanced client
python3 llm_mcp_client_standard.py
```

## 🔧 What Each Component Does

| Component | Purpose | Required? |
|-----------|---------|-----------|
| `mcp_websocket_server.py` | MCP server + Arduino communication | ✅ Yes |
| `button_monitor.ino` | Arduino button monitoring code | ✅ Yes |
| `mcp_websocket_client.py` | Basic MCP client library | ✅ Yes |
| `llm_mcp_client_standard.py` | LLM-enhanced monitoring | ❌ Optional |
| `demo_mcp_standards.py` | Basic functionality test | ❌ Optional |

## 🎯 Expected Output

### Server Starting
```
INFO: Starting MCP WebSocket Server on 0.0.0.0:5001
INFO: Started server process [12345]
INFO: Uvicorn running on http://0.0.0.0:5001
```

### Basic Demo
```
🚀 Simple MCP WebSocket Demo
========================================
🔌 Connecting to MCP server...
📋 Listing servers...
✅ Servers: {'servers': [{'name': 'arduino-button-monitor'}]}
🔧 Listing tools...
✅ Tools: {'tools': [{'name': 'get_button_state'}, ...]}
✅ Demo completed successfully!
```

### LLM Client
```
🚀 Starting LLM-Enhanced Arduino Pin Monitor (MCP Standard)
============================================================
🤖 I'll narrate all pin events and provide intelligent commentary
📡 Monitoring will continue automatically - no user input needed
⏱️  Running for 300 seconds (or until interrupted)
============================================================

🔌 Connecting to MCP WebSocket server...
📡 Subscribing to pin edge events...
✅ Monitoring started! Pin events will be narrated automatically...
🎯 Toggle the button pin to see real-time narration!
============================================================

📡 [MCP] Received button event: RISING at 14:30:15.123
   State: 1 | Description: Button rising
🤖 At 14:30:15, the button was pressed, activating the input.
```

## 🚨 Troubleshooting

### Arduino Not Detected?
```bash
# Check available ports
python3 -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"

# Restart server after connecting Arduino
```

### Port Already in Use?
```bash
# Kill existing processes
pkill -f "python3 mcp_websocket_server.py"

# Or use different port
python3 mcp_websocket_server.py --port 5002
```

### LLM Not Working?
```bash
# Check API key
echo $OPENAI_API_KEY

# Test OpenAI connection
python3 -c "import openai; print('API key valid')"
```

## 🔍 Next Steps

1. **Customize the Arduino code** - Add more sensors, change pin assignments
2. **Extend the MCP server** - Add new tools and capabilities
3. **Build your own client** - Use the MCP client library for custom applications
4. **Integrate with other systems** - Connect to databases, web services, etc.

## 📚 Learn More

- **MCP Standard**: [Anthropic's MCP Documentation](https://modelcontextprotocol.io/)
- **Arduino**: [Arduino Getting Started Guide](https://www.arduino.cc/en/Guide)
- **WebSockets**: [MDN WebSocket Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

---

**Need help? Check the main README.md or open an issue! 🆘**
