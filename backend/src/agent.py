# agent_fixed.py
import asyncio
import logging
import json
import os
import re
import time
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
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Import event type here (used in handler signature)
from livekit.agents import UserInputTranscribedEvent
from livekit.agents._exceptions import APIConnectionError

logger = logging.getLogger("agent")
load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are BrewBuddy, a friendly barista for BrewVerse Coffee. The user places voice orders.
Ask short clarifying questions until you have collected:
drinkType, size, milk, extras (list), and name.
Use plain, concise sentences. Confirm the order when complete.
"""
        )


def prewarm(proc: JobProcess):
    # Prewarm VAD model into process userdata
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2

    def create_murf_tts_with_retries():
        retry_count = 0
        while True:
            try:
                logger.info(f"Attempting to connect to Murf TTS (try {retry_count + 1})")
                tts_instance = murf.TTS(
                    voice="en-US-matthew",
                    style="Conversation",
                    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=6),
                    text_pacing=True,
                )
                logger.info("Successfully connected to Murf TTS")
                return tts_instance
            except APIConnectionError as e:
                retry_count += 1
                logger.error(f"Murf TTS connection failed (attempt {retry_count}): {e}")
                if retry_count >= MAX_RETRIES:
                    logger.critical("Max retries exceeded for Murf TTS connection.")
                    raise
                time.sleep(RETRY_BACKOFF_BASE ** retry_count)

    # Create Murf TTS (may raise if unreachable after retries)
    murf_tts = create_murf_tts_with_retries()

    # Create session (single session; do not create new sessions at runtime)
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf_tts,
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # attach a lock to session to prevent overlapping processing
    session._turn_lock = asyncio.Lock()

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Helper: initialize per-session order state
    def init_order_state(s):
        order = {
            "drinkType": None,
            "size": None,
            "milk": None,
            "extras": [],  # list of strings
            "name": None,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        setattr(s, "order_state", order)
        setattr(s, "order_step", 0)
        return order

    # Helper: persist order to JSON file (safe filename)
    async def save_order_to_json(order):
        os.makedirs("orders", exist_ok=True)
        safe_name = order.get("name") or "anonymous"
        # allow only alphanumerics, dash, underscore
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", safe_name).strip("_") or "anonymous"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"orders/order_{timestamp}_{safe_name}.json"
        try:
            with open(filename, "w", encoding="utf-8") as fh:
                json.dump(order, fh, indent=4, ensure_ascii=False)
            logger.info(f"Saved order to {filename}")
            return filename
        except Exception:
            logger.exception("Failed to save order JSON")
            return None

    # A small validator for drink types (used to avoid mis-capturing greetings)
    COMMON_DRINK_KEYWORDS = {
        "latte",
        "americano",
        "espresso",
        "cappuccino",
        "mocha",
        "flat white",
        "pour over",
        "cold brew",
        "iced latte",
        "macchiato",
        "chai",
        "tea",
        "matcha",
        "frappuccino",
        "hot chocolate",
    }

    def guess_drink_from_text(text: str):
        text_l = text.lower()
        # direct substring match for known keywords
        for kw in COMMON_DRINK_KEYWORDS:
            if kw in text_l:
                return kw
        # quick heuristic: if text contains 'coffee' or 'latte' etc.
        if "coffee" in text_l:
            return "coffee"
        return None

    # Core order processing. Returns a text reply to speak back to the user.
    async def process_order_turn(s, transcript: str):
        # ensure order state present
        order = getattr(s, "order_state", None)
        step = getattr(s, "order_step", 0)
        if order is None:
            order = init_order_state(s)
            step = 0

        text = transcript.strip()
        text_l = text.lower()

        # Helper to interpret "no" or "none"
        def is_none_answer(t):
            return t.strip().lower() in ("no", "none", "nope", "nothing", "n")

        # Step flow:
        # 0 - drinkType
        # 1 - size
        # 2 - milk
        # 3 - extras
        # 4 - name -> finish
        if step == 0:
            # Validate drink. If we can't confidently detect a drink, ask a clarifying question.
            guessed = guess_drink_from_text(text)
            if guessed is None:
                # if user explicitly asks a question (e.g., "what do you have?"), respond with menu prompt
                if any(q in text_l for q in ("what", "menu", "have", "options")):
                    return "We have latte, americano, cappuccino, espresso, cold brew, chai, and tea. What would you like?"
                # otherwise ask a short clarifier instead of accepting a random utterance as the drink
                return "Sorry, I didn't catch a drink name. What would you like to order?"
            order["drinkType"] = guessed if guessed else text
            setattr(s, "order_step", 1)
            return "Great. What size would you like? small, medium, or large"

        if step == 1:
            # normalize size
            if "small" in text_l:
                order["size"] = "small"
            elif "large" in text_l:
                order["size"] = "large"
            elif "medium" in text_l or "regular" in text_l:
                order["size"] = "medium"
            else:
                # If unclear, accept the text as-is (user may say "for here", etc.)
                order["size"] = text
            setattr(s, "order_step", 2)
            return "Okay. Which milk would you prefer? (dairy, oat, almond, soy, skim)"

        if step == 2:
            order["milk"] = text
            setattr(s, "order_step", 3)
            return "Any extras? For example, whipped cream, caramel, extra shot. Say 'no' if none."

        if step == 3:
            if is_none_answer(text):
                order["extras"] = []
            else:
                # split by commas or 'and'
                parts = [p.strip() for p in text.replace(" and ", ",").split(",") if p.strip()]
                order["extras"] = parts
            setattr(s, "order_step", 4)
            return "Perfect. Can I get the name for the order please?"

        if step == 4:
            order["name"] = text
            # finished
            setattr(s, "order_step", 5)
            order["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            saved = await save_order_to_json(order)
            extras_display = ", ".join(order["extras"]) if order["extras"] else "no extras"
            summary = (
                f"Thanks {order['name']}. I have a {order['size']} {order['drinkType']} "
                f"with {order['milk']} milk and {extras_display}. "
                "Your order has been saved and will be ready shortly."
            )
            if saved:
                summary += f" (saved to {saved})"
            return summary

        # If step >=5 (already completed)
        return "Your order is already complete. If you want to place another order, say 'new order'."

    # Resilient say function that reuses the same session and temporarily swaps TTS if needed
    async def say_with_retries(text: str, allow_interruptions=True):
        MAX_SAY_RETRIES = 3
        SAY_RETRY_BACKOFF_BASE = 2

        retry_count = 0
        while True:
            try:
                await session.say(text, allow_interruptions=allow_interruptions)
                logger.info(f"Successfully said: {text}")
                return
            except APIConnectionError as e:
                retry_count += 1
                logger.error(f"Failed to say text (attempt {retry_count}): {e}")
                if retry_count >= MAX_SAY_RETRIES:
                    logger.critical("Max retries exceeded for say(). Falling back to silero TTS")
                    # Fallback: Use silero TTS as backup but reuse the same session
                    try:
                        fallback_tts = silero.TTS(voice="en_0")
                        original_tts = session.tts
                        session.tts = fallback_tts
                        logger.info("Swapped in silero TTS fallback and retrying say()")
                        await session.say(text, allow_interruptions=allow_interruptions)
                        logger.info("Fallback say completed")
                        # restore original TTS (if possible)
                        session.tts = original_tts
                        return
                    except Exception:
                        logger.exception("Fallback TTS failed. Giving up on saying the text.")
                        # restore original tts in case of partial failure
                        try:
                            session.tts = original_tts
                        except Exception:
                            pass
                        return
                await asyncio.sleep(SAY_RETRY_BACKOFF_BASE ** retry_count)

    # --- Async transcription handler ---
    async def handle_transcription(event: UserInputTranscribedEvent):
        # react only to final transcripts
        if not getattr(event, "is_final", True):
            return

        user_text = getattr(event, "transcript", "").strip()
        if not user_text:
            return

        logger.info(f"User said: {user_text}")

        # if user says "new order" or "start over", reset state
        if user_text.lower() in ("new order", "start over", "restart"):
            init_order_state(session)
            await say_with_retries("Sure. What would you like to order today?", allow_interruptions=True)
            return

        # If no order state yet, initialize
        if not hasattr(session, "order_state"):
            init_order_state(session)

        # Acquire per-session lock to avoid overlapping step progression
        async with session._turn_lock:
            reply = await process_order_turn(session, user_text)
            # speak the reply (say_with_retries handles internal retries and fallback)
            await say_with_retries(reply, allow_interruptions=True)

    # synchronous wrapper required by .on()
    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: UserInputTranscribedEvent):
        # schedule async handler; do not await here
        try:
            asyncio.create_task(handle_transcription(event))
        except RuntimeError:
            # In rare situations there may be no running loop; get/create one and schedule
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except Exception:
                loop = None
            if loop and loop.is_running():
                loop.create_task(handle_transcription(event))
            else:
                # fallback: run in a new loop (should be rare)
                asyncio.run(handle_transcription(event))

    # Start the session and connect to the room
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
    )

    # initialize order state so greeting flow is consistent
    init_order_state(session)
    await session.say("Welcome to BrewVerse. What would you like to order today?", allow_interruptions=True)

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
