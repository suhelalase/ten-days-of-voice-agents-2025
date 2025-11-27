import pytest
import json
import os
from livekit.agents import AgentSession, inference, llm
from agent import Assistant

from livekit.plugins import google

def _llm() -> llm.LLM:
    return google.LLM(model="gemini-2.5-flash")

@pytest.mark.asyncio
async def test_barista_order_flow() -> None:
    """Evaluation of the barista agent's order taking flow."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        assistant = Assistant()
        await session.start(assistant)

        # 1. User initiates order with incomplete info
        result = await session.run(user_input="I want a latte")
        
        # Agent should ask for details (Size, Milk, Extras, Name)
        # We just check it responds with a message
        await result.expect.next_event().is_message(role="assistant")

        # 2. User provides remaining details
        # "Medium, Oat milk, no extras, for Alice"
        result = await session.run(user_input="Medium, Oat milk, no extras, for Alice")

        # Agent should now have enough info and submit the order
        # We expect a tool call or a confirmation message. 
        # Since we decorated with @ai_callable, the agent might call the tool.
        # The test framework's `is_tool_call` might be needed if we want to intercept it, 
        # but here we just want to see if the file is created eventually or if the agent confirms.
        
        # The agent will likely call the tool, then respond to the user.
        # We can check for the tool call event if we want, or just wait for the final response.
        
        # Let's just wait for the turn to finish (which includes tool execution)
        # and then check the file.
        
        # Wait for potential tool call and response
        # Note: In the real agent loop, the tool is executed and result fed back.
        # In this test harness, `session.run` simulates the turn.
        
        # We expect the agent to say something like "Order submitted"
        await result.expect.next_event().is_message(role="assistant")
        
        # Check if order.json exists and has correct content
        assert os.path.exists("order.json")
        with open("order.json", "r") as f:
            data = json.load(f)
        
        assert data["drinkType"].lower() == "latte"
        assert data["size"].lower() == "medium"
        assert data["milk"].lower() == "oat"
        assert "alice" in data["name"].lower()
        # Extras might be empty list or ["None"] depending on LLM, but let's check it's a list
        assert isinstance(data["extras"], list)

        # Clean up
        os.remove("order.json")
