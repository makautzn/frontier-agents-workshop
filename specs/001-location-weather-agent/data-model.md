# Data Model: Location-Aware Weather and Time Agent

**Feature**: Location-Aware Weather and Time Agent  
**Date**: 2026-02-12  
**Source**: Derived from [spec.md](spec.md) Key Entities and [research.md](research.md)

## Overview

This feature uses **in-memory, conversational state** rather than persistent data storage. The "data model" here describes the conceptual entities and their relationships as understood by the agent through conversation context and external MCP server calls.

**Storage Strategy**: 
- **Agent**: Conversation history in `ChatMessageStore` (in-memory)
- **User Data**: Managed by User MCP Server (external)
- **Weather Data**: Retrieved from Weather MCP Server (external, no storage)

---

## Core Entities

### 1. User

**Description**: Represents a person interacting with the agent

**Attributes**:
| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `username` | string | User identifier (e.g., "Dennis") | User MCP: `get_current_user()` |
| `current_location` | string (IANA timezone) | User's current timezone location (e.g., "Europe/Berlin") | User MCP: `get_current_location(username)` |

**Storage**: User MCP Server (external)

**Operations**:
- **Retrieve Current User**: `get_current_user()` → username
- **Get User Location**: `get_current_location(username)` → location (timezone)
- **Update Location**: `move(username, newlocation)` → updates current_location

**Lifecycle**: 
- User data pre-exists in MCP server
- Location can be updated during conversation via `move()`
- Changes persist in MCP server (not agent-managed)

**Relationships**:
- User HAS-A Location (current_location)
- User location determines timezone for time queries
- User location used to fetch weather data

---

### 2. Location

**Description**: Represents a geographic place with timezone information

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Human-readable city/region name | "London", "Berlin" |
| `timezone` | string (IANA) | IANA timezone identifier | "Europe/London", "Europe/Berlin" |

**Format**:
- **Display Name**: Common city name (e.g., "London")
- **Technical Format**: IANA timezone (e.g., "Europe/London")
- **Mapping**: Handled by MCP servers and LLM understanding

**Supported Locations** (Weather MCP):
- Seattle → America/Los_Angeles
- New York → America/New_York  
- London → Europe/London
- Berlin → Europe/Berlin
- Tokyo → Asia/Tokyo
- Sydney → Australia/Sydney

**Operations**:
- **List Supported**: Weather MCP `list_supported_locations()` → city names
- **Get Timezone**: Implicit mapping in User/Weather MCP servers
- **Validate**: Weather MCP returns error for unsupported locations

**Relationships**:
- Location associated with User (current_location)
- Location required for WeatherData retrieval
- Location required for TimeInformation retrieval

---

### 3. WeatherData

**Description**: Information about current weather conditions, time-of-day aware

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `location` | string | City name | "London" |
| `timestamp` | string | Local date/time | "2026-02-12 14:30" |
| `time_bucket` | enum | Time of day category | "afternoon", "morning", "evening", "night" |
| `description` | string | Weather description | "Mild temperatures with scattered clouds and good visibility." |

**Time Buckets**:
- **morning**: 05:00 - 11:59
- **afternoon**: 12:00 - 17:59
- **evening**: 18:00 - 21:59
- **night**: 22:00 - 04:59

**Static Descriptions** (per time bucket):
```
morning: "Cool and clear with a light breeze."
afternoon: "Mild temperatures with scattered clouds and good visibility."
evening: "Calm conditions with a gentle breeze and fading light."
night: "Quiet, mostly clear skies and cooler air."
```

**Storage**: Not stored; retrieved on-demand from Weather MCP

**Operations**:
- **Single Location**: `get_weather_at_location(location)` → weather string
- **Multiple Locations**: `get_weather_for_multiple_locations(locations)` → list of weather strings

**Format** (returned by MCP):
```
"Weather for {location} at {timestamp} ({time_bucket}): {description}"
```

**Limitations**:
- ⚠️ **Static data**: Not real-time weather, deterministic based on time-of-day
- ⚠️ **Limited locations**: Only 6 supported cities
- ⚠️ **No 24-hour forecast**: Current implementation provides time-of-day weather only

**Relationships**:
- WeatherData tied to Location
- WeatherData time_bucket determined by current local time at Location

---

### 4. TimeInformation

**Description**: Current time data for a specific location's timezone

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `location` | string (IANA timezone) | Timezone identifier | "Europe/London" |
| `current_time` | string | Formatted time | "02:30:45 PM" |

**Format**: 12-hour format with AM/PM (e.g., "02:30:45 PM")

**Storage**: Not stored; computed on-demand by User MCP

**Operations**:
- **Get Current Time**: `get_current_time(location)` → formatted time string

**Error Handling**:
- Returns: "Sorry, I couldn't find the timezone for that location." for invalid timezones

**Relationships**:
- TimeInformation requires Location (timezone)
- TimeInformation used to determine WeatherData time_bucket

---

### 5. ConversationThread

**Description**: In-memory container for conversation state and message history

**Attributes**:
| Attribute | Type | Description | Implementation |
|-----------|------|-------------|----------------|
| `thread_id` | string | Unique conversation identifier | `AgentThread` instance ID |
| `messages` | list[ChatMessage] | Ordered message history | `ChatMessageStore` |
| `created_at` | datetime | Thread creation time | Python datetime |

**Message Types**:
- **User messages**: User input text
- **Agent messages**: Agent responses
- **Tool calls**: Function invocations to MCP servers
- **Tool results**: MCP server responses

**Storage**: In-memory Python objects (`AgentThread` + `ChatMessageStore`)

