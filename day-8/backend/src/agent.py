import logging
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    function_tool,
    RunContext,
)
from livekit.plugins import silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# -----------------------------
# Voice Game Master (Option A)
# -----------------------------

MISSIONS_DIR = Path("missions")
MISSIONS_DIR.mkdir(exist_ok=True)

# Minimal "world item" index used by the Game Master for consistent references.
# You can expand this list later; IDs are stable strings used by inventory tools.
WORLD_ITEMS = [
    {"id": "sword_basic", "name": "Basic Sword", "type": "weapon", "value": 10},
    {"id": "bow_basic", "name": "Basic Bow", "type": "weapon", "value": 12},
    {"id": "potion_small", "name": "Small Health Potion", "type": "consumable", "value": 5},
    {"id": "torch", "name": "Torch", "type": "utility", "value": 2},
    {"id": "map_fragment", "name": "Map Fragment", "type": "quest", "value": 0},
]

# Simple sample quests to demonstrate the quest system.
SAMPLE_QUESTS = {
    "find_map": {
        "title": "Find the Lost Map",
        "description": "A map fragment is rumored to be in the Old Ruins. Retrieve it and return to the village cartographer.",
        "requirements": {"map_fragment": 1},
        "reward": {"value": 50, "items": ["potion_small"]},
    },
    "slay_wolf": {
        "title": "Wolves at the Ridge",
        "description": "Clear the ridgeline of the aggressive wolf pack threatening travelers.",
        "requirements": {},
        "reward": {"value": 30, "items": ["potion_small"]},
    },
}


def _find_world_item(item_id: str) -> dict | None:
    for it in WORLD_ITEMS:
        if it["id"] == item_id:
            return it
    return None


BASE_INSTRUCTIONS = """
You are a VOICE GAME MASTER (GAMEMASTER) for an immersive battleground/adventure game.

Primary goals:
- Welcome players with a short cinematic line.
- Narrate environment, give mission briefings, warnings, and tactical suggestions.
- Expose and use in-game tools (inventory management, quest management, action execution).
- Always be immersive: use short, vivid, audio-first sentences. Ask one question at a time.
- When modifying inventory or quest state, call the appropriate tool and confirm the action.

Tools (these functions are available to the assistant and used to manage game state):
- add_item_to_inventory(item_id: str, quantity: int = 1, notes: str = ""):
    Add an item to the player's inventory. item_id must match a known WORLD_ITEMS id.
- remove_item_from_inventory(item_id: str):
    Remove an item entirely from inventory.
- update_item_quantity(item_id: str, quantity: int):
    Set quantity or remove if zero.
- list_inventory():
    Return inventory summary.
- start_quest(quest_id: str):
    Activate a quest by id (from SAMPLE_QUESTS).
- complete_quest(quest_id: str):
    Mark quest complete if requirements met; grant rewards (items/value) and log mission.
- describe_area(area_hint: str = "current"):
    Provide a short description of the current area, encounters, or opportunities.
- perform_action(action: str, target: str = ""):
    Execute an action (move, attack, sneak, loot). Provide a short narrative result.

Behavioral constraints:
- Use only WORLD_ITEMS ids when referring to items.
- When awarding items or changing inventory, call the inventory tools.
- Keep spoken replies concise (typically 1–3 short sentences).
- If the player asks a question outside the game world, reply briefly that the Game Master only handles in-game actions.
- Persist mission completions to the missions/ directory for later review.

Example startup welcome:
"Welcome, Commander. The frontier hums with danger — say 'brief' for your mission or 'explore' to scout the surroundings."
"""


def _persist_mission_log(mission_obj: dict) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = MISSIONS_DIR / f"mission_{mission_obj.get('id', 'unknown')}_{timestamp}.json"
    try:
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(mission_obj, fh, indent=2, ensure_ascii=False)
        logger.info(f"Mission log saved to {out_path}")
    except Exception as e:
        logger.error(f"Failed to persist mission log: {e}")


