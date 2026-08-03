# Multi-Agent Code Review System (MACR)

![CI](https://github.com/AdyaSinha1/MACR/actions/workflows/ci.yml/badge.svg)

MACR (Multi-Agent Code Review System) is an autonomous AI-powered code review platform that uses multiple specialized AI agents to analyze source code. Instead of depending on a single LLM prompt, MACR deploys collaborative agents for **Style Analysis, Bug Detection, and Security Auditing** coordinated through an intelligent orchestration layer.

The system combines an **Evaluator-Optimizer Loop**, **Consensus Engine**, and **FAISS-powered Retrieval Augmented Memory (RAG)** to generate reliable, context-aware, and explainable code review reports.

---

# Features

## Multi-Agent Code Analysis

MACR uses specialized agents that independently inspect source code:

### Style Agent
- Detects code quality issues
- Identifies formatting problems
- Suggests maintainability improvements

### Bug Agent
- Finds logical errors
- Detects potential runtime failures
- Identifies incorrect implementations

### Security Agent
- Detects vulnerabilities
- Finds unsafe coding practices
- Identifies security risks

Agents execute concurrently using an asynchronous orchestration system.

---

# Evaluator-Optimizer Loop

Each agent follows an iterative reasoning workflow:

1. Generate initial findings
2. Evaluate confidence score
3. Refine incorrect or weak suggestions
4. Produce optimized final output

This reduces false positives and improves review accuracy.

---

# Consensus Engine

MACR combines outputs from multiple agents using:

- Semantic similarity comparison
- Severity-based prioritization
- Duplicate finding removal
- Confidence-based ranking

The final report represents a consensus between multiple AI reviewers.

---

# RAG Memory System

MACR includes a historical learning layer using:

- FAISS Vector Database
- Sentence Transformer Embeddings
- Similar review retrieval

Previous review knowledge is retrieved to provide better contextual suggestions for future analyses.

---

# Architecture

```
                         Code Input
                             |
                             v
                       Coordinator
                             |
        ------------------------------------------------
        |                     |                        |
        v                     v                        v
   Style Agent            Bug Agent             Security Agent
        |                     |                        |
        ------------------------------------------------
                             |
                             v
                    Consensus Engine
                             |
                             v
                    FAISS Memory Store
                             |
                             v
                    Review Report Generator
                             |
                             v
                     Markdown Report
```

---

# Demo

![MACR Demo](docs/images/macr.png)

---

# Installation

## Clone Repository

```bash
git clone https://github.com/AdyaSinha1/MACR.git
cd MACR
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## Install Dependencies

Basic installation:

```bash
pip install -e .
```

Development installation:

```bash
pip install -e ".[dev]"
```

Memory/RAG dependencies:

```bash
pip install -e ".[memory]"
```

Complete installation:

```bash
pip install -e ".[dev,memory]"
```

---

# Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

# Usage

## Run Code Review

Analyze a Python file:

```bash
python -m src.cli.main samples/test.py
```

Generated report:

```
review_report.md
```

Example execution:

```
Initializing memory store...

Starting multi-agent review...

StyleAgent analyzing code...
BugAgent analyzing code...
SecurityAgent analyzing code...

Running consensus analysis...

Storing review in FAISS memory...

Review complete!
```

---

# Web API Interface

Start the API server:

```bash
uvicorn src.api.app:app --reload
```

Access:

```
http://127.0.0.1:8000
```

---

# Docker Support

Build Docker image:

```bash
docker build -t macr .
```

Run:

```bash
docker run macr
```

Using docker compose:

```bash
docker-compose build
docker-compose run macr
```

---

# Evaluation

Run evaluation on sample files:

```bash
python scripts/evaluate.py samples/test.py
```

---

# Testing

Run complete test suite:

```bash
pytest tests/
```

Run linting:

```bash
flake8 src/ tests/
```

Check formatting:

```bash
black --check src/ tests/
```

Run type checking:

```bash
mypy src/
```

---

# Continuous Integration

MACR uses GitHub Actions for automated validation.

Every push and pull request runs:

- Dependency installation
- Code formatting checks
- Static analysis
- Type checking
- Unit tests
- Docker build verification

CI Pipeline:

```
Push / Pull Request

        |
        v

GitHub Actions

        |
        +----------------+
        |                |
        v                v

 Python Tests       Docker Build

        |
        v

 Successful Deployment
```

---

# Project Structure

```
MACR
│
├── src
│   │
│   ├── agents
│   │   ├── style_agent.py
│   │   ├── bug_agent.py
│   │   └── security_agent.py
│   │
│   ├── orchestrator
│   │   ├── coordinator.py
│   │   └── consensus.py
│   │
│   ├── memory
│   │   ├── embeddings.py
│   │   └── faiss_store.py
│   │
│   ├── core
│   │
│   ├── reporting
│   │
│   └── api
│
├── tests
│
├── samples
│
├── scripts
│
├── Dockerfile
│
├── docker-compose.yml
│
├── pyproject.toml
│
└── README.md
```

---

# Example Review Report

MACR produces structured reports containing:

- Severity level
- File location
- Responsible agent
- Confidence score
- Consensus reasoning
- Suggested improvements


Example:

```
Finding:
Hardcoded API key detected

Severity:
Critical

Detected By:
SecurityAgent

Consensus:
Confirmed by multiple agents

Confidence:
100%
```

---

# Key Technologies

| Component | Technology |
|---|---|
| Language | Python |
| AI Agents | LLM-based Agents |
| Orchestration | AsyncIO |
| Memory | FAISS |
| Embeddings | Sentence Transformers |
| API | FastAPI |
| Testing | Pytest |
| CI/CD | GitHub Actions |
| Containerization | Docker |

---

# Future Improvements

- AST-based intelligent code chunking
- Pull Request automation
- Multi-language support
- Automated code fixing
- Advanced learning from previous reviews
- IDE extension support

---

# License

MIT License