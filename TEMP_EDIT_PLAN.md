Edit Plan for Improving Murf TTS Connection Handling in backend/src/agent.py

1. Import required exception classes from livekit.agents._exceptions if necessary (e.g. APIConnectionError).
2. Wrap the AgentSession initialization for the murf.TTS instance within a try-except block to catch APIConnectionError and log the failure clearly.
3. Implement a retry loop with a limited number of retries and exponential backoff delay around the murf.TTS connection setup.
4. Add detailed logging for each connection attempt, success, and failure, including the request_id if available from the caught exception.
5. If maximum retries are exceeded, log an unrecoverable error but prevent the entire agent session from crashing immediately.
6. Optionally, allow fallback to an alternative TTS like silero.TTS to allow continued operation.
7. Retain the rest of the AgentSession setup and event handling as is.
8. Test to confirm that transient Murf AI connection issues no longer cause session closure and improve observability of the problem.

Dependent files: backend/src/agent.py only.

Followup steps:
- Test locally with induced connection failures or by disabling network temporarily.
- Review logs for improved diagnostics and retry behavior.
- Optionally document environment variables/configuration for Murf AI usage.

This plan aims to improve robustness and observability of the Murf TTS component in the LiveKit Agent.

Next action: Wait for user confirmation to proceed with the edit plan.
