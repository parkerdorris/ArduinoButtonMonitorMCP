#!/usr/bin/env python3
"""
MCP Button Monitor WebSocket Server

This server implements the MCP (Model Context Protocol) server for the button monitor project
using WebSocket transport as specified in the MCP standard.

MCP Methods:
- mcp/servers/list: Lists available servers
- mcp/servers/read: Reads server information
- mcp/tools/list: Lists available tools
- mcp/tools/call: Calls tools
- mcp/tools/subscribe: Subscribes to tool updates
- mcp/notifications/subscribe: Subscribes to notifications
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, Set, List
from websockets.exceptions import ConnectionClosed
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# Import our Arduino connection manager
from mcp_server import ArduinoConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPWebSocketServer:
    """WebSocket-based MCP server for button monitoring."""
    
    def __init__(self):
        self.arduino_manager = ArduinoConnectionManager()
        self.active_connections: Set[WebSocket] = set()
        self.tool_subscriptions: Dict[str, Set[WebSocket]] = {}
        self.notification_subscriptions: Set[WebSocket] = set()
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Create FastAPI app for WebSocket support
        self.app = FastAPI(
            title="MCP Button Monitor WebSocket Server",
            description="WebSocket MCP server for Arduino button monitoring",
            version="1.0.0"
        )
        
        # Setup routes
        self._setup_routes()
        
        # Initialize monitoring task
        self.monitoring_task = None
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server information."""
            return {
                "name": "MCP Button Monitor WebSocket Server",
                "version": "1.0.0",
                "transport": "WebSocket",
                "endpoint": "/ws",
                "mcp_version": "1.0.0"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "arduino_connected": self.arduino_manager.connected,
                "arduino_port": self.arduino_manager.port_name,
                "active_connections": len(self.active_connections),
                "timestamp": time.time()
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Main WebSocket endpoint for MCP protocol."""
            await websocket.accept()
            self.active_connections.add(websocket)
            
            try:
                await self._handle_mcp_connection(websocket)
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.active_connections.discard(websocket)
                # Remove from all subscriptions
                for tool_name, subscribers in self.tool_subscriptions.items():
                    subscribers.discard(websocket)
                self.notification_subscriptions.discard(websocket)
    
    async def _handle_mcp_connection(self, websocket: WebSocket):
        """Handle MCP protocol messages over WebSocket."""
        try:
            async for message in websocket.iter_text():
                try:
                    data = json.loads(message)
                    await self._process_mcp_message(websocket, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON", "parse_error")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self._send_error(websocket, str(e), "internal_error")
        except ConnectionClosed:
            logger.info("WebSocket connection closed")
    
    async def _process_mcp_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Process MCP protocol messages."""
        method = message.get("method")
        params = message.get("params", {})
        message_id = message.get("id")
        
        logger.info(f"🔍 Processing MCP message: {method} with id: {message_id}")
        
        if not method:
            await self._send_error(websocket, "Missing method", "invalid_request", message_id)
            return
        
        # Handle MCP protocol methods
        if method == "mcp/servers/list":
            logger.info("📋 Calling _handle_servers_list")
            await self._handle_servers_list(websocket, message_id)
        elif method == "mcp/servers/read":
            logger.info("📋 Calling _handle_servers_read")
            await self._handle_servers_read(websocket, params, message_id)
        elif method == "mcp/tools/list":
            logger.info("📋 Calling _handle_tools_list")
            await self._handle_tools_list(websocket, message_id)
        elif method == "mcp/tools/call":
            logger.info("📋 Calling _handle_tools_call")
            await self._handle_tools_call(websocket, params, message_id)
        elif method == "mcp/tools/subscribe":
            logger.info("📋 Calling _handle_tools_subscribe")
            await self._handle_tools_subscribe(websocket, params, message_id)
        elif method == "mcp/notifications/subscribe":
            logger.info("📋 Calling _handle_notifications_subscribe")
            await self._handle_notifications_subscribe(websocket, message_id)
        else:
            logger.warning(f"⚠️ Unknown method: {method}")
            await self._send_error(websocket, f"Unknown method: {method}", "method_not_found", message_id)
    
    async def _handle_servers_list(self, websocket: WebSocket, message_id: Optional[str]):
        """Handle mcp/servers/list request."""
        logger.info(f"🔍 _handle_servers_list called with message_id: {message_id}")
        
        response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "servers": [
                    {
                        "name": "arduino-button-monitor",
                        "description": "MCP server for monitoring Arduino button state and events",
                        "transport": "websocket"
                    }
                ]
            }
        }
        
        logger.info(f"📤 Sending response: {json.dumps(response)}")
        await websocket.send_text(json.dumps(response))
        logger.info("✅ Response sent successfully")
    
    async def _handle_servers_read(self, websocket: WebSocket, params: Dict[str, Any], message_id: Optional[str]):
        """Handle mcp/servers/read request."""
        server_name = params.get("name")
        
        if server_name != "arduino-button-monitor":
            await self._send_error(websocket, f"Server not found: {server_name}", "server_not_found", message_id)
            return
        
        response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "name": "arduino-button-monitor",
                "description": "MCP server for monitoring Arduino button state and events",
                "transport": "websocket",
                "version": "1.0.0"
            }
        }
        await websocket.send_text(json.dumps(response))
    
    async def _handle_tools_list(self, websocket: WebSocket, message_id: Optional[str]):
        """Handle mcp/tools/list request."""
        tools = [
            {
                "name": "get_button_state",
                "description": "Get the current state of the button (0 or 1)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "subscribe_button_edges",
                "description": "Subscribe to button edge events (RISING/FALLING)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "connect_arduino",
                "description": "Connect to Arduino on specified or auto-detected port",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "string",
                            "description": "Serial port name (optional, will auto-detect if not specified)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "disconnect_arduino",
                "description": "Disconnect from Arduino",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {"tools": tools}
        }
        await websocket.send_text(json.dumps(response))
    
    async def _handle_tools_call(self, websocket: WebSocket, params: Dict[str, Any], message_id: Optional[str]):
        """Handle mcp/tools/call request."""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        try:
            if tool_name == "get_button_state":
                result = await self._call_get_button_state()
            elif tool_name == "subscribe_button_edges":
                result = await self._call_subscribe_button_edges(websocket)
            elif tool_name == "connect_arduino":
                result = await self._call_connect_arduino(tool_params)
            elif tool_name == "disconnect_arduino":
                result = await self._call_disconnect_arduino()
            else:
                await self._send_error(websocket, f"Unknown tool: {tool_name}", "tool_not_found", message_id)
                return
            
            # Send success response
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": result
            }
            await websocket.send_text(json.dumps(response))
            
        except Exception as e:
            await self._send_error(websocket, str(e), "tool_execution_error", message_id)
    
    async def _handle_tools_subscribe(self, websocket: WebSocket, params: Dict[str, Any], message_id: Optional[str]):
        """Handle mcp/tools/subscribe request."""
        tool_name = params.get("name")
        
        logger.info(f"🔔 Tool subscription request: {tool_name} from WebSocket {id(websocket)}")
        
        if tool_name not in ["get_button_state", "subscribe_button_edges"]:
            await self._send_error(websocket, f"Cannot subscribe to tool: {tool_name}", "invalid_subscription", message_id)
            return
        
        # Add to tool subscriptions
        if tool_name not in self.tool_subscriptions:
            self.tool_subscriptions[tool_name] = set()
        self.tool_subscriptions[tool_name].add(websocket)
        
        logger.info(f"✅ WebSocket {id(websocket)} subscribed to tool: {tool_name}")
        logger.info(f"📊 Current subscriptions for {tool_name}: {len(self.tool_subscriptions[tool_name])}")
        
        response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {"subscribed": True}
        }
        await websocket.send_text(json.dumps(response))
    
    async def _handle_notifications_subscribe(self, websocket: WebSocket, message_id: Optional[str]):
        """Handle mcp/notifications/subscribe request."""
        self.notification_subscriptions.add(websocket)
        
        response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {"subscribed": True}
        }
        await websocket.send_text(json.dumps(response))
    
    async def _call_get_button_state(self) -> Dict[str, Any]:
        """Call the get_button_state tool."""
        if not self.arduino_manager.connected:
            raise Exception("Arduino not connected. Use connect_arduino first.")
        
        if not self.arduino_manager.check_connection_health():
            raise Exception("Arduino connection lost")
        
        if self.arduino_manager.send_command("STATE"):
            response = self.arduino_manager.read_response()
            
            if response and response.isdigit():
                state = int(response)
                return {
                    "state": state,
                    "timestamp": time.time()
                }
            else:
                raise Exception(f"Invalid response from Arduino: {response}")
        else:
            raise Exception("Failed to send command to Arduino")
    
    async def _call_subscribe_button_edges(self, websocket: WebSocket) -> Dict[str, Any]:
        """Call the subscribe_button_edges tool."""
        if not self.arduino_manager.connected:
            raise Exception("Arduino not connected. Use connect_arduino first.")
        
        if self.arduino_manager.send_command("SUBSCRIBE"):
            response = self.arduino_manager.read_response()
            
            if response == "OK":
                # Add this WebSocket to button event subscriptions
                if "subscribe_button_edges" not in self.tool_subscriptions:
                    self.tool_subscriptions["subscribe_button_edges"] = set()
                self.tool_subscriptions["subscribe_button_edges"].add(websocket)
                
                # Start monitoring if not already started
                if not self.monitoring_task or self.monitoring_task.done():
                    self.monitoring_task = asyncio.create_task(self._monitor_arduino_events())
                
                logger.info(f"✅ WebSocket {id(websocket)} subscribed to button events")
                
                return {
                    "subscribed": True,
                    "message": "Subscribed to button edge events"
                }
            else:
                raise Exception(f"Failed to subscribe to button events: {response}")
        else:
            raise Exception("Failed to send subscribe command to Arduino")
    
    async def _call_connect_arduino(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call the connect_arduino tool."""
        port = params.get("port")
        
        if self.arduino_manager.connect(port):
            return {
                "connected": True,
                "message": f"Connected to Arduino on {self.arduino_manager.port_name}",
                "port": self.arduino_manager.port_name
            }
        else:
            raise Exception("Failed to connect to Arduino")
    
    async def _call_disconnect_arduino(self) -> Dict[str, Any]:
        """Call the disconnect_arduino tool."""
        self.arduino_manager.disconnect()
        return {
            "disconnected": True,
            "message": "Disconnected from Arduino"
        }
    
    async def _send_error(self, websocket: WebSocket, message: str, code: str, message_id: Optional[str] = None):
        """Send an error response."""
        error_response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {
                "code": -32000,
                "message": message,
                "data": {
                    "code": code
                }
            }
        }
        await websocket.send_text(json.dumps(error_response))
    
    async def _monitor_arduino_events(self):
        """Monitor Arduino for button events and send notifications."""
        logger.info("Starting Arduino event monitoring")
        
        try:
            while True:
                if not self.arduino_manager.connected:
                    await asyncio.sleep(1)
                    continue
                
                # Check if we have any subscribers
                if not self.tool_subscriptions.get("subscribe_button_edges"):
                    await asyncio.sleep(1)
                    continue
                
                # Read all available serial data
                while self.arduino_manager.serial_port and self.arduino_manager.serial_port.in_waiting > 0:
                    try:
                        line = self.arduino_manager.serial_port.readline().decode().strip()
                        if line in ["RISING", "FALLING"]:
                            await self._notify_button_event(line)
                    except Exception as e:
                        logger.error(f"Error reading Arduino event: {e}")
                
                await asyncio.sleep(0.05)  # Check every 50ms
                
        except asyncio.CancelledError:
            logger.info("Arduino event monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in Arduino event monitoring: {e}")
    
    async def _notify_button_event(self, event_type: str):
        """Notify subscribers of button events."""
        notification = {
            "jsonrpc": "2.0",
            "method": "button_event",
            "params": {
                "event": event_type,
                "timestamp": time.time()
            }
        }
        
        logger.info(f"🔔 Sending button event notification: {event_type}")
        
        # Notify tool subscribers
        if "subscribe_button_edges" in self.tool_subscriptions:
            subscriber_count = len(self.tool_subscriptions["subscribe_button_edges"])
            logger.info(f"📡 Notifying {subscriber_count} tool subscribers")
            for websocket in self.tool_subscriptions["subscribe_button_edges"]:
                try:
                    await websocket.send_text(json.dumps(notification))
                    logger.debug(f"✅ Notification sent to tool subscriber {id(websocket)}")
                except Exception as e:
                    logger.error(f"❌ Failed to send notification to tool subscriber: {e}")
        else:
            logger.warning("⚠️ No tool subscribers for button events")
    
    async def start(self, host: str = "0.0.0.0", port: int = 5001):
        """Start the MCP WebSocket server."""
        logger.info(f"Starting MCP WebSocket Server on {host}:{port}")
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """Main entry point."""
    server = MCPWebSocketServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
