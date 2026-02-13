"""
Test script for location-weather-agent.py

Tests all 5 input queries from the specification to ensure 100% success (SC-006).
This script automates the validation of the agent's core functionality.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from samples.shared.model_client import create_chat_client
from agent_framework import ChatAgent, AgentThread, MCPStreamableHTTPTool
from dotenv import load_dotenv

load_dotenv()

# MCP server URLs (must match .env configuration)
USER_MCP_URL = os.environ.get("USER_MCP_SERVER_URL", "http://localhost:8002/mcp")
WEATHER_MCP_URL = os.environ.get("WEATHER_MCP_SERVER_URL", "http://localhost:8001/mcp")


async def test_agent():
    """Run all 5 test queries and validate responses"""
    
    print("=" * 60)
    print("LOCATION-WEATHER-AGENT TEST SUITE")
    print("=" * 60)
    print()
    
    # Initialize MCP tools
    print("Initializing MCP connections...")
    user_mcp = MCPStreamableHTTPTool(name="User Server", url=USER_MCP_URL)
    weather_mcp = MCPStreamableHTTPTool(name="Weather Server", url=WEATHER_MCP_URL)
    print(f"✓ User MCP: {USER_MCP_URL}")
    print(f"✓ Weather MCP: {WEATHER_MCP_URL}")
    print()
    
    # Get model configuration from environment
    completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
    medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
    small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")
    
    # Create chat client (using small model for efficiency)
    model_name = small_model_name or medium_model_name or completion_model_name
    if not model_name:
        print("❌ Error: No model configured in .env file")
        return 1
    
    client = create_chat_client(model_name)
    
    # Create agent with comprehensive instructions
    agent = ChatAgent(
        chat_client=client,
        tools=[user_mcp, weather_mcp],
        instructions="""You are a helpful location-aware weather and time assistant.

You can help users with:
1. Storing and recalling their current location
2. Providing weather information for their location
3. Telling the current time for their timezone

When a user tells you their location (e.g., "I am in London" or "I moved to Berlin"):
- Use get_current_user() to get their username
- Use move(username, location) to store their location
- Acknowledge the location update naturally

When asked about weather:
- Use get_current_location() to find where they are (if needed)
- Use get_weather_at_location(city_name) to get weather data
- Present the information naturally

When asked about time:
- Use get_current_location() to get their timezone (if needed)
- Use get_current_time(location_timezone) with IANA timezone format
- Present the time naturally

Always maintain context from previous conversation turns. If location is not established, ask the user to provide it."""
    )
    
    # Create thread for conversation state
    thread = AgentThread()
    
    # Test queries from specification
    test_queries = [
        ("Query 1: Establish location", "I am currently in London"),
        ("Query 2: Get weather for current location", "What is the weather now here?"),
        ("Query 3: Get current time", "What time is it for me right now?"),
        ("Query 4: Update location and get weather", "I moved to Berlin, what is the weather like today?"),
        ("Query 5: Recall location", "Can you remind me where I said I am based?"),
    ]
    
    results = []
    
    for i, (description, query) in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST {i}/5: {description}")
        print(f"{'=' * 60}")
        print(f"User: {query}")
        print()
        
        try:
            result = await agent.run(query, thread=thread)
            
            # Extract assistant response - handle different message structures
            assistant_message = result.messages[-1]
            
            # Try different ways to get the content
            if hasattr(assistant_message, 'content'):
                if isinstance(assistant_message.content, str):
                    response_text = assistant_message.content
                elif isinstance(assistant_message.content, list):
                    response_text = "\n".join(
                        getattr(part, "text", str(part)) 
                        for part in assistant_message.content 
                        if hasattr(part, "text") or isinstance(part, str)
                    )
                else:
                    response_text = str(assistant_message.content)
            elif hasattr(assistant_message, 'text'):
                response_text = assistant_message.text
            else:
                # Fallback: convert message to string
                response_text = str(assistant_message)
            
            print(f"Assistant: {response_text}")
            print()
            
            # Validate response based on query
            success = validate_response(i, query, response_text)
            results.append((description, success))
            
            if success:
                print(f"✅ TEST {i} PASSED")
            else:
                print(f"❌ TEST {i} FAILED")
                
        except Exception as e:
            print(f"❌ TEST {i} FAILED WITH ERROR: {e}")
            results.append((description, False))
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for i, (description, success) in enumerate(results, 1):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - Test {i}: {description}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - SC-006 SATISFIED")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed - Review needed")
        return 1


def validate_response(test_num, query, response):
    """Validate that response is appropriate for the query"""
    
    response_lower = response.lower()
    
    if test_num == 1:
        # Should acknowledge London location
        return "london" in response_lower
    
    elif test_num == 2:
        # Should provide weather information (temperature, conditions, etc.)
        weather_keywords = ["weather", "temperature", "sunny", "cloudy", "rainy", 
                            "clear", "overcast", "°", "degrees", "wind", "humid"]
        return any(keyword in response_lower for keyword in weather_keywords)
    
    elif test_num == 3:
        # Should provide time information
        time_keywords = ["time", ":", "am", "pm", "o'clock", "clock"]
        return any(keyword in response_lower for keyword in time_keywords)
    
    elif test_num == 4:
        # Should acknowledge move to Berlin and provide Berlin weather
        return "berlin" in response_lower and any(
            keyword in response_lower 
            for keyword in ["weather", "temperature", "sunny", "cloudy", "clear"]
        )
    
    elif test_num == 5:
        # Should recall Berlin (not London)
        return "berlin" in response_lower
    
    return False


if __name__ == "__main__":
    exit_code = asyncio.run(test_agent())
    sys.exit(exit_code)