**Lifecycle**:
1. **Created**: When conversation starts
2. **Updated**: Each user input / agent response appended
3. **Destroyed**: When Python process ends (no persistence)

**Operations**:
- **Create**: `AgentThread()`
- **Add Message**: Automatic via agent.run()
- **Retrieve History**: Automatic context for agent on each turn
- **Clear**: No explicit clear (thread persists until process ends)

**Relationships**:
- ConversationThread contains location mentions in user messages
- ConversationThread enables agent to recall earlier location statements
- ConversationThread scoped to single session (no persistence)

---

## Conceptual Relationships

```
User (MCP Server)
  ├─ current_location: IANA timezone
  └─ username: string

Location
  ├─ name: city name
  └─ timezone: IANA format

ConversationThread (In-Memory)
  ├─ messages[]
  │   ├─ User: "I am in London"
  │   ├─ Agent: acknowledges location
  │   ├─ User: "What is the weather?"
  │   ├─ Tool Call: get_weather_at_location("London")
  │   ├─ Tool Result: WeatherData
  │   └─ Agent: reports weather
  └─ implicit location tracking via message history

WeatherData (External MCP)
  ├─ retrieved via: get_weather_at_location(location)
  ├─ time_bucket: derived from local time
  └─ description: static per time_bucket

TimeInformation (External MCP)
  ├─ retrieved via: get_current_time(location)
  └─ formatted: 12-hour AM/PM
```

---

## Data Flow

### Scenario: "What is the weather now here?"

```
1. User sends message
   ↓
2. Agent receives message + full conversation history (from ConversationThread)
   ↓
3. Agent extracts location from history (e.g., "I am in London")
   ↓
4. Agent calls: get_current_user() → "Dennis"
   ↓
5. Agent calls: get_current_location("Dennis") → "Europe/London"
   ↓
6. Agent calls: get_weather_at_location("London") → WeatherData string
   ↓
7. Agent formats response with weather information
   ↓
8. Response stored in ConversationThread
   ↓
9. User sees weather description
```

### Scenario: "I moved to Berlin"

```
1. User sends message
   ↓
2. Agent understands location change
   ↓
3. Agent calls: get_current_user() → "Dennis"
   ↓
4. Agent calls: move("Dennis", "Europe/Berlin") → true
   ↓
5. User location updated in MCP server
   ↓
6. Subsequent queries use new location
```

---

## Validation Rules

### Location Format
- **User Input**: Flexible (e.g., "London", "I am in Berlin")
- **MCP Server**: Must match supported locations (weather) or valid IANA timezone (time)
- **Error Handling**: 
  - Invalid location → Ask user to rephrase with common city name
  - Ambiguous location → Assume most common/populous (e.g., "Paris" → "Europe/Paris")

### Conversation State
- **Persistence**: In-memory only, lost on restart
- **Scope**: Single session, no cross-session state
- **History Length**: Unlimited within memory constraints

### Weather Data
- **Supported Locations**: 6 cities only (Seattle, NYC, London, Berlin, Tokyo, Sydney)
- **Unsupported Request**: Returns error message from MCP
- **Time Bucket**: Automatically determined by local time

### Time Information
- **Timezone Format**: IANA timezone (e.g., "America/New_York")
- **Invalid Timezone**: Returns error message from MCP
- **Format**: Always 12-hour AM/PM

---

## Implementation Notes

### No Database Schema Required
- All data retrieved from external MCP servers
- No CREATE TABLE statements
- No SQL/NoSQL schemas
- No persistence layer

### In-Memory Structures

**AgentThread**:
```python
thread = AgentThread()  # Automatically creates ChatMessageStore
```

**MCP Tool Connections**:
```python
user_tool = MCPStreamableHTTPTool(url="http://localhost:8002/mcp")
weather_tool = MCPStreamableHTTPTool(url="http://localhost:8001/mcp")
```

**Agent with Tools**:
```python
agent = ChatAgent(
    model_client=client,
    tools=[user_tool, weather_tool],
    name="LocationWeatherAgent"
)
```

### Data Access Patterns

**Pattern 1: Location Recall** (from conversation history)
- Agent receives full message history on each turn
- LLM extracts location from prior user messages
- No explicit parsing needed

**Pattern 2: Weather Retrieval** (MCP call)
```python
result = await agent.run("What is the weather in London?")
# Agent internally calls: get_weather_at_location("London")
```

**Pattern 3: Time Retrieval** (MCP call)
```python
result = await agent.run("What time is it in Berlin?")
# Agent internally calls: get_current_time("Europe/Berlin")
```

---

## Alignment with Specification

### Entities Mapped

| Spec Entity | Data Model | Storage |
|-------------|-----------|---------|
| User | User | User MCP Server |
| Location | Location | Implicit in MCP servers |
| Weather Data | WeatherData | Weather MCP Server (on-demand) |
| Time Information | TimeInformation | User MCP Server (computed) |
| Conversation Thread | ConversationThread | In-memory (AgentThread) |

### Functional Requirements Coverage

- **FR-001**: Conversational state → `ConversationThread` with `ChatMessageStore`
- **FR-002**: Store/recall location → Message history + `get_current_location()`
- **FR-003**: Connect to user MCP → `MCPStreamableHTTPTool` (user)
- **FR-004**: Connect to weather MCP → `MCPStreamableHTTPTool` (weather)
- **FR-005**: Provide weather → `get_weather_at_location()`
- **FR-006**: Provide time → `get_current_time()`
- **FR-007**: Update location → `move(username, newlocation)`

**Constraint**: Weather MCP provides time-of-day weather only, not explicit 24-hour forecast as mentioned in FR-005 clarification. This is a known limitation documented in research.md.
