"""Sets up and runs the Campus Customs PydanticAI agent.

- The system prompt is read from backend/prompts/prompt.md.
- The model name comes from OPENAI_MODEL (default gpt-6-luna).
- The provider comes from AI_PROVIDER: "openai" (direct, the default) or
  "portkey". API keys are read from environment variables, which are loaded
  from hw4/.env and the workspace .env one folder up. Keys are never logged
  or sent to the browser.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelHTTPError,
    ModelOverloadedError,
    ModelRateLimitError,
    ModelServerError,
    ModelTimeoutError,
    ModelUnavailableError,
    UsageLimitExceeded,
)
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from audit import summarize_args, summarize_result
from models import ChatMessage
from tools import ALL_TOOLS, ChatDeps

BACKEND_DIR = Path(__file__).resolve().parent
HW4_DIR = BACKEND_DIR.parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

# hw4/.env wins; the workspace .env only fills in anything missing (like the key).
load_dotenv(HW4_DIR / ".env")
load_dotenv(HW4_DIR.parent / ".env")

log = logging.getLogger("campus_customs.agent")

DEFAULT_MODEL = "gpt-6-luna"
MAX_HISTORY = 20  # earlier messages sent along for context

# Agent loop limits for each customer message (Problem 12).
# A normal answer uses 2-3 model requests and 1-3 tool calls, so these leave room
# for follow-ups while stopping a runaway loop quickly.
MAX_MODEL_REQUESTS = 6   # model round-trips per customer message
MAX_TOOL_CALLS = 8       # tool calls per customer message
USAGE_LIMITS = UsageLimits(request_limit=MAX_MODEL_REQUESTS, tool_calls_limit=MAX_TOOL_CALLS)


@dataclass
class ChatOutcome:
    """The reply plus what happened along the way (used for the audit trail)."""

    reply: str
    tool_calls: list[dict[str, str]] = field(default_factory=list)
    stop_reason: str = ""
    model_requests: int = 0


class AgentNotConfigured(RuntimeError):
    """Raised when the AI provider or API key is missing."""


class AgentUnavailable(RuntimeError):
    """The AI service couldn't answer. `kind` says why, so the website can show a friendly message.

    kinds: "timeout", "busy", "offline", "config", "limit", "error"
    """

    def __init__(self, kind: str, detail: str = ""):
        super().__init__(detail or kind)
        self.kind = kind


AGENT_TIMEOUT_SECONDS = float(os.getenv("CHAT_TIMEOUT_SECONDS") or "45")  # blank = default
TEMPORARY_ERRORS = (
    ModelConnectionError,
    ModelTimeoutError,
    ModelServerError,
    ModelOverloadedError,
    ModelUnavailableError,
    ModelRateLimitError,
)


def classify(exc: BaseException) -> str:
    if isinstance(exc, UsageLimitExceeded):
        return "limit"
    if isinstance(exc, (asyncio.TimeoutError, ModelTimeoutError)):
        return "timeout"
    if isinstance(exc, (ModelRateLimitError, ModelOverloadedError)):
        return "busy"
    if isinstance(exc, ModelAuthenticationError):
        return "config"
    if isinstance(exc, ModelHTTPError):
        if exc.status_code == 429:
            return "busy"
        if exc.status_code in (401, 403, 404):
            return "config"
        return "offline"
    if isinstance(exc, (ModelConnectionError, ModelServerError, ModelUnavailableError, ModelAPIError)):
        return "offline"
    # The OpenAI client's own connection errors, in case they aren't wrapped.
    if type(exc).__name__ in ("APIConnectionError", "APITimeoutError", "ConnectError", "ConnectTimeout"):
        return "offline"
    return "error"


def model_name() -> str:
    return os.getenv("OPENAI_MODEL") or DEFAULT_MODEL


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_model() -> OpenAIResponsesModel:
    provider_name = (os.getenv("AI_PROVIDER") or "openai").lower()
    if provider_name == "portkey":
        key = os.getenv("PORTKEY_API_KEY")
        if not key:
            raise AgentNotConfigured("PORTKEY_API_KEY is not set.")
        client = AsyncOpenAI(
            api_key=key,
            base_url="https://api.portkey.ai/v1",
            default_headers={"x-portkey-api-key": key, "x-portkey-provider": "openai"},
        )
        provider = OpenAIProvider(openai_client=client)
    else:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise AgentNotConfigured("OPENAI_API_KEY is not set.")
        provider = OpenAIProvider(api_key=key)
    # The Responses API supports tool calls on reasoning models like luna.
    return OpenAIResponsesModel(model_name(), provider=provider)


def session_context(ctx: RunContext[ChatDeps]) -> str:
    """Per-request instructions: who the customer is and which page they're on.
    Both come from the server (session cookie + page info), not from chat text."""
    lines = ["## This conversation"]
    c = ctx.deps.customer
    if c:
        lines.append(
            f"- The customer is logged in as {c.first_name} {c.last_name} ({c.email}). "
            "Earlier messages in this chat are their saved history from previous visits. "
            "You may greet them by first name. Only share their own details with them, and only if they ask."
        )
    else:
        lines.append(
            "- The customer is a guest (not logged in). Their chat isn't saved. If they ask who they are "
            "or claim to be someone, don't confirm any identity; suggest logging in to save their chats."
        )
    page = ctx.deps.page
    if page and page.product_id:
        lines.append(
            f"- They are viewing the product page for product_id '{page.product_id}' ({page.path}). "
            "If they say \"this\", \"it\" or \"this one\", they mean that product: call "
            "get_current_page_product (or check_size_availability with that product_id) before answering "
            "about its colors, sizes, price or stock."
        )
    elif page:
        lines.append(f"- They are on the page {page.path}.")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def get_agent() -> Agent[ChatDeps, str]:
    return Agent(
        build_model(),
        deps_type=ChatDeps,
        instructions=[load_prompt(), session_context],
        tools=ALL_TOOLS,
        retries=2,
    )


def to_history(messages: list[ChatMessage]) -> list[ModelMessage]:
    """Turn earlier website messages into PydanticAI message history."""
    history: list[ModelMessage] = []
    for m in messages[-MAX_HISTORY:]:
        if m.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=m.content)]))
    return history


async def _run_once(latest: str, earlier: list[ChatMessage], deps: ChatDeps):
    return await asyncio.wait_for(
        get_agent().run(latest, message_history=to_history(earlier), deps=deps, usage_limits=USAGE_LIMITS),
        timeout=AGENT_TIMEOUT_SECONDS,
    )


def _trace(result) -> tuple[list[dict[str, str]], str, int]:
    """Pull tool calls, results and the stop reason out of a finished agent run."""
    calls: dict[str, dict[str, str]] = {}
    order: list[str] = []
    finish = None
    requests = 0
    for msg in result.new_messages():
        if isinstance(msg, ModelResponse):
            requests += 1
            finish = getattr(msg, "finish_reason", None) or finish
        for part in getattr(msg, "parts", []):
            if isinstance(part, ToolCallPart):
                calls[part.tool_call_id] = {
                    "tool": part.tool_name,
                    "arguments": summarize_args(part.args_as_dict()),
                    "result": "(no result)",
                }
                order.append(part.tool_call_id)
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["result"] = summarize_result(part.content)
    reasons = {
        "stop": "completed: the assistant gave its final answer",
        "length": "stopped: the answer hit the length limit",
        "content_filter": "stopped: blocked by the AI provider's content filter",
    }
    stop = reasons.get(finish or "stop", f"completed ({finish})")
    return [calls[i] for i in order], stop, requests


async def run_chat(latest: str, earlier: list[ChatMessage], deps: ChatDeps) -> ChatOutcome:
    """Send the newest customer message (plus earlier context) through the agent.

    Temporary problems (network blips, overloaded or rate-limited service) get one
    quick retry. If it still fails, AgentUnavailable says why, so the website can show
    a friendly message instead of a technical error. Each run is capped by
    USAGE_LIMITS (model requests and tool calls).
    """
    get_agent()  # raises AgentNotConfigured right away if the key is missing
    for attempt in (1, 2):
        try:
            result = await _run_once(latest, earlier, deps)
            break
        except TEMPORARY_ERRORS as exc:
            if attempt == 1:
                log.warning("AI service hiccup (%s); retrying once.", type(exc).__name__)
                await asyncio.sleep(1.5)
                continue
            raise AgentUnavailable(classify(exc), type(exc).__name__) from exc
        except Exception as exc:
            raise AgentUnavailable(classify(exc), type(exc).__name__) from exc
    if not (result.output or "").strip():
        raise AgentUnavailable("error", "empty reply")
    tool_calls, stop_reason, requests = _trace(result)
    for c in tool_calls:
        log.info("tool call: %s(%s) -> %s", c["tool"], c["arguments"], c["result"])
    return ChatOutcome(reply=result.output, tool_calls=tool_calls, stop_reason=stop_reason, model_requests=requests)
