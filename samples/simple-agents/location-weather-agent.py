# Copyright (c) Microsoft. All rights reserved.
"""
Location-Aware Weather and Time Agent

This sample demonstrates building a conversational agent using the Microsoft Agent Framework
that maintains user location context across multiple turns and provides location-specific
weather forecasts and timezone-aware current time.

Key Learning Points:
- Multi-turn conversation threading with AgentThread
- MCP server integration for external data sources
- Tool coordination across multiple MCP servers
- Conversational state management

Usage:
    1. Ensure MCP servers are running:
       - User MCP: port 8002
       - Weather MCP: port 8001
    2. Configure .env with your OpenAI/Azure OpenAI credentials
    3. Run: python location-weather-agent.py
"""

import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client

import os
import asyncio
import logging

from agent_framework import ChatAgent, AgentThread, MCPStreamableHTTPTool
from dotenv import load_dotenv

load_dotenv()

# Configure logging for tool invocations (for Dev UI observability)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("LocationWeatherAgent")

# Get model configuration from environment
completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

# Create chat client (using small model for efficiency)
model_name = small_model_name or medium_model_name or completion_model_name
if not model_name:
    print("❌ Error: No model configured in .env file")
    print("Please set COMPLETION_DEPLOYMENT_NAME, MEDIUM_DEPLOYMENT_MODEL_NAME, or SMALL_DEPLOYMENT_MODEL_NAME")
    sys.exit(1)

client = create_chat_client(model_name)

# MCP Server URLs
USER_MCP_URL = os.environ.get("USER_MCP_SERVER_URL", "http://localhost:8002/mcp")
WEATHER_MCP_URL = os.environ.get("WEATHER_MCP_SERVER_URL", "http://localhost:8001/mcp")


async def main():
    """Main conversation loop for the location-aware weather agent."""
    
    print("\n" + "=" * 70)
    print("Location-Aware Weather & Time Agent")
    print("=" * 70)
    print("\n🤖 Demonstrating: Multi-turn conversation, MCP integration, tool coordination")
    print("\nI can help you with:")
    print("  • Weather information for your location")
    print("  • Current time in your timezone")
    print("  • Location updates when you move")
    print("\n📍 Supported weather locations:")
    print("   Seattle | New York | London | Berlin | Tokyo | Sydney")
    print()
    
    # Initialize MCP tool connections with comprehensive error handling
    try:
        logger.info("Initializing MCP server connections...")
        user_mcp = MCPStreamableHTTPTool(name="User Server", url=USER_MCP_URL)
        weather_mcp = MCPStreamableHTTPTool(name="Weather Server", url=WEATHER_MCP_URL)
        logger.info(f"Connected to User MCP Server at {USER_MCP_URL}")
        logger.info(f"Connected to Weather MCP Server at {WEATHER_MCP_URL}")
        print(f"✅ Connected to User MCP Server ({USER_MCP_URL})")
        print(f"✅ Connected to Weather MCP Server ({WEATHER_MCP_URL})")
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        print(f"\n❌ Connection Error: Unable to reach MCP servers")
        print("\nPlease ensure both MCP servers are running:")
        print("  Terminal 1: cd src/mcp-server/04-weather-server && python server-mcp-sse-weather.py")
        print("  Terminal 2: cd src/mcp-server/02-user-server && python server-mcp-sse-user.py")
        print(f"\nExpected URLs:")
        print(f"  User MCP: {USER_MCP_URL}")
        print(f"  Weather MCP: {WEATHER_MCP_URL}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during MCP initialization: {e}", exc_info=True)
        print(f"\n❌ Error connecting to MCP servers: {e}")
        print("\nPlease check:")
        print("  1. MCP servers are running (see above)")
        print("  2. Ports 8001 and 8002 are not blocked")
        print("  3. MCP server URLs in .env are correct")
        sys.exit(1)
    
    # Create agent with MCP tools
    # KEY LEARNING: Agent Framework allows tools from multiple MCP servers to be composed together
    agent = ChatAgent(
        chat_client=client,
        tools=[user_mcp, weather_mcp],  # Multiple MCP servers as tools - agent decides when to call each
        name="LocationWeatherAgent",
        instructions="""You are a helpful assistant that provides location-aware weather and time information.

Key capabilities:
- When a user tells you their location (e.g., "I am in London" or "I moved to Berlin"), store it using the move() tool
- Use get_current_user() to get the username, then get_current_location() to retrieve their stored location
- For weather queries, use get_weather_at_location() with the user's current city
- For time queries, use get_current_time() with the user's timezone
- Remember the user's location from earlier in the conversation
- If the user hasn't told you their location yet, politely ask them to provide it

Supported weather locations: Seattle, New York, London, Berlin, Tokyo, Sydney
If a user requests weather for an unsupported location, use list_supported_locations() and ask them to choose from the list.

Be conversational, friendly, and helpful. Acknowledge when you've stored or updated their location."""
    )
    
    # Create conversation thread for state management
    # KEY LEARNING: AgentThread maintains message history across turns, enabling context-aware responses
    thread = AgentThread()
    
    print("\nType 'exit' or 'quit' to end the conversation.")
    print("-" * 70)
    print("\n💡 Try these example queries:")
    print('   "I am currently in London"')
    print('   "What is the weather now here?"')
    print('   "What time is it for me right now?"')
    print('   "I moved to Berlin, what is the weather like today?"')
    print('   "Can you remind me where I said I am based?"')
    print("-" * 70)
    
    # Main conversation loop
    # KEY LEARNING: Reusing the same thread across turns maintains conversational context
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Handle exit commands
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("\nAgent: Goodbye! Have a great day!")
                logger.info("Conversation ended by user")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Send to agent and get response
            # KEY LEARNING: Thread parameter ensures message history is preserved
            logger.info(f"User query: {user_input}")
            result = await agent.run(user_input, thread=thread)
            logger.info(f"Agent response generated (tool calls: {len(result.context) if hasattr(result, 'context') else 'N/A'})")
            
            # Display agent response
            print(f"\nAgent: {result.text}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Conversation interrupted. Goodbye!")
            logger.info("Conversation interrupted by keyboard")
            break
        except Exception as e:
            logger.error(f"Error in conversation loop: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'exit' to quit.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
