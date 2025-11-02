import datetime
import json
from typing import Any

import boto3

from doc_redaction.agent import MODEL_IDS
from doc_redaction.utils.commons import InvalidContentType

bedrock_runtime = boto3.client("bedrock-runtime")

INPUT_TYPES: tuple = ("inputTokens", "outputTokens")

_COST_RATES: dict[str, float] = {
    "amazon.nova-lite-v1:0_inputTokens": 0.078 / 1_000_000,
    "amazon.nova-lite-v1:0_outputTokens": 0.0195 / 1_000_000,
    "anthropic.claude-haiku-4-5-20251001-v1:0_inputTokens": 0.25 / 1_000_000,
    "anthropic.claude-haiku-4-5-20251001-v1:0_outputTokens": 1.25 / 1_000_000,
    "anthropic.claude-sonnet-4-20250514-v1:0_inputTokens": 3.0 / 1_000_000,
    "anthropic.claude-sonnet-4-20250514-v1:0_outputTokens": 15.0 / 1_000_000,
    "anthropic.claude-sonnet-4-5-20250929-v1:0_inputTokens": 3.3 / 1_000_000,
    "anthropic.claude-sonnet-4-5-20250929-v1:0_outputTokens": 16.5 / 1_000_000,
}


def summarize_token_usage(all_agents_tokens: dict[str, dict[str, Any]]) -> str:
    totals: dict[str, dict[str, Any]] = {}

    for token_type in INPUT_TYPES:
        token_sum = 0
        cost_sum = 0.0
        for agent_data in all_agents_tokens.values():
            td = agent_data.get(token_type, {})
            token_sum += td.get("tokens", 0)
            cost_sum += td.get("costs", 0.0)

        totals[token_type] = {"total_tokens": token_sum, "total_costs": cost_sum}

    grand_totals: dict[str, Any] = {
        "tokens": sum(v["total_tokens"] for v in totals.values()),
        "costs": sum(v["total_costs"] for v in totals.values()),
    }

    summary: dict[str, Any] = {"token_type": totals, "grand_total": grand_totals}

    return json.dumps(summary)


def token_usage(content: str | dict[str, Any], model: str = MODEL_IDS["default"], token_type: str = "outputTokens") -> dict[str, dict[str, Any]]:
    """Calculate token usage for the entire workflow."""

    if isinstance(content, str):
        content = {token_type: content}
    elif isinstance(content, dict):
        content = content

    token_usage: dict[str, dict[str, Any]] = {
        input_type: count_tokens(
            content=tokens,
            token_type=input_type,
            model=model,
        )
        for input_type, tokens in content.items()
        if input_type in ["inputTokens", "outputTokens"]
    }

    return token_usage


def count_tokens(
    content: str | int,
    model: str = MODEL_IDS["default"],
    token_type: str = "outputTokens",
) -> dict[str, Any]:
    """
    Count tokens for model input and estimate cost using Bedrock.

    If content is a string, constructs an Anthropic-style Bedrock request and calls
    bedrock_runtime.count_tokens. If content is an integer, it is treated as a
    precomputed token count.

    Args:
        content: User content to tokenize (str) or a precomputed token count (int).
        model: Model id from MODEL_IDS to use for counting.
        token_type: Pricing category to apply when computing cost, either "input" or "output".

    Returns:
        A dict containing:
            - timestamp: Measurement timestamp string.
            - model_id: The model id used.
            - tokens: The total token count.
            - costs: Estimated cost for the given model and token_type.
    Example:
        agent_output_in = count_tokens(content=convert_result.metrics.accumulated_usage["inputTokens"])
        agent_output_out = count_tokens(content=convert_result.metrics.accumulated_usage["outputTokens"])
        structured_output = count_tokens(content=detector_result, token_type="output")
    """

    if isinstance(content, str):
        input_to_count = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": content}],
        })

        response: dict[str, Any] = bedrock_runtime.count_tokens(modelId=model.removeprefix("eu."), input={"invokeModel": {"body": input_to_count}})

        tokens: int = response["inputTokens"]

    elif isinstance(content, int):
        tokens: int = content

    else:
        raise InvalidContentType(type(content))

    timestamp: str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%ms")

    costs: float = _calculate_token_cost(token=tokens, model=model, token_type=token_type)

    result: dict[str, Any] = {
        "timestamp": timestamp,
        "model_id": model,
        "token_type": token_type,
        "tokens": tokens,
        "costs": costs,
    }

    return result


def _calculate_token_cost(token: int, model: str = MODEL_IDS["default"], token_type: str = "outputTokens") -> float:
    """
    Estimate the token cost for a given model and token type using per‑million token rates.

    Parameters:
    - token (int): Number of tokens to bill (non-negative).
    - model (str): Model ID used to infer provider ("anthropic" or "amazon"); defaults to MODEL_IDS["default"]. The ID must follow the "eu.<provider>..." pattern.
    - token_type (Literal["input", "output"]): Direction of tokens; defaults to "output".

    Returns:
    - float: Estimated cost based on rates per 1,000,000 tokens (anthropic: input=3, output=15; amazon: input=0.96, output=3.84).

    Raises:
    - KeyError: If the provider cannot be derived from the model ID or the combination is unsupported.

    Example:
        cost = _calculate_token_cost(token=1500, model="eu.anthropic.claude-sonnet-4-20250514-v1:0", token_type="output")
    """

    cost_category: str = f"{model.removeprefix('eu.')}_{token_type}"

    return token * _COST_RATES[cost_category]
