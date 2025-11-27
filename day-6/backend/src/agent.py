# agent.py
import logging
import json
import os
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Dict

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
    tokenize,
    llm,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# Database file path (placed in backend working directory)
DB_PATH = Path("fraud_bank.db")

# ---------------------------------------------------------------------
# Database utilities: ensure DB exists and seeded with example data
# ---------------------------------------------------------------------
def ensure_db():
    """Create DB and seed sample data if it doesn't exist."""
    created = False
    if not DB_PATH.exists():
        created = True

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        account_number TEXT UNIQUE,
        mother_name TEXT,
        mother_fav_color TEXT
    );
    """)

    # transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        location TEXT,
        timestamp TEXT,
        is_flagged INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    conn.commit()

    # If new DB, seed with sample users + transactions
    if created:
        seed_sample_data(conn)

    conn.close()
    if created:
        logger.info("Created and seeded fraud_bank.db")
    else:
        logger.info("fraud_bank.db exists (ensured schema)")

def seed_sample_data(conn: sqlite3.Connection):
    cursor = conn.cursor()
    users = [
        ("Rahul Kumar", "1234567890", "Sunita", "Blue"),
        ("Amit Verma", "2345678901", "Kavita", "Red"),
        ("Sneha Patil", "3456789012", "Meena", "Green"),
        ("Priya Sharma", "4567890123", "Lata", "Yellow"),
        ("Vivek Singh", "5678901234", "Rekha", "Purple")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO users (name, account_number, mother_name, mother_fav_color)
    VALUES (?, ?, ?, ?)
    """, users)

    locations = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad",
        "Pune", "Chennai", "Kolkata", "Ahmedabad",
        "Jaipur", "Noida"
    ]

    # Add a few deterministic flagged transactions for testing
    now = datetime.now()
    for user_id in range(1, 6):
        # one high-value flagged transaction
        cursor.execute("""
        INSERT INTO transactions (user_id, amount, location, timestamp, is_flagged)
        VALUES (?, ?, ?, ?, 1)
        """, (user_id, random.randint(30000, 90000), random.choice(locations),
              (now - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d %H:%M:%S")))

        # 4 more recent non-flagged transactions
        for j in range(4):
            cursor.execute("""
            INSERT INTO transactions (user_id, amount, location, timestamp, is_flagged)
            VALUES (?, ?, ?, ?, 0)
            """, (user_id, random.randint(500, 20000), random.choice(locations),
                  (now - timedelta(days=random.randint(5, 40))).strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()


# ---------------------------------------------------------------------
# The Agent: Bank Fraud Alert Voice Assistant
# ---------------------------------------------------------------------
class BankFraudAssistant(Agent):
    def __init__(self) -> None:
        # ensure DB exists and seeded
        ensure_db()

        # Provide clear, concise system instructions for banking/fraud checking
        instructions = f"""You are a Bank Fraud Alert Voice Assistant for a retail bank.
Your primary role is to:
- Verify a customer's identity using short security questions (account number, mother's name, mother's favourite color).
- Retrieve and read suspicious (flagged) transactions from the bank database.
- Ask the customer if they recognise each flagged transaction.
- If the customer denies a transaction, mark it as fraud and suggest blocking the card / escalating to fraud ops.
- If the customer confirms it, mark the transaction as valid and close the alert.
- Never give medical, legal, or unrelated advice. Keep responses short, professional, and transactional.
- If you are unsure whether to escalate, ask the customer to confirm and then escalate if they deny authorization.

When interacting, follow this conversation flow:
1. Greet user briefly.
2. Ask for account number.
3. Ask for mother's name.
4. Ask for mother's favourite color.
5. Verify identity via the verify_identity tool.
6. If verification succeeds: fetch flagged transactions via list_flagged_transactions tool and present them one-by-one, asking the user: "Do you recognise this transaction of <amount> at <location> on <timestamp>?"
   - If user says "No" or similar: call mark_transaction(..., "fraud") and respond: "Understood — I've marked this as fraudulent and will block the card and escalate to fraud operations. Please contact your bank for further assistance."
   - If user says "Yes": call mark_transaction(..., "valid") and respond: "Thanks — I've marked this as valid. No further action required for this transaction."
7. If verification fails: politely inform the user and suggest contacting customer support for identity issues.
8.When asking the user for identity details (account number, mother’s name, favourite color):
- Extract only the clean value.
- Do NOT include extra words like “my mother’s name is…”.
- Always transform the user’s answer into exact short string parameters for the tool call.

Example:
User: “My mother’s name is Sunita”
Tool call → mother_name="Sunita"

Always be concise and do not reveal any internal system details.
"""

        super().__init__(instructions=instructions)

    # -------------------------
    # Function tools for the LLM to call
    # -------------------------
    @function_tool
    async def verify_identity(self, context: RunContext, account_number: str, mother_name: str, favorite_color: str):
        """
        Verifies the user's identity against the local SQLite DB.
        Returns a dict: {"ok": bool, "user_id": int | None, "message": str}
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, name FROM users
                WHERE account_number = ? AND lower(mother_name) = lower(?) AND lower(mother_fav_color) = lower(?)
            """, (account_number, mother_name.strip(), favorite_color.strip()))
            row = cur.fetchone()
            conn.close()
            if row:
                user_id, name = row[0], row[1] if len(row) > 1 else None
                return {"ok": True, "user_id": user_id, "message": f"Identity verified for account {account_number}."}
            else:
                return {"ok": False, "user_id": None, "message": "Identity verification failed. Please check the details."}
        except Exception as e:
            logger.exception("verify_identity error")
            return {"ok": False, "user_id": None, "message": f"Error verifying identity: {str(e)}"}

    @function_tool
    async def list_flagged_transactions(self, context: RunContext, account_number: str):
        """
        Returns a list of flagged transactions for the given account number.
        Each item: {"id": int, "amount": float, "location": str, "timestamp": str}
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id, t.amount, t.location, t.timestamp
                FROM transactions t
                JOIN users u ON u.user_id = t.user_id
                WHERE u.account_number = ? AND t.is_flagged = 1
                ORDER BY t.timestamp DESC
            """, (account_number,))
            rows = cur.fetchall()
            conn.close()

            transactions = [{"id": r[0], "amount": float(r[1]), "location": r[2], "timestamp": r[3]} for r in rows]
            if not transactions:
                return {"transactions": [], "message": "No flagged transactions found for this account."}
            return {"transactions": transactions, "message": f"Found {len(transactions)} flagged transaction(s)."}
        except Exception as e:
            logger.exception("list_flagged_transactions error")
            return {"transactions": [], "message": f"Error fetching transactions: {str(e)}"}

    @function_tool
    async def mark_transaction(self, context: RunContext, transaction_id: int, action: str):
        """
        Mark a transaction as 'fraud' or 'valid'.
        action should be "fraud" or "valid".
        """
        try:
            if action not in ("fraud", "valid"):
                return {"ok": False, "message": "Invalid action. Use 'fraud' or 'valid'."}

            new_flag = 1 if action == "fraud" else 0
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("UPDATE transactions SET is_flagged = ? WHERE id = ?", (new_flag, transaction_id))
            conn.commit()
            conn.close()
            verb = "marked as fraudulent" if action == "fraud" else "marked as valid"
            return {"ok": True, "message": f"Transaction {transaction_id} {verb}."}
        except Exception as e:
            logger.exception("mark_transaction error")
            return {"ok": False, "message": f"Error updating transaction: {str(e)}"}

    @function_tool
    async def get_recent_transactions(self, context: RunContext, account_number: str, limit: int = 5):
        """
        Optional helper: return recent transactions (flagged or not) for context.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id, t.amount, t.location, t.timestamp, t.is_flagged
                FROM transactions t
                JOIN users u ON u.user_id = t.user_id
                WHERE u.account_number = ?
                ORDER BY t.timestamp DESC
                LIMIT ?
            """, (account_number, limit))
            rows = cur.fetchall()
            conn.close()
            txs = [{"id": r[0], "amount": float(r[1]), "location": r[2], "timestamp": r[3], "is_flagged": bool(r[4])} for r in rows]
            return {"transactions": txs}
        except Exception as e:
            logger.exception("get_recent_transactions error")
            return {"transactions": [], "message": f"Error fetching recent transactions: {str(e)}"}


# ---------------------------------------------------------------------
# LiveKit prewarm + entrypoint (mostly same as original pipeline)
# ---------------------------------------------------------------------
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Add any other context you want in logs
    ctx.log_context_fields = {"room": ctx.room.name}

    # Start agent session: STT, LLM, TTS, VAD, turn detection
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Metrics handling
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Create the agent instance (this will ensure DB exists)
    agent = BankFraudAssistant()

    # Start the session and join the room
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
