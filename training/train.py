"""Task 2: Train EleutherAI/pythia-70m via Sequence-Level Knowledge Distillation on CPU.

Usage:
  python training/train.py [--config training/config.yaml] [--subset 50] [--version v1]
"""

import os
import sys
import yaml
import json
import random
import hashlib
import argparse
from pathlib import Path

import torch
torch.set_num_threads(2)
from torch.utils.data import Dataset, DataLoader
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def compute_dir_sha256(dir_path: Path, output_file: Path):
    """Compute sha256 of all files in dir_path and save to output_file."""
    lines = []
    for f in sorted(dir_path.glob("*")):
        if f.is_file() and f.name != output_file.name:
            sha = hashlib.sha256()
            with open(f, "rb") as fp:
                while chunk := fp.read(65536):
                    sha.update(chunk)
            lines.append(f"{sha.hexdigest()}  {f.name}\n")
    with open(output_file, "w", encoding="utf-8") as out:
        out.writelines(lines)
    print(f"Checksums saved to {output_file}", flush=True)


class CommandDataset(Dataset):
    def __init__(self, records, tokenizer, max_length=64):
        self.samples = []
        for r in records:
            cmd = r.get("text", "")
            raw_json = r.get("teacher_raw")
            if not raw_json:
                raw_json = json.dumps({
                    "intent": r.get("intent"),
                    "date": r.get("date"),
                    "time": r.get("time"),
                    "place": r.get("place")
                })
            
            prompt_prefix = f"Command: {cmd}\nJSON:\n"
            full_text = f"{prompt_prefix}{raw_json}\n"
            
            enc_full = tokenizer(
                full_text,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt"
            )
            input_ids = enc_full["input_ids"].squeeze(0)
            attention_mask = enc_full["attention_mask"].squeeze(0)
            
            # Mask out prompt prefix and padding tokens from loss calculation
            enc_prompt = tokenizer(prompt_prefix, truncation=True, max_length=max_length)
            prompt_len = min(len(enc_prompt["input_ids"]), max_length)
            
            labels = input_ids.clone()
            labels[attention_mask == 0] = -100
            labels[:prompt_len] = -100
            
            self.samples.append({
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels
            })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="training/config.yaml")
    parser.add_argument("--subset", type=int, default=None)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--data", default="datasets/v1/train.jsonl")
    args = parser.parse_args()

    # Support SUBSET from environment variable as well (for make train SUBSET=50)
    subset_env = os.environ.get("SUBSET")
    if subset_env and subset_env.isdigit():
        args.subset = int(subset_env)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    seed = cfg.get("seed", 42)
    lr = float(cfg.get("learning_rate", 1e-4))
    batch_size = int(cfg.get("batch_size", 8))
    num_epochs = int(cfg.get("num_epochs", 3))
    max_length = int(cfg.get("max_seq_length", 64))
    model_name = cfg.get("model_name", "EleutherAI/pythia-70m")

    # If training v2, add 1 epoch and change seed
    if args.version == "v2":
        num_epochs += 1
        seed += 1

    set_seed(seed)

    print(f"--- Training Pythia-70M ({args.version}) ---", flush=True)
    print(f"Seed: {seed}, Epochs: {num_epochs}, Batch Size: {batch_size}, LR: {lr}", flush=True)

    # Load data
    records = []
    with open(args.data, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    # Keep records in id order
    records.sort(key=lambda x: x["id"])

    # Limit to subset (default max 1500 as per Section 6)
    limit = args.subset if args.subset else min(1500, len(records))
    records = records[:limit]
    print(f"Loaded {len(records)} records for training (subset={limit}).", flush=True)

    # Tokenizer & Model
    print("Loading tokenizer and model...", flush=True)
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, local_files_only=True)
    except Exception:
        model = AutoModelForCausalLM.from_pretrained(model_name)

    # Convert to float32 to prevent float16 overflow on CPU
    model = model.float()
    device = torch.device("cpu")
    model.to(device)

    dataset = CommandDataset(records, tokenizer, max_length=max_length)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=lr,
        weight_decay=cfg.get("weight_decay", 0.01)
    )

    # Loss logging
    loss_csv = Path("training/loss.csv")
    loss_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(loss_csv, "w", encoding="utf-8") as f:
        f.write("epoch,loss\n")

    model.train()
    print("Starting training loop...", flush=True)
    for epoch in range(1, num_epochs + 1):
        total_loss = 0.0
        batches = 0
        for step, batch in enumerate(dataloader, 1):
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            if torch.isnan(loss):
                continue
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()
            batches += 1
            if step % 25 == 0 or step == len(dataloader):
                print(f"  [Epoch {epoch}] Batch {step}/{len(dataloader)} - batch loss: {loss.item():.4f}", flush=True)

        avg_loss = total_loss / max(batches, 1)
        print(f"Epoch {epoch}/{num_epochs} - Loss: {avg_loss:.4f}", flush=True)
        with open(loss_csv, "a", encoding="utf-8") as f:
            f.write(f"{epoch},{avg_loss:.4f}\n")

    # Save model and tokenizer
    out_dir = Path(f"models/{args.version}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving model and tokenizer to {out_dir}...", flush=True)
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)

    sha_file = out_dir / "model.sha256"
    compute_dir_sha256(out_dir, sha_file)
    print(f"Training completed for {args.version}.", flush=True)


if __name__ == "__main__":
    train()
