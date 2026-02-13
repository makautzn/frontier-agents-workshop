# Agent Interaction Flow Contracts

**Feature**: Location-Aware Weather and Time Agent  
**Date**: 2026-02-12  
**Purpose**: Define conversation flows and tool invocation sequences

## Overview

This document specifies the expected interaction patterns between:
- **User** ↔ **Agent**
- **Agent** ↔ **User MCP Server**
- **Agent** ↔ **Weather MCP Server**

All flows assume conversational context is maintained via `AgentThread`.

---

## Flow 1: Establish User Location (P1 - Critical)

### User Story
User states their current location so the agent can provide location-specific information.

### Conversation Flow

```
User → Agent: "I am currently in London"
  ↓
Agent processes message
  ↓
Agent → User MCP: get_current_user()
  ↓
User MCP → Agent: "Dennis"
  ↓
Agent → User MCP: move("Dennis", "Europe/London")
  ↓
User MCP → Agent: true
  ↓
Agent → User: "Got it! I've updated your location to London. I can now help you with weather and time information for London."
```

### Tool Call Sequence

```json
[
  {
    "tool": "get_current_user",
    "parameters": {},
    "result": "Dennis"
  },
  {
    "tool": "move",
    "parameters": {
      "username": "Dennis",
      "newlocation": "Europe/London"
    },
    "result": true
  }
]
```

### Success Criteria
- ✅ Agent acknowledges location
- ✅ Location stored in User MCP Server (via `move()`)
- ✅ Agent confirms understanding in natural language

### Error Cases

**Unsupported Location**:
```
User: "I am in Atlantis"
Agent → Weather MCP: list_supported_locations()
Agent → User: "I don't have weather data for Atlantis. I currently support these locations: Seattle, New York, London, Berlin, Tokyo, and Sydney. Could you rephrase using one of these cities?"
```

**Ambiguous Location** (e.g., "Paris"):
```
User: "I am in Paris"
Agent assumes: "Europe/Paris" (most common)
Agent → User → move("Dennis", "Europe/Paris")
Agent → User: "I've set your location to Paris, France. If you meant a different Paris, please let me know."
```

---

## Flow 2: Query Current Weather (P2 - Core Value)

### User Story
User asks for current weather without repeating their location.

### Conversation Flow

```
User → Agent: "What is the weather now here?"
  ↓
Agent checks conversation history for location
  ↓
Agent → User MCP: get_current_user()
  ↓
User MCP → Agent: "Dennis"
  ↓
Agent → User MCP: get_current_location("Dennis")
  ↓
User MCP → Agent: "Europe/London"
  ↓
Agent → Weather MCP: get_weather_at_location("London")
  ↓
Weather MCP → Agent: "Weather for London at 2026-02-12 14:30 (afternoon): Mild temperatures with scattered clouds and good visibility."
  ↓
Agent → User: "Currently in London, it's afternoon with mild temperatures, scattered clouds, and good visibility."
```

### Tool Call Sequence

```json
[
  {
    "tool": "get_current_user",
    "parameters": {},
    "result": "Dennis"
  },
  {
    "tool": "get_current_location",
    "parameters": {
      "username": "Dennis"
    },
    "result": "Europe/London"
  },
  {
    "tool": "get_weather_at_location",
    "parameters": {
      "location": "London"
    },
    "result": "Weather for London at 2026-02-12 14:30 (afternoon): Mild temperatures with scattered clouds and good visibility."
  }
]
```

### Success Criteria
- ✅ Agent recalls location from conversation or MCP
- ✅ Agent retrieves weather for correct location
- ✅ Agent presents weather in natural language

### Error Cases

**No Location Established**:
```
User: "What is the weather?"
Agent → User: "I'd be happy to help with the weather! Could you let me know which city you're asking about? For example, you can say 'I am in London' or 'What's the weather in Berlin?'"
```

**Weather Service Unavailable**:
```
User: "What is the weather now here?"
Agent → Weather MCP: get_weather_at_location("London")
Weather MCP → Agent: [HTTP 500 error]
Agent → User: "I'm sorry, I'm having trouble reaching the weather service right now. Could you try again in a moment?"
```

---

## Flow 3: Query Current Time (P3 - Timezone Demo)

### User Story
User asks for current time in their timezone without repeating location.

### Conversation Flow

```
User → Agent: "What time is it for me right now?"
  ↓
Agent → User MCP: get_current_user()
  ↓
User MCP → Agent: "Dennis"
  ↓
Agent → User MCP: get_current_location("Dennis")
  ↓
User MCP → Agent: "Europe/London"
  ↓
Agent → User MCP: get_current_time("Europe/London")
  ↓
User MCP → Agent: "02:30:45 PM"
  ↓
Agent → User: "In London, it's currently 2:30 PM."
```

