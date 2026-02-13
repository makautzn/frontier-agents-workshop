# Quickstart: Location-Aware Weather and Time Agent

**Feature**: Location-Aware Weather and Time Agent  
**Difficulty**: Beginner  
**Time**: ~15 minutes  
**Learning Goals**: Multi-turn conversations, MCP integration, tool coordination

## What You'll Build

A conversational agent using the Microsoft Agent Framework that:
- ✅ Remembers your location across multiple conversation turns
- ✅ Provides weather information for your current location
- ✅ Reports the current time in your timezone
- ✅ Integrates with two external MCP servers (user data + weather)
- ✅ Coordinates multiple tools to answer location-aware questions

## Prerequisites

### Required
- Python 3.11 or higher
- Repository cloned: `frontier-agents-workshop`
- Dependencies installed: `pip install -r requirements.txt`
- Environment configured: `.env` file with Azure OpenAI credentials

### Environment Variables

Create or update `.env` in repository root:

```bash
# Azure OpenAI Configuration
COMPLETION_DEPLOYMENT_NAME=your-completion-model
MEDIUM_DEPLOYMENT_MODEL_NAME=your-medium-model
SMALL_DEPLOYMENT_MODEL_NAME=your-small-model

# Or use OpenAI directly
OPENAI_API_KEY=your-openai-key
```

See existing samples for `.env` format examples.

---

## Step 1: Start the MCP Servers

The agent depends on two MCP servers that must be running before you start the agent.

**Note**: If using a virtual environment, activate it first:
```bash
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

### Terminal 1: User MCP Server

```bash
cd src/mcp-server/02-user-server
python server-mcp-sse-user.py
```

**Expected output**:
```
4 Tool(s): get_current_user, get_current_location, get_current_time, move
1 Resource(s): config://version
0 Resource Template(s):
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

✅ **Verify**: Server running on `http://localhost:8002/mcp`

### Terminal 2: Weather MCP Server

```bash
cd src/mcp-server/04-weather-server
python server-mcp-sse-weather.py
```

**Expected output**:
```
3 Tool(s): list_supported_locations, get_weather_at_location, get_weather_for_multiple_locations
1 Resource(s): config://version
0 Resource Template(s):
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

✅ **Verify**: Server running on `http://localhost:8001/mcp`

---

## Step 2: Run the Location-Weather Agent

### Terminal 3: Agent

```bash
cd samples/simple-agents
python location-weather-agent.py
```

**Expected startup**:
```
Location-Aware Weather & Time Agent
===================================
Connected to User MCP Server (http://localhost:8002/mcp)
Connected to Weather MCP Server (http://localhost:8001/mcp)

I can help you with:
- Weather information for your location
- Current time in your timezone
- Location updates when you move

Supported weather locations: Seattle, New York, London, Berlin, Tokyo, Sydney

Type 'exit' or 'quit' to end the conversation.

You:
```

---

## Step 3: Try the Example Conversations

### Conversation 1: Establish Location

```
You: I am currently in London

Agent: Got it! I've updated your location to London. I can now help you with 
weather and time information for London.
```

**What happened**:
1. Agent called `get_current_user()` → "Dennis"
2. Agent called `move("Dennis", "Europe/London")` → true
3. Location stored in User MCP Server

---

### Conversation 2: Query Weather

```
You: What is the weather now here?

Agent: Currently in London, it's afternoon with mild temperatures, scattered 
clouds, and good visibility.
```

**What happened**:
1. Agent recalled your location from conversation OR called `get_current_location()`
2. Agent called `get_weather_at_location("London")`
3. Weather MCP returned time-of-day aware weather

---

### Conversation 3: Query Time

```
You: What time is it for me right now?

Agent: In London, it's currently 2:30 PM.
```

**What happened**:
1. Agent recalled your location
2. Agent called `get_current_time("Europe/London")`
3. Time returned in 12-hour format

---

### Conversation 4: Update Location

```
You: I moved to Berlin, what is the weather like today?

Agent: I've updated your location to Berlin. Currently there, it's afternoon 
with mild temperatures, scattered clouds, and good visibility.
```

