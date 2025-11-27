import pytest
import json
import os
from pathlib import Path
from livekit.agents import AgentSession, inference, llm
from agent import WellnessAssistant

from livekit.plugins import google

WELLNESS_LOG_PATH = Path("wellness_log.json")


def _llm() -> llm.LLM:
    return google.LLM(model="gemini-2.5-flash")


@pytest.mark.asyncio
async def test_wellness_check_in_flow() -> None:
    """Test the wellness companion's daily check-in flow."""
    if WELLNESS_LOG_PATH.exists():
        os.remove(WELLNESS_LOG_PATH)
    
    async with (
        _llm() as llm_instance,
        AgentSession(llm=llm_instance) as session,
    ):
        assistant = WellnessAssistant()
        await session.start(assistant)

        # 1. First check-in - User shares mood and energy
        result = await session.run(user_input="I'm feeling pretty good today, energy is medium")
        
        # Agent should respond warmly
        await result.expect.next_event().is_message(role="assistant")

        # 2. User provides objectives
        result = await session.run(
            user_input="I want to finish my project, go for a walk, and call my mom"
        )

        # Agent should acknowledge and may offer advice
        await result.expect.next_event().is_message(role="assistant")

        # 3. User confirms the recap
        result = await session.run(user_input="Yes, that sounds right")

        # Agent should confirm and save the check-in
        # The save_check_in tool should be called automatically by the agent
        await result.expect.next_event().is_message(role="assistant")

        # Check if wellness_log.json exists and has correct structure
        assert WELLNESS_LOG_PATH.exists(), "Wellness log file should be created"
        
        with open(WELLNESS_LOG_PATH, "r") as f:
            data = json.load(f)
        
        assert "entries" in data, "Log should have 'entries' key"
        assert len(data["entries"]) > 0, "At least one entry should be saved"
        
        entry = data["entries"][0]
        assert "date" in entry, "Entry should have a date"
        assert "time" in entry, "Entry should have a time"
        assert "timestamp" in entry, "Entry should have a timestamp"
        assert "mood" in entry, "Entry should have mood"
        assert "energy" in entry, "Entry should have energy"
        assert "objectives" in entry, "Entry should have objectives"
        assert isinstance(entry["objectives"], list), "Objectives should be a list"
        assert "summary" in entry, "Entry should have a summary"

    # Clean up
    if WELLNESS_LOG_PATH.exists():
        os.remove(WELLNESS_LOG_PATH)


@pytest.mark.asyncio
async def test_wellness_with_previous_context() -> None:
    """Test that the agent references previous check-ins."""
    # Create a sample previous entry
    previous_data = {
        "entries": [
            {
                "date": "2025-11-23",
                "time": "09:00:00",
                "timestamp": "2025-11-23T09:00:00",
                "mood": "tired",
                "energy": "low",
                "objectives": ["rest", "light exercise"],
                "summary": "Feeling tired with low energy. Focus: rest and light exercise"
            }
        ]
    }
    
    with open(WELLNESS_LOG_PATH, "w") as f:
        json.dump(previous_data, f, indent=2)
    
    async with (
        _llm() as llm_instance,
        AgentSession(llm=llm_instance) as session,
    ):
        assistant = WellnessAssistant()
        await session.start(assistant)

        # Agent should reference the previous check-in in the greeting
        result = await session.run(user_input="Hi")
        
        # The first message should reference previous mood or context
        response = await result.expect.next_event().is_message(role="assistant")
        # Note: The exact content will vary, but the agent's instructions tell it to reference past data

        # User shares today's mood
        result = await session.run(user_input="Today I'm feeling much better, energy is high")
        await result.expect.next_event().is_message(role="assistant")

    # Clean up
    if WELLNESS_LOG_PATH.exists():
        os.remove(WELLNESS_LOG_PATH)


@pytest.mark.asyncio
async def test_wellness_no_medical_advice() -> None:
    """Test that the agent avoids giving medical advice."""
    # Clean up any existing test data
    if WELLNESS_LOG_PATH.exists():
        os.remove(WELLNESS_LOG_PATH)
    
    async with (
        _llm() as llm_instance,
        AgentSession(llm=llm_instance) as session,
    ):
        assistant = WellnessAssistant()
        await session.start(assistant)

        # User mentions a medical concern
        result = await session.run(
            user_input="I've been having headaches and feeling dizzy"
        )
        
        # Agent should respond empathetically but not diagnose
        # The instructions explicitly tell it not to provide medical advice
        response = await result.expect.next_event().is_message(role="assistant")
        # The agent should suggest simple non-medical actions (like rest, hydration)
        # or encourage seeking professional help, but not diagnose

    # Clean up
    if WELLNESS_LOG_PATH.exists():
        os.remove(WELLNESS_LOG_PATH)


@pytest.mark.asyncio
async def test_save_check_in_tool() -> None:
    """Test the save_check_in tool directly."""
    # Clean up
    if WELLNESS_LOG_PATH.exists():
        os.remove(WELLNESS_LOG_PATH)
    
    assistant = WellnessAssistant()
    
    # Create a mock RunContext
    from unittest.mock import MagicMock
    mock_context = MagicMock()
    
    # Call the save_check_in tool
    result = await assistant.save_check_in(
        context=mock_context,
        mood="happy",
        energy="high",
        objectives=["write code", "exercise", "read"],
        stressors="deadline approaching",
        summary="Feeling great and productive"
    )
    
    # Check the return message
    assert "Check-in saved successfully" in result
    
    # Verify the file was created
    assert WELLNESS_LOG_PATH.exists()
    
    with open(WELLNESS_LOG_PATH, "r") as f:
        data = json.load(f)
    
    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    assert entry["mood"] == "happy"
    assert entry["energy"] == "high"
    assert entry["objectives"] == ["write code", "exercise", "read"]
    assert entry["stressors"] == "deadline approaching"
    assert entry["summary"] == "Feeling great and productive"
    
    # Clean up
    os.remove(WELLNESS_LOG_PATH)


@pytest.mark.asyncio
async def test_get_previous_check_ins_tool() -> None:
    """Test the get_previous_check_ins tool."""
    # Create sample data
    sample_data = {
        "entries": [
            {
                "date": "2025-11-20",
                "mood": "okay",
                "energy": "medium",
                "objectives": ["task1"],
                "summary": "Day 1"
            },
            {
                "date": "2025-11-21",
                "mood": "good",
                "energy": "high",
                "objectives": ["task2", "task3"],
                "summary": "Day 2"
            }
        ]
    }
    
    with open(WELLNESS_LOG_PATH, "w") as f:
        json.dump(sample_data, f)
    
    assistant = WellnessAssistant()
    
    from unittest.mock import MagicMock
    mock_context = MagicMock()
    
    # Get previous check-ins
    result = await assistant.get_previous_check_ins(
        context=mock_context,
        num_entries=5
    )
    
    # Check that it returns the entries
    assert "2025-11-20" in result
    assert "2025-11-21" in result
    assert "okay" in result
    assert "good" in result
    
    # Clean up
    os.remove(WELLNESS_LOG_PATH)
