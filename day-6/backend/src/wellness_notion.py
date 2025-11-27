"""
Notion Client for Wellness Companion
Handles all interactions with Notion API for storing check-in data
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger("notion_client")


class NotionWellnessClient:
    """Client for managing wellness check-ins in Notion database"""
    
    def __init__(self):
        """Initialize Notion client with API key from environment"""
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.enabled = os.getenv("ENABLE_NOTION_MCP", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("Notion integration is disabled")
            self.client = None
            return
            
        if not self.api_key:
            logger.warning("NOTION_API_KEY not found in environment")
            self.client = None
            self.enabled = False
            return
            
        if not self.database_id:
            logger.warning("NOTION_DATABASE_ID not found in environment")
            self.client = None
            self.enabled = False
            return
        
        try:
            self.client = Client(auth=self.api_key)
            logger.info("Notion client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Notion client: {e}")
            self.client = None
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Notion integration is enabled and configured"""
        return self.enabled and self.client is not None
    
    async def create_wellness_entry(
        self,
        date: str,
        mood: str,
        energy: str,
        objectives: List[str],
        stressors: Optional[str] = None,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new wellness check-in entry in Notion database
        
        Args:
            date: Date of check-in (YYYY-MM-DD format)
            mood: User's mood (e.g., "Good", "Great", "Okay", "Low", "Tired")
            energy: User's energy level (e.g., "High", "Medium", "Low")
            objectives: List of daily objectives (1-3 items)
            stressors: Optional stressors or concerns
            summary: Optional summary of the check-in
            
        Returns:
            Dictionary with Notion page data
            
        Raises:
            APIResponseError: If Notion API request fails
        """
        if not self.is_enabled():
            raise ValueError("Notion integration is not enabled or configured")
        
        objectives_text = "\n".join(f"• {obj}" for obj in objectives)
        
        
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": f"Check-in: {date}"
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": date
                }
            },
            "Mood": {
                "select": {
                    "name": mood.capitalize()
                }
            },
            "Energy": {
                "select": {
                    "name": energy.capitalize()
                }
            },
            "Objectives": {
                "rich_text": [
                    {
                        "text": {
                            "content": objectives_text
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": "Planned"
                }
            }
        }
        
        # Add optional fields
        if stressors:
            properties["Stressors"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": stressors
                        }
                    }
                ]
            }
        
        if summary:
            properties["Summary"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": summary
                        }
                    }
                ]
            }
        
        try:
            
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"Created Notion entry: {response['id']}")
            return {
                "success": True,
                "page_id": response["id"],
                "url": response["url"],
                "created_time": response["created_time"]
            }
            
        except APIResponseError as e:
            logger.error(f"Notion API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Notion entry: {e}")
            raise
    
    async def update_objective_status(
        self,
        page_id: str,
        status: str = "Completed"
    ) -> Dict[str, Any]:
        """
        Update the status of a wellness entry
        
        Args:
            page_id: Notion page ID to update
            status: New status (e.g., "Planned", "In Progress", "Completed")
            
        Returns:
            Updated page data
        """
        if not self.is_enabled():
            raise ValueError("Notion integration is not enabled")
        
        try:
            response = self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            
            logger.info(f"Updated Notion entry {page_id} to status: {status}")
            return {
                "success": True,
                "page_id": response["id"],
                "status": status
            }
            
        except APIResponseError as e:
            logger.error(f"Notion API error updating status: {e}")
            raise
    
    async def get_recent_entries(
        self,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent wellness entries from Notion
        
        Args:
            limit: Maximum number of entries to retrieve
            
        Returns:
            List of entry dictionaries
        """
        if not self.is_enabled():
            raise ValueError("Notion integration is not enabled")
        
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                sorts=[
                    {
                        "property": "Date",
                        "direction": "descending"
                    }
                ],
                page_size=limit
            )
            
            entries = []
            for page in response["results"]:
                props = page["properties"]
                
                
                entry = {
                    "page_id": page["id"],
                    "url": page["url"],
                    "date": props.get("Date", {}).get("date", {}).get("start", "Unknown"),
                    "mood": props.get("Mood", {}).get("select", {}).get("name", "Not set"),
                    "energy": props.get("Energy", {}).get("select", {}).get("name", "Not set"),
                    "status": props.get("Status", {}).get("select", {}).get("name", "Unknown"),
                }
                
               
                objectives_rich_text = props.get("Objectives", {}).get("rich_text", [])
                if objectives_rich_text:
                    entry["objectives"] = objectives_rich_text[0].get("text", {}).get("content", "")
                else:
                    entry["objectives"] = ""
                
                entries.append(entry)
            
            logger.info(f"Retrieved {len(entries)} entries from Notion")
            return entries
            
        except APIResponseError as e:
            logger.error(f"Notion API error retrieving entries: {e}")
            raise



_notion_client_instance = None


def get_notion_client() -> NotionWellnessClient:
    """Get singleton Notion client instance"""
    global _notion_client_instance
    if _notion_client_instance is None:
        _notion_client_instance = NotionWellnessClient()
    return _notion_client_instance