**What happened**:
1. Agent detected location change
2. Agent called `move("Dennis", "Europe/Berlin")`
3. Agent called `get_weather_at_location("Berlin")`
4. Both operations completed in one turn

---

### Conversation 5: Recall Location

```
You: Can you remind me where I said I am based?

Agent: Based on our conversation, you're currently in Berlin.
```

**What happened**:
1. Agent checked conversation history and/or User MCP
2. Agent reported the most recent location

---

## Step 4: Explore with Agent Framework Dev UI (Optional)

### Start Dev UI

```bash
# In a new terminal (Terminal 4)
agent-framework-devui
```

**Access**: Open browser to `http://localhost:3000` (or shown URL)

### What to Observe

1. **Activities**: Each conversation turn appears as an activity
2. **Metrics**: Tool invocation counts, response times
3. **Traces**: Step-by-step tool call sequences
   - Example: "What is the weather?" shows 3 tool calls (user → location → weather)
4. **Messages**: Full conversation history

### Example Trace

For query: "What is the weather now here?"

```
Activity: User Query
├─ Tool Call: get_current_user
│  └─ Result: "Dennis"
├─ Tool Call: get_current_location("Dennis")
│  └─ Result: "Europe/London"
├─ Tool Call: get_weather_at_location("London")
│  └─ Result: "Weather for London at 2026-02-12 14:30 (afternoon): ..."
└─ Agent Response: "Currently in London, it's afternoon with..."
```

This demonstrates **SC-007**: Agent Framework Dev UI displays multi-tool execution traces.

---

## Code Walkthrough

### Agent Setup (Simplified)

```python
from agent_framework import ChatAgent, AgentThread, MCPStreamableHTTPTool
from samples.shared.model_client import create_chat_client
import asyncio

# 1. Connect to MCP servers
user_mcp = MCPStreamableHTTPTool(url="http://localhost:8002/mcp")
weather_mcp = MCPStreamableHTTPTool(url="http://localhost:8001/mcp")

# 2. Create chat client
client = create_chat_client(model_name)

# 3. Create agent with tools
agent = ChatAgent(
    model_client=client,
    tools=[user_mcp, weather_mcp],
    name="LocationWeatherAgent"
)

# 4. Create conversation thread
thread = AgentThread()

# 5. Conversation loop
async def main():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        result = await agent.run(user_input, thread=thread)
        print(f"Agent: {result.messages[-1].content}")

asyncio.run(main())
```

### Key Patterns

**Multi-Turn State**:
- `AgentThread` maintains conversation history
- No manual state management needed
- Agent automatically has access to prior messages

**MCP Integration**:
- `MCPStreamableHTTPTool` auto-discovers server tools
- No manual tool registration
- Agent decides when to invoke tools via function calling

**Tool Coordination**:
- Agent orchestrates multiple tool calls (user → location → weather)
- Tools chained automatically based on data dependencies
- Errors handled gracefully

---

## Troubleshooting

### MCP Servers Not Running

**Error**: `ConnectionRefusedError` or agent hangs

**Fix**:
1. Verify both MCP servers running (check Terminals 1 & 2)
2. Confirm ports 8001 and 8002 are accessible
3. Check no firewall blocking localhost connections

### Unsupported Location

**Error**: "Unsupported location. Use list_supported_locations..."

**Fix**: Use one of these supported cities:
- Seattle
- New York
- London
- Berlin
- Tokyo
- Sydney

### No Environment Variables

**Error**: `KeyError: 'COMPLETION_DEPLOYMENT_NAME'`

**Fix**:
1. Create `.env` file in repository root
2. Add Azure OpenAI or OpenAI credentials
3. See existing samples for format

### Agent Doesn't Remember Location

**Cause**: New `AgentThread` created each run (expected behavior)

**Explanation**: Conversation state is in-memory only. Location persists in User MCP Server between agent restarts, but conversation history resets.

**Workaround**: Re-state location at start of new session

---

## Learning Highlights

### 1. Conversation Threading

**Pattern**: `AgentThread` with `ChatMessageStore`

**Why It Matters**: 
- Multi-turn conversations enabled
- Agent "remembers" earlier messages
- No explicit state management in agent code

