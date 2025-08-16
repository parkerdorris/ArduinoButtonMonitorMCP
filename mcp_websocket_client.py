#!/usr/bin/env python3
"""
MCP Button Monitor WebSocket Client

This client connects to the MCP Button Monitor WebSocket server and follows
the official MCP protocol specification for tool calls and subscriptions.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Callable
import websockets
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPWebSocketClient:
    """WebSocket-based MCP client for button monitoring."""
    
    def __init__(self, server_url: str = "ws://localhost:5001/ws"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.message_id_counter = 0
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.event_handlers: Dict[str, Callable] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> bool:
        """Connect to the MCP WebSocket server."""
        try:
            logger.info(f"🔌 Connecting to MCP WebSocket server at {self.server_url}")
            
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            
            # Start message handling
            self.monitoring_task = asyncio.create_task(self._handle_messages())
            
            logger.info("✅ Connected to MCP WebSocket server successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP WebSocket server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP WebSocket server."""
        try:
            self.connected = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            logger.info("🔌 Disconnected from MCP WebSocket server")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def _get_next_id(self) -> str:
        """Get the next message ID."""
        self.message_id_counter += 1
        return str(self.message_id_counter)
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request and wait for response."""
        if not self.connected or not self.websocket:
            raise Exception("Not connected to server")
        
        message_id = self._get_next_id()
        request = {
            "jsonrpc": "2.0",
            "id": message_id,
            "method": method,
            "params": params or {}
        }
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[message_id] = future
        
        try:
            await self.websocket.send(json.dumps(request))
            response = await asyncio.wait_for(future, timeout=10.0)
            return response
        finally:
            self.pending_requests.pop(message_id, None)
    
    async def _handle_messages(self):
        """Handle incoming messages from the server."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in message handling: {e}")
        finally:
            self.connected = False
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process incoming messages."""
        if "id" in message:
            # This is a response to a request
            message_id = message["id"]
            if message_id in self.pending_requests:
                future = self.pending_requests[message_id]
                if not future.done():
                    if "error" in message:
                        future.set_exception(Exception(message["error"]["message"]))
                    else:
                        future.set_result(message.get("result"))
        elif "method" in message:
            # This is a notification
            await self._handle_notification(message)
    
    async def _handle_notification(self, notification: Dict[str, Any]):
        """Handle incoming notifications."""
        method = notification.get("method")
        params = notification.get("params", {})
        
        # Log ALL notifications received for debugging
        logger.info(f"🔔 Received notification: {method} with params: {params}")
        
        if method == "button_event":
            event_type = params.get("event")
            timestamp = params.get("timestamp")
            logger.info(f"📡 Button event: {event_type} at {timestamp}")
            
            # Call event handler if registered
            if "button_event" in self.event_handlers:
                try:
                    logger.info(f"🎯 Calling button event handler for: {event_type}")
                    await self.event_handlers["button_event"](event_type, timestamp)
                    logger.info(f"✅ Button event handler completed for: {event_type}")
                except Exception as e:
                    logger.error(f"❌ Error in button event handler: {e}")
            else:
                logger.warning(f"⚠️ No button event handler registered for: {event_type}")
        
        elif method == "arduino_connection_lost":
            message = params.get("message")
            logger.warning(f"⚠️ Arduino connection lost: {message}")
            
            # Call connection lost handler if registered
            if "connection_lost" in self.event_handlers:
                try:
                    await self.event_handlers["connection_lost"](message)
                except Exception as e:
                    logger.error(f"Error in connection lost handler: {e}")
        else:
            logger.info(f"📝 Unhandled notification method: {method}")
    
    async def list_servers(self) -> Dict[str, Any]:
        """List available MCP servers."""
        return await self._send_request("mcp/servers/list")
    
    async def read_server(self, server_name: str) -> Dict[str, Any]:
        """Read information about a specific server."""
        return await self._send_request("mcp/servers/read", {"name": server_name})
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return await self._send_request("mcp/tools/list")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool."""
        return await self._send_request("mcp/tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
    
    async def subscribe_to_tool(self, tool_name: str) -> Dict[str, Any]:
        """Subscribe to tool updates."""
        return await self._send_request("mcp/tools/subscribe", {"name": tool_name})
    
    async def subscribe_to_notifications(self) -> Dict[str, Any]:
        """Subscribe to general notifications."""
        return await self._send_request("mcp/notifications/subscribe")
    
    async def connect_arduino(self, port: Optional[str] = None) -> Dict[str, Any]:
        """Connect to Arduino."""
        params = {}
        if port:
            params["port"] = port
        
        return await self.call_tool("connect_arduino", params)
    
    async def disconnect_arduino(self) -> Dict[str, Any]:
        """Disconnect from Arduino."""
        return await self.call_tool("disconnect_arduino")
    
    async def get_button_state(self) -> Dict[str, Any]:
        """Get current button state."""
        return await self.call_tool("get_button_state")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register a handler for specific event types."""
        self.event_handlers[event_type] = handler
        logger.info(f"Registered event handler for: {event_type}")
    
    async def run_demo(self, duration: int = 300):
        """Run a demo of the MCP WebSocket client."""
        try:
            print("🚀 Starting MCP WebSocket Client Demo")
            print("=" * 50)
            print(f"⏱️  Running for {duration} seconds (or until interrupted)")
            print("=" * 50)
            
            # Connect to server
            print("\n🔌 Connecting to MCP WebSocket server...")
            if not await self.connect():
                print("❌ Failed to connect to server. Demo cannot continue.")
                return
            
            # List servers
            print("\n📋 Listing available servers...")
            servers = await self.list_servers()
            print(f"✅ Found servers: {servers}")
            
            # Read server info
            print("\n📖 Reading server information...")
            server_info = await self.read_server("arduino-button-monitor")
            print(f"✅ Server info: {server_info}")
            
            # List tools
            print("\n🔧 Listing available tools...")
            tools = await self.list_tools()
            print(f"✅ Available tools: {tools}")
            
            # Connect to Arduino
            print("\n🔌 Connecting to Arduino...")
            arduino_result = await self.connect_arduino()
            print(f"✅ Arduino connection: {arduino_result}")
            
            # Subscribe to button events
            print("\n📡 Subscribing to button events...")
            # First call the subscribe_button_edges tool to enable Arduino streaming
            subscribe_result = await self.call_tool("subscribe_button_edges")
            print(f"✅ Button events enabled: {subscribe_result}")
            
            # Subscribe to notifications
            print("\n🔔 Subscribing to notifications...")
            notify_result = await self.subscribe_to_notifications()
            print(f"✅ Notifications subscription: {notify_result}")
            
            # Get initial button state
            print("\n📊 Getting initial button state...")
            try:
                state_result = await self.get_button_state()
                print(f"✅ Initial button state: {state_result}")
            except Exception as e:
                print(f"⚠️ Could not get initial state: {e}")
            
            print("\n🎯 Monitoring button events... (toggle the button to see events!)")
            print("=" * 50)
            
            # Monitor for events
            start_time = time.time()
            while time.time() - start_time < duration and self.connected:
                await asyncio.sleep(1)
                
                # Provide periodic status updates
                if int(time.time() - start_time) % 30 == 0:  # Every 30 seconds
                    elapsed = int(time.time() - start_time)
                    remaining = duration - elapsed
                    print(f"\n⏰ Demo status: {elapsed}s elapsed, {remaining}s remaining")
                    
                    # Get current button state
                    try:
                        state_result = await self.get_button_state()
                        current_state = state_result.get("state", "unknown")
                        print(f"📊 Current button state: {current_state}")
                    except Exception as e:
                        print(f"⚠️ Could not get current state: {e}")
            
            print("\n🏁 Demo completed!")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.disconnect()

async def main():
    """Main entry point for the MCP WebSocket client demo."""
    try:
        client = MCPWebSocketClient()
        await client.run_demo(duration=300)  # 5 minutes
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
