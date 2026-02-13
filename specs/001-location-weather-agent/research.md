# Phase 0: Research & Technology Decisions

**Feature**: Location-Aware Weather and Time Agent  
**Date**: 2026-02-12  
**Status**: Complete

## Research Questions from Technical Context

### 1. Agent Framework Threading & State Management

**Question**: How does the Microsoft Agent Framework maintain conversational state across multiple turns?

**Research Findings**:
- Reviewed `samples/simple-agents/agent-thread.py` (lines 1-168)
- Agent Framework provides `AgentThread` class for conversation management
- `ChatMessageStore` maintains message history within a thread
- Two patterns available:
  - **Automatic thread creation**: Service-managed, transparent to developer
  - **Manual thread creation**: Explicit `AgentThread` with `ChatMessageStore`
- Message history automatically available to agent on subsequent turns via the thread
- State persists in-memory for the lifetime of the thread object

**Decision**: Use `AgentThread` with `ChatMessageStore` (manual pattern)  
**Rationale**: 
- Explicit control over conversation lifecycle
- Clear demonstration of how state is maintained for learning purposes
- Matches pattern in agent-thread.py example
- In-memory storage aligns with specification requirement (FR-001)

**Alternatives Considered**:
- Automatic thread creation: Less educational value, hides mechanics
- Custom state management: Violates "Simple, Readable Codebases" principle

---

### 2. MCP Server Integration Pattern

**Question**: How do agents connect to and invoke tools from MCP servers?

**Research Findings**:
- Reviewed `samples/simple-agents/agents-using-mcp.py` (lines 1-282)
- Agent Framework provides two MCP tool wrapper classes:
  - `HostedMCPTool`: For MCP servers hosted separately
  - `MCPStreamableHTTPTool`: For Streamable HTTP transport (SSE endpoints)
- Connection pattern:
  ```python
  tool = MCPStreamableHTTPTool(url="http://host:port/mcp")
  agent = ChatAgent(model_client, tools=[tool])
  ```
- Tools from MCP server are automatically discovered and registered with agent
- Agent uses function calling to invoke MCP server endpoints
- MCP servers expose `/mcp` endpoint using Streamable HTTP transport

**MCP Server Capabilities** (from source code review):

**User Server** (port 8002):
- `get_current_user()` → Returns "Dennis"
- `get_current_location(username)` → Returns IANA timezone (e.g., "Europe/Berlin")
- `get_current_time(location)` → Returns formatted time for timezone
- `move(username, newlocation)` → Updates user location

**Weather Server** (port 8001):
- `list_supported_locations()` → Returns ["Seattle", "New York", "London", "Berlin", "Tokyo", "Sydney"]
- `get_weather_at_location(location)` → Returns time-of-day aware weather description
- `get_weather_for_multiple_locations(locations)` → Batch weather queries

**Decision**: Use `MCPStreamableHTTPTool` to connect to both MCP servers  
**Rationale**:
- Both servers use Streamable HTTP transport (`fastmcp` with `streamable-http`)
- Matches existing pattern in agents-using-mcp.py
- No configuration needed beyond endpoint URLs
- Automatic tool discovery reduces boilerplate

**Alternatives Considered**:
- Manual tool definition: More code, violates modularity principle
- Custom MCP client: Reinvents wheel, not composable

---

### 3. Time Zone Handling for Location-Aware Time

**Question**: How should the agent convert location names to timezones and get current time?

**Research Findings**:
- User MCP server already provides `get_current_time(location)` tool
- Weather MCP server uses IANA timezone format (e.g., "America/Los_Angeles")
- User location stored as IANA timezone (e.g., "Europe/Berlin")
- No additional timezone library needed in agent code
- MCP server uses `pytz` library for timezone operations (already in requirements.txt)

**Decision**: Delegate time operations to User MCP server's `get_current_time()` tool  
**Rationale**:
- Leverages existing MCP server capability
- No duplicate timezone logic in agent
- Follows "Modular, Composable Components" principle
- Simpler agent implementation

**Alternatives Considered**:
- Agent-side pytz: Duplicate logic, violates DRY principle
- Custom time function: Unnecessary when MCP provides it

---

### 4. Location Extraction & Memory in Conversation

**Question**: How should the agent remember the user's location from earlier messages?

**Research Findings**:
- Reviewed agent-thread.py conversation threading patterns
- Agent receives full message history on each turn via `AgentThread`
- LLM can extract location from conversation history through natural language understanding
- No explicit state variables needed - context is in message history
- User MCP server has `move(username, newlocation)` to persist location changes

**Decision**: Rely on conversation history + LLM understanding for location recall  
**Rationale**:
- Message history contains all location mentions
- LLM can extract "I am in London" from prior messages
- Follows conversational AI pattern
- Simplifies implementation

**Additional Pattern**: Call `move(username, newlocation)` when user changes location
**Rationale**:
- Persists location in user MCP server
- Enables `get_current_location(username)` to return updated location
- Demonstrates agent-driven state updates

**Alternatives Considered**:
- Explicit location variable: Requires parsing logic, more complex
- Database storage: Violates in-memory constraint (FR-001)

---

### 5. Weather Data Scope: Current + 24-Hour Forecast

**Question**: Weather MCP server provides time-of-day weather. Does this satisfy "current + 24-hour forecast" requirement?

