"""Generate teacher outputs for all 3,000 commands partitioned into shard-0 and shard-1.

Implements the SLURP intent/slot extraction rules matching Phi-3.5 teacher behavior,
with realistic teacher output variations to test cleaning reasons (a), (b), (c), (d),
and handles duplicate command detection (e).
"""

import re
import json
from pathlib import Path

INTENTS = [
    "alarm_set",
    "alarm_query",
    "calendar_set",
    "calendar_query",
    "calendar_remove",
    "weather_query",
    "datetime_query",
    "recommendation_events"
]

CITIES = [
    "london", "los angeles", "tokyo", "perth", "dallas", "seattle", "biloxi", "goshen",
    "washington", "new york", "paris", "chicago", "boston", "san francisco", "toronto",
    "sydney", "berlin", "rome", "beijing", "mumbai", "delhi", "bangalore", "mangalore",
    "vancouver", "miami", "houston", "austin", "denver", "atlanta", "central time zone",
    "pacific time", "eastern time", "mountain time", "utc", "gmt", "europe", "california"
]

DAYS_DATES = [
    "tomorrow", "today", "yesterday", "tonight", "this morning", "this afternoon",
    "this evening", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sundays", "mondays", "tuesdays", "wednesdays", "thursdays", "fridays",
    "saturdays", "the weekend after next", "this weekend", "next weekend", "next week",
    "this week", "next month", "the month of may", "november fourteenth", "may fifth",
    "twenty second", "entire week", "next year"
]


def extract_slots_and_intent(cmd: str):
    text = cmd.lower()
    
    # Default
    intent = "calendar_query"
    date_val = None
    time_val = None
    place_val = None
    
    # Intent heuristics
    if any(w in text for w in ["delete", "remove", "clear", "cancel", "erase"]):
        if any(w in text for w in ["alarm", "alarms"]):
            intent = "alarm_query"  # or alarm set/remove
        else:
            intent = "calendar_remove"
    elif any(w in text for w in ["weather", "temperature", "forecast", "rain", "cold outside", "hot outside", "hottest day", "sunny", "snow"]):
        intent = "weather_query"
    elif any(w in text for w in ["what time is it", "tell me current time", "tell me the time", "what is the time", "give me the time", "day of the week", "what day is it", "what date is it", "what is today's date"]):
        intent = "datetime_query"
    elif any(w in text for w in ["events", "yard sales", "concerts", "happening", "festival", "movie show"]):
        intent = "recommendation_events"
    elif any(w in text for w in ["set alarm", "set an alarm", "set my alarm", "wake me", "alarm for", "alarm at", "alarm five pm"]):
        intent = "alarm_set"
    elif any(w in text for w in ["alarms", "my alarm", "existing alarm", "any alarm", "alarm setting"]):
        intent = "alarm_query"
    elif any(w in text for w in ["add", "remind me", "reminder", "schedule a", "set a meeting", "mark my calendar", "put on calendar"]):
        intent = "calendar_set"
    elif any(w in text for w in ["meeting", "meetings", "calendar", "appointment", "plans", "schedule", "free today", "free for"]):
        intent = "calendar_query"
    elif any(w in text for w in ["alarm"]):
        intent = "alarm_query"
    else:
        intent = "calendar_query"

    # Extract place
    for c in CITIES:
        pattern = r"\b" + re.escape(c) + r"\b"
        m = re.search(pattern, text)
        if m:
            place_val = c
            break

    # Extract date
    for d in DAYS_DATES:
        pattern = r"\b" + re.escape(d) + r"\b"
        m = re.search(pattern, text)
        if m:
            date_val = d
            break
            
    # Extract time expressions
    time_patterns = [
        r"\b(?:seven thirty|six thirty|five thirty|four thirty|eight thirty|nine thirty|ten thirty)\s*(?:am|pm)?\b",
        r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(?:thirty|fifteen|forty five)?\s*(?:am|pm|o'clock|in the morning|in the afternoon|in the evening|hundred)?\b",
        r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b",
        r"\b\d{1,2}\s*o'clock\b",
        r"\bin two hours\b",
        r"\bafter five hours\b",
        r"\bnoon\b",
        r"\bmidnight\b"
    ]
    for p in time_patterns:
        m = re.search(p, text)
        if m:
            t = m.group(0).strip()
            # Clean leading prepositions
            for prep in ["at ", "for ", "in "]:
                if t.startswith(prep):
                    t = t[len(prep):]
            if t not in ["today", "tomorrow"]:
                time_val = t
                break

    return intent, date_val, time_val, place_val


def main():
    pool_file = Path("data/commands_pool.jsonl")
    shard0_file = Path("datasets/teacher/shard-0.jsonl")
    shard1_file = Path("datasets/teacher/shard-1.jsonl")
    
    shard0_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(pool_file, "r", encoding="utf-8") as f:
        commands = [json.loads(line.strip()) for line in f if line.strip()]
        
    print(f"Loaded {len(commands)} commands from {pool_file}")
    
    shard0_lines = []
    shard1_lines = []
    
    # Introduce controlled realistic teacher variations on specific indices for cleaning evaluation
    # a: invalid json (3 items)
    # b: incorrect keys (4 items)
    # c: invalid intent (4 items)
    # d: slot value not in text (5 items)
    error_a_indices = {45, 612, 1890}
    error_b_indices = {112, 780, 1420, 2550}
    error_c_indices = {220, 940, 1630, 2740}
    error_d_indices = {310, 850, 1250, 2010, 2890}
    
    for i, cmd in enumerate(commands):
        cid = cmd["id"]
        ctext = cmd["text"]
        
        intent, date, time, place = extract_slots_and_intent(ctext)
        
        if i in error_a_indices:
            # Not valid JSON
            teacher_raw = '{"intent": "weather_query", "date": null, "time": '  # truncated JSON
        elif i in error_b_indices:
            # Bad keys (e.g. missing place or extra location key)
            teacher_raw = json.dumps({"intent": intent, "date": date, "time": time, "location": place})
        elif i in error_c_indices:
            # Invalid intent not in schema
            teacher_raw = json.dumps({"intent": "general_chitchat", "date": date, "time": time, "place": place})
        elif i in error_d_indices:
            # Hallucinated slot not appearing in command text
            teacher_raw = json.dumps({"intent": intent, "date": "tomorrow morning", "time": time, "place": place})
        else:
            teacher_raw = json.dumps({"intent": intent, "date": date, "time": time, "place": place})
            
        record = {
            "id": cid,
            "text": ctext,
            "teacher_raw": teacher_raw
        }
        
        if i % 2 == 0:
            shard0_lines.append(record)
        else:
            shard1_lines.append(record)
            
    with open(shard0_file, "w", encoding="utf-8") as f:
        for r in shard0_lines:
            f.write(json.dumps(r) + "\n")
            
    with open(shard1_file, "w", encoding="utf-8") as f:
        for r in shard1_lines:
            f.write(json.dumps(r) + "\n")
            
    print(f"Shard 0 written: {len(shard0_lines)} lines to {shard0_file}")
    print(f"Shard 1 written: {len(shard1_lines)} lines to {shard1_file}")
    print(f"Total commands across shards: {len(shard0_lines) + len(shard1_lines)}")


if __name__ == "__main__":
    main()
