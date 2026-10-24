"""Asking Gemini about a scan. See ../chat.py for what it is told.

Every failure becomes a ChatError with fixed text. Nothing from the provider's reply, and never the API key, is passed on
or logged. The call is made from the server, so the key stays in .env.
"""

from __future__ import annotations

import logging

from google import genai
from google.genai import errors, types

from ..chat import MAX_REPLY_CHARS, REFUSAL_REPLY, SYSTEM_PROMPT, build_turns

log = logging.getLogger(__name__)

# Room for the model's thinking as well as a short answer.
MAX_OUTPUT_TOKENS = 8192
# Under gunicorn's 120 second timeout, so a slow call ends here and not as a killed worker.
TIMEOUT_SECONDS = 90

# Reasons Gemini gives for declining to answer.
DECLINED = frozenset(
    {types.FinishReason.SAFETY, types.FinishReason.BLOCKLIST, types.FinishReason.PROHIBITED_CONTENT, types.FinishReason.SPII}
)


class ChatError(Exception):
    def __init__(self, message: str, code: str, status: int) -> None:
        super().__init__(message)
        self.message, self.code, self.status = message, code, status


def unavailable() -> ChatError:
    return ChatError("Chat isn't working on this server right now. Nothing has been changed.", "chat_unavailable", 503)


def busy() -> ChatError:
    return ChatError("The assistant is busy right now. Wait a moment and try again. Nothing has been changed.", "chat_busy", 429)


def failed() -> ChatError:
    return ChatError("We couldn't get an answer just now. Try again in a moment. Nothing has been changed.", "chat_failed", 502)


def _problem(error: errors.APIError) -> ChatError:
    """The ChatError for a Gemini error. Only the status is logged: the message could repeat what we sent."""
    # Gemini answers a bad key with 400 and a reason in the details, not with 401. 402 means the key's project has no
    # billing set up. None of these fix themselves, so it isn't a "try again in a moment".
    if error.code in (401, 402, 403) or "API_KEY_INVALID" in str(error.details):
        log.error("Gemini won't answer for this key (status %s, %s)", error.code, error.status)
        return unavailable()
    if error.code in (429, 503):  # out of quota, or the model is overloaded
        return busy()
    log.error("Gemini returned status %s (%s)", error.code, error.status)
    return failed()


class Assistant:
    """Answers questions about one scan. `client` is for tests; otherwise it talks to Gemini with `api_key`."""

    def __init__(self, api_key: str | None, model: str, client: genai.Client | None = None) -> None:
        self.model = model
        self.client = client or genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_SECONDS * 1000))

    def reply(self, scan: dict, history: list[dict]) -> str:
        """The assistant's answer to the last message in `history`. Raises ChatError when it can't."""
        contents = [
            types.Content(
                role="model" if turn["role"] == "assistant" else "user",
                parts=[types.Part(text=text) for text in turn["texts"]],
            )
            for turn in build_turns(scan, history)
        ]
        config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, max_output_tokens=MAX_OUTPUT_TOKENS)
        try:
            response = self.client.models.generate_content(model=self.model, contents=contents, config=config)
        except errors.APIError as problem:
            raise _problem(problem) from None
        except Exception as problem:  # noqa: BLE001 - a dropped connection or a timeout; the message isn't logged
            log.error("Couldn't get an answer from Gemini (%s)", type(problem).__name__)
            raise failed() from None

        candidate = response.candidates[0] if response.candidates else None
        if (response.prompt_feedback and response.prompt_feedback.block_reason) or (candidate and candidate.finish_reason in DECLINED):
            return REFUSAL_REPLY
        text = (response.text or "").strip()
        if not text:
            log.error("Gemini returned no text (finish reason %s)", getattr(candidate and candidate.finish_reason, "name", None))
            raise failed()
        return text if len(text) <= MAX_REPLY_CHARS else text[: MAX_REPLY_CHARS - 1].rstrip() + "…"