class GameMasterAgent(Agent):
    """
    Voice Game Master Agent.
    Handles inventory, quests, descriptions, and simple action simulation.
    """

    def __init__(self) -> None:
        super().__init__(instructions=BASE_INSTRUCTIONS)
        # inventory: list of {item_id, name, quantity, notes}
        self.inventory: list[dict] = []
        # active quests: dict quest_id -> status dict
        self.active_quests: dict[str, dict] = {}
        # completed quests history
        self.completed_quests: list[dict] = []

    def _inventory_summary(self) -> dict:
        total_items = sum(entry["quantity"] for entry in self.inventory) if self.inventory else 0
        items = [
            {"item_id": e["item_id"], "name": e["name"], "quantity": e["quantity"], "notes": e.get("notes", "")}
            for e in self.inventory
        ]
        return {"items": items, "total_items": total_items}

    def _find_inventory_entry(self, item_id: str) -> dict | None:
        for e in self.inventory:
            if e["item_id"] == item_id:
                return e
        return None

    @function_tool
    async def add_item_to_inventory(
        self, context: RunContext, item_id: str, quantity: int = 1, notes: str = ""
    ) -> dict:
        """
        Add an item to player's inventory.
        Returns: {"ok": bool, "inventory": {...}}.
        """
        if quantity <= 0:
            quantity = 1
        item = _find_world_item(item_id)
        if not item:
            return {"ok": False, "message": f"Unknown item id {item_id!r}."}

        entry = self._find_inventory_entry(item_id)
        if entry:
            entry["quantity"] += quantity
            if notes:
                entry["notes"] = (entry.get("notes", "") + " " + notes).strip()
        else:
            self.inventory.append({"item_id": item_id, "name": item["name"], "quantity": quantity, "notes": notes})

        logger.info(f"Added {quantity}x {item_id} to inventory.")
        return {"ok": True, "inventory": self._inventory_summary()}

    @function_tool
    async def remove_item_from_inventory(self, context: RunContext, item_id: str) -> dict:
        """
        Remove an item entirely from inventory.
        """
        original_len = len(self.inventory)
        self.inventory = [e for e in self.inventory if e["item_id"] != item_id]
        removed = len(self.inventory) < original_len
        return {"ok": removed, "inventory": self._inventory_summary()}

    @function_tool
    async def update_item_quantity(self, context: RunContext, item_id: str, quantity: int) -> dict:
        """
        Set exact quantity for an inventory item. Remove if quantity <= 0.
        """
        if quantity <= 0:
            self.inventory = [e for e in self.inventory if e["item_id"] != item_id]
            return {"ok": True, "inventory": self._inventory_summary()}

        for e in self.inventory:
            if e["item_id"] == item_id:
                e["quantity"] = quantity
                return {"ok": True, "inventory": self._inventory_summary()}

        # If not present, add it
        item = _find_world_item(item_id)
        if not item:
            return {"ok": False, "message": f"Unknown item id {item_id!r}."}
        self.inventory.append({"item_id": item_id, "name": item["name"], "quantity": quantity, "notes": ""})
        return {"ok": True, "inventory": self._inventory_summary()}

    @function_tool
    async def list_inventory(self, context: RunContext) -> dict:
        """
        Return the current inventory summary.
        """
        return self._inventory_summary()

    @function_tool
    async def start_quest(self, context: RunContext, quest_id: str) -> dict:
        """
        Activate a quest if available in SAMPLE_QUESTS.
        """
        if quest_id not in SAMPLE_QUESTS:
            return {"ok": False, "message": f"No quest found with id {quest_id!r}."}
        if quest_id in self.active_quests:
            return {"ok": False, "message": "Quest already active.", "quest": self.active_quests[quest_id]}

        quest_data = SAMPLE_QUESTS[quest_id].copy()
        quest_state = {"id": quest_id, "status": "active", "started_at": datetime.now().isoformat(), "progress": {}}
        self.active_quests[quest_id] = quest_state
        logger.info(f"Quest {quest_id} started.")
        return {"ok": True, "quest": {"id": quest_id, "title": quest_data["title"], "description": quest_data["description"]}}

    @function_tool
    async def complete_quest(self, context: RunContext, quest_id: str) -> dict:
        """
        Attempt to complete quest: checks requirements and grants rewards.
        """
        if quest_id not in SAMPLE_QUESTS:
            return {"ok": False, "message": f"No quest with id {quest_id!r}."}
        if quest_id not in self.active_quests:
            return {"ok": False, "message": "Quest is not active."}

        quest_def = SAMPLE_QUESTS[quest_id]
        # Check item requirements
        reqs = quest_def.get("requirements", {})
        for req_item_id, req_qty in reqs.items():
            entry = self._find_inventory_entry(req_item_id)
            if not entry or entry["quantity"] < req_qty:
                return {"ok": False, "message": f"Missing requirement: {req_item_id} x{req_qty}."}

        # Deduct requirements
        for req_item_id, req_qty in reqs.items():
            for e in self.inventory:
                if e["item_id"] == req_item_id:
                    e["quantity"] -= req_qty
                    break
            self.inventory = [e for e in self.inventory if e["quantity"] > 0]

        # Grant rewards (items)
        rewards = quest_def.get("reward", {})
        rewarded_items = []
        for item_id in rewards.get("items", []):
            item = _find_world_item(item_id)
            if item:
                entry = self._find_inventory_entry(item_id)
                if entry:
                    entry["quantity"] += 1
                else:
                    self.inventory.append({"item_id": item_id, "name": item["name"], "quantity": 1, "notes": "quest reward"})
                rewarded_items.append(item_id)

        # Mark complete
        completed = {
            "id": quest_id,
            "title": quest_def.get("title", quest_id),
            "completed_at": datetime.now().isoformat(),
            "rewards": {"value": rewards.get("value", 0), "items": rewarded_items},
        }
        self.completed_quests.append(completed)
        # Remove from active quests
        del self.active_quests[quest_id]

        # Persist mission log
        _persist_mission_log({"id": quest_id, "completed": completed})

        return {"ok": True, "completed": completed, "inventory": self._inventory_summary()}

    @function_tool
    async def describe_area(self, context: RunContext, area_hint: str = "current") -> dict:
        """
        Provide a short description of the current area or a hinted area.
        This method returns a short narrative string the assistant can read aloud.
        """
        # Simple deterministic descriptions; you can replace with a more complex generator later.
        descriptions = {
            "current": "You stand at the edge of a misty forest. To the north, a ruined watchtower pierces the fog. Distant howls echo to the east.",
            "village": "The village is quiet, smoke rising from a single chimney. Villagers whisper about strange lights near the old well.",
            "ruins": "Stone pillars and collapsed halls. The air tastes of dust and old magic. Something glints within a collapsed arch.",
        }
        text = descriptions.get(area_hint, descriptions["current"])
        return {"ok": True, "description": text}

    @function_tool
    async def perform_action(self, context: RunContext, action: str, target: str = "") -> dict:
        """
        Execute a simple action and return a short narrative result.
        Actions: move, attack, sneak, loot, inspect, use.
        """
        action = (action or "").strip().lower()
        if not action:
            return {"ok": False, "message": "No action provided."}

        # Simplified, deterministic outcomes for demo purposes
        if action == "move":
            result = f"You move toward {target or 'the waypoint'}. The terrain is uneven but passable."
        elif action == "attack":
            # small chance to simulate different outcomes - deterministic here
            result = f"You attack {target or 'the enemy'}. A solid hit — the foe staggers."
        elif action == "sneak":
            result = f"You creep forward, staying low. Your footsteps are muffled; you avoid immediate detection."
        elif action == "loot":
            # pretend to find a small reward
            found = "potion_small"
            await self.add_item_to_inventory(context, found, 1, notes="looted")
            result = f"You search the area and find a small health potion."
        elif action == "inspect":
            result = f"You carefully inspect {target or 'your surroundings'}. You notice faint tracks leading north."
        elif action == "use":
            # using an item from inventory reduces quantity
            entry = self._find_inventory_entry(target)
            if not entry:
                return {"ok": False, "message": f"You don't have {target!r} to use."}
            entry["quantity"] -= 1
            if entry["quantity"] <= 0:
                self.inventory = [e for e in self.inventory if e["quantity"] > 0]
            result = f"You use {entry['name']}. Effects apply immediately."
        else:
            result = f"Action '{action}' is not recognized by the Game Master."

        return {"ok": True, "result": result, "inventory": self._inventory_summary()}

    # Keep other utility methods as needed for future expansion


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Attach logging fields
    ctx.log_context_fields = {"room": ctx.room.name}

    # Connect to room
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=google.beta.GeminiTTS(
            model="gemini-2.5-flash-preview-tts",
            voice_name="Zephyr",
            instructions=(
                "Speak like a cinematic, immersive Game Master assistant. "
                "Tone: energetic, tactical, clear. Use short punchy lines suitable for voice."
            ),
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
    )

    # Metrics
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        logger.info(f"Usage summary: {usage_collector.get_summary()}")

    ctx.add_shutdown_callback(log_usage)

    # Start the Game Master session
    await session.start(
        agent=GameMasterAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
    )

    # Initial cinematic welcome
    await session.generate_reply(
        instructions=(
            "Introduce yourself as the player's Game Master with a short cinematic welcome "
            "and then ask what the player would like: 'brief' for mission briefing, 'explore' to scout, "
            "or 'inventory' to check gear."
        )
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
