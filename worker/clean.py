"""Clean raw teacher outputs from all shards and produce train.jsonl and train.sha256.

Filters applied in order:
  (a) replies that are not valid JSON
  (b) replies whose keys are not exactly intent, date, time, and place
  (c) replies whose intent is not one of the eight
  (d) replies with a slot value that is neither null nor text that appears in the command
  (e) duplicate commands (keep the one with the smallest id)

Ensures:
  input = (a) + (b) + (c) + (d) + duplicates + kept
"""

import os
import sys
import json
import glob
import hashlib
from pathlib import Path

VALID_INTENTS = {
    "alarm_set",
    "alarm_query",
    "calendar_set",
    "calendar_query",
    "calendar_remove",
    "weather_query",
    "datetime_query",
    "recommendation_events"
}

REQUIRED_KEYS = {"intent", "date", "time", "place"}


def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def clean_dataset(shard_pattern="datasets/teacher/shard-*.jsonl",
                  out_dir="datasets/v1"):
    shard_files = sorted(glob.glob(shard_pattern))
    if not shard_files:
        # Fallback to local data if no shards found
        shard_files = sorted(glob.glob("datasets/teacher/*.jsonl"))
    
    if not shard_files:
        sys.exit(f"Error: No shard files found matching {shard_pattern}")
    
    print(f"Reading {len(shard_files)} shard file(s): {shard_files}")
    
    all_records = []
    for sf in shard_files:
        with open(sf, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_records.append(json.loads(line))
                    
    # Sort all input records initially by id
    all_records.sort(key=lambda x: x["id"])
    
    total_input = len(all_records)
    rejected_a = 0
    rejected_b = 0
    rejected_c = 0
    rejected_d = 0
    duplicates = 0
    
    valid_after_d = []
    
    for r in all_records:
        raw = r.get("teacher_raw", "")
        # Check (a): valid JSON
        try:
            if isinstance(raw, dict):
                parsed = raw
            else:
                parsed = json.loads(str(raw).strip())
            if not isinstance(parsed, dict):
                rejected_a += 1
                continue
        except Exception:
            rejected_a += 1
            continue
            
        # Check (b): keys exactly intent, date, time, place
        if set(parsed.keys()) != REQUIRED_KEYS:
            rejected_b += 1
            continue
            
        # Check (c): intent is one of the eight
        if parsed.get("intent") not in VALID_INTENTS:
            rejected_c += 1
            continue
            
        # Check (d): slot value is either null or text that appears in command
        cmd_text = r.get("text", "")
        cmd_lower = cmd_text.lower()
        slot_error = False
        for slot in ["date", "time", "place"]:
            val = parsed.get(slot)
            if val is not None:
                if not isinstance(val, str):
                    slot_error = True
                    break
                if val.strip().lower() not in cmd_lower:
                    slot_error = True
                    break
        if slot_error:
            rejected_d += 1
            continue
            
        valid_after_d.append({
            "id": r["id"],
            "text": cmd_text,
            "intent": parsed["intent"],
            "date": parsed["date"],
            "time": parsed["time"],
            "place": parsed["place"],
            "teacher_raw": json.dumps(parsed, ensure_ascii=False)
        })
        
    # Check (e): duplicate commands (keep the one with smallest id)
    # Since valid_after_d is already sorted by id, the first occurrence has the smallest id
    seen_texts = set()
    kept_records = []
    for item in valid_after_d:
        normalized_text = item["text"].strip().lower()
        if normalized_text in seen_texts:
            duplicates += 1
        else:
            seen_texts.add(normalized_text)
            kept_records.append(item)
            
    # Kept records are in id order
    kept_records.sort(key=lambda x: x["id"])
    kept_count = len(kept_records)
    
    # Verify invariant: input = (a) + (b) + (c) + (d) + duplicates + kept
    assert total_input == (rejected_a + rejected_b + rejected_c + rejected_d + duplicates + kept_count), \
        f"Mismatch: {total_input} != {rejected_a + rejected_b + rejected_c + rejected_d + duplicates + kept_count}"
        
    # Write output
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    train_file = out_path / "train.jsonl"
    sha_file = out_path / "train.sha256"
    stats_file = out_path / "cleaning_stats.json"
    
    with open(train_file, "w", encoding="utf-8") as f:
        for item in kept_records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    checksum = compute_sha256(train_file)
    with open(sha_file, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  train.jsonl\n")
        
    stats = {
        "input_records": total_input,
        "rejected_a_invalid_json": rejected_a,
        "rejected_b_bad_keys": rejected_b,
        "rejected_c_invalid_intent": rejected_c,
        "rejected_d_slot_not_in_command": rejected_d,
        "duplicates": duplicates,
        "records_kept": kept_count,
        "sha256": checksum
    }
    
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print("\n--- Cleaning Summary ---")
    print(f"Total Input:                   {total_input}")
    print(f"(a) Invalid JSON:              {rejected_a}")
    print(f"(b) Incorrect Keys:            {rejected_b}")
    print(f"(c) Invalid Intent:            {rejected_c}")
    print(f"(d) Slot Not In Command Text:  {rejected_d}")
    print(f"(e) Duplicate Commands:        {duplicates}")
    print(f"Records Kept:                  {kept_count}")
    print(f"Checksum:                      {checksum}")
    print(f"Verification Check:            {total_input} == {rejected_a + rejected_b + rejected_c + rejected_d + duplicates + kept_count} (PASS)")
    print(f"Outputs written to:            {train_file} and {sha_file}")


if __name__ == "__main__":
    clean_dataset()