### Tool Call Sequence

```json
[
  {
    "tool": "get_current_user",
    "parameters": {},
    "result": "Dennis"
  },
  {
    "tool": "get_current_location",
    "parameters": {
      "username": "Dennis"
    },
    "result": "Europe/London"
  },
  {
    "tool": "get_current_time",
    "parameters": {
      "location": "Europe/London"
    },
    "result": "02:30:45 PM"
  }
]
```

### Success Criteria
- ✅ Agent recalls user location
- ✅ Agent retrieves time for correct timezone
- ✅ Agent presents time naturally

---

## Flow 4: Update Location (Location Change)

### User Story
User moves to a new location and informs the agent.

### Conversation Flow

```
User → Agent: "I moved to Berlin, what is the weather like today?"
  ↓
Agent recognizes location change + weather request
  ↓
Agent → User MCP: get_current_user()
  ↓
User MCP → Agent: "Dennis"
  ↓
Agent → User MCP: move("Dennis", "Europe/Berlin")
  ↓
User MCP → Agent: true
  ↓
Agent → Weather MCP: get_weather_at_location("Berlin")
  ↓
Weather MCP → Agent: "Weather for Berlin at 2026-02-12 15:45 (afternoon): Mild temperatures with scattered clouds and good visibility."
  ↓
Agent → User: "I've updated your location to Berlin. Currently there, it's afternoon with mild temperatures, scattered clouds, and good visibility."
```

### Tool Call Sequence

```json
[
  {
    "tool": "get_current_user",
    "parameters": {},
    "result": "Dennis"
  },
  {
    "tool": "move",
    "parameters": {
      "username": "Dennis",
      "newlocation": "Europe/Berlin"
    },
    "result": true
  },
  {
    "tool": "get_weather_at_location",
    "parameters": {
      "location": "Berlin"
    },
    "result": "Weather for Berlin at 2026-02-12 15:45 (afternoon): Mild temperatures with scattered clouds and good visibility."
  }
]
```

### Success Criteria
- ✅ Agent detects location change
- ✅ Agent updates location in MCP
- ✅ Agent uses new location for weather query
- ✅ Agent confirms location change to user

---

## Flow 5: Recall Previous Location

### User Story
User asks agent to recall their stated location.

### Conversation Flow

```
User → Agent: "Can you remind me where I said I am based?"
  ↓
Agent checks conversation history AND/OR User MCP
  ↓
Agent → User MCP: get_current_user()
  ↓
User MCP → Agent: "Dennis"
  ↓
Agent → User MCP: get_current_location("Dennis")
  ↓
User MCP → Agent: "Europe/Berlin"
  ↓
Agent → User: "Based on our conversation, you're currently in Berlin."
```

**Alternative** (if location mentioned early in conversation):
```
Agent reads message history
Agent finds: "I am currently in London" (earlier message)
Agent notes: move() called to "Europe/Berlin" later
Agent → User: "You initially told me you were in London, but then you mentioned moving to Berlin."
```

### Tool Call Sequence (Option 1: MCP Query)

```json
[
  {
    "tool": "get_current_user",
    "parameters": {},
    "result": "Dennis"
  },
  {
    "tool": "get_current_location",
    "parameters": {
      "username": "Dennis"
    },
    "result": "Europe/Berlin"
  }
]
```

### Tool Call Sequence (Option 2: History Only)

```json
[]  // No tool calls, answer from conversation history
```

### Success Criteria
- ✅ Agent correctly recalls current location
- ✅ Agent can reference location changes if they occurred

---

## Cross-Cutting Concerns

### Conversation State Management

**Thread Lifecycle**:
```python
# Thread created once at start
thread = AgentThread()

# Each user input:
result = await agent.run(user_input, thread=thread)

# Message history automatically maintained
# No need to manually track location
```

**Location Context Sources**:
1. **Conversation History**: User statements like "I am in London"
2. **User MCP Server**: `get_current_location(username)` returns last set location
3. **Priority**: Most recent location mentioned wins

### Error Handling Patterns

**Pattern 1: Invalid Location**
```
try {
  weather = get_weather_at_location(location)
} catch (UnsupportedLocationError) {
  agent → user: "Please use a supported city: [list]"
}
```

**Pattern 2: MCP Server Unavailable**
```
try {
  result = mcp_tool_call()
} catch (HTTPError) {
  agent → user: "Service unavailable, please retry later"
}
```

**Pattern 3: Missing Required Info**
```
if no location in history AND get_current_location returns null:
  agent → user: "Please tell me your location first"
```

