#!/usr/bin/env python3
"""
LLM-Enhanced Arduino Button Monitor (MCP Standard)

This client connects to the MCP WebSocket server and provides intelligent narration
of button events using OpenAI's GPT-4o model. It follows the MCP standard protocol.

Features:
- Real-time button event monitoring via MCP WebSocket
- Intelligent event narration using GPT-4o
- Automatic Arduino connection and management
- Conversation context tracking
- Simple, clean output format
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Import our MCP WebSocket client
from mcp_websocket_client import MCPWebSocketClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ButtonEvent:
    """Represents a button event."""
    timestamp: datetime
    event_type: str
    button_state: int
    description: str

class ConversationContext:
    """Manages conversation context for the LLM."""
    
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.events: List[ButtonEvent] = []
        self.max_context_length = 20
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append({"role": role, "content": content})
        
        # Keep context manageable
        if len(self.messages) > self.max_context_length:
            self.messages = self.messages[-self.max_context_length:]
    
    def add_event(self, event: ButtonEvent):
        """Add a button event to the context."""
        self.events.append(event)
        
        # Keep recent events
        if len(self.events) > 10:
            self.events = self.events[-10:]
    
    def get_context_summary(self) -> str:
        """Get a summary of recent button events for context."""
        if not self.events:
            return "No button events recorded yet."
        
        recent_events = self.events[-5:]  # Last 5 events
        summary = "Recent button events:\n"
        
        for event in recent_events:
            time_str = event.timestamp.strftime("%H:%M:%S")
            summary += f"- {time_str}: {event.event_type} (state: {event.button_state})\n"
        
        return summary

class LLMMCPClient:
    """LLM-enhanced MCP client for intelligent button monitoring."""
    
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.openai_client = AsyncOpenAI(api_key=api_key)
        
        # Initialize MCP client
        self.mcp_client = MCPWebSocketClient()
        
        # Initialize conversation context
        self.conversation_context = ConversationContext()
        
        # Monitoring state
        self.monitoring_active = False
        
        # Register event handlers
        self.mcp_client.register_event_handler("button_event", self._handle_button_event)
        self.mcp_client.register_event_handler("connection_lost", self._handle_connection_lost)
    
    async def _handle_button_event(self, event_type: str, timestamp: float):
        """Handle button events from the MCP server."""
        try:
            # Create button event object
            event = ButtonEvent(
                timestamp=datetime.fromtimestamp(timestamp),
                event_type=event_type,
                button_state=1 if event_type == "RISING" else 0,
                description=f"Button {event_type.lower()}"
            )
            
            # Add to conversation context
            self.conversation_context.add_event(event)
            
            # Show raw event - THIS MUST ALWAYS APPEAR
            print(f"\n📡 [MCP] Received button event: {event_type} at {datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3]}")
            print(f"   State: {event.button_state} | Description: {event.description}")
            
            # Provide simple LLM narration (just 1-2 lines)
            try:
                await self._narrate_event_simple(event)
            except Exception as e:
                print(f"⚠️ LLM narration failed, but event was captured: {e}")
                # Fallback narration if LLM fails
                if event.event_type == "RISING":
                    print(f"🤖 Button pressed (HIGH)")
                else:
                    print(f"🤖 Button released (LOW)")
                
        except Exception as e:
            # Even if event handling fails, we MUST show the event was received
            print(f"\n❌ [ERROR] Failed to handle button event {event_type} at {datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3]}: {e}")
            logger.error(f"Error handling button event: {e}")
    
    async def _handle_connection_lost(self, message: str):
        """Handle Arduino connection lost notification."""
        print(f"⚠️ [MCP] Arduino connection lost: {message}")
        logger.warning(f"Arduino connection lost: {message}")
    
    async def connect(self) -> bool:
        """Connect to the MCP WebSocket server."""
        try:
            logger.info("🔌 Connecting to MCP WebSocket server...")
            
            if not await self.mcp_client.connect():
                logger.error("Failed to connect to MCP WebSocket server")
                return False
            
            # List available tools
            tools = await self.mcp_client.list_tools()
            logger.info(f"Available tools: {tools}")
            
            # Connect to Arduino through MCP
            arduino_result = await self.mcp_client.connect_arduino()
            logger.info(f"Arduino connection: {arduino_result}")
            
            # Get initial button state
            await self._get_initial_state()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP WebSocket server: {e}")
            return False
    
    async def _get_initial_state(self):
        """Get initial button state from the MCP server."""
        try:
            state_result = await self.mcp_client.get_button_state()
            initial_state = state_result.get('state', 0)
            initial_event = ButtonEvent(
                timestamp=datetime.now(),
                event_type='STATE_CHANGE',
                button_state=initial_state,
                description=f"Initial button state: {initial_state}"
            )
            
            self.conversation_context.add_event(initial_event)
            logger.info(f"📊 Initial button state: {initial_state}")
                
        except Exception as e:
            logger.error(f"Failed to get initial button state: {e}")
    
    async def subscribe_to_events(self) -> bool:
        """Subscribe to button edge events through MCP."""
        try:
            logger.info("📡 Subscribing to button edge events...")
            
            # First call the subscribe_button_edges tool to enable Arduino streaming
            # This also automatically subscribes the WebSocket to button event notifications
            subscribe_result = await self.mcp_client.call_tool("subscribe_button_edges")
            logger.info(f"Button events enabled: {subscribe_result}")
            
            # Note: We don't need to subscribe to general notifications since button events
            # are already being sent to tool subscribers. This prevents duplicate events.
            
            self.monitoring_active = True
            logger.info("✅ Successfully subscribed to button edge events")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            return False
    
    async def _narrate_event_simple(self, event: ButtonEvent):
        """Use LLM to provide simple, brief narration of a button event."""
        try:
            # Simple prompt for brief narration
            narration_prompt = f"""Briefly describe this button event in 1-2 lines:

Event: {event.event_type} at {event.timestamp.strftime('%H:%M:%S')}
State: {event.button_state}

Keep it conversational but very brief."""

            # Get LLM narration
            narration = await self._query_llm(narration_prompt, auto_analysis=True)
            if narration:
                print(f"🤖 {narration}")
            else:
                # Fallback narration if LLM fails
                if event.event_type == "RISING":
                    print(f"🤖 Button pressed (HIGH)")
                else:
                    print(f"🤖 Button released (LOW)")
                    
        except Exception as e:
            print(f"⚠️ LLM narration failed: {e}")
            # Fallback narration
            if event.event_type == "RISING":
                print(f"🤖 Button pressed (HIGH)")
            else:
                print(f"🤖 Button released (LOW)")
    
    async def _query_llm(self, prompt: str, auto_analysis: bool = False) -> Optional[str]:
        """Query the LLM with the given prompt."""
        try:
            # Add user message to context
            self.conversation_context.add_message("user", prompt)
            
            # Prepare messages for OpenAI API
            messages = self.conversation_context.messages.copy()
            
            # Add button context if this is a user query
            if not auto_analysis:
                context_summary = self.conversation_context.get_context_summary()
                context_message = f"Current button monitoring context:\n{context_summary}"
                messages.append({"role": "user", "content": context_message})
            
            # Call OpenAI API - handle both sync and async versions
            try:
                # Try async call first (newer openai library)
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7
                )
            except TypeError:
                # Fallback to sync call wrapped in thread (older openai library)
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7
                )
            
            # Extract response
            llm_response = response.choices[0].message.content
            
            if llm_response:
                # Add assistant response to context
                self.conversation_context.add_message("assistant", llm_response)
                
                if not auto_analysis:
                    logger.info(f"🤖 LLM Response: {llm_response}")
                
                return llm_response
            
            return None
            
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return None
    
    async def start_monitoring(self, duration: int = 300):
        """Start monitoring button events with LLM narration."""
        try:
            print("🚀 Starting LLM-Enhanced Arduino Pin Monitor (MCP Standard)")
            print("=" * 60)
            print("🤖 I'll narrate all pin events and provide intelligent commentary")
            print("📡 Monitoring will continue automatically - no user input needed")
            print(f"⏱️  Running for {duration} seconds (or until interrupted)")
            print("=" * 60)
            
            # Connect to server
            print("\n🔌 Connecting to MCP WebSocket server...")
            if not await self.connect():
                print("❌ Failed to connect to server. Monitoring cannot continue.")
                return
            
            # Subscribe to events
            print("\n📡 Subscribing to pin edge events...")
            if not await self.subscribe_to_events():
                print("❌ Failed to subscribe to events. Monitoring cannot continue.")
                return
            
            print("✅ Monitoring started! Pin events will be narrated automatically...")
            print("🎯 Toggle the button pin to see real-time narration!")
            print("=" * 60)
            
            # Monitor for events
            start_time = time.time()
            while time.time() - start_time < duration and self.monitoring_active:
                await asyncio.sleep(1)
                
                # Provide periodic status updates
                if int(time.time() - start_time) % 30 == 0:  # Every 30 seconds
                    elapsed = int(time.time() - start_time)
                    remaining = duration - elapsed
                    print(f"\n⏰ Monitoring status: {elapsed}s elapsed, {remaining}s remaining")
                    
                    # Get current button state
                    try:
                        state_result = await self.mcp_client.get_button_state()
                        current_state = state_result.get("state", "unknown")
                        print(f"📊 Current pin state: {current_state}")
                    except Exception as e:
                        print(f"⚠️ Could not get current state: {e}")
            
            print("\n🏁 Monitoring completed!")
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            print("\n🧹 Cleaning up...")
            
            if self.mcp_client:
                await self.mcp_client.disconnect()
            
            logger.info("🧹 Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point."""
    try:
        client = LLMMCPClient()
        await client.start_monitoring(duration=300)  # 5 minutes
        
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
