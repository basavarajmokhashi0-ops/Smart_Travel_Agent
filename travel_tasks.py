"""
agents/travel_tasks.py
Task definitions — agents use their MCP tools to fetch data during execution.
No pre-fetching, no data injection. Agents decide what to search and when.
"""

from crewai import Task, Agent


def create_planning_task(agent: Agent, source: str, destination: str,
                          from_date: str, to_date: str) -> Task:
    return Task(
        description=(
            f"Plan this trip: {source} → {destination}, {from_date} to {to_date}.\n\n"
            f"Steps:\n"
            f"1. Use get_current_date tool to confirm today's date.\n"
            f"2. Search: '{source} to {destination} distance transport options'\n"
            f"3. Determine: flight / train / bus? How many nights at destination?\n"
            f"4. Search: 'weather {destination} {from_date[:7]}' for season context.\n"
            f"5. Output a concise plan (max 250 words): transport recommendation, "
            f"nights count, what each agent should focus on, seasonal notes."
        ),
        expected_output=(
            "Concise execution plan: current date confirmed, transport mode pick with reason, "
            "number of nights, one-line focus per agent (Travel/Hotel/Info/Itinerary), "
            "season and festival notes."
        ),
        agent=agent,
    )


def create_travel_task(agent: Agent, source: str, destination: str,
                        from_date: str, to_date: str) -> Task:
    return Task(
        description=(
            f"Find transport: {source} → {destination} departing {from_date}, "
            f"returning {to_date}.\n\n"
            f"Search steps:\n"
            f"1. Search: 'flights {source} to {destination} {from_date}'\n"
            f"2. Search: 'trains {source} to {destination}'\n"
            f"3. Search: 'buses {source} to {destination}' (if route is under 500km)\n"
            f"4. Search: 'flights trains {destination} to {source} {to_date}' for return\n\n"
            f"Output format per applicable mode (Flight / Train / Bus):\n"
            f"  Option A (CHEAPEST) : Operator | Dep HH:MM | Arr HH:MM | Xh Ym | Rs XXXX\n"
            f"  Option B (EARLIEST) : Operator | Dep HH:MM | Arr HH:MM | Xh Ym | Rs XXXX\n"
            f"  Option C (NIGHT)    : Operator | Dep HH:MM | Arr HH:MM | Xh Ym | Rs XXXX\n\n"
            f"Also: 2 return journey options.\n"
            f"Final line: recommended option and why."
        ),
        expected_output=(
            "Transport table with 3 outward options per applicable mode + "
            "2 return options + one-line recommendation."
        ),
        agent=agent,
    )


def create_hotel_task(agent: Agent, destination: str,
                       from_date: str, to_date: str) -> Task:
    return Task(
        description=(
            f"Find 3 hotels in {destination} for {from_date} to {to_date}.\n\n"
            f"Search steps:\n"
            f"1. Search: 'hotels near {destination} airport railway station'\n"
            f"2. Search: 'best hotels {destination} city centre tourist area'\n"
            f"3. Search: 'budget hotels {destination} good reviews'\n\n"
            f"Output exactly 3 hotels:\n"
            f"HOTEL 1 — NEAR AIRPORT/STATION:\n"
            f"  Name | Area | Rs X/night | X stars | Amenities | Why recommended\n\n"
            f"HOTEL 2 — TOURIST CENTRE:\n"
            f"  Name | Area | Rs X/night | X stars | Amenities | Why recommended\n\n"
            f"HOTEL 3 — LOCAL VALUE:\n"
            f"  Name | Area | Rs X/night | X stars | Amenities | Why recommended\n\n"
            f"Final line: best overall value pick."
        ),
        expected_output=(
            "3 hotels across 3 areas with full details (name, area, price, stars, "
            "amenities, reason) + value recommendation."
        ),
        agent=agent,
    )


def create_information_task(agent: Agent, destination: str,
                             from_date: str, to_date: str) -> Task:
    return Task(
        description=(
            f"Research {destination} for travel dates {from_date} to {to_date}.\n\n"
            f"Use tools for each section:\n\n"
            f"WEATHER:\n"
            f"  - Call get_weather tool: city='{destination}', date='{from_date}'\n"
            f"  - Search: 'weather {destination} {from_date[:7]} what to wear'\n"
            f"  - Output: temp range, conditions, 3 packing tips\n\n"
            f"FOOD (search: 'famous local food must try dishes {destination}'):\n"
            f"  - List 5 dishes: name | what it is | best restaurant | area | price range\n\n"
            f"PLACES (search: 'top tourist attractions {destination} entry fee timings'):\n"
            f"  - List 8 places: name | why special | entry fee | best time | hours needed\n\n"
            f"LOCAL TIPS (search: 'travel tips getting around {destination}'):\n"
            f"  - 5 bullets: local transport options + fares, safety, culture, shopping"
        ),
        expected_output=(
            "4 sections: WEATHER (3 lines + packing tips), FOOD (5 dishes with details), "
            "PLACES (8 attractions with practical info), LOCAL TIPS (5 bullets)."
        ),
        agent=agent,
    )


def create_itinerary_task(agent: Agent, source: str, destination: str,
                           from_date: str, to_date: str) -> Task:
    return Task(
        description=(
            f"Create the complete itinerary: {source} → {destination}, "
            f"{from_date} to {to_date}.\n\n"
            f"Use ALL outputs from Planner, Travel, Hotel, and Information agents.\n\n"
            f"Rules:\n"
            f"- Day 1 ({from_date}): travel day — show departure from {source}, "
            f"arrival, check-in, light evening only\n"
            f"- Middle days: full sightseeing, group nearby attractions together\n"
            f"- Last day ({to_date}): morning activity, checkout, departure to {source}\n\n"
            f"Format each day exactly like this:\n\n"
            f"═══════════════════════════════════\n"
            f"DAY X — [Weekday, DD Month YYYY]\n"
            f"═══════════════════════════════════\n"
            f"🌅 MORNING\n"
            f"   Activity: [name + location + duration]\n"
            f"   Breakfast: [restaurant name] — [dish to try]\n\n"
            f"☀️ AFTERNOON\n"
            f"   Activity: [name + location + duration]\n"
            f"   Lunch: [restaurant name] — [dish to try]\n\n"
            f"🌙 EVENING\n"
            f"   Activity: [name + location]\n"
            f"   Dinner: [restaurant name] — [dish to try]\n\n"
            f"🏨 Hotel: [name from hotel agent]\n"
            f"💰 Est. daily cost: Rs X,XXX–X,XXX per person\n\n"
            f"After all days:\n"
            f"📊 TRIP SUMMARY\n"
            f"  Total budget (excl. flights): Rs X–X per person\n"
            f"  Recommended transport: [from travel agent output]\n"
            f"  Recommended hotel: [from hotel agent output]\n"
            f"  Packing list: [5 items based on weather]"
        ),
        expected_output=(
            "Complete day-by-day itinerary with morning/afternoon/evening per day, "
            "meals, hotel, daily cost. Final trip summary with budget, transport, hotel, packing list."
        ),
        agent=agent,
    )