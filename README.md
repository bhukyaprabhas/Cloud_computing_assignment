# Cloud Computing (CS3081) Mini Project: Knowledge Distillation and Local Cloud Deployment

**Student Name**: Bhukya Prabhas  
**Roll Number**: 230103031  
**GitHub Repository**: [https://github.com/bhukyaprabhas/Cloud_computing_assignment](https://github.com/bhukyaprabhas/Cloud_computing_assignment)  
**Submission Tag**: `final`

A complete, production-grade cloud computing and machine learning pipeline that distills natural language command parsing from a 3.8B parameter teacher (`Phi-3.5-mini-instruct`) into an ultra-lightweight 70M parameter student model (`EleutherAI/pythia-70m`), containerizes the inference service, and deploys it on a local Kubernetes cluster with automated autoscaling, rolling updates, network access control, and CI/CD quality gates.

---

## 1. Architecture Overview

The system consists of three distinct tiers:
1. **Data & Storage Tier**: SeaweedFS S3-compatible object storage hosted in Kubernetes namespace `data` managing dataset shards (`datasets/`) and trained model checkpoints (`models/`).
2. **Compute & Inference Tier**: FastAPI-based microservice containerized with CPU-optimized PyTorch (<1.5 GB image), deployed in namespace `app` with 2 replicas, Traefik Ingress routing, resource limits (1 CPU, 1 GiB RAM), and Horizontal Pod Autoscaler (HPA).
3. **Security & Network Tier**: VLSM-derived subnetting over `10.20.0.0/16` and stateless Network Access Control List (NACL) enforcing strict perimeter isolation.

---

## 2. Directory Structure

```text
├── cluster/
│   └── k3d.yaml                 # k3d local cluster configuration
├── data/
│   ├── commands_pool.jsonl      # 3,000 raw SLURP commands
│   ├── validation.jsonl         # 100 gold validation examples
│   ├── schema.json              # 4-key JSON schema & 8 intents
│   └── rate_card.json           # Cloud cost rate card (INR)
├── datasets/
│   ├── teacher/                 # Sharded raw teacher outputs
│   └── v1/
│       ├── train.jsonl          # Cleaned training dataset (2,936 records)
│       └── train.sha256         # SHA-256 checksum of train.jsonl
├── k8s/
│   ├── deployment.yaml          # Parser Deployment (2 replicas, limits, probes)
│   ├── hpa.yaml                 # HorizontalPodAutoscaler (70% CPU target)
│   ├── ingress.yaml             # Traefik Ingress routing /parse
│   ├── pipeline.yaml            # Parallel worker job manifests
│   ├── seaweedfs.yaml           # SeaweedFS deployment in namespace data
│   ├── secret.yaml              # S3 credentials secret in namespace app
│   └── service.yaml             # ClusterIP service on port 8000
├── models/
│   ├── v1/                      # Trained student model v1 & model.sha256
│   └── v2/                      # Trained student model v2 & model.sha256
├── network/
│   ├── nacl.json                # Stateless Network ACL rules for public subnet
│   ├── packets_sample.jsonl     # Sample test packets
│   └── subnets.md               # Subnet allocations and technical proofs
├── prompts/
│   └── teacher_prompt.txt       # Strict four-key prompt for Phi-3.5
├── report/
│   └── report.pdf               # Comprehensive 8-page academic report
├── results/
│   ├── loadtest_headers.json    # Load test header distribution
│   ├── loadtest_stats.csv       # Locust latency and throughput statistics
│   ├── student_score.json       # Student validation score report (99% validity)
│   ├── teacher_validation.json  # Teacher validation score report (59% full-frame)
│   └── untrained_score.json     # Untrained baseline score report
├── service/
│   ├── app.py                   # FastAPI inference service (/parse, /healthz, /readyz)
│   ├── Dockerfile               # Pinned CPU-only container image
│   └── requirements.txt         # Pinned production dependencies
├── tests/
│   └── test_service.py          # Unit tests (health, parse, fault injection, errors)
├── tools/
│   ├── locustfile.py            # Locust load test script with header counting
│   ├── nacl_sim.py              # Stateless NACL simulator
│   └── score.py                 # Evaluation and scoring harness
├── training/
│   ├── config.yaml              # Hyperparameters and library versions
│   ├── loss.csv                 # Per-epoch training loss log
│   └── train.py                 # Sequence-level knowledge distillation trainer
├── worker/
│   ├── clean.py                 # Data cleaning and deduplication pipeline
│   └── worker.py                # Sharded teacher labelling worker
├── .github/workflows/ci.yml     # CI/CD workflow (Lint, Test, Security, Quality Gate)
├── AI_USE.md                    # AI usage disclosure and verification log
├── Makefile                     # Build, deploy, train, test, and teardown automation
└── README.md                    # Project documentation
```

---

## 3. Quickstart: Commands to Build, Deploy, Test, and Teardown

### A. Environment Setup
Install the required tools and dependencies:
```bash
pip install -r service/requirements.txt
pip install locust pytest flake8
```

### B. How to Build
1. **Clean Teacher Shards**:
   ```bash
   python worker/clean.py
   ```
2. **Train the Student Model (Task 2)**:
   ```bash
   # Full training on first 1,500 records (saves to models/v1/)
   make train
   
   # Verification run on 50 records (test mode):
   make train SUBSET=50
   
   # Train version 2 for rolling update testing:
   python training/train.py --version v2
   ```
3. **Build the Inference Container (Task 3)**:
   ```bash
   docker build -t parser:v1 -f service/Dockerfile .
   ```

### C. How to Deploy (Task 4)
Deploy the entire infrastructure to a local Kubernetes cluster using `make up` (in at most 3 commands):
```bash
make up
```
This single command automatically:
1. Creates the local cluster from `cluster/k3d.yaml` with port forwards (`8080:80`, `8443:443`).
2. Deploys SeaweedFS object storage and initial datasets into namespace `data`.
3. Applies namespace `app` secrets, deployment (2 replicas, CPU/memory requests & limits, health probes), service, ingress, and HPA.

### D. How to Test
1. **Unit Tests (Task 6.2)**:
   ```bash
   make test
   # Or directly:
   pytest tests/test_service.py -v
   ```
2. **Model Evaluation & Quality Gate (Task 2.6 & 6.2)**:
   ```bash
   make eval
   # Evaluates student model:
   python tools/score.py results/student_predictions.jsonl data/validation.jsonl --min-validity 95
   ```
3. **Network Access Control Simulation (Task 5)**:
   ```bash
   python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check
   ```
4. **Locust Load Test (Task 4 & 7)**:
   ```bash
   locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
   ```

### E. How to Teardown
To safely tear down and delete the cluster and all associated resources:
```bash
make down
```

---

## 4. Key Results & Performance Summary

| Metric | Untrained Pythia-70M | Teacher (Phi-3.5) | Distilled Student (v1) | Target Threshold |
| :--- | :---: | :---: | :---: | :---: |
| **JSON Validity** | 0.0% | 100.0% | **99.0%** | $\ge 95.0\%$ (PASS) |
| **Intent Accuracy** | 0.0% | 75.0% | **72.0%** | - |
| **Date Accuracy** | 0.0% | 86.0% | **78.0%** | - |
| **Time Accuracy** | 0.0% | 93.0% | **91.0%** | - |
| **Place Accuracy** | 0.0% | 93.0% | **89.0%** | - |
| **Full-Frame Accuracy** | 0.0% | 59.0% | **46.0%** | $\ge 29.5\%$ (PASS) |

### Load Test & Production Metrics
- **Throughput**: 8.33 req/sec (1,000 requests in 2 minutes)
- **Median Latency (p50)**: 110 ms
- **95th Percentile Latency (p95)**: 245 ms (Strictly $\le 5,000$ ms)
- **Error Rate**: 0.2% (Strictly $\le 1.0\%$)
- **Cost per 1,000 Requests**: ₹0.258 INR (derived via `data/rate_card.json`)
- **Load Balancing**: Replica 1 served 51.4%, Replica 2 served 48.4% ($\ge 30\%$ requirement).
