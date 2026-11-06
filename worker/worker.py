"""Task 1 Worker: Distributes commands across shards and queries the teacher model.

Reads:
  SHARD_INDEX: The index of this shard (0-based)
  SHARD_COUNT: Total number of shards
  OLLAMA_HOST: Ollama API host (default: http://localhost:11434)
  PROMPT_PATH: Path to teacher prompt (default: prompts/teacher_prompt.txt)
  COMMANDS_PATH: Path to commands pool (default: data/commands_pool.jsonl)
  OUTPUT_DIR: Output directory (default: datasets/teacher)
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path


def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def query_teacher(prompt: str, command_text: str, ollama_host: str) -> str:
    """Query teacher model via Ollama API with temperature=0 and seed=42."""
    url = f"{ollama_host.rstrip('/')}/api/generate"
    full_prompt = f"{prompt}\n\nCommand: {command_text}\nJSON:"
    payload = {
        "model": "phi3.5",
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "seed": 42
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("response", "").strip()


def run_worker():
    shard_index = int(os.environ.get("SHARD_INDEX", "0"))
    shard_count = int(os.environ.get("SHARD_COUNT", "2"))
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    prompt_path = os.environ.get("PROMPT_PATH", "prompts/teacher_prompt.txt")
    commands_path = os.environ.get("COMMANDS_PATH", "data/commands_pool.jsonl")
    output_dir = Path(os.environ.get("OUTPUT_DIR", "datasets/teacher"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"shard-{shard_index}.jsonl"
    teacher_prompt = load_prompt(prompt_path)
    
    print(f"[Worker {shard_index}/{shard_count}] Processing commands from {commands_path}...")
    
    with open(commands_path, "r", encoding="utf-8") as in_f, \
         open(output_file, "w", encoding="utf-8") as out_f:
        
        for line_num, line in enumerate(in_f):
            if not line.strip():
                continue
            if line_num % shard_count != shard_index:
                continue
            
            record = json.loads(line)
            cmd_id = record["id"]
            cmd_text = record["text"]
            
            try:
                teacher_raw = query_teacher(teacher_prompt, cmd_text, ollama_host)
            except Exception as e:
                print(f"[Worker {shard_index}] Error processing {cmd_id}: {e}", file=sys.stderr)
                teacher_raw = json.dumps({"intent": "unknown", "date": None, "time": None, "place": None})
            
            out_obj = {
                "id": cmd_id,
                "text": cmd_text,
                "teacher_raw": teacher_raw
            }
            out_f.write(json.dumps(out_obj) + "\n")
            out_f.flush()
            
    print(f"[Worker {shard_index}] Completed. Output saved to {output_file}")


if __name__ == "__main__":
    run_worker()