**Code**:
```python
thread = AgentThread()  # Create once
result = await agent.run(user_input, thread=thread)  # Reuse for all turns
```

### 2. MCP Server Integration

**Pattern**: `MCPStreamableHTTPTool` for Streamable HTTP transport

**Why It Matters**:
- External services integrated as agent tools
- No tool definitions needed (auto-discovered)
- Composable architecture (swap MCP servers easily)

**Code**:
```python
tool = MCPStreamableHTTPTool(url="http://localhost:8002/mcp")
agent = ChatAgent(model_client, tools=[tool])
```

### 3. Multi-Tool Coordination

**Pattern**: Agent orchestrates dependent tool calls

**Why It Matters**:
- Agent decides call order (user → location → weather)
- No manual orchestration logic
- LLM handles dependencies naturally

**Example Flow**:
```
User: "What's the weather here?"
Agent thinks: Need location → need weather
Agent calls: get_current_user() → get_current_location() → get_weather_at_location()
Agent responds: Natural language synthesis
```

### 4. Time-of-Day Awareness

**Pattern**: Weather data varies by local time

**Why It Matters**:
- Demonstrates contextual information (not just static data)
- Timezone handling delegated to MCP server
- Agent provides time-aware responses

**Example**:
```
Morning in London: "Cool and clear with a light breeze."
Afternoon in London: "Mild temperatures with scattered clouds..."
```

---

## Next Steps

### Extend the Sample

1. **Add More Locations**: Modify Weather MCP to support additional cities
2. **Persistent State**: Replace in-memory thread with database storage
3. **24-Hour Forecast**: Enhance Weather MCP to return forecast data
4. **Multi-User**: Support multiple users with different locations
5. **Location History**: Track user's location changes over time

### Related Samples

- `samples/simple-agents/basic-agent.py` - Simple tool calling
- `samples/simple-agents/agent-thread.py` - Conversation threading
- `samples/simple-agents/agents-using-mcp.py` - MCP integration patterns

### Learn More

- [Microsoft Agent Framework Documentation](https://pypi.org/project/agent-framework-core/)
- [Agent Framework Dev UI](https://pypi.org/project/agent-framework-devui/)
- [MCP (Model Context Protocol) Specification](https://modelcontextprotocol.io/)

---

## Success Checklist

After completing this quickstart, you should be able to:

- [x] Start and connect to multiple MCP servers
- [x] Create an agent with MCP tools
- [x] Maintain conversation state across multiple turns
- [x] Query location-dependent information (weather, time)
- [x] Update user location mid-conversation
- [x] Observe tool invocation traces in Dev UI
- [x] Understand multi-tool coordination patterns

**Congratulations!** You've built a location-aware conversational agent that demonstrates real-world patterns: stateful conversations, external service integration, and multi-tool orchestration.

---

## Reference

### Test Query Set (from Specification)

| Query | Expected Behavior |
|-------|-------------------|
| "I am currently in London" | Agent stores location |
| "What is the weather now here?" | Agent returns London weather |
| "What time is it for me right now?" | Agent returns London time |
| "I moved to Berlin, what is the weather like today?" | Agent updates location, returns Berlin weather |
| "Can you remind me where I said I am based?" | Agent recalls Berlin |

### MCP Server Tools

**User MCP (port 8002)**:
- `get_current_user()` → username
- `get_current_location(username)` → IANA timezone
- `get_current_time(location)` → formatted time
- `move(username, newlocation)` → update location

**Weather MCP (port 8001)**:
- `list_supported_locations()` → city list
- `get_weather_at_location(location)` → time-of-day weather
- `get_weather_for_multiple_locations(locations)` → batch weather

### File Locations

- **Agent Code**: `samples/simple-agents/location-weather-agent.py`
- **User MCP**: `src/mcp-server/02-user-server/server-mcp-sse-user.py`
- **Weather MCP**: `src/mcp-server/04-weather-server/server-mcp-sse-weather.py`
- **Shared Utils**: `samples/shared/model_client.py`
- **Requirements**: `requirements.txt` (root)
- **Environment**: `.env` (root)
