from typing import Any

from loguru import logger
from strands import Agent
from strands.models import BedrockModel

from doc_redaction.utils import MissingArgumentError

DEFAULT_MODEL_ID: str = "eu.anthropic.claude-sonnet-4-20250514-v1:0"
REGION: str = "eu-central-1"

bedrock_model = BedrockModel(
    model_id=DEFAULT_MODEL_ID,
    region_name=REGION,
    streaming=False,
)


def create_agent(
    system_prompt: str,
    model: BedrockModel = bedrock_model,
    tools: list[str | dict[str, str] | Any] | None = None,
) -> Agent:
    """
    Create and return a configured Agent.

    Initializes a strands Agent with the provided BedrockModel, system prompt, optional callback handler, and tools.

    Parameters:
    - model: BedrockModel powering the Agent.
    - system_prompt: Instructional prompt guiding the Agent.
    - callback_handler: Optional callback handler; defaults to the standard handler.
    - tools: Optional list of tool names, specs, or tool objects to register.

    Returns:
    - Agent: The initialized Agent instance.

    Raises:
    - ValueError: If model or system_prompt is not provided.

    Example:
    ```python
    agent = create_agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
    )
    ```
    """
    if not model:
        raise MissingArgumentError("model")
    if not system_prompt:
        raise MissingArgumentError("system_prompt")

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
    )
    logger.info("Agent created successfully.")

    return agent
