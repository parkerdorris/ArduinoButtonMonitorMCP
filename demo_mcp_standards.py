#!/usr/bin/env python3
"""
Simple MCP WebSocket Demo

This script demonstrates the basic MCP WebSocket client functionality
without requiring an OpenAI API key.
"""

import asyncio
import logging
from mcp_websocket_client import MCPWebSocketClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run a simple MCP demo."""
    print("🚀 Simple MCP WebSocket Demo")
    print("=" * 40)
    
    client = MCPWebSocketClient()
    
    try:
        # Connect to server
        print("🔌 Connecting to MCP server...")
        if not await client.connect():
            print("❌ Failed to connect")
            return
        
        # List servers
        print("\n📋 Listing servers...")
        servers = await client.list_servers()
        print(f"✅ Servers: {servers}")
        
        # List tools
        print("\n🔧 Listing tools...")
        tools = await client.list_tools()
        print(f"✅ Tools: {tools}")
        
        print("\n✅ Demo completed successfully!")
        print("💡 Run 'python3 llm_mcp_client_standard.py' for the full LLM experience")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
