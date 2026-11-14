from io import StringIO
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

import pandas as pd
import requests

URL = "https://www.brederodes.nl/273/uitslagen--programma/"

def get_matches() -> pd.DataFrame:
    response = requests.get(URL, timeout=15)
    response.raise_for_status()
    
    tables = pd.read_html(
        StringIO(response.text),
        converters={"Datum": str, "Tijd": str})
    
    for table in tables:
        required_columns = {"Datum", "Tijd", "Thuis", "Uit"}
        
        if required_columns.issubset(table.columns):
            return table
    
    raise ValueError("No matches found")

MONTHS = {
    "jan": 1, "feb": 2, "mrt": 3,
    "apr": 4, "mei": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9,
    "okt": 10, "nov": 11, "dec": 12,
}


def create_calendar(matches: pd.DataFrame) -> Path:
    calendar = Calendar()
    calendar.add("prodid", "-//Brederodes 6//NL")
    calendar.add("version", "2.0")
    calendar.add("X-WR-CALNAME", "Brederodes Zaterdag 6")

    dutch_timezone = ZoneInfo("Europe/Amsterdam")
    now = datetime.now(dutch_timezone)

    # Season spans 2 calendar years
    season_start = now.year if now.month >= 7 else now.year - 1

    for _, match in matches.iterrows():
        day, month_name = str(match["Datum"]).lower().split()[:2]
        month = MONTHS[month_name[:3]]
        year = season_start if month >= 7 else season_start + 1

        time = str(match["Tijd"]).replace(":", ".")
        hour, minute = map(int, time.split(".")[:2])

        start = datetime(
            year, month, int(day), hour, minute,
            tzinfo=dutch_timezone,
        )

        home = str(match["Thuis"]).strip()
        away = str(match["Uit"]).strip()
        match_type = str(match.get("Type", "")).strip()

        event = Event()
        event.add("summary", f"{home} - {away}")
        event.add("dtstart", start)
        event.add("dtend", start + timedelta(hours=2))
        event.add("dtstamp", datetime.now(timezone.utc))

        # ID stays same if time changes.
        match_key = f"{season_start}|{home}|{away}|{match_type}"
        match_id = sha256(match_key.encode()).hexdigest()[:24]

        event.add("uid", f"{match_id}@brederodes-calendar")
        event.add("description", "Wedstrijdprogramma VV Brederodes 6")

        calendar.add_component(event)

    output = Path("docs/brederodes6.ics")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(calendar.to_ical())

    return output


if __name__ == "__main__":
    matches = get_matches()
    output = create_calendar(matches)
    
    print(f"{len(matches)} matches processed")
    print(f"Calender saved: {output}")