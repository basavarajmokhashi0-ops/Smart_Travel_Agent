# ✈️ Smart Travel Planner — CrewAI + MCP Multi-Agent System

A production-grade autonomous multi-agent travel planning system built with **CrewAI** and **MCP (Model Context Protocol)** tools. Enter source, destination, and dates — 5 specialized AI agents collaborate to produce a complete travel plan.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit UI (app.py)                       │
│         [Source] [Destination] [From Date] [To Date] [Plan]     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CrewAI Crew (crew.py)                        │
│                   Process: Sequential                           │
│                                                                 │
│  ┌─────────────────┐                                            │
│  │  🧠 Planner      │  Analyzes route, decides execution order   │
│  │     Agent        │  Identifies transport modes needed         │
│  └────────┬────────┘                                            │
│           │ context flows down                                  │
│  ┌────────▼────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  ✈️ Travel       │  │  🏨 Hotel Agent   │  │ 📍 Info Agent  │  │
│  │     Agent        │  │  3 hotels in     │  │ Weather, food, │  │
│  │  Flights/trains/ │  │  diff. areas     │  │ attractions    │  │
│  │  buses, 3 each   │  └──────────────────┘  └───────────────┘  │
│  └────────┬────────┘           │                      │          │
│           └───────────────────┬┘──────────────────────┘          │
│                               ▼                                  │
│              ┌────────────────────────────┐                      │
│              │  📅 Itinerary Agent         │                      │
│              │  Synthesizes all outputs   │                      │
│              │  Day-by-day optimized plan │                      │
│              └────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌────────────┐ ┌──────────────┐
    │  MCP Tool:   │ │  MCP Tool: │ │  MCP Server: │
    │  Web Search  │ │  Weather   │ │  search_     │
    │  (Serper /   │ │  (OpenWx / │ │  server.py   │
    │   DDG)       │ │  estimated)│ │  (stdio MCP) │
    └──────────────┘ └────────────┘ └──────────────┘
```

---

## 📁 Project Structure

```
smart_travel_planner/
├── app.py                      # Streamlit UI
├── crew.py                     # CrewAI crew orchestration
├── requirements.txt
├── .env.example                # API key template
│
├── agents/
│   ├── __init__.py
│   ├── travel_agents.py        # All 5 agent definitions
│   └── travel_tasks.py         # All 5 task definitions
│
├── tools/
│   ├── __init__.py
│   └── mcp_tools.py            # MCP-backed CrewAI tools
│
└── mcp_servers/
    └── search_server.py        # Standalone stdio MCP server
```

---

## 🚀 Setup & Run

### Step 1: Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Get API keys

| Key | Required? | Where to get | Cost |
|-----|-----------|--------------|------|
| `GROQ_API_KEY` | **YES** (or OpenAI/Anthropic) | [console.groq.com](https://console.groq.com) | 🆓 Free |
| `SERPER_API_KEY` | Recommended | [serper.dev](https://serper.dev) | 🆓 Free 2500/mo |
| `OPENWEATHER_API_KEY` | Optional | [openweathermap.org/api](https://openweathermap.org/api) | 🆓 Free |
| `OPENAI_API_KEY` | Alternative LLM | [platform.openai.com](https://platform.openai.com) | 💰 Paid |

### Step 3: Configure

```bash
cp .env.example .env
# Edit .env and add your keys
```

`.env` file:
```env
GROQ_API_KEY=gsk_your_key_here
MODEL_NAME=groq/llama-3.3-70b-versatile
SERPER_API_KEY=your_serper_key        # optional but recommended
OPENWEATHER_API_KEY=your_owm_key      # optional
```

### Step 4: Run

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## 🤖 Agent Details

### 1. 🧠 Planner Agent
- **Role**: Master Travel Coordinator
- **Does**: Analyzes source→destination distance, determines which transport modes are relevant (flight vs train vs bus), estimates trip structure
- **Output**: Execution plan with context for all sub-agents

### 2. ✈️ Travel Agent
- **Role**: Transport Research Specialist
- **Does**: Searches for real transport options
- **Output**:
  - **Flights** (if applicable): 3 options → Cheapest | Earliest | Night Flight
  - **Trains** (if applicable): 3 options → Cheapest | Fastest | Overnight
  - **Buses** (if applicable): 3 options → Budget | Earliest | Sleeper
  - Each option: Operator, Departure Time, Arrival Time, Duration, Price (₹)

### 3. 🏨 Hotel Agent
- **Role**: Accommodation Research Specialist
- **Does**: Finds hotels in 3 different areas
- **Output**: 3 hotels:
  1. Near airport/transit hub
  2. Central/tourist area
  3. Local/budget neighborhood
  - Each: Name, Area, ₹/night, Stars, Amenities, Why recommended

### 4. 📍 Information Agent
- **Role**: Destination Intelligence Specialist
- **Does**: Weather + local knowledge
- **Output**:
  - 🌤️ Weather forecast with packing tips
  - 🍛 5+ must-try local dishes + restaurant recommendations
  - 🗺️ 8+ must-visit attractions with entry fees + timings
  - 💡 Local tips: transport, safety, culture, shopping

### 5. 📅 Itinerary Agent
- **Role**: Itinerary Architect
- **Does**: Synthesizes everything into a day-by-day plan
- **Output**:
  - Day-by-day: Morning / Afternoon / Evening activities
  - Meals at each slot
  - Geographic routing (nearby places grouped)
  - Daily cost estimate
  - Trip summary + budget + packing list

---

## 🛠️ MCP Tools

### WebSearchTool
```python
# tools/mcp_tools.py
class WebSearchTool(BaseTool):
    name = "Web Search"
    # Primary: Serper.dev (Google results)
    # Fallback: DuckDuckGo instant answers
```

### WeatherTool
```python
class WeatherTool(BaseTool):
    name = "Weather Lookup"
    # Primary: OpenWeatherMap API
    # Fallback: Deterministic estimation
```

### Standalone MCP Server
```bash
# Can be used by Claude Desktop or any MCP client
python mcp_servers/search_server.py

# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "travel-search": {
      "command": "python",
      "args": ["/path/to/smart_travel_planner/mcp_servers/search_server.py"]
    }
  }
}
```

---

## ⚡ How It Works (Flow)

1. User fills the form: Source, Destination, From Date, To Date
2. `crew.py` creates all 5 agents and tasks
3. **Sequential execution** begins:
   - `PlannerAgent` runs first → produces execution strategy
   - `TravelAgent`, `HotelAgent`, `InfoAgent` run with Planner's context
   - `ItineraryAgent` runs last with context from ALL previous agents
4. Each agent uses **MCP tools** (web search + weather) to fetch real data
5. Results displayed in 5 Streamlit tabs + downloadable report

---

## 🔧 Customization

### Change LLM model
Edit `.env`:
```env
# Groq (free, fast)
MODEL_NAME=groq/llama-3.3-70b-versatile

# OpenAI
MODEL_NAME=gpt-4o-mini

# Anthropic
MODEL_NAME=claude-3-5-haiku-20241022
```

### Add more agents
In `agents/travel_agents.py` → create new agent
In `agents/travel_tasks.py` → create new task
In `crew.py` → add to agents list, tasks list, set context

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `AuthenticationError` | Check your API key is correctly set in `.env` or sidebar |
| Agents give generic answers | Add `SERPER_API_KEY` for real web search results |
| Slow execution | Normal — 5 agents × multiple LLM calls = 3-6 min |
| `ModuleNotFoundError` | Run from `smart_travel_planner/` directory |
| Weather shows "estimated" | Add `OPENWEATHER_API_KEY` to `.env` |