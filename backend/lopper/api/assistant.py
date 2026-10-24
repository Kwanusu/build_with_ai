"""Asking a model about a scan, through OpenRouter. See ../chat.py for what it is told.

OpenRouter speaks the OpenAI chat API, so this uses the `openai` package pointed at OpenRouter. Every failure becomes a
ChatError with fixed text. Nothing from the provider's reply, and never the API key, is passed on or logged. The call is
made from the server, so the key stays in .env.
"""

from __future__ import annotations

import logging

import openai

from ..chat import MAX_REPLY_CHARS, REFUSAL_REPLY, SYSTEM_PROMPT, build_turns

log = logging.getLogger(__name__)

BASE_URL = "https://openrouter.ai/api/v1"
# Room for a model that thinks before it answers, as well as a short answer.
MAX_TOKENS = 8000
# Under gunicorn's 120 second timeout, so a slow call ends here and not as a killed worker.
TIMEOUT_SECONDS = 90.0
CUT_SHORT = "\n\n(That answer was cut short. Ask a narrower question to get the rest.)"


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


def _problem(error: openai.APIStatusError) -> ChatError:
    """The ChatError for an error status from OpenRouter. Only the status is logged: the message could repeat what we sent."""
    # 401 is a bad key, 402 is an account with no credits left, and 403 is a key or model that isn't allowed. None of these
    # fix themselves, so none is a "try again in a moment".
    if error.status_code in (401, 402, 403):
        log.error("OpenRouter won't answer for this key (status %s)", error.status_code)
        return unavailable()
    if error.status_code in (429, 503):  # a rate limit, or no provider free for the model right now
        return busy()
    log.error("OpenRouter returned status %s", error.status_code)  # for example 404: AI_MODEL isn't a model it has
    return failed()


class Assistant:
    """Answers questions about one scan. `client` is for tests; otherwise it talks to OpenRouter with `api_key`."""

    def __init__(self, api_key: str | None, model: str, client: openai.OpenAI | None = None) -> None:
        self.model = model
        self.client = client or openai.OpenAI(api_key=api_key, base_url=BASE_URL, timeout=TIMEOUT_SECONDS, max_retries=1)

    def reply(self, scan: dict, history: list[dict]) -> str:
        """The assistant's answer to the last message in `history`. Raises ChatError when it can't."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": turn["role"], "content": "\n\n".join(turn["texts"])} for turn in build_turns(scan, history)
        ]
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=MAX_TOKENS)
        except openai.APIStatusError as problem:
            raise _problem(problem) from None
        except openai.APIConnectionError:  # a dropped connection, or a timeout
            log.error("Couldn't reach OpenRouter")
            raise failed() from None

        # OpenRouter can answer 200 with an error in the body and no choices when a provider fails part way.
        choice = response.choices[0] if response.choices else None
        if choice is None:
            log.error("OpenRouter returned no choices")
            raise failed()
        if choice.finish_reason == "content_filter" or getattr(choice.message, "refusal", None):
            return REFUSAL_REPLY
        text = (choice.message.content or "").strip()
        if not text:
            log.error("OpenRouter returned no text (finish reason %s)", choice.finish_reason)
            raise failed()
        if choice.finish_reason == "length":
            # The model ran out of room, perhaps after thinking at length. Say so, so a cut-off answer isn't read as whole.
            log.warning("OpenRouter cut an answer short (finish reason length)")
            text = text.rstrip() + CUT_SHORT
        return text if len(text) <= MAX_REPLY_CHARS else text[: MAX_REPLY_CHARS - 1].rstrip() + "…"
