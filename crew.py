"""
crew.py
CrewAI orchestration with Gemini 2.5 Flash + real MCP tool calling.

Flow:
  Planner Agent  → uses get_current_date + web_search tools
  Travel Agent   → uses web_search tool  
  Hotel Agent    → uses web_search tool
  Info Agent     → uses web_search + get_weather tools
  Itinerary Agent→ uses web_search tool (for any extra lookups)
  
  All tool calls happen at agent runtime via Gemini function calling.
  No pre-fetching — agents decide what to search and when.
"""

import os
import time
import logging
from crewai import Crew, Process

from agents.travel_agents import (
    create_planner_agent,
    create_travel_agent,
    create_hotel_agent,
    create_information_agent,
    create_itinerary_agent,
)
from agents.travel_tasks import (
    create_planning_task,
    create_travel_task,
    create_hotel_task,
    create_information_task,
    create_itinerary_task,
)

log = logging.getLogger(__name__)


def _run_with_retry(crew: Crew, max_retries: int = 4) -> object:
    """Retry on rate limit errors with exponential backoff."""
    wait_times = [20, 40, 80, 160]
    for attempt in range(max_retries):
        try:
            return crew.kickoff()
        except Exception as exc:
            err = str(exc).lower()
            is_rate_limit = any(kw in err for kw in
                ["rate_limit", "ratelimit", "429", "quota", "resource_exhausted"])
            if is_rate_limit and attempt < max_retries - 1:
                wait = wait_times[attempt]
                print(f"\n⏳ Rate limit — waiting {wait}s "
                      f"(attempt {attempt+1}/{max_retries})...\n")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("Max retries exceeded.")


def run_travel_crew(
    source: str,
    destination: str,
    from_date: str,
    to_date: str,
) -> dict:
    """
    Runs the 5-agent travel planning crew.
    Agents use MCP tools (web_search, get_weather, get_current_date) at runtime.
    Returns dict: plan, travel, hotels, information, itinerary, raw
    """

    # ── Build agents (with MCP tools attached) ────────────────────────────────
    planner_agent   = create_planner_agent()
    travel_agent    = create_travel_agent()
    hotel_agent     = create_hotel_agent()
    info_agent      = create_information_agent()
    itinerary_agent = create_itinerary_agent()

    # ── Build tasks ───────────────────────────────────────────────────────────
    plan_task      = create_planning_task(planner_agent, source, destination, from_date, to_date)
    travel_task    = create_travel_task(travel_agent, source, destination, from_date, to_date)
    hotel_task     = create_hotel_task(hotel_agent, destination, from_date, to_date)
    info_task      = create_information_task(info_agent, destination, from_date, to_date)
    itinerary_task = create_itinerary_task(itinerary_agent, source, destination, from_date, to_date)

    # ── Wire context (each agent sees previous agents' outputs) ───────────────
    travel_task.context    = [plan_task]
    hotel_task.context     = [plan_task]
    info_task.context      = [plan_task]
    itinerary_task.context = [plan_task, travel_task, hotel_task, info_task]

    # ── Assemble and run ──────────────────────────────────────────────────────
    crew = Crew(
        agents=[planner_agent, travel_agent, hotel_agent, info_agent, itinerary_agent],
        tasks=[plan_task, travel_task, hotel_task, info_task, itinerary_task],
        process=Process.sequential,
        verbose=True,
        memory=False,
    )

    _run_with_retry(crew)

    # ── Collect outputs ───────────────────────────────────────────────────────
    outputs = {}
    for name, task in zip(
        ["plan", "travel", "hotels", "information", "itinerary"],
        [plan_task, travel_task, hotel_task, info_task, itinerary_task],
    ):
        try:
            outputs[name] = task.output.raw if task.output else "No output generated."
        except Exception:
            outputs[name] = "Output unavailable."

    outputs["raw"] = str(outputs.get("itinerary", ""))
    return outputs


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = run_travel_crew("Delhi", "Goa", "2024-12-20", "2024-12-25")
    print("\n=== ITINERARY ===\n")
    print(result["itinerary"])