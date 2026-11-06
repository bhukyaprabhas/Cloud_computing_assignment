"""Evaluate trained student model on validation.jsonl."""

import json
import re
from pathlib import Path
import torch
torch.set_num_threads(2)
from transformers import AutoTokenizer, AutoModelForCausalLM

model_dir = "models/v1"
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForCausalLM.from_pretrained(model_dir).float()
model.eval()

val_path = Path("data/validation.jsonl")
out_path = Path("results/student_predictions.jsonl")
out_path.parent.mkdir(parents=True, exist_ok=True)

with open(val_path, "r", encoding="utf-8") as f_in, open(out_path, "w", encoding="utf-8") as f_out:
    for line in f_in:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cmd_id = row["id"]
        text = row["text"]
        
        prompt = f"Command: {text}\nJSON:\n"
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=40,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=False
            )
        generated = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        
        # Extract first JSON object {...} if present
        match = re.search(r"\{.*?\}", generated, re.DOTALL)
        if match:
            prediction_str = match.group(0)
        else:
            prediction_str = generated
            
        f_out.write(json.dumps({"id": cmd_id, "prediction": prediction_str}) + "\n")

print(f"Generated {out_path}", flush=True)
