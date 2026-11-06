"""Run untrained Pythia-70m on validation.jsonl to produce baseline score."""

import json
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("EleutherAI/pythia-70m", local_files_only=True)
model = AutoModelForCausalLM.from_pretrained("EleutherAI/pythia-70m", local_files_only=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

val_path = Path("data/validation.jsonl")
out_path = Path("results/untrained_predictions.jsonl")
out_path.parent.mkdir(parents=True, exist_ok=True)

with open(val_path, "r", encoding="utf-8") as f_in, open(out_path, "w", encoding="utf-8") as f_out:
    for line in f_in:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cmd_id = row["id"]
        text = row["text"]
        
        prompt = f"Command: {text}\nJSON: "
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=40,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=False
            )
        generated = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        f_out.write(json.dumps({"id": cmd_id, "prediction": generated}) + "\n")

print(f"Generated {out_path}")
