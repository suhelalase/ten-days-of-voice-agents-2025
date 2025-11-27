"""
Tests for Notion integration with Wellness Companion
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from wellness_notion import NotionWellnessClient, get_notion_client


class TestNotionClient:
    """Test suite for NotionWellnessClient"""
    
    def test_client_initialization_without_env(self):
        """Test that client initializes but is disabled without environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            client = NotionWellnessClient()
            assert not client.is_enabled()
            assert client.client is None
    
    def test_client_initialization_with_env(self):
        """Test that client initializes when environment variables are set"""
        with patch.dict(os.environ, {
            'NOTION_API_KEY': 'test_secret_key',
            'NOTION_DATABASE_ID': 'test_database_id',
            'ENABLE_NOTION_MCP': 'true'
        }):
            with patch('wellness_notion.Client') as mock_client:
                client = NotionWellnessClient()
                assert client.api_key == 'test_secret_key'
                assert client.database_id == 'test_database_id'
                assert client.enabled == True
    
    def test_client_disabled_when_flag_false(self):
        """Test that client is disabled when ENABLE_NOTION_MCP is false"""
        with patch.dict(os.environ, {
            'NOTION_API_KEY': 'test_key',
            'NOTION_DATABASE_ID': 'test_id',
            'ENABLE_NOTION_MCP': 'false'
        }):
            client = NotionWellnessClient()
            assert not client.is_enabled()
    
    @pytest.mark.asyncio
    async def test_create_wellness_entry_disabled(self):
        """Test that create_wellness_entry raises error when disabled"""
        with patch.dict(os.environ, {}, clear=True):
            client = NotionWellnessClient()
            
            with pytest.raises(ValueError, match="not enabled"):
                await client.create_wellness_entry(
                    date="2025-11-24",
                    mood="Good",
                    energy="High",
                    objectives=["Test objective"]
                )
    
    @pytest.mark.asyncio
    async def test_create_wellness_entry_success(self):
        """Test successful creation of wellness entry in Notion"""
        mock_response = {
            "id": "test-page-id-123",
            "url": "https://notion.so/test-page",
            "created_time": "2025-11-24T10:00:00.000Z"
        }
        
        with patch.dict(os.environ, {
            'NOTION_API_KEY': 'test_key',
            'NOTION_DATABASE_ID': 'test_database_id',
            'ENABLE_NOTION_MCP': 'true'
        }):
            with patch('wellness_notion.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.pages.create.return_value = mock_response
                mock_client_class.return_value = mock_client
                
                client = NotionWellnessClient()
                
                result = await client.create_wellness_entry(
                    date="2025-11-24",
                    mood="Good",
                    energy="High",
                    objectives=["Exercise", "Meditate", "Read"],
                    stressors="None",
                    summary="Feeling great today"
                )
                
                assert result["success"] == True
                assert result["page_id"] == "test-page-id-123"
                assert result["url"] == "https://notion.so/test-page"
                
                
                mock_client.pages.create.assert_called_once()
                call_args = mock_client.pages.create.call_args
                
                assert call_args[1]["parent"]["database_id"] == "test_database_id"
                
                
                props = call_args[1]["properties"]
                assert "Good" in str(props["Mood"])
                assert "High" in str(props["Energy"])
                assert "Exercise" in str(props["Objectives"])
    
    @pytest.mark.asyncio
    async def test_create_wellness_entry_without_optional_fields(self):
        """Test creating entry without stressors and summary"""
        mock_response = {
            "id": "test-id",
            "url": "https://notion.so/test",
            "created_time": "2025-11-24T10:00:00.000Z"
        }
        
        with patch.dict(os.environ, {
            'NOTION_API_KEY': 'test_key',
            'NOTION_DATABASE_ID'
: 'test_db',
            'ENABLE_NOTION_MCP': 'true'
        }):
            with patch('wellness_notion.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.pages.create.return_value = mock_response
                mock_client_class.return_value = mock_client
                
                client = NotionWellnessClient()
                
                result = await client.create_wellness_entry(
                    date="2025-11-24",
                    mood="Okay",
                    energy="Medium",
                    objectives=["Work"]
                )
                
                assert result["success"] == True
                
                props = mock_client.pages.create.call_args[1]["properties"]
                assert "Stressors" not in props
                assert "Summary" not in props
    
    @pytest.mark.asyncio
    async def test_update_objective_status(self):
        """Test updating entry status in Notion"""
        mock_response = {
            "id": "test-page-id",
            "object": "page"
        }
        
        with patch.dict(os.environ, {
            'NOTION_API_KEY': 'test_key',
            'NOTION_DATABASE_ID': 'test_db',
            'ENABLE_NOTION_MCP': 'true'
        }):
            with patch('wellness_notion.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.pages.update.return_value = mock_response
                mock_client_class.return_value = mock_client
                
                client = NotionWellnessClient()
                
                result = await client.update_objective_status(
                    page_id="test-page-id",
                    status="Completed"
                )
                
                assert result["success"] == True
                assert result["status"] == "Completed"
                
                mock_client.pages.update.assert_called_once_with(
                    page_id="test-page-id",
                    properties={
                        "Status": {
                            "select": {
                                "name": "Completed"
                            }
                        }
                    }
                )
    
    @pytest.mark.asyncio
    async def test_get_recent_entries(self):
        """Test retrieving recent entries from Notion"""
        mock_response = {
            "results": [
                {
                    "id": "page-1",
                    "url": "https://notion.so/page-1",
                    "properties": {
                        "Date": {"date": {"start": "2025-11-24"}},
                        "Mood": {"select": {"name": "Good"}},
                        "Energy": {"select": {"name": "High"}},
                        "Status": {"select": {"name": "Planned"}},
                        "Objectives": {
                            "rich_text": [
                                {"text": {"content": "• Exercise\n• Meditate"}}
                            ]
                        }
                    }
                }
            ]
        }
        
        with patch.dict(os.environ, {
            'NOTION_API_KEY': 'test_key',
            'NOTION_DATABASE_ID': 'test_db',
            'ENABLE_NOTION_MCP': 'true'
        }):
            with patch('wellness_notion.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.databases.query.return_value = mock_response
                mock_client_class.return_value = mock_client
                
                client = NotionWellnessClient()
                
                entries = await client.get_recent_entries(limit=5)
                
                assert len(entries) == 1
                assert entries[0]["page_id"] == "page-1"
                assert entries[0]["date"] == "2025-11-24"
                assert entries[0]["mood"] == "Good"
                assert entries[0]["energy"] == "High"
                assert entries[0]["status"] == "Planned"
                assert "Exercise" in entries[0]["objectives"]
    
    def test_singleton_pattern(self):
        """Test that get_notion_client returns the same instance"""
        with patch.dict(os.environ, {
            'NOTION_API_KEY': 'test_key',
            'NOTION_DATABASE_ID': 'test_db',
            'ENABLE_NOTION_MCP': 'true'
        }):
            client1 = get_notion_client()
            client2 = get_notion_client()
            
            assert client1 is client2


class TestAgentNotionIntegration:
    """Test Notion integration within the agent"""
    
    @pytest.mark.asyncio
    async def test_save_to_notion_tool_success(self):
        """Test the save_to_notion tool in the agent"""
        from agent import WellnessAssistant
        from unittest.mock import MagicMock
        
        test_log_data = {
            "entries": [
                {
                    "date": "2025-11-24",
                    "mood": "Good",
                    "energy": "High",
                    "objectives": ["Exercise", "Work on project"],
                    "summary": "Feeling great"
                }
            ]
        }
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = str(test_log_data)
            
            with patch('agent.get_notion_client') as mock_get_client:
                mock_notion = AsyncMock()
                mock_notion.is_enabled.return_value = True
                mock_notion.create_wellness_entry.return_value = {
                    "success": True,
                    "page_id": "test-id",
                    "url": "https://notion.so/test"
                }
                mock_get_client.return_value = mock_notion
                
                assistant = WellnessAssistant()
                mock_context = MagicMock()
                
                result = await assistant.save_to_notion(mock_context)
                
                assert "Perfect!" in result
                assert "Daily Wellness database" in result
    
    @pytest.mark.asyncio
    async def test_save_to_notion_when_disabled(self):
        """Test save_to_notion when Notion is disabled"""
        from agent import WellnessAssistant
        from unittest.mock import MagicMock
        
        with patch('agent.get_notion_client') as mock_get_client:
            mock_notion = Mock()
            mock_notion.is_enabled.return_value = False
            mock_get_client.return_value = mock_notion
            
            assistant = WellnessAssistant()
            mock_context = MagicMock()
            
            result = await assistant.save_to_notion(mock_context)
            
            assert "isn't set up yet" in result
            assert "saved locally" in result
