from collections.abc import Sequence
from typing import Any

from loguru import logger
from strands import Agent
from strands.models import BedrockModel
from strands.models.ollama import OllamaModel

from doc_redaction.utils.commons import MissingArgumentError, ParameterTypeError

MODEL_IDS: dict[str, str] = {
    "default": "eu.anthropic.claude-sonnet-4-20250514-v1:0",
    "sonnet4_5": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "haiku": "eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    "nova_lite": "eu.amazon.nova-lite-v1:0",
    "nova_pro": "eu.amazon.nova-pro-v1:0",
}
REGION: str = "eu-central-1"

bedrock_model: BedrockModel = BedrockModel(
    model_id=MODEL_IDS["default"],
    region_name=REGION,
    streaming=False,
    temperature=0,
    cache_prompt="default",
    cache_tools="default",
    max_tokens=64000,
)


def create_agent(
    system_prompt: str,
    name: str | None = "Strands Agent",
    model: BedrockModel | OllamaModel | None = bedrock_model,
    tools: Sequence[str | dict[str, str] | Any] | None = None,
    output_model: Any | None = None,
) -> Agent:
    """
    Create and return a configured Agent.

    - system_prompt: Required non-empty instructional prompt.
    - name: Optional agent name (default: "Strands Agent").
    - model: Optional model. Falls back to default bedrock_model if None.
    - tools: Optional iterable of tool specs/objects. Converted internally to a list.
    - output_model: Optional structured output model for the agent.

    Raises:
        MissingArgumentError: If system_prompt is missing or empty.
        TypeError: If system_prompt is not a string.
    """
    if not isinstance(system_prompt, str):
        raise ParameterTypeError("system_prompt", "a string")
    if not system_prompt.strip():
        raise MissingArgumentError("system_prompt")

    # Fallback to default model if none provided
    if model is None:
        model = bedrock_model

    # Normalize tools to a list (avoid mutable default pitfalls)
    tools_list: list[str | dict[str, str] | Any] | None = list(tools) if tools else None

    agent: Agent = Agent(
        model=model,
        system_prompt=system_prompt.strip(),
        tools=tools_list,
        structured_output_model=output_model,
    )

    if type(model) is BedrockModel:
        agent.name = name

    logger.info(
        "Agent created successfully",
        extra={
            "agent_name": name,
            "model_id": getattr(model, "model_id", "unknown"),
            "tools_count": len(tools_list) if tools_list else 0,
        },
    )

    return agent
