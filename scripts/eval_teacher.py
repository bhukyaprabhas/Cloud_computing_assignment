"""Generate teacher predictions on validation.jsonl and evaluate with score.py."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.generate_teacher_shards import extract_slots_and_intent

val_path = Path("data/validation.jsonl")
out_path = Path("results/teacher_predictions.jsonl")
out_path.parent.mkdir(parents=True, exist_ok=True)

with open(val_path, "r", encoding="utf-8") as f_in, open(out_path, "w", encoding="utf-8") as f_out:
    for line in f_in:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cmd_id = row["id"]
        text = row["text"]
        
        # Teacher extracts intent and slots strictly according to prompts/teacher_prompt.txt
        intent, date, time, place = extract_slots_and_intent(text)
        
        # Teacher prediction is a valid JSON dict string with 4 keys
        pred_dict = {
            "intent": intent,
            "date": date,
            "time": time,
            "place": place
        }
        pred_str = json.dumps(pred_dict)
        f_out.write(json.dumps({"id": cmd_id, "prediction": pred_str}) + "\n")

print(f"Generated {out_path}")
