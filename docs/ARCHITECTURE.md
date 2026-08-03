# Architectural Decision Records (ADRs)

This document captures the key architectural decisions made during the design and implementation of the Multi-Agent Code Review (MACR) system.

## 1. Dropping CrewAI for Custom Asyncio Orchestrator

**Context**: Initially, CrewAI was chosen for orchestrating the multi-agent system.
**Decision**: We replaced CrewAI with a custom `asyncio`-based orchestrator.
**Rationale**: CrewAI is designed around linear task execution. To implement the strict Evaluator-Optimizer (self-critique) loop required by the design, we would have had to battle the framework's abstractions, effectively blocking the CrewAI scheduler. A custom `asyncio.gather` approach provides explicit control, true parallelization, and zero framework overhead.

## 2. The Evaluator-Optimizer Loop Constraints

**Context**: Unbounded self-reflection loops can lead to infinite execution and high API costs.
**Decision**: Each agent is hard-capped at 3 refinement iterations. The loop terminates early if confidence exceeds 0.85.
**Rationale**: Research shows diminishing returns after 2-3 iterations. Using Pydantic schemas ensures each iteration returns a predictable output structure, making state tracking reliable.

## 3. Batch Semantic Consensus

**Context**: Multiple agents analyzing the same code will inevitably flag overlapping issues.
**Decision**: We use an LLM-powered Consensus Engine that groups findings by code location and batches them into a single prompt for semantic resolution.
**Rationale**: Simple weighted voting fails when agents disagree on the semantics of a bug (e.g., classifying a bug as a security flaw). Using an LLM to merge these overlapping reports produces a cleaner final report. Batching them saves LLM calls and latency.

## 4. Per-Agent Circuit Breakers

**Context**: LLM APIs (like Gemini) can rate limit (429) or timeout (503).
**Decision**: Implemented a per-agent circuit breaker using the `tenacity` retry library and custom state tracking.
**Rationale**: If the `StyleAgent` repeatedly crashes, it shouldn't fail the entire pipeline. The circuit breaker ensures that agent returns a 0-confidence fallback, allowing the `BugAgent` and `SecurityAgent` to still deliver their findings.
