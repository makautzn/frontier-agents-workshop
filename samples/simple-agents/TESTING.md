# Testing location-weather-agent

## Prerequisites

Before running tests, configure valid API credentials in `/workspaces/frontier-agents-workshop/.env`:

### Option 1: Azure OpenAI
```env
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-actual-api-key
SMALL_DEPLOYMENT_MODEL_NAME=gpt-4o-mini  # Remove "openai/" prefix for Azure
```

### Option 2: OpenAI
```env
SMALL_DEPLOYMENT_MODEL_NAME=openai/gpt-4o-mini  # Keep "openai/" prefix
# No AZURE_ variables needed; OpenAI API key detected automatically
```

## Running Tests

### Automated Test Suite
```bash
cd samples/simple-agents
source ../../.venv/bin/activate
python test_location_weather_agent.py
```

**Expected Output** (with valid credentials):
```
✅ TEST 1 PASSED - Query 1: Establish location
✅ TEST 2 PASSED - Query 2: Get weather for current location
✅ TEST 3 PASSED - Query 3: Get current time
✅ TEST 4 PASSED - Query 4: Update location and get weather
✅ TEST 5 PASSED - Query 5: Recall location

Results: 5/5 tests passed
🎉 ALL TESTS PASSED - SC-006 SATISFIED
```

### Manual Interactive Testing
```bash
cd samples/simple-agents
source ../../.venv/bin/activate
python location-weather-agent.py
```

Then test with these queries:
1. "I am currently in London"
2. "What is the weather now here?"
3. "What time is it for me right now?"
4. "I moved to Berlin, what is the weather like today?"
5. "Can you remind me where I said I am based?"

## Test Validation

**T033 (Automated Testing)**:
- ✅ Test script created and executes correctly
- ✅ MCP server connections verified
- ✅ Test query structure validated
- ⚠️  **Requires user-provided API credentials to run**

**Note**: Test executions will fail with "Connection error" if `.env` contains placeholder values.

## Troubleshooting

### "Connection error" during tests
- **Cause**: Invalid or missing API credentials in `.env`
- **Fix**: Update `.env` with valid Azure OpenAI or OpenAI credentials

### MCP server connection errors
- **Cause**: MCP servers not running
- **Fix**: Start servers (see [quickstart.md](../../specs/001-location-weather-agent/quickstart.md) Step 1)

### Import errors
- **Cause**: Virtual environment not activated
- **Fix**: `source ../../.venv/bin/activate` before running tests
