# Makefile for Cloud Computing (CS3081) Mini Project

.PHONY: all up down train test lint eval

CLUSTER_NAME = parser-cluster
SUBSET ?= 1500

all: test

# Task 6.1: Deploy full system in at most three commands
up:
	k3d cluster create $(CLUSTER_NAME) --config cluster/k3d.yaml || true
	kubectl apply -f k8s/seaweedfs.yaml
	kubectl apply -f k8s/secret.yaml -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml -f k8s/hpa.yaml

# Task 6.1: Delete cluster
down:
	k3d cluster delete $(CLUSTER_NAME) || true

# Task 2.2: Single command training reading config.yaml, supports SUBSET=50
train:
	python training/train.py --config training/config.yaml --subset $(SUBSET) --version v1

# Unit tests (Task 6.2)
test:
	pytest tests/test_service.py -v

# Linting stage (Task 6.2)
lint:
	python -m py_compile service/app.py training/train.py worker/clean.py worker/worker.py

# Model evaluation & Quality Gate (Task 6.2)
eval:
	python scripts/eval_student.py
	python tools/score.py results/student_predictions.jsonl data/validation.jsonl --out results/student_score.json --min-validity 95
