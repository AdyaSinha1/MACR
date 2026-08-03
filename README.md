# Multi-Agent Code Review System (MACR)

![CI](https://github.com/yourusername/macr/actions/workflows/ci.yml/badge.svg)

MACR is a highly resilient, multi-agent AI system designed to perform autonomous code reviews. Instead of relying on a single large prompt, MACR deploys specialized agents (Style, Bug, Security) that collaborate via a shared blackboard. 

It leverages an **Evaluator-Optimizer loop** for true reasoning autonomy, a **Consensus Engine** to resolve overlapping findings, and **FAISS Vector Memory** to learn from historical reviews.

## Architecture

MACR is built on a custom `asyncio` orchestrator (bypassing heavy frameworks like CrewAI) to maintain strict control over concurrency and self-reflection loops.

### Key Features
1. **Multi-Agent Orchestration**: Specialized agents run concurrently, managed by a custom asyncio coordinator.
2. **Evaluator-Optimizer Loop**: Each agent self-critiques and refines its output (capped at 3 iterations) to minimize hallucinations.
3. **Resilience**: Per-agent circuit breakers with exponential backoff prevent cascading API failures (e.g., rate limits).
4. **Semantic Consensus**: A Consensus Engine uses fuzzy line-range grouping (±5 lines) and an LLM to merge overlapping findings from different agents.
5. **Memory (RAG)**: FAISS + `sentence-transformers` caches and retrieves similar past reviews to inject historical context into the agents' prompts.

*(Note: AST-based chunking for large files >1000 lines is planned as a future enhancement.)*

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/macr.git
cd macr

# Install core CLI
pip install -e .

# Install with memory (FAISS) and dev dependencies
pip install -e ".[memory,dev]"
```

## Usage

Set your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key"
```

Run a review on a file:
```bash
macr review path/to/your/file.py --output report.md --verbose
```

### Docker
You can also run MACR fully containerized. The multi-stage Docker build automatically caches the ML models:
```bash
docker-compose build
docker-compose run macr review samples/test.py
```

## Evaluation

To demonstrate MACR's pipeline metrics, you can run the evaluation script on a sample file:
```bash
python scripts/evaluate.py samples/test.py
```
