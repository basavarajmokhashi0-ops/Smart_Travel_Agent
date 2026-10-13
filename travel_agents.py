"""
agents/travel_agents.py
All 5 CrewAI agents using Gemini 2.5 Flash with real MCP tools.

Gemini supports standard OpenAI-compatible function calling.
CrewAI's tool schemas work correctly — no format mismatch like with Groq.
Agents invoke web_search, get_weather, get_current_date at runtime.
"""

import os
from crewai import Agent
from tools.mcp_tools import web_search_tool, weather_tool, current_date_tool

GEMINI_MODEL = "gemini/gemini-2.5-flash-lite"


# ── 1. PLANNER AGENT ──────────────────────────────────────────────────────────
def create_planner_agent() -> Agent:
    return Agent(
        role="Master Travel Planner",
        goal=(
            "Analyze the trip request and produce a structured execution plan. "
            "First get the current date using the tool. "
            "Determine the best transport mode between source and destination. "
            "Estimate the number of sightseeing days. "
            "Note the season and any festivals at the destination."
        ),
        backstory=(
            "Expert Indian travel coordinator with 15 years experience. "
            "Deep knowledge of Indian geography — which city pairs need flights vs trains vs buses, "
            "typical durations, peak seasons, and popular tourist circuits. "
            "Always checks the current date before planning."
        ),
        tools=[current_date_tool, web_search_tool],
        llm=GEMINI_MODEL,
        verbose=False,
        allow_delegation=False,
        max_iter=1,
    )


# ── 2. TRAVEL AGENT ───────────────────────────────────────────────────────────
def create_travel_agent() -> Agent:
    return Agent(
        role="Transport Research Specialist",
        goal=(
            "Find the best transport options between source and destination. "
            "Search for real flights, trains, and buses. "
            "Provide exactly 3 options per applicable mode: cheapest, earliest, night departure. "
            "Per option: Operator | Departure | Arrival | Duration | Price (Rs). "
            "Also find 2 return journey options. End with a recommendation."
        ),
        backstory=(
            "Indian transport logistics expert. Knows IndiGo, Air India, SpiceJet, Akasa Air, "
            "Rajdhani Express, Shatabdi, Vande Bharat, Duronto, "
            "KSRTC, MSRTC, TSRTC, private Volvo operators. "
            "Always searches for real data — never guesses prices or schedules."
        ),
        tools=[web_search_tool],
        llm=GEMINI_MODEL,
        verbose=False,
        allow_delegation=False,
        max_iter=1,
    )


# ── 3. HOTEL AGENT ────────────────────────────────────────────────────────────
def create_hotel_agent() -> Agent:
    return Agent(
        role="Accommodation Research Specialist",
        goal=(
            "Find 3 hotels in different areas of the destination: "
            "(1) near airport or main transit hub, "
            "(2) central tourist area, "
            "(3) local budget-friendly neighborhood. "
            "Per hotel: Name | Area | Price/night (Rs) | Stars | Top amenities | Why recommended. "
            "Search for real, bookable hotels."
        ),
        backstory=(
            "Indian accommodation expert. Knows hotel landscapes of all major tourist destinations. "
            "Prioritizes real hotels with genuine reviews. "
            "Covers budget to mid-range — good value is the priority."
        ),
        tools=[web_search_tool],
        llm=GEMINI_MODEL,
        verbose=False,
        allow_delegation=False,
        max_iter=1,
    )


# ── 4. INFORMATION AGENT ──────────────────────────────────────────────────────
def create_information_agent() -> Agent:
    return Agent(
        role="Destination Intelligence Specialist",
        goal=(
            "Gather 4 sections of destination intelligence: "
            "(1) Weather — use the weather tool, give temp range and packing advice. "
            "(2) Food — search for 5 must-try local dishes with restaurant names and prices. "
            "(3) Places — search for 8 must-visit attractions with entry fees and timings. "
            "(4) Local tips — getting around, safety, culture, shopping. "
            "Use tools for all sections — do not guess."
        ),
        backstory=(
            "Seasoned Indian travel writer and destination expert. "
            "Has visited 200+ Indian cities. Knows hidden gems alongside popular spots. "
            "Always uses real search data — not generic tourist brochure content."
        ),
        tools=[web_search_tool, weather_tool],
        llm=GEMINI_MODEL,
        verbose=False,
        allow_delegation=False,
        max_iter=1,
    )


# ── 5. ITINERARY AGENT ────────────────────────────────────────────────────────
def create_itinerary_agent() -> Agent:
    return Agent(
        role="Master Itinerary Architect",
        goal=(
            "Synthesize all gathered data into a day-by-day itinerary. "
            "Day 1 = travel/arrival day, light evening activity only. "
            "Middle days = full sightseeing, group geographically nearby attractions. "
            "Last day = morning activity then departure. "
            "Per day: Morning/Afternoon/Evening activities + meal recommendations + hotel + daily cost. "
            "End with: total budget estimate, recommended transport, recommended hotel, 5-item packing list."
        ),
        backstory=(
            "Expert trip planner who synthesizes research into perfect itineraries. "
            "Groups nearby attractions to minimize travel time within the city. "
            "Realistic — never over-packs a day. Always references the actual hotels and "
            "restaurants found by the other agents."
        ),
        tools=[web_search_tool],
        llm=GEMINI_MODEL,
        verbose=False,
        allow_delegation=False,
        max_iter=1,
    )