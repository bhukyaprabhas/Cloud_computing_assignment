# AI Use Disclosure and Verification Document (AI_USE.md)

**Course**: Cloud Computing (CS3081) Mini Project  
**Project**: Knowledge Distillation and Deployment of a Lightweight Command-Parsing Language Model on a Local Cloud  
**Student Name**: Bhukya Prabhas  
**Student Roll Number**: 230103031  
**GitHub Repository**: https://github.com/bhukyaprabhas/Cloud_computing_assignment  

---

## 1. Summary of AI Tools Utilized

In compliance with Section 6 and Section 7.6 of the project specification, AI-assisted development tools were used with full transparency and rigorous verification. The following AI tools and models were employed throughout the project:

| Tool / Model | Version / Provider | Scope of Application |
| :--- | :--- | :--- |
| **Google Antigravity AI Assistant** | Claude 3.7 Sonnet / Gemini 2.5 | Code drafting, bash/powershell scripting, Dockerfile optimization, Kubernetes manifest structuring, LaTeX report authoring. |
| **Phi-3.5-mini-instruct (Teacher)** | 3.8B Parameters (Microsoft / Ollama) | Teacher model for sequence-level knowledge distillation (`datasets/teacher/shard-*.jsonl`). Temperature: 0, Seed: 42. |
| **EleutherAI/pythia-70m (Student)** | 70M Parameters (EleutherAI / HF) | Base student model fine-tuned on CPU via sequence distillation. |

---

## 2. Detailed Task Breakdown & How AI Was Used

### Task 1: Object Storage and Parallel Teacher Labelling
- **AI Tool**: Antigravity Assistant & Phi-3.5-mini-instruct.
- **Usage**:
  - Drafting the worker sharding script (`worker/worker.py`) using modulus partitioning (`line_index % SHARD_COUNT == SHARD_INDEX`).
  - Generating raw teacher replies adhering strictly to `prompts/teacher_prompt.txt` with four-key JSON extraction.
  - Designing the cleaning pipeline (`worker/clean.py`) to systematically filter out bad outputs (a: invalid JSON, b: non-standard keys, c: invalid intent, d: slot hallucination, e: duplicates).
- **Verification Method**:
  - Validated mathematical partitioning invariant: every single command ID from `C0001` to `C3000` appeared in exactly one shard with zero duplicates and zero omissions.
  - Formally verified data cleaning identity: $\text{Total (3000)} = (a) + (b) + (c) + (d) + (e) + \text{Kept (2936)}$.
  - Cryptographically hashed dataset with SHA-256 (`eb73fe6451477fd0f7e498f3589150529d134ee3dddd0b435a45f6b1beb9de6a`).

### Task 2: Training the Student (Sequence-Level Distillation)
- **AI Tool**: Antigravity Assistant.
- **Usage**:
  - Formulating the PyTorch sequence-level knowledge distillation training loop (`training/train.py`).
  - Debugging CPU multi-threading lock contention and float16 underflow/overflow by converting the model to float32 and pinning thread count (`torch.set_num_threads(2)`).
  - Masking prompt prefix tokens (`labels[:prompt_len] = -100`) so loss is calculated purely on JSON output tokens.
- **Verification Method**:
  - Measured loss progression per epoch in `training/loss.csv`.
  - Executed `tools/score.py` independently on `data/validation.jsonl`:
    - Untrained baseline: 0.0% validity, 0.0% full frame.
    - Teacher baseline: 100.0% validity, 59.0% full frame.
    - Student model: 99.0% validity (exceeds $\ge 95\%$ requirement), 46.0% full frame (exceeds $\ge 29.5\%$ requirement).

### Task 3: The Inference Service in a Container
- **AI Tool**: Antigravity Assistant.
- **Usage**:
  - Drafting the FastAPI inference service (`service/app.py`) providing `/parse`, `/healthz`, and `/readyz`.
  - Structuring the multi-stage Dockerfile using CPU-only PyTorch wheels (`torch==2.11.0+cpu`) to keep image size well below the 2 GB threshold.
  - Implementing fault injection logic (`FAULT_INJECT=1`).
- **Verification Method**:
  - Unit tested all endpoints, headers (`X-Model-Version`, `X-Served-By`), and error handling using pytest (`tests/test_service.py`).
  - Verified container image footprint and memory ceiling under 1 CPU / 1 GiB constraints.

### Task 4: Kubernetes Deployment, Scaling, and Reliability
- **AI Tool**: Antigravity Assistant.
- **Usage**:
  - Writing declarative Kubernetes manifests (`k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/ingress.yaml`, `k8s/hpa.yaml`, `k8s/secret.yaml`).
  - Designing HPA configuration with target CPU utilization at 70%.
- **Verification Method**:
  - Validated syntax with `kubectl --dry-run=client`.
  - Simulated rolling update and rollback workflows, pod termination recovery, and traffic distribution across replicas.

### Task 5: Subnetting and Network Access Control (NACL)
- **AI Tool**: Antigravity Assistant.
- **Usage**:
  - Calculating VLSM prefix allocations for subnets `app`, `public`, `data`, and `management`.
  - Writing the JSON NACL rule table (`network/nacl.json`).
- **Verification Method**:
  - Tested rules against `network/packets_sample.jsonl` using `tools/nacl_sim.py --check`: achieved 100.0% match (6/6 packets).
  - Formally proved stateless packet routing, ephemeral port ranges (1024-65535), and rule priority precedence.

### Task 6: Reproducibility, Testing, and CI/CD
- **AI Tool**: Antigravity Assistant.
- **Usage**:
  - Writing `Makefile` (`make up`, `make down`, `make train`, `make test`, `make eval`).
  - Authoring GitHub Actions workflow (`.github/workflows/ci.yml`).
- **Verification Method**:
  - Verified local target execution with `make train SUBSET=50`.
  - Verified quality gate enforcement (`score.py --min-validity 95`).

---

## 3. Reflection on AI Independence & Critical Thinking

While AI tools dramatically accelerated boilerplate generation, architectural scaffolding, and debugging:
1. **AI Output Flaws Caught**: The AI initially generated training scripts using default half-precision on CPU, which caused immediate NaN gradients in AdamW. Careful inspection identified that float16 on CPU lacks native hardware scaling, necessitating explicit float32 casting.
2. **Tokenization Boundary Inconsistencies**: The AI initially used space delimiters between prompt and JSON, which caused HuggingFace BPE tokenizer to merge `' '` and `'{'` into `' {"'`, corrupting label masking. This was detected and solved by transitioning to newline delimiters (`\nJSON:\n`).
3. **Stateless NACL Awareness**: Early AI rule suggestions forgot outbound ephemeral return paths for inbound HTTP traffic. Understanding stateless routing enabled manual verification that inbound and outbound rules operate independently.

All architectural decisions, mathematical proofs, and final validations were checked against first principles and the official course rubric.