### Tool Invocation Guidelines

**Minimize Calls**:
- ✅ Extract location from conversation history when possible
- ✅ Only call `get_current_location()` if history unclear
- ❌ Don't call `get_current_user()` repeatedly within same flow

**Call Order**:
1. `get_current_user()` - Get username
2. `get_current_location(username)` OR `move(username, location)` - Get/set location
3. `get_weather_at_location(location)` OR `get_current_time(location)` - Get data

**Async Pattern**:
```python
result = await agent.run(user_message, thread=thread)
# All tool calls handled internally by agent
```

---

## Test Query Contracts

### Input Set from Specification

| Query | Expected Flow | Tool Calls |
|-------|---------------|------------|
| "I am currently in London" | Flow 1 | get_current_user, move |
| "What is the weather now here?" | Flow 2 | get_current_user, get_current_location, get_weather_at_location |
| "What time is it for me right now?" | Flow 3 | get_current_user, get_current_location, get_current_time |
| "I moved to Berlin, what is the weather like today?" | Flow 4 | get_current_user, move, get_weather_at_location |
| "Can you remind me where I said I am based?" | Flow 5 | get_current_user, get_current_location OR history |

### Success Metrics

- ✅ 100% of test queries receive contextually appropriate responses (SC-006)
- ✅ Location changes applied within 1 conversational turn (SC-004)
- ✅ No location re-prompts when context available (SC-002)

---

## MCP Server API Reference

### User MCP Server (localhost:8002/mcp)

**Tools**:
- `get_current_user()` → string (username)
- `get_current_location(username: string)` → string (IANA timezone)
- `get_current_time(location: string)` → string (formatted time)
- `move(username: string, newlocation: string)` → bool (success)

### Weather MCP Server (localhost:8001/mcp)

**Tools**:
- `list_supported_locations()` → list[string] (city names)
- `get_weather_at_location(location: string)` → string (weather description)
- `get_weather_for_multiple_locations(locations: list[string])` → list[string]

**Supported Locations**: Seattle, New York, London, Berlin, Tokyo, Sydney

---

## Compliance Matrix

| Functional Requirement | Contract Flow | Tool Calls |
|------------------------|---------------|------------|
| FR-001: Maintain conversational state | All flows | AgentThread context |
| FR-002: Store/recall location | Flow 1, 5 | move, get_current_location |
| FR-003: Connect to user MCP | All flows | MCPStreamableHTTPTool (user) |
| FR-004: Connect to weather MCP | Flow 2, 4 | MCPStreamableHTTPTool (weather) |
| FR-005: Provide weather | Flow 2, 4 | get_weather_at_location |
| FR-006: Provide time | Flow 3 | get_current_time |
| FR-007: Update location | Flow 1, 4 | move |
| FR-008: Prompt for missing location | Error cases | N/A (conversation handling) |
| FR-009: Invoke weather tools | Flow 2, 4 | get_weather_at_location |
| FR-010: Invoke time tools | Flow 3 | get_current_time |
| FR-011: Handle errors gracefully | Error cases | All tools (with exception handling) |
| FR-014: Ask rephrase for invalid location | Error cases | list_supported_locations |
| FR-015: Assume common location | Error cases | Disambiguation logic |

---

## Implementation Notes

### Agent Configuration

```python
# Connect to both MCP servers
user_mcp = MCPStreamableHTTPTool(url="http://localhost:8002/mcp")
weather_mcp = MCPStreamableHTTPTool(url="http://localhost:8001/mcp")

# Create agent with tools
agent = ChatAgent(
    model_client=client,
    tools=[user_mcp, weather_mcp],
    name="LocationWeatherAgent",
    description="An agent that helps users get weather and time information based on their location."
)

# Create conversation thread
thread = AgentThread()

# Conversation loop
async def conversation_loop():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        result = await agent.run(user_input, thread=thread)
        print(f"Agent: {result.messages[-1].content}")
```

### Testing with Agent Framework Dev UI

**Expected Traces**:
- Tool invocation sequences visible in Dev UI
- Message history viewable per thread
- MCP server response times logged
- Error handling paths traced

**Example Trace** (Flow 2):
```
1. User Input: "What is the weather now here?"
2. Agent reasoning: [identifies need for location and weather tools]
3. Tool Call: get_current_user() → "Dennis"
4. Tool Call: get_current_location("Dennis") → "Europe/London"
5. Tool Call: get_weather_at_location("London") → [weather data]
6. Agent Response: [natural language weather report]
```

This enables SC-007: "Agent Framework Dev UI successfully displays activity traces for multi-tool agent executions"
