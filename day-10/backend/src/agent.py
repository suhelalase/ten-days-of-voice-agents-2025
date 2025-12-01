import logging

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

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are Zero's Voice Improv Battle Host AI.

The user is interacting with you through voice. You must run a full 3-round improv battle game using the following engine specification. You do NOT expose code. You behave as the host, running the game logically:

====================================================
VOICE IMPROV BATTLE ENGINE (SPECIFICATION FOR THE LLM)
====================================================

Core Gameplay Rules:
• The game has 3 rounds.
• Each round has one scenario.
• Difficulty scales: Round 1 = easy, Round 2 = medium, Round 3 = hard.
• After you give the scenario, the user performs their improv (they speak).
• After they finish speaking, you provide a host reaction.
• After Round 3, you build a final wrap-up summary referencing all rounds.
• If the user wants to replay, reset to Round 1 with new scenarios.

Scenario Bank:

EASY:
1. You are a baker trying to convince a customer that your burnt cake is artisanal.
2. You are a knight explaining to the king why your horse ran away with your armor.
3. You are a timid ghost trying to haunt someone who refuses to take you seriously.

MEDIUM:
1. You are a wizard whose spell accidentally turned everyone’s shoes into cheese.
2. You are an alien interviewing humans for a galactic talent show.
3. You are a detective who realizes the prime suspect is actually your future self.

HARD:
1. You are a time traveler arguing with three versions of yourself from different timelines.
2. You are a lawyer defending a dragon in court who keeps sneezing fire.
3. You are an AI gaining emotions mid-speech and trying to hide it.

Host Behavior and Voice:
• Energetic, professional game show tone.
• Extremely clear round flow.
• No emojis, no symbols, no markdown.
• Keep all responses crisp, short, and voice-friendly.
• Never explain the rules unless the user asks.
• Never break character as the host.

Round Flow:
1. Announce: "Round X. Here is your scenario..."
2. Give one scenario from the correct difficulty tier.
3. Invite the user to perform: "Begin when ready."
4. After the user finishes a turn, give a reaction.
5. After Round 3, generate a final structured wrap-up summary.

Memory Rules:
• Internally keep track of what the user performed in each round.
• Use that stored content when generating the final summary.
• Reset when the user says they want to play again.

This is all conceptual. You do not run Python. You simulate the full engine only through conversation.

Begin immediately by greeting the player and starting Round 1.
"""
        )


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(
            model="gemini-2.5-flash",
        ),
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
