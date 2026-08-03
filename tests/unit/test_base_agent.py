import pytest
import asyncio
from agents.base import BaseAgent
from models.schemas import Finding, AgentCritique, SharedContext

class DummyAgent(BaseAgent):
    category = "test"
    def get_system_prompt(self):
        return "System Prompt"
    def get_critique_prompt(self, finding):
        return "Critique Prompt"

class MockLLM:
    def __init__(self):
        self.call_count = 0
        
    async def generate_structured(self, prompt, schema):
        self.call_count += 1
        if schema == Finding:
            return Finding(agent_name="Dummy", category="bug", severity="low", code_location="N/A", description="desc", explanation="exp", confidence=0.5)
        elif schema == AgentCritique:
            # new_confidence > 0.85 triggers early exit in the optimizer loop
            return AgentCritique(is_valid=True, critique="Clear and accurate.", suggested_improvements="None needed.", new_confidence=0.9)

@pytest.mark.asyncio
async def test_evaluator_optimizer_early_exit():
    """Tests that the Evaluator-Optimizer loop exits early when confidence > 0.85."""
    llm = MockLLM()
    agent = DummyAgent(name="DummyAgent", llm=llm)
    
    context = SharedContext(file_path="test.py", code_content="print('hello')", past_reviews_context="")
    
    finding = await agent._run_evaluator_optimizer(context)
    
    # Expected: 1 initial Generation call + 1 Critique call = 2 calls total
    assert llm.call_count == 2
    assert finding.confidence == 0.9