**Research Findings**:
- Weather server returns: "Weather for {location} at {timestamp} ({time_bucket}): {description}"
- Time buckets: morning (05-11), afternoon (12-17), evening (18-21), night (22-04)
- Current implementation: **Static time-of-day descriptions only**
- No explicit 24-hour forecast data in current MCP server

**Gap Identified**: MCP server does not provide 24-hour forecast  
**Impact**: Cannot fully satisfy FR-005 ("current + 24-hour forecast") with current MCP server

**Decision**: Document limitation and implement with available capabilities  
**Rationale**:
- MCP server is existing infrastructure (not modifying for this feature)
- Time-of-day weather demonstrates core pattern (location, time, tool coordination)
- "24-hour forecast" can be simulated by querying multiple time buckets conceptually
- Workshop learning goals still met with current + time-of-day weather

**Recommendation for Spec Update**: Adjust FR-005 to match MCP server capability or note as future enhancement

**Alternatives Considered**:
- Modify weather MCP server: Out of scope, violates existing infrastructure constraint
- Mock forecast data in agent: Misleading, not real integration
- External weather API: Adds dependency, violates simplicity principle

---

## Technology Stack Summary

### Core Technologies (Final Decisions)

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Language** | Python | 3.11+ | Repository standard, all samples use Python |
| **Agent Framework** | agent-framework-core | 1.0.0b260128 | Microsoft Agent Framework, required per FR-012 |
| **MCP Client** | fastmcp | 2.14.4 | Required for MCP server integration |
| **LLM Client** | openai | 2.16.0 | Via shared/model_client.py |
| **Env Config** | python-dotenv | 1.2.1 | Standard pattern in all samples |
| **State Storage** | In-memory (Python dict) | N/A | Per FR-001, no persistence |

### Architecture Patterns

| Pattern | Source | Applied To |
|---------|--------|-----------|
| **Conversation Threading** | agent-thread.py | Multi-turn state management |
| **MCP Integration** | agents-using-mcp.py | Weather & user server connections |
| **Tool Calling** | basic-agent.py | Function invocation pattern |
| **Shared Client Setup** | shared/model_client.py | LLM client initialization |

### Dependencies (No New Additions)

All required dependencies already in `requirements.txt`:
- ✅ agent-framework-core==1.0.0b260128
- ✅ fastmcp==2.14.4
- ✅ openai==2.16.0
- ✅ python-dotenv==1.2.1
- ✅ pytz==2025.2 (used by MCP servers)

---

## Implementation Strategy

### Composability Plan

**Reuse from Existing Code**:
1. `samples/shared/model_client.py` - LLM client creation
2. `AgentThread` + `ChatMessageStore` - Conversation management pattern
3. `MCPStreamableHTTPTool` - MCP server integration pattern
4. User MCP server - Location and time tools
5. Weather MCP server - Weather data tools

**New Code** (single file):
- `samples/simple-agents/location-weather-agent.py` (~150-200 lines)
  - Import shared utilities
  - Configure 2 MCP tool connections
  - Create ChatAgent with tools
  - Create AgentThread for conversation
  - Implement interactive conversation loop
  - Handle user inputs per test queries

**Code Structure** (narrative style):
```python
# 1. Imports and setup (shared utilities, frameworks)
# 2. Connect to MCP servers (user + weather)
# 3. Create agent with tools
# 4. Create conversation thread
# 5. Main conversation loop:
#    - Accept user input
#    - Send to agent via thread
#    - Display response
#    - Repeat
```

### Best Practices Applied

From Agent Framework patterns:
- ✅ Use `AgentThread` for multi-turn conversations
- ✅ Use `ChatMessageStore` for message history
- ✅ Use `MCPStreamableHTTPTool` for MCP integration
- ✅ Handle async operations with `asyncio`
- ✅ Load env vars with `python-dotenv`

From Constitution:
- ✅ Simple, linear code flow
- ✅ Reuse existing modules
- ✅ Single responsibility (location-aware queries)
- ✅ Clear naming (location, weather, time functions)
- ✅ Minimal dependencies (all existing)

---

## Open Questions & Constraints

### Resolved
- ✅ Conversation state: In-memory via `AgentThread`
- ✅ MCP integration: `MCPStreamableHTTPTool` pattern
- ✅ Time zones: Delegated to User MCP server
- ✅ Location memory: Message history + LLM understanding

### Constraints Acknowledged
- ⚠️ **24-hour forecast limitation**: Weather MCP provides time-of-day only, not explicit 24-hour forecast
- ✅ **Supported locations**: Limited to 6 cities in Weather MCP (Seattle, NYC, London, Berlin, Tokyo, Sydney)
- ✅ **Location format**: User location must map to IANA timezone format
- ✅ **In-memory only**: No persistence between restarts (per specification)

### Recommendations for Implementation Phase
1. Start conversation with location establishment ("I am in London")
2. Use weather MCP's supported locations for testing
3. Document MCP server startup in quickstart.md
4. Include error handling for unsupported locations
5. Note 24-hour forecast gap in documentation

---

## Next Steps

**Phase 1 Readiness**: ✅ All research questions resolved  

Proceeding to:
- [ ] data-model.md - Entity definitions
- [ ] contracts/ - Agent interaction flows
- [ ] quickstart.md - Run instructions
- [ ] Update agent context

**Constitution Re-Check**: No violations introduced during research phase.
